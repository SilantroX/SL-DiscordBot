"""
Módulo de Autoroles Interactivos (cogs/roles.py).
------------------------------------------------
Permite a los usuarios auto-asignarse y removerse roles de forma interactiva y sin saturar el chat:
- Paneles públicos persistentes con botón interactivo [🎭 Seleccionar Roles].
- Menús desplegables efímeros (StringSelect con multi-selección min_values=0, max_values=N).
- Pre-selección visual automática: el usuario ve marcados en el menú los roles que ya posee.
- Sincronización atómica de roles (adición de nuevos, remoción de desmarcados).
- Comprobación estricta de jerarquía de roles para evitar errores 403 Forbidden.
- Comandos administrativos para crear paneles, añadir y eliminar opciones de roles.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

import database.queries as queries
from utils.embeds import EmbedBuilder, EmbedColors

logger = logging.getLogger("bot.roles")


# ==============================================================================
# 1. GENERADOR DE EMBED DEL PANEL PÚBLICO DE AUTOROLES
# ==============================================================================

def build_role_panel_embed(
    title: str,
    description: Optional[str],
    options: List[Dict[str, Any]],
    guild: discord.Guild,
    menu_id: Optional[int] = None,
) -> discord.Embed:
    """Construye el embed informativo del panel público de autoroles."""
    embed = discord.Embed(
        title=f"🎭 {title}",
        description=description or "Haz clic en el botón de abajo para elegir o modificar tus roles de interés.",
        color=EmbedColors.ROLES,
        timestamp=datetime.now(timezone.utc),
    )

    if options:
        lines: List[str] = []
        for opt in options:
            role = guild.get_role(opt["role_id"])
            mention = role.mention if role else f"`[Rol eliminado ID: {opt['role_id']}]`"
            emoji = f"{opt['emoji']} " if opt.get("emoji") else "• "
            desc = f" — *{opt['description']}*" if opt.get("description") else ""
            lines.append(f"{emoji}**{opt['label']}** ({mention}){desc}")
        embed.add_field(name="📋 Roles Disponibles en este Panel", value="\n".join(lines), inline=False)
    else:
        embed.add_field(
            name="📋 Roles Disponibles en este Panel",
            value="*Aún no se han configurado roles en este panel. Un administrador debe usar `/autorol_agregar_opcion`.*",
            inline=False,
        )

    footer_id = f"ID de Panel: {menu_id} • " if menu_id else ""
    embed.set_footer(text=f"{footer_id}Bot Discord • Sistema de Autoroles")
    return embed


# ==============================================================================
# 2. VISTA Y SELECTOR DESPLEGABLE EFÍMERO
# ==============================================================================

class RoleSelectDropdown(discord.ui.Select):
    """Menú desplegable multi-selección efímero para asignar o remover roles."""

    def __init__(self, select_options: List[discord.SelectOption], menu_id: int) -> None:
        super().__init__(
            placeholder="Selecciona tus roles (puedes elegir varios)...",
            min_values=0,
            max_values=len(select_options),
            options=select_options,
            custom_id=f"temp:role_select_menu_{menu_id}",
        )
        self.menu_id = menu_id

    async def callback(self, interaction: discord.Interaction) -> None:
        """Procesa la selección de roles del usuario y sincroniza con Discord."""
        guild = interaction.guild
        member = interaction.user

        if not guild or not isinstance(member, discord.Member):
            return

        # Verificar permisos del bot
        if not guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Error de Permisos",
                    "El bot no tiene permisos de `Gestionar Roles` en este servidor.",
                ),
                ephemeral=True,
            )
            return

        # 1. Obtener todas las opciones registradas en este menú
        options = await queries.get_menu_options(self.menu_id)
        if not options:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Error", "Este panel ya no contiene roles configurados."),
                ephemeral=True,
            )
            return

        # IDs seleccionadas por el usuario en el menú desplegable
        selected_role_ids = {int(val) for val in self.values}
        # IDs totales que gestiona este panel
        panel_role_ids = {opt["role_id"] for opt in options}
        # IDs que el miembro actualmente tiene de este panel
        current_member_panel_roles = {r.id for r in member.roles if r.id in panel_role_ids}

        # Roles que deben ser añadidos (seleccionados pero que no tenía)
        to_add_ids = selected_role_ids - current_member_panel_roles
        # Roles que deben ser removidos (pertenecían al panel, ya los tenía, pero no fueron seleccionados)
        to_remove_ids = current_member_panel_roles - selected_role_ids

        added_roles: List[str] = []
        removed_roles: List[str] = []
        failed_roles: List[str] = []

        # Procesar adiciones
        for rid in to_add_ids:
            role = guild.get_role(rid)
            if not role:
                continue
            if guild.me.top_role <= role:
                failed_roles.append(role.name)
                continue
            try:
                await member.add_roles(role, reason=f"Autoroles: seleccionado por {member.name}")
                added_roles.append(role.mention)
            except discord.HTTPException as exc:
                logger.error("Error al asignar rol %s a %s: %s", role.name, member.name, exc)
                failed_roles.append(role.name)

        # Procesar remociones
        for rid in to_remove_ids:
            role = guild.get_role(rid)
            if not role:
                continue
            if guild.me.top_role <= role:
                failed_roles.append(role.name)
                continue
            try:
                await member.remove_roles(role, reason=f"Autoroles: desmarcado por {member.name}")
                removed_roles.append(role.mention)
            except discord.HTTPException as exc:
                logger.error("Error al remover rol %s de %s: %s", role.name, member.name, exc)
                failed_roles.append(role.name)

        # 2. Reconstruir las opciones del Select con los nuevos estados 'default'
        updated_member_roles = {r.id for r in member.roles}
        # Actualizar con los que acabamos de añadir y quitar
        updated_member_roles = (updated_member_roles | {int(r.split('&')[1].replace('>', '')) for r in added_roles if '&' in r}) - to_remove_ids

        new_select_options: List[discord.SelectOption] = []
        for opt in options:
            role = guild.get_role(opt["role_id"])
            if not role:
                continue
            has_role = role.id in selected_role_ids
            new_select_options.append(
                discord.SelectOption(
                    label=opt["label"][:100],
                    value=str(opt["role_id"]),
                    description=opt.get("description")[:100] if opt.get("description") else None,
                    emoji=opt.get("emoji"),
                    default=has_role,
                )
            )

        # 3. Crear embed de respuesta y actualizar la vista
        embed = discord.Embed(
            title="🎭 Sincronización de Roles Completada",
            color=EmbedColors.SUCCESS if not failed_roles else EmbedColors.WARNING,
            timestamp=datetime.now(timezone.utc),
        )

        embed.add_field(
            name="✅ Roles Asignados",
            value=", ".join(added_roles) if added_roles else "*Ninguno nuevo*",
            inline=True,
        )
        embed.add_field(
            name="❌ Roles Removidos",
            value=", ".join(removed_roles) if removed_roles else "*Ninguno retirado*",
            inline=True,
        )

        if failed_roles:
            embed.add_field(
                name="⚠️ Errores de Jerarquía",
                value=f"No se pudieron modificar: {', '.join(failed_roles)} (el rol del bot debe estar por encima).",
                inline=False,
            )

        # Roles que tiene actualmente en este panel
        active_panel_roles = [f"<@&{rid}>" for rid in selected_role_ids]
        embed.add_field(
            name="📋 Tus Roles Actuales en este Panel",
            value=", ".join(active_panel_roles) if active_panel_roles else "*No tienes ningún rol asignado de este panel.*",
            inline=False,
        )

        # Actualizar el componente con los nuevos defaults
        new_view = RoleDropdownView(new_select_options, self.menu_id)
        await interaction.response.edit_message(embed=embed, view=new_view)


class RoleDropdownView(discord.ui.View):
    """Vista efímera contenedora del menú desplegable de selección de roles."""

    def __init__(self, options: List[discord.SelectOption], menu_id: int) -> None:
        super().__init__(timeout=180)
        self.add_item(RoleSelectDropdown(options, menu_id))


# ==============================================================================
# 3. VISTA PERSISTENTE DEL PANEL PÚBLICO
# ==============================================================================

class RolePanelPersistentView(discord.ui.View):
    """
    Vista fija con botón que permanece activa tras reinicios.
    Al pulsarse, abre un menú selector efímero personalizado para el usuario.
    """

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Seleccionar Roles",
        style=discord.ButtonStyle.primary,
        emoji="🎭",
        custom_id="persistent:role_select_button",
    )
    async def open_role_menu(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Abre el menú desplegable efímero mostrando los roles preseleccionados del miembro."""
        guild = interaction.guild
        member = interaction.user
        message = interaction.message

        if not guild or not message or not isinstance(member, discord.Member):
            return

        # 1. Comprobar si el menú está registrado en BD
        menu = await queries.get_role_menu_by_message_id(message.id)
        if not menu:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Panel No Encontrado",
                    "Este panel de autoroles no está registrado en la base de datos o fue eliminado.",
                ),
                ephemeral=True,
            )
            return

        # 2. Obtener las opciones de roles
        options = await queries.get_menu_options(menu["menu_id"])
        if not options:
            await interaction.response.send_message(
                embed=EmbedBuilder.warning(
                    "Sin Roles Disponibles",
                    "Aún no se han configurado roles en este panel. Notifica a un administrador.",
                ),
                ephemeral=True,
            )
            return

        # 3. Construir opciones del Select marcando por defecto los roles que el usuario ya tiene
        select_options: List[discord.SelectOption] = []
        user_role_ids = {r.id for r in member.roles}

        for opt in options:
            role = guild.get_role(opt["role_id"])
            if not role:
                continue  # Rol borrado en Discord

            has_role = role.id in user_role_ids
            select_options.append(
                discord.SelectOption(
                    label=opt["label"][:100],
                    value=str(opt["role_id"]),
                    description=opt.get("description")[:100] if opt.get("description") else None,
                    emoji=opt.get("emoji"),
                    default=has_role,
                )
            )

        if not select_options:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Roles No Disponibles",
                    "Ninguno de los roles configurados en este panel existe actualmente en el servidor.",
                ),
                ephemeral=True,
            )
            return

        dropdown_view = RoleDropdownView(select_options, menu["menu_id"])
        embed = discord.Embed(
            title=f"🎭 Selección de Roles • {menu['title']}",
            description=(
                "Utiliza el menú desplegable de abajo para elegir qué roles deseas tener.\n"
                "• Los roles que ya posees aparecen marcados por defecto.\n"
                "• Puedes marcar varios roles al mismo tiempo.\n"
                "• Si desmarcas un rol, te será retirado automáticamente."
            ),
            color=EmbedColors.ROLES,
        )
        await interaction.response.send_message(embed=embed, view=dropdown_view, ephemeral=True)


# ==============================================================================
# 4. COG PRINCIPAL DE AUTOROLES
# ==============================================================================

class RolesCog(commands.Cog, name="Autoroles"):
    """Gestión y configuración de paneles de autoroles interactivos."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Registra la vista persistente del panel para que funcione tras reinicios."""
        self.bot.add_view(RolePanelPersistentView())
        logger.info("✅ Vista persistente de Autoroles registrada correctamente.")

    # ==========================================================================
    # COMANDO /setup_autoroles
    # ==========================================================================

    @app_commands.command(
        name="setup_autoroles",
        description="Publica un nuevo panel interactivo de autoroles en el canal indicado.",
    )
    @app_commands.describe(
        canal="Canal donde se publicará el panel de autoroles.",
        titulo="Título temático del panel (ej. Notificaciones, Videojuegos, Idiomas).",
        descripcion="Instrucciones o descripción que aparecerá en el panel.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_autoroles_command(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        titulo: str,
        descripcion: Optional[str] = None,
    ) -> None:
        """Crea el mensaje con vista persistente y registra el panel en la base de datos."""
        guild = interaction.guild
        if not guild:
            return

        # Validar permisos del bot en el canal
        bot_perms = canal.permissions_for(guild.me)
        if not (bot_perms.send_messages and bot_perms.embed_links):
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Permisos Insuficientes",
                    f"El bot necesita permisos de `Enviar Mensajes` e `Insertar Enlaces` en {canal.mention}.",
                ),
                ephemeral=True,
            )
            return

        if not guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Permiso Faltante",
                    "El bot necesita el permiso global de `Gestionar Roles` para administrar autoroles.",
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 1. Enviar mensaje del panel con la vista persistente
        initial_embed = build_role_panel_embed(
            title=titulo,
            description=descripcion,
            options=[],
            guild=guild,
        )
        panel_view = RolePanelPersistentView()
        msg = await canal.send(embed=initial_embed, view=panel_view)

        # 2. Registrar en la base de datos
        menu_id = await queries.create_role_menu(
            guild_id=guild.id,
            channel_id=canal.id,
            message_id=msg.id,
            title=titulo,
            description=descripcion,
        )

        # 3. Actualizar embed con el ID asignado
        final_embed = build_role_panel_embed(
            title=titulo,
            description=descripcion,
            options=[],
            guild=guild,
            menu_id=menu_id,
        )
        await msg.edit(embed=final_embed, view=panel_view)

        # 4. Guardar canal en configuración
        await queries.update_guild_setting(guild.id, "roles_channel_id", canal.id)

        confirm_embed = EmbedBuilder.success(
            "Panel de Autoroles Creado",
            (
                f"El panel ha sido publicado con éxito en {canal.mention}.\n\n"
                f"• **ID del Panel:** `{menu_id}`\n"
                f"• **Título:** {titulo}\n\n"
                f"Para añadir roles a este panel, utiliza el comando:\n"
                f"`/autorol_agregar_opcion menu_id:{menu_id} rol:@Rol etiqueta:Nombre`"
            ),
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /autorol_agregar_opcion
    # ==========================================================================

    @app_commands.command(
        name="autorol_agregar_opcion",
        description="Añade un rol seleccionable a un panel existente de autoroles.",
    )
    @app_commands.describe(
        menu_id="ID numérico del panel de autoroles.",
        rol="Rol de Discord que el usuario podrá auto-asignarse.",
        etiqueta="Nombre legible que aparecerá en el menú desplegable.",
        emoji="Emoji opcional para la opción (ej. 🎮, 💻).",
        descripcion="Descripción corta que aparecerá bajo la opción (máximo 100 caracteres).",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def autorol_agregar_opcion_command(
        self,
        interaction: discord.Interaction,
        menu_id: int,
        rol: discord.Role,
        etiqueta: str,
        emoji: Optional[str] = None,
        descripcion: Optional[str] = None,
    ) -> None:
        """Valida jerarquía y añade una opción al panel de autoroles."""
        guild = interaction.guild
        if not guild:
            return

        # 1. Comprobar existencia del panel
        menu = await queries.get_role_menu(menu_id)
        if not menu or menu["guild_id"] != guild.id:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Panel No Encontrado", f"No existe ningún panel con ID `{menu_id}` en este servidor."),
                ephemeral=True,
            )
            return

        # 2. Validaciones de Rol y Jerarquía
        if rol.is_default():
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Rol Inválido", "No es posible configurar el rol `@everyone` como autorol."),
                ephemeral=True,
            )
            return

        if rol.managed:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Rol Gestionado", "No puedes asignar roles gestionados automáticamente por bots o integraciones."),
                ephemeral=True,
            )
            return

        if guild.me.top_role <= rol:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Jerarquía Insuficiente",
                    f"Mi rol más alto ({guild.me.top_role.name}) no tiene suficiente jerarquía para gestionar {rol.mention}. "
                    "Coloca el rol del bot por encima de este rol en los ajustes de Discord.",
                ),
                ephemeral=True,
            )
            return

        # 3. Validar límite de 25 opciones por select menu
        existing_options = await queries.get_menu_options(menu_id)
        if len(existing_options) >= 25:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Límite Alcanzado",
                    "Un panel de autoroles no puede contener más de 25 roles debido al límite nativo de menús desplegables de Discord.",
                ),
                ephemeral=True,
            )
            return

        if any(opt["role_id"] == rol.id for opt in existing_options):
            await interaction.response.send_message(
                embed=EmbedBuilder.warning("Rol Duplicado", f"El rol {rol.mention} ya está agregado a este panel."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 4. Guardar en base de datos
        await queries.add_role_option(
            menu_id=menu_id,
            role_id=rol.id,
            label=etiqueta.strip()[:100],
            emoji=emoji.strip() if emoji else None,
            description=descripcion.strip()[:100] if descripcion else None,
        )

        # 5. Actualizar el mensaje público del panel
        updated_options = await queries.get_menu_options(menu_id)
        channel = guild.get_channel(menu["channel_id"])
        if isinstance(channel, discord.TextChannel):
            try:
                panel_msg = await channel.fetch_message(menu["message_id"])
                new_embed = build_role_panel_embed(
                    title=menu["title"],
                    description=menu["description"],
                    options=updated_options,
                    guild=guild,
                    menu_id=menu_id,
                )
                await panel_msg.edit(embed=new_embed, view=RolePanelPersistentView())
            except (discord.NotFound, discord.HTTPException) as exc:
                logger.warning("No se pudo actualizar el mensaje del panel #%s: %s", menu_id, exc)

        confirm_embed = EmbedBuilder.success(
            "Opción de Rol Añadida",
            (
                f"Se ha añadido con éxito {rol.mention} al panel `{menu['title']}`.\n\n"
                f"• **Etiqueta:** {etiqueta}\n"
                f"• **Emoji:** {emoji or 'Ninguno'}\n"
                f"• **Total de opciones en el panel:** {len(updated_options)}/25"
            ),
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /autorol_eliminar_opcion
    # ==========================================================================

    @app_commands.command(
        name="autorol_eliminar_opcion",
        description="Elimina una opción de rol de un panel de autoroles.",
    )
    @app_commands.describe(
        menu_id="ID numérico del panel de autoroles.",
        rol="Rol que deseas remover del panel.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def autorol_eliminar_opcion_command(
        self,
        interaction: discord.Interaction,
        menu_id: int,
        rol: discord.Role,
    ) -> None:
        """Elimina una opción y actualiza el mensaje público del panel."""
        guild = interaction.guild
        if not guild:
            return

        menu = await queries.get_role_menu(menu_id)
        if not menu or menu["guild_id"] != guild.id:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Panel No Encontrado", f"No existe el panel `{menu_id}` en este servidor."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        await queries.delete_role_option_by_role(menu_id, rol.id)

        # Actualizar panel público
        updated_options = await queries.get_menu_options(menu_id)
        channel = guild.get_channel(menu["channel_id"])
        if isinstance(channel, discord.TextChannel):
            try:
                panel_msg = await channel.fetch_message(menu["message_id"])
                new_embed = build_role_panel_embed(
                    title=menu["title"],
                    description=menu["description"],
                    options=updated_options,
                    guild=guild,
                    menu_id=menu_id,
                )
                await panel_msg.edit(embed=new_embed, view=RolePanelPersistentView())
            except (discord.NotFound, discord.HTTPException):
                pass

        embed = EmbedBuilder.success(
            "Opción Eliminada",
            f"El rol {rol.mention} ha sido retirado del panel `{menu['title']}`.",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /autorol_listar
    # ==========================================================================

    @app_commands.command(
        name="autorol_listar",
        description="Muestra la lista de paneles de autoroles activos en el servidor.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def autorol_listar_command(self, interaction: discord.Interaction) -> None:
        """Lista todos los paneles de autoroles creados en el servidor."""
        guild = interaction.guild
        if not guild:
            return

        menus = await queries.get_role_menus_by_guild(guild.id)
        if not menus:
            await interaction.response.send_message(
                embed=EmbedBuilder.info("Sin Paneles", "No hay paneles de autoroles configurados en este servidor."),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="📋 Paneles de Autoroles Registrados",
            color=EmbedColors.ROLES,
            timestamp=datetime.now(timezone.utc),
        )

        for m in menus:
            opts = await queries.get_menu_options(m["menu_id"])
            channel = guild.get_channel(m["channel_id"])
            ch_mention = channel.mention if channel else f"`Canal eliminado ({m['channel_id']})`"
            embed.add_field(
                name=f"ID #{m['menu_id']} • {m['title']}",
                value=f"• Canal: {ch_mention}\n• Opciones: **{len(opts)}/25** roles configurados\n• Mensaje ID: `{m['message_id']}`",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Función de entrada para registrar el Cog de Autoroles."""
    await bot.add_cog(RolesCog(bot))
