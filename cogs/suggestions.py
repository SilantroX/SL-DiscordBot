"""
Módulo de Sugerencias Comunitarias (cogs/suggestions.py).
---------------------------------------------------------
Gestiona el ciclo de vida completo de las sugerencias del servidor:
- Publicación automática de sugerencias en el canal designado.
- Vistas interactivas persistentes con botones de votación (A favor / En contra).
- Lógica anti-spam: prevención de auto-votos y control de un voto por usuario (toggle y switch).
- Resolución administrativa del staff: Aprobación, Rechazo o Estado En Progreso con comentarios.
- Actualización dinámica de embeds y desactivación de votaciones al resolverse.
- Notificaciones privadas por DM al autor original cuando su sugerencia es evaluada.
"""

from __future__ import annotations

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import database.queries as queries
from utils.checks import is_staff_or_admin
from utils.embeds import EmbedBuilder, EmbedColors

logger = logging.getLogger("bot.suggestions")


# ==============================================================================
# 1. VISTA PERSISTENTE DE VOTACIÓN
# ==============================================================================

class SuggestionVoteView(discord.ui.View):
    """
    Vista interactiva persistente que contiene los botones de votación.
    Permanece activa tras reinicios del bot gracias a sus custom_id estáticos.
    """

    def __init__(self, disabled: bool = False) -> None:
        super().__init__(timeout=None)
        if disabled:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

    async def _handle_vote(self, interaction: discord.Interaction, vote_type: int) -> None:
        """Lógica común para procesar votos a favor (+1) o en contra (-1)."""
        guild = interaction.guild
        message = interaction.message
        user = interaction.user

        if not guild or not message:
            return

        # 1. Obtener la sugerencia correspondiente al mensaje
        suggestion = await queries.get_suggestion_by_message_id(message.id)
        if not suggestion:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Sugerencia No Encontrada",
                    "Esta sugerencia no está registrada en la base de datos del bot.",
                ),
                ephemeral=True,
            )
            return

        # 2. Verificar si la sugerencia aún está abierta
        if suggestion["status"] != "PENDING":
            await interaction.response.send_message(
                embed=EmbedBuilder.warning(
                    "Votación Cerrada",
                    f"Esta sugerencia ya ha sido resuelta con estado **{suggestion['status']}** y no admite nuevos votos.",
                ),
                ephemeral=True,
            )
            return

        # 3. Evitar que el autor vote en su propia sugerencia
        if suggestion["user_id"] == user.id:
            await interaction.response.send_message(
                embed=EmbedBuilder.warning(
                    "Acción No Permitida",
                    "No puedes votar en tu propia sugerencia.",
                ),
                ephemeral=True,
            )
            return

        # 4. Registrar o actualizar el voto en la base de datos
        upvotes, downvotes, action = await queries.record_suggestion_vote(
            suggestion["suggestion_id"],
            user.id,
            vote_type,
        )

        # 5. Obtener datos del autor para reconstruir el embed
        author = guild.get_member(suggestion["user_id"])
        if not author:
            try:
                author = await interaction.client.fetch_user(suggestion["user_id"])
            except Exception:
                author = None

        reviewer = None
        if suggestion["reviewed_by"]:
            reviewer = guild.get_member(suggestion["reviewed_by"])

        updated_embed = EmbedBuilder.suggestion(
            suggestion_id=suggestion["suggestion_id"],
            content=suggestion["content"],
            author=author,
            status=suggestion["status"],
            upvotes=upvotes,
            downvotes=downvotes,
            staff_comment=suggestion["staff_comment"],
            reviewer=reviewer,
        )

        # 6. Actualizar el mensaje original con el nuevo balance
        await message.edit(embed=updated_embed, view=self)

        # 7. Responder de forma privada al usuario confirmando la acción
        if action == "added":
            vote_label = "👍 **A favor**" if vote_type == 1 else "👎 **En contra**"
            desc = f"Has registrado tu voto: {vote_label}."
        elif action == "removed":
            desc = "Has retirado tu voto previamente emitido."
        else:  # switched
            vote_label = "👍 **A favor**" if vote_type == 1 else "👎 **En contra**"
            desc = f"Has cambiado tu voto a: {vote_label}."

        await interaction.response.send_message(
            embed=EmbedBuilder.success("Voto Registrado", desc),
            ephemeral=True,
        )

    @discord.ui.button(
        label="A favor",
        style=discord.ButtonStyle.success,
        emoji="👍",
        custom_id="persistent:suggestion_upvote",
    )
    async def upvote_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Botón para votar a favor (+1)."""
        await self._handle_vote(interaction, 1)

    @discord.ui.button(
        label="En contra",
        style=discord.ButtonStyle.danger,
        emoji="👎",
        custom_id="persistent:suggestion_downvote",
    )
    async def downvote_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Botón para votar en contra (-1)."""
        await self._handle_vote(interaction, -1)


# ==============================================================================
# 2. COG PRINCIPAL DE SUGERENCIAS
# ==============================================================================

class SuggestionsCog(commands.Cog, name="Sugerencias"):
    """Comandos para envío, votación y gestión de sugerencias de la comunidad."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Registra la vista persistente de votación para garantizar interactividad tras reinicios."""
        self.bot.add_view(SuggestionVoteView())
        logger.info("✅ Vista persistente de Votación de Sugerencias registrada correctamente.")

    # ==========================================================================
    # COMANDO /setup_suggestions
    # ==========================================================================

    @app_commands.command(
        name="setup_suggestions",
        description="Configura el canal oficial donde se publicarán y votarán las sugerencias.",
    )
    @app_commands.describe(canal="Canal de texto destinado a las sugerencias de la comunidad.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_suggestions_command(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
    ) -> None:
        """Guarda el canal de sugerencias en la configuración del servidor."""
        guild = interaction.guild
        if not guild:
            return

        bot_perms = canal.permissions_for(guild.me)
        if not (bot_perms.send_messages and bot_perms.embed_links):
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Permisos Insuficientes en el Canal",
                    f"El bot necesita permisos de `Enviar Mensajes` e `Insertar Enlaces` en {canal.mention}.",
                ),
                ephemeral=True,
            )
            return

        await queries.update_guild_setting(guild.id, "suggestions_channel_id", canal.id)

        embed = EmbedBuilder.success(
            "Canal de Sugerencias Configurado",
            f"El canal {canal.mention} ha sido asignado como el canal oficial de sugerencias.\n"
            f"Los usuarios pueden proponer ideas utilizando el comando `/sugerir`.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /sugerir
    # ==========================================================================

    @app_commands.command(
        name="sugerir",
        description="Envía una sugerencia para mejorar la comunidad o el servidor.",
    )
    @app_commands.describe(texto="Descripción detallada de la propuesta o sugerencia.")
    async def sugerir_command(self, interaction: discord.Interaction, texto: str) -> None:
        """Publica una nueva sugerencia con botones de votación interactivos."""
        guild = interaction.guild
        user = interaction.user
        if not guild or not isinstance(user, discord.Member):
            return

        # 1. Validar longitud mínima
        if len(texto.strip()) < 10:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Texto Demasiado Corto",
                    "Por favor proporciona una descripción más detallada (mínimo 10 caracteres).",
                ),
                ephemeral=True,
            )
            return

        # 2. Consultar canal configurado
        settings = await queries.get_guild_settings(guild.id)
        channel_id = settings.get("suggestions_channel_id") if settings else None

        if not channel_id:
            await interaction.response.send_message(
                embed=EmbedBuilder.warning(
                    "Canal no Configurado",
                    "El canal de sugerencias no ha sido configurado en este servidor. Un administrador debe usar `/setup_suggestions`.",
                ),
                ephemeral=True,
            )
            return

        target_channel = guild.get_channel(channel_id)
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Canal Inválido",
                    "El canal configurado para sugerencias no existe o no es accesible.",
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 3. Enviar mensaje inicial al canal para obtener el message_id
        placeholder_embed = EmbedBuilder.base(
            title="💡 Registrando sugerencia...",
            description=texto,
        )
        vote_view = SuggestionVoteView()
        msg = await target_channel.send(embed=placeholder_embed, view=vote_view)

        # 4. Registrar en base de datos
        sug_id = await queries.create_suggestion(
            guild_id=guild.id,
            message_id=msg.id,
            user_id=user.id,
            content=texto.strip(),
        )

        # 5. Generar embed definitivo con el ID asignado y autor
        final_embed = EmbedBuilder.suggestion(
            suggestion_id=sug_id,
            content=texto.strip(),
            author=user,
            status="PENDING",
            upvotes=0,
            downvotes=0,
        )
        await msg.edit(embed=final_embed, view=vote_view)

        # 6. Confirmar al autor
        confirm_embed = EmbedBuilder.success(
            "Sugerencia Publicada",
            f"Tu sugerencia **#{sug_id}** ha sido enviada exitosamente a {target_channel.mention}.\n"
            f"[Haz clic aquí para ver tu sugerencia]({msg.jump_url})",
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /responder_sugerencia (Staff)
    # ==========================================================================

    @app_commands.command(
        name="responder_sugerencia",
        description="Permite al Staff aprobar, rechazar o poner en desarrollo una sugerencia.",
    )
    @app_commands.describe(
        id="Número identificador de la sugerencia.",
        estado="Resolución oficial del equipo para la sugerencia.",
        comentario="Explicación o comentarios adicionales del Staff.",
    )
    @app_commands.choices(
        estado=[
            app_commands.Choice(name="Aprobada", value="APPROVED"),
            app_commands.Choice(name="Rechazada", value="REJECTED"),
            app_commands.Choice(name="En Progreso / En Desarrollo", value="IN_PROGRESS"),
        ]
    )
    async def responder_sugerencia_command(
        self,
        interaction: discord.Interaction,
        id: int,
        estado: app_commands.Choice[str],
        comentario: Optional[str] = None,
    ) -> None:
        """Actualiza el estado de una sugerencia, edita el embed y desactiva la votación."""
        guild = interaction.guild
        staff_member = interaction.user

        if not guild or not isinstance(staff_member, discord.Member):
            return

        # 1. Verificar permisos de Staff o Administrador
        settings = await queries.get_guild_settings(guild.id)
        staff_role_id = settings.get("staff_role_id") if settings else None
        if not is_staff_or_admin(staff_member, staff_role_id=staff_role_id):
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Acceso Denegado",
                    "No tienes permisos de Staff o Administrador para responder sugerencias.",
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 2. Buscar la sugerencia en la base de datos
        suggestion = await queries.get_suggestion(id)
        if not suggestion or suggestion["guild_id"] != guild.id:
            await interaction.followup.send(
                embed=EmbedBuilder.error(
                    "Sugerencia No Encontrada",
                    f"No existe ninguna sugerencia con el ID `#{id}` en este servidor.",
                ),
                ephemeral=True,
            )
            return

        # 3. Actualizar estado en la base de datos
        updated_sug = await queries.update_suggestion_status(
            suggestion_id=id,
            status=estado.value,
            staff_comment=comentario,
            reviewed_by=staff_member.id,
        )

        if not updated_sug:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Error", "No se pudo actualizar la sugerencia en la base de datos."),
                ephemeral=True,
            )
            return

        # 4. Actualizar el mensaje original en el canal de sugerencias si está disponible
        settings = await queries.get_guild_settings(guild.id)
        channel_id = settings.get("suggestions_channel_id") if settings else None

        if channel_id:
            channel = guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                try:
                    target_msg = await channel.fetch_message(updated_sug["message_id"])

                    # Obtener autor original
                    author = guild.get_member(updated_sug["user_id"])
                    if not author:
                        try:
                            author = await interaction.client.fetch_user(updated_sug["user_id"])
                        except Exception:
                            author = None

                    new_embed = EmbedBuilder.suggestion(
                        suggestion_id=id,
                        content=updated_sug["content"],
                        author=author,
                        status=estado.value,
                        upvotes=updated_sug["upvotes"],
                        downvotes=updated_sug["downvotes"],
                        staff_comment=comentario,
                        reviewer=staff_member,
                    )

                    # Desactivar botones de votación
                    disabled_view = SuggestionVoteView(disabled=True)
                    await target_msg.edit(embed=new_embed, view=disabled_view)
                except (discord.NotFound, discord.HTTPException) as exc:
                    logger.warning("No se pudo editar el mensaje original de la sugerencia #%s: %s", id, exc)

        # 5. Intentar notificar al autor por DM
        try:
            author_user = guild.get_member(updated_sug["user_id"])
            if not author_user:
                author_user = await self.bot.fetch_user(updated_sug["user_id"])

            dm_embed = EmbedBuilder.info(
                f"Sugerencia #{id} Actualizada",
                f"Tu sugerencia en **{guild.name}** ha recibido una resolución oficial:\n\n"
                f"• **Estado:** {estado.name}\n"
                f"• **Comentario del Staff:** {comentario or 'Sin comentarios adicionales.'}\n"
                f"• **Revisada por:** {staff_member.mention}",
            )
            await author_user.send(embed=dm_embed)
        except Exception:
            # Si el usuario tiene los DMs bloqueados, no interrumpe el flujo
            pass

        # 6. Confirmar al moderador
        confirm_embed = EmbedBuilder.success(
            "Sugerencia Respondida",
            f"La sugerencia **#{id}** ha sido actualizada con éxito a estado **{estado.name}**.",
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    # ==========================================================================
    # COMANDO /ver_sugerencia
    # ==========================================================================

    @app_commands.command(
        name="ver_sugerencia",
        description="Consulta los detalles y estadísticas actuales de una sugerencia.",
    )
    @app_commands.describe(id="Número identificador de la sugerencia.")
    async def ver_sugerencia_command(self, interaction: discord.Interaction, id: int) -> None:
        """Muestra el embed completo de una sugerencia específica."""
        guild = interaction.guild
        if not guild:
            return

        suggestion = await queries.get_suggestion(id)
        if not suggestion or suggestion["guild_id"] != guild.id:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(
                    "Sugerencia No Encontrada",
                    f"No existe ninguna sugerencia registrada con el ID `#{id}`.",
                ),
                ephemeral=True,
            )
            return

        author = guild.get_member(suggestion["user_id"])
        if not author:
            try:
                author = await interaction.client.fetch_user(suggestion["user_id"])
            except Exception:
                author = None

        reviewer = None
        if suggestion["reviewed_by"]:
            reviewer = guild.get_member(suggestion["reviewed_by"])

        embed = EmbedBuilder.suggestion(
            suggestion_id=id,
            content=suggestion["content"],
            author=author,
            status=suggestion["status"],
            upvotes=suggestion["upvotes"],
            downvotes=suggestion["downvotes"],
            staff_comment=suggestion["staff_comment"],
            reviewer=reviewer,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Función de entrada requerida por discord.py para registrar el Cog."""
    await bot.add_cog(SuggestionsCog(bot))
