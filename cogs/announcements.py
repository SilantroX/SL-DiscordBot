"""
Módulo de Anuncios Oficiales (cogs/announcements.py).
----------------------------------------------------
Permite al equipo de Staff redactar y publicar anuncios oficiales de forma segura:
- Redacción desde canal privado mediante formulario interactivo (Modal).
- Vista previa de seguridad (Preview) con botones interactivos [🚀 Publicar] y [❌ Cancelar].
- Replicación y difusión automática en el canal público global configurado (#anuncios).
- Soporte para menciones opcionales (@everyone, @here o ninguna) y banners visuales.
- Registro histórico en base de datos SQLite y canal de auditoría (#mod-logs).
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import database.queries as queries
from utils.checks import is_staff_or_admin
from utils.embeds import EmbedBuilder, EmbedColors

logger = logging.getLogger("bot.announcements")


# ==============================================================================
# 1. VISTA DE CONFIRMACIÓN Y VISTA PREVIA
# ==============================================================================

class AnnouncementPreviewView(discord.ui.View):
    """
    Vista interactiva que despliega los controles de seguridad en el canal privado de staff:
    [🚀 Publicar Anuncio] o [❌ Cancelar].
    """

    def __init__(
        self,
        bot: commands.Bot,
        title: str,
        content: str,
        banner_url: Optional[str],
        mention_type: str,
        author_id: int,
    ) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.title = title
        self.content = content
        self.banner_url = banner_url
        self.mention_type = mention_type
        self.author_id = author_id

    async def _disable_all(self, interaction: discord.Interaction) -> None:
        """Desactiva todos los botones de la vista."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    async def on_timeout(self) -> None:
        """Desactiva los controles cuando expira el tiempo límite de confirmación (5 min)."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    @discord.ui.button(label="Publicar Anuncio", style=discord.ButtonStyle.success, emoji="🚀")
    async def confirm_publish(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Publica el anuncio en el canal público global y notifica el resultado."""
        guild = interaction.guild
        user = interaction.user

        if not guild or not isinstance(user, discord.Member):
            return

        # 1. Comprobar que solo el autor o un administrador pueda confirmar
        if user.id != self.author_id and not user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Acceso Denegado", "Solo el autor del borrador o un Administrador pueden confirmar la publicación."),
                ephemeral=True,
            )
            return

        # 2. Consultar canal global de anuncios configurado
        settings = await queries.get_guild_settings(guild.id)
        target_channel_id = settings.get("announcements_channel_id") if settings else None

        if not target_channel_id:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Canal No Configurado",
                    "No se ha configurado el canal público de anuncios. Un administrador debe usar `/setup_anuncios`.",
                ),
                ephemeral=True,
            )
            return

        target_channel = guild.get_channel(target_channel_id)
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Canal Inválido", "El canal de anuncios configurado no existe o no es accesible."),
                ephemeral=True,
            )
            return

        # 3. Construir embed definitivo
        author_member = guild.get_member(self.author_id)
        final_embed = EmbedBuilder.announcement(
            title=self.title,
            content=self.content,
            author=author_member,
            image_url=self.banner_url,
        )

        # 4. Determinar texto de mención
        mention_text = None
        if self.mention_type == "@everyone":
            mention_text = "@everyone"
        elif self.mention_type == "@here":
            mention_text = "@here"

        try:
            # 5. Publicar en el canal público de anuncios
            published_msg = await target_channel.send(content=mention_text, embed=final_embed)
        except discord.HTTPException as exc:
            logger.error("Error al enviar anuncio a %s: %s", target_channel.name, exc)
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Error de Publicación", f"No se pudo enviar el anuncio al canal: {exc}"),
                ephemeral=True,
            )
            return

        # 6. Registrar en la base de datos
        announcement_id = await queries.log_announcement(
            guild_id=guild.id,
            author_id=self.author_id,
            target_channel_id=target_channel.id,
            published_message_id=published_msg.id,
            title=self.title,
            content=self.content,
            mention_type=self.mention_type,
        )

        # 7. Registrar en el canal de auditoría #mod-logs si existe
        mod_logs_channel_id = settings.get("mod_logs_channel_id") if settings else None
        if mod_logs_channel_id:
            mod_logs_channel = guild.get_channel(mod_logs_channel_id)
            if isinstance(mod_logs_channel, discord.TextChannel):
                audit_embed = EmbedBuilder.info(
                    "📢 Anuncio Oficial Publicado",
                    (
                        f"• **Publicado por:** {user.mention} (`{user.id}`)\n"
                        f"• **Canal destino:** {target_channel.mention}\n"
                        f"• **Título:** {self.title}\n"
                        f"• **Mención:** `{self.mention_type}`\n"
                        f"• **ID de Registro:** `#{announcement_id}`\n\n"
                        f"[Ir al Anuncio Publicado]({published_msg.jump_url})"
                    ),
                )
                try:
                    await mod_logs_channel.send(embed=audit_embed)
                except Exception:
                    pass

        # 8. Desactivar botones y actualizar mensaje privado en el canal de staff
        await self._disable_all(interaction)
        success_embed = EmbedBuilder.success(
            "Anuncio Publicado Exitosamente",
            (
                f"El anuncio ha sido difundido correctamente en {target_channel.mention}.\n\n"
                f"• **Título:** {self.title}\n"
                f"• **Mención:** `{self.mention_type}`\n"
                f"• **Registro BD:** `#{announcement_id}`\n\n"
                f"[🚀 Haz clic aquí para ver el mensaje oficial]({published_msg.jump_url})"
            ),
        )
        await interaction.response.edit_message(content=None, embed=success_embed, view=self)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_publish(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Descarta la publicación del anuncio."""
        user = interaction.user
        if user.id != self.author_id and not (isinstance(user, discord.Member) and user.guild_permissions.administrator):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Acceso Denegado", "Solo el autor del borrador o un Administrador pueden cancelarlo."),
                ephemeral=True,
            )
            return

        await self._disable_all(interaction)
        cancel_embed = EmbedBuilder.warning(
            "Publicación Cancelada",
            f"El borrador del anuncio **'{self.title}'** fue descartado y no ha sido publicado.",
        )
        await interaction.response.edit_message(content=None, embed=cancel_embed, view=self)


# ==============================================================================
# 2. FORMULARIO MODAL DE REDACCIÓN DE ANUNCIOS
# ==============================================================================

class AnnouncementModal(discord.ui.Modal, title="📝 Redactar Anuncio Oficial"):
    """Formulario emergente interactivo para redactar el título, cuerpo e imagen del anuncio."""

    titulo = discord.ui.TextInput(
        label="Título del Anuncio",
        placeholder="Ej: Gran Torneo de la Comunidad • Apertura de Inscripciones",
        min_length=4,
        max_length=100,
        required=True,
    )

    contenido = discord.ui.TextInput(
        label="Contenido del Anuncio (Markdown)",
        style=discord.TextStyle.paragraph,
        placeholder="Escribe el cuerpo del anuncio. Puedes usar negritas, listas y enlaces en Markdown...",
        min_length=10,
        max_length=3000,
        required=True,
    )

    banner_url = discord.ui.TextInput(
        label="URL de Banner o Imagen (Opcional)",
        placeholder="https://i.imgur.com/ejemplo.png",
        required=False,
        max_length=300,
    )

    def __init__(self, bot: commands.Bot, mention_type: str = "none") -> None:
        super().__init__()
        self.bot = bot
        self.mention_type = mention_type

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Genera la vista previa en el canal privado de staff con controles interactivos."""
        guild = interaction.guild
        user = interaction.user
        if not guild or not isinstance(user, discord.Member):
            return

        # Validar URL de imagen si fue provista
        image_url: Optional[str] = self.banner_url.value.strip() if self.banner_url.value else None
        if image_url and not (image_url.startswith("http://") or image_url.startswith("https://")):
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "URL Inválida",
                    "La URL del banner debe comenzar con `http://` o `https://`.",
                ),
                ephemeral=True,
            )
            return

        # Crear embed de vista previa
        preview_embed = EmbedBuilder.announcement(
            title=self.titulo.value.strip(),
            content=self.contenido.value.strip(),
            author=user,
            image_url=image_url,
        )

        preview_view = AnnouncementPreviewView(
            bot=self.bot,
            title=self.titulo.value.strip(),
            content=self.contenido.value.strip(),
            banner_url=image_url,
            mention_type=self.mention_type,
            author_id=user.id,
        )

        content_warning = (
            f"👁️ **Vista Previa de Anuncio** (Mención configurada: `{self.mention_type}`)\n"
            f"*Verifica que el formato y contenido sean correctos antes de difundirlo públicamente.*"
        )
        await interaction.response.send_message(content=content_warning, embed=preview_embed, view=preview_view)


# ==============================================================================
# 3. COG PRINCIPAL DE ANUNCIOS
# ==============================================================================

class AnnouncementsCog(commands.Cog, name="Anuncios"):
    """Comandos para configuración, redacción y difusión de anuncios oficiales."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ==========================================================================
    # COMANDO /setup_anuncios
    # ==========================================================================

    @app_commands.command(
        name="setup_anuncios",
        description="Configura el canal público oficial donde se publicarán los anuncios.",
    )
    @app_commands.describe(canal="Canal público de texto destinado a los anuncios.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_anuncios_command(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
    ) -> None:
        """Guarda el canal de anuncios en la configuración del servidor."""
        guild = interaction.guild
        if not guild:
            return

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

        await queries.update_guild_setting(guild.id, "announcements_channel_id", canal.id)

        embed = EmbedBuilder.success(
            "Canal de Anuncios Configurado",
            (
                f"El canal {canal.mention} ha sido configurado como el canal oficial de anuncios.\n\n"
                f"Para redactar un anuncio desde un canal privado de moderación, usa el comando `/anuncio`."
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /anuncio
    # ==========================================================================

    @app_commands.command(
        name="anuncio",
        description="Abre el formulario para redactar un anuncio oficial desde un canal privado.",
    )
    @app_commands.describe(
        mencion="Mención opcional que acompañará el anuncio en el canal público.",
    )
    @app_commands.choices(
        mencion=[
            app_commands.Choice(name="Ninguna (Sin ping)", value="none"),
            app_commands.Choice(name="@here (Usuarios conectados)", value="@here"),
            app_commands.Choice(name="@everyone (Todos los miembros)", value="@everyone"),
        ]
    )
    async def anuncio_command(
        self,
        interaction: discord.Interaction,
        mencion: Optional[app_commands.Choice[str]] = None,
    ) -> None:
        """Despliega el modal de redacción de anuncio."""
        guild = interaction.guild
        member = interaction.user

        if not guild or not isinstance(member, discord.Member):
            return

        # 1. Comprobar permisos de Staff o Administrador
        settings = await queries.get_guild_settings(guild.id)
        staff_role_id = settings.get("staff_role_id") if settings else None

        if not is_staff_or_admin(member, staff_role_id=staff_role_id):
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Acceso Denegado",
                    "No tienes permisos de Staff o Administrador para redactar anuncios.",
                ),
                ephemeral=True,
            )
            return

        # 2. Comprobar que el canal oficial de anuncios esté configurado
        target_channel_id = settings.get("announcements_channel_id") if settings else None
        if not target_channel_id:
            await interaction.response.send_message(
                embed=EmbedBuilder.warning(
                    "Canal no Configurado",
                    "El canal de anuncios aún no ha sido asignado. Un administrador debe usar primero `/setup_anuncios`.",
                ),
                ephemeral=True,
            )
            return

        mencion_value = mencion.value if mencion else "none"

        # 3. Enviar formulario modal de redacción
        modal = AnnouncementModal(bot=self.bot, mention_type=mencion_value)
        await interaction.response.send_modal(modal)

    # ==========================================================================
    # COMANDO /anuncios_historial
    # ==========================================================================

    @app_commands.command(
        name="anuncios_historial",
        description="Muestra el registro de los últimos anuncios oficiales publicados.",
    )
    @app_commands.describe(limite="Cantidad de anuncios a mostrar (entre 1 y 15).")
    async def anuncios_historial_command(
        self,
        interaction: discord.Interaction,
        limite: Optional[app_commands.Range[int, 1, 15]] = 5,
    ) -> None:
        """Consulta el historial de anuncios en SQLite."""
        guild = interaction.guild
        member = interaction.user

        if not guild or not isinstance(member, discord.Member):
            return

        settings = await queries.get_guild_settings(guild.id)
        staff_role_id = settings.get("staff_role_id") if settings else None

        if not is_staff_or_admin(member, staff_role_id=staff_role_id):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Acceso Denegado", "Solo el Staff puede consultar el historial de anuncios."),
                ephemeral=True,
            )
            return

        announcements = await queries.get_announcements_by_guild(guild.id, limit=limite or 5)
        if not announcements:
            await interaction.response.send_message(
                embed=EmbedBuilder.info("Sin Anuncios", "No hay registros de anuncios oficiales publicados en este servidor."),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="📢 Historial de Anuncios Publicados",
            color=EmbedColors.ANNOUNCEMENT,
            timestamp=datetime.now(timezone.utc),
        )

        for a in announcements:
            author = guild.get_member(a["author_id"])
            author_name = author.display_name if author else f"ID {a['author_id']}"
            channel = guild.get_channel(a["target_channel_id"])
            ch_name = channel.mention if channel else f"Canal ID {a['target_channel_id']}"

            embed.add_field(
                name=f"#{a['announcement_id']} • {a['title']}",
                value=(
                    f"• **Autor:** {author_name}\n"
                    f"• **Canal:** {ch_name}\n"
                    f"• **Mención:** `{a['mention_type']}`\n"
                    f"• **Fecha:** `{a['created_at']}`"
                ),
                inline=False,
            )

        embed.set_footer(text="SilantroLabs • Auditoría de Anuncios")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Función de entrada para registrar el Cog de Anuncios."""
    await bot.add_cog(AnnouncementsCog(bot))
