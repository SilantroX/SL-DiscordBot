"""
Módulo de Tickets de Soporte (cogs/tickets.py).
----------------------------------------------
Sistema completo e interactivo de soporte al usuario:
- Vistas persistentes (Persistent Views) para paneles fijos que sobreviven a reinicios.
- Formularios modales (Modals) para solicitar motivo y descripción detallada.
- Canales privados automáticos con permisos dinámicos (PermissionOverwrites).
- Controles dentro del ticket: Reclamar atención, Confirmación de cierre y Transcripciones HTML estilo Discord.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import database.queries as queries
from utils.checks import is_staff_or_admin
from utils.embeds import EmbedBuilder, EmbedColors
from utils.transcript import generate_ticket_transcript

logger = logging.getLogger("bot.tickets")


# ==============================================================================
# 1. FORMULARIO MODAL PARA ABRIR TICKET
# ==============================================================================

class TicketCreateModal(discord.ui.Modal, title="📩 Abrir Ticket de Soporte"):
    """Formulario emergente interactivo que solicita el motivo y los detalles de la consulta."""

    asunto = discord.ui.TextInput(
        label="Asunto / Título corto",
        placeholder="Ej: Problemas con mi compra, reporte de usuario...",
        min_length=4,
        max_length=100,
        required=True,
    )

    descripcion = discord.ui.TextInput(
        label="Descripción detallada de tu caso",
        style=discord.TextStyle.paragraph,
        placeholder="Explica detalladamente qué ocurre para que el equipo pueda ayudarte...",
        min_length=10,
        max_length=1000,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Procesa el envío del modal creando el canal privado de soporte."""
        guild = interaction.guild
        user = interaction.user
        if not guild or not isinstance(user, discord.Member):
            return

        # Aplazar respuesta para tener tiempo de crear el canal y permisos
        await interaction.response.defer(ephemeral=True)

        # 1. Verificar si el usuario ya tiene un ticket abierto
        open_ticket = await queries.get_open_ticket_by_user(guild.id, user.id)
        if open_ticket:
            existing_ch = guild.get_channel(open_ticket["channel_id"])
            ch_mention = existing_ch.mention if existing_ch else f"`#{open_ticket['channel_id']}`"
            await interaction.followup.send(
                embed=EmbedBuilder.warning(
                    "Ticket Existente",
                    f"Ya tienes un ticket abierto actualmente en {ch_mention}. Por favor resuélvelo antes de abrir uno nuevo.",
                ),
                ephemeral=True,
            )
            return

        # 2. Obtener configuración del servidor
        settings = await queries.get_guild_settings(guild.id)
        category: Optional[discord.CategoryChannel] = None
        staff_role: Optional[discord.Role] = None

        if settings:
            if settings.get("ticket_category_id"):
                cat = guild.get_channel(settings["ticket_category_id"])
                if isinstance(cat, discord.CategoryChannel):
                    category = cat
            if settings.get("staff_role_id"):
                staff_role = guild.get_role(settings["staff_role_id"])

        # 3. Configurar permisos del canal privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True,
            ),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True,
                manage_messages=True,
            )

        # 4. Crear canal de texto
        clean_username = "".join(c for c in user.name.lower() if c.isalnum() or c in "-_")[:15]
        channel_name = f"ticket-{clean_username}-{user.id % 10000:04d}"

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket de soporte para {user.name} ({user.id}) | Asunto: {self.asunto.value}",
                reason=f"Apertura de ticket por {user.name}",
            )
        except discord.Forbidden:
            await interaction.followup.send(
                embed=EmbedBuilder.error(
                    "Error de Permisos",
                    "No tengo permisos suficientes para crear canales o configurar permisos en la categoría de tickets.",
                ),
                ephemeral=True,
            )
            return

        # 5. Registrar en la base de datos
        ticket_id = await queries.create_ticket(
            guild_id=guild.id,
            channel_id=ticket_channel.id,
            user_id=user.id,
            subject=self.asunto.value,
        )

        # 6. Enviar mensaje de bienvenida y controles en el canal del ticket
        welcome_embed = EmbedBuilder.base(
            title=f"🎫 Ticket #{ticket_id}: {self.asunto.value}",
            description=(
                f"¡Hola {user.mention}! Gracias por ponerte en contacto con el equipo de soporte.\n\n"
                f"**Asunto:** {self.asunto.value}\n"
                f"**Descripción:**\n{self.descripcion.value}\n\n"
                f"Un miembro del equipo de soporte te atenderá en breve. Mientras tanto, puedes detallar más información si lo deseas."
            ),
            color=EmbedColors.SUCCESS,
        )
        welcome_embed.set_thumbnail(url=user.display_avatar.url)
        welcome_embed.set_footer(text=f"Ticket ID: #{ticket_id} • Creado el")

        # Controles interactivos dentro del ticket
        control_view = TicketControlView()
        mention_target = staff_role.mention if staff_role else "@here"

        await ticket_channel.send(
            content=f"{user.mention} | {mention_target}",
            embed=welcome_embed,
            view=control_view,
        )

        # 7. Responder confirmación al usuario
        await interaction.followup.send(
            embed=EmbedBuilder.success(
                "Ticket Creado",
                f"Tu ticket ha sido creado correctamente en {ticket_channel.mention}.",
            ),
            ephemeral=True,
        )


# ==============================================================================
# 2. VISTA PERSISTENTE DEL PANEL PÚBLICO (BOTÓN 'ABRIR TICKET')
# ==============================================================================

class TicketPanelPersistentView(discord.ui.View):
    """Vista persistente que contiene el botón público para abrir tickets."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir Ticket",
        style=discord.ButtonStyle.primary,
        emoji="📩",
        custom_id="persistent:ticket_open_button",
    )
    async def open_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Despliega el modal de solicitud de soporte al usuario."""
        await interaction.response.send_modal(TicketCreateModal())


# ==============================================================================
# 3. VISTA DE CONTROLES DENTRO DEL CANAL DE TICKET
# ==============================================================================

class TicketControlView(discord.ui.View):
    """Controles interactivos disponibles en cada canal de soporte."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Reclamar",
        style=discord.ButtonStyle.secondary,
        emoji="🙋",
        custom_id="persistent:ticket_claim_button",
    )
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Permite a un miembro del staff asignarse la atención del ticket."""
        guild = interaction.guild
        member = interaction.user
        channel = interaction.channel
        if not guild or not isinstance(member, discord.Member) or not isinstance(channel, discord.TextChannel):
            return

        settings = await queries.get_guild_settings(guild.id)
        staff_role_id = settings.get("staff_role_id") if settings else None

        # Validar permisos de moderación o rol de staff
        if not is_staff_or_admin(member, staff_role_id):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Permiso Denegado", "Solo miembros del Staff pueden reclamar tickets."),
                ephemeral=True,
            )
            return

        # Registrar en la base de datos
        await queries.claim_ticket(channel.id, member.id)

        # Actualizar tema del canal
        current_topic = channel.topic or ""
        new_topic = f"{current_topic} | Atendido por: {member.display_name}"
        try:
            await channel.edit(topic=new_topic)
        except discord.Forbidden:
            pass

        embed = EmbedBuilder.info(
            "Ticket Reclamado",
            f"El miembro del Staff {member.mention} se ha asignado la atención de este ticket.",
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(
        label="Cerrar Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="persistent:ticket_close_button",
    )
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Despliega una confirmación de dos pasos antes de cerrar el ticket."""
        confirm_view = TicketCloseConfirmView()
        embed = EmbedBuilder.warning(
            "Confirmación de Cierre",
            "¿Estás seguro de que deseas cerrar este ticket? Se generará una transcripción y el canal se eliminará.",
        )
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

    @discord.ui.button(
        label="Transcripción",
        style=discord.ButtonStyle.primary,
        emoji="📄",
        custom_id="persistent:ticket_transcript_button",
    )
    async def transcript_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Genera y envía de inmediato la transcripción HTML en el canal."""
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return

        await interaction.response.defer(ephemeral=True)
        transcript_file = await generate_ticket_transcript(channel)

        await interaction.followup.send(
            content="📄 **Transcripción generada:**",
            file=transcript_file,
            ephemeral=True,
        )


# ==============================================================================
# 4. VISTA DE CONFIRMACIÓN DE CIERRE DE TICKET
# ==============================================================================

class TicketCloseConfirmView(discord.ui.View):
    """Cuadro de confirmación de 2 pasos para prevenir cierres accidentales."""

    def __init__(self) -> None:
        super().__init__(timeout=60)

    @discord.ui.button(label="Sí, cerrar ticket", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        channel = interaction.channel
        guild = interaction.guild
        user = interaction.user
        if not guild or not isinstance(channel, discord.TextChannel):
            return

        # Desactivar botones de la confirmación
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.response.edit_message(view=self)

        # Aviso de inicio de cierre
        close_embed = EmbedBuilder.error(
            "Ticket Cerrado",
            f"Ticket cerrado por {user.mention}.\nGenerando transcripción final y eliminando canal en `5` segundos...",
        )
        await channel.send(embed=close_embed)

        # 1. Obtener datos del ticket desde SQLite
        ticket_data = await queries.get_ticket_by_channel(channel.id)

        # 2. Generar archivo de transcripción HTML
        transcript_file = await generate_ticket_transcript(channel)

        # 3. Enviar copia de la transcripción a logs del servidor
        settings = await queries.get_guild_settings(guild.id)
        if settings and settings.get("ticket_logs_channel_id"):
            log_ch = guild.get_channel(settings["ticket_logs_channel_id"])
            if isinstance(log_ch, discord.TextChannel):
                t_owner = f"<@{ticket_data['user_id']}>" if ticket_data else "Desconocido"
                subject = ticket_data.get("subject", "N/A") if ticket_data else "N/A"
                log_embed = EmbedBuilder.info(
                    title="📁 Transcripción de Ticket Cerrado",
                    description=(
                        f"• **Canal:** `#{channel.name}`\n"
                        f"• **Creador:** {t_owner}\n"
                        f"• **Cerrado por:** {user.mention}\n"
                        f"• **Asunto:** {subject}"
                    ),
                )
                try:
                    await log_ch.send(embed=log_embed, file=transcript_file)
                except discord.Forbidden:
                    pass

        # 4. Enviar transcripción por mensaje directo al creador del ticket
        if ticket_data and ticket_data.get("user_id"):
            owner = guild.get_member(ticket_data["user_id"])
            if owner:
                try:
                    dm_file = await generate_ticket_transcript(channel)
                    dm_embed = EmbedBuilder.info(
                        title=f"Tu ticket en {guild.name} ha sido cerrado",
                        description=f"Adjuntamos el historial completo de tu consulta (Asunto: *{ticket_data.get('subject', 'Soporte')}*).",
                    )
                    await owner.send(embed=dm_embed, file=dm_file)
                except discord.Forbidden:
                    pass

        # 5. Actualizar estado en la base de datos
        await queries.close_ticket(channel.id)

        # 6. Cuenta regresiva y eliminación del canal
        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Ticket cerrado por {user.name}")
        except discord.NotFound:
            pass

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.response.edit_message(content="❌ Cierre de ticket cancelado.", embed=None, view=self)


# ==============================================================================
# 5. COG PRINCIPAL DE TICKETS
# ==============================================================================

class TicketsCog(commands.Cog, name="Tickets"):
    """Comandos de configuración y gestión de tickets de soporte."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Registra las vistas persistentes para que los botones sigan activos tras reinicios."""
        self.bot.add_view(TicketPanelPersistentView())
        self.bot.add_view(TicketControlView())
        logger.info("✅ Vistas persistentes de Tickets registradas correctamente.")

    # ==========================================================================
    # COMANDO /setup_tickets
    # ==========================================================================

    @app_commands.command(
        name="setup_tickets",
        description="Configura la categoría donde se crearán los tickets y el canal de logs.",
    )
    @app_commands.describe(
        categoria="Categoría de Discord donde se crearán los canales privados de tickets.",
        canal_logs="Canal de texto donde se archivarán las transcripciones de tickets cerrados.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets_command(
        self,
        interaction: discord.Interaction,
        categoria: discord.CategoryChannel,
        canal_logs: discord.TextChannel,
    ) -> None:
        """Guarda la categoría y el canal de logs de tickets en la base de datos."""
        guild = interaction.guild
        if not guild:
            return

        await queries.update_guild_setting(guild.id, "ticket_category_id", categoria.id)
        await queries.update_guild_setting(guild.id, "ticket_logs_channel_id", canal_logs.id)

        embed = EmbedBuilder.success(
            "Módulo de Tickets Configurado",
            (
                f"• **Categoría de Tickets:** {categoria.name} (`{categoria.id}`)\n"
                f"• **Canal de Transcripciones (Logs):** {canal_logs.mention}\n\n"
                f"Para desplegar el panel de soporte para usuarios, usa el comando `/ticket_panel`."
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /ticket_panel
    # ==========================================================================

    @app_commands.command(
        name="ticket_panel",
        description="Envía el panel público fijado con el botón interactivo para abrir tickets.",
    )
    @app_commands.describe(
        canal="Canal donde se publicará el panel (por defecto el canal actual).",
        titulo="Título personalizado del panel.",
        descripcion="Descripción o instrucciones del panel.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel_command(
        self,
        interaction: discord.Interaction,
        canal: Optional[discord.TextChannel] = None,
        titulo: Optional[str] = "Centro de Soporte y Ayuda",
        descripcion: Optional[str] = None,
    ) -> None:
        """Publica el embed con la vista persistente en el canal indicado."""
        target_channel = canal or interaction.channel
        guild = interaction.guild
        if not isinstance(target_channel, discord.TextChannel) or not guild:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Canal Inválido", "Debes especificar un canal de texto válido."),
                ephemeral=True,
            )
            return

        desc_default = (
            "¿Tienes dudas, problemas o necesitas comunicarte con el equipo de soporte?\n\n"
            "Haz clic en el botón de abajo **📩 Abrir Ticket** para iniciar una conversación privada con nuestro equipo."
        )
        embed = EmbedBuilder.base(
            title=f"🎫 {titulo}",
            description=descripcion or desc_default,
            color=EmbedColors.SUCCESS,
        )
        embed.set_footer(text=f"{guild.name} • Soporte Oficial")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        panel_view = TicketPanelPersistentView()
        await target_channel.send(embed=embed, view=panel_view)

        await interaction.response.send_message(
            embed=EmbedBuilder.success(
                "Panel Desplegado",
                f"El panel de tickets fue publicado correctamente en {target_channel.mention}.",
            ),
            ephemeral=True,
        )

    # ==========================================================================
    # COMANDO /ticket_add
    # ==========================================================================

    @app_commands.command(name="ticket_add", description="Agrega a un miembro adicional al canal del ticket actual.")
    @app_commands.describe(miembro="Miembro que tendrá acceso al ticket.")
    async def ticket_add_command(self, interaction: discord.Interaction, miembro: discord.Member) -> None:
        channel = interaction.channel
        guild = interaction.guild
        if not isinstance(channel, discord.TextChannel) or not guild:
            return

        ticket_data = await queries.get_ticket_by_channel(channel.id)
        if not ticket_data:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("No es un Ticket", "Este comando solo puede ejecutarse dentro de un canal de ticket activo."),
                ephemeral=True,
            )
            return

        await channel.set_permissions(
            miembro,
            view_channel=True,
            send_messages=True,
            attach_files=True,
            read_message_history=True,
        )

        embed = EmbedBuilder.success(
            "Miembro Añadido",
            f"{miembro.mention} ha sido añadido al ticket por {interaction.user.mention}.",
        )
        await interaction.response.send_message(embed=embed)

    # ==========================================================================
    # COMANDO /ticket_remove
    # ==========================================================================

    @app_commands.command(name="ticket_remove", description="Remueve a un miembro del ticket actual.")
    @app_commands.describe(miembro="Miembro al que se le revocará el acceso.")
    async def ticket_remove_command(self, interaction: discord.Interaction, miembro: discord.Member) -> None:
        channel = interaction.channel
        guild = interaction.guild
        if not isinstance(channel, discord.TextChannel) or not guild:
            return

        ticket_data = await queries.get_ticket_by_channel(channel.id)
        if not ticket_data:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("No es un Ticket", "Este comando solo puede ejecutarse dentro de un canal de ticket activo."),
                ephemeral=True,
            )
            return

        if ticket_data["user_id"] == miembro.id:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Acción Denegada", "No puedes remover al creador original del ticket."),
                ephemeral=True,
            )
            return

        await channel.set_permissions(miembro, overwrite=None)

        embed = EmbedBuilder.warning(
            "Miembro Removido",
            f"{miembro.mention} ha sido retirado del ticket por {interaction.user.mention}.",
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Función de entrada requerida por discord.py para cargar el Cog."""
    await bot.add_cog(TicketsCog(bot))
