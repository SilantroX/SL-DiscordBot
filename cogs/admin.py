"""
Módulo de Administración y Moderación (cogs/admin.py).
------------------------------------------------------
Proporciona comandos Slash completos para la gestión y moderación de miembros:
- /setup admin: Configuración de canal de auditoría y rol de staff
- /kick: Expulsa a un miembro del servidor
- /ban: Banea a un miembro del servidor (con opción de purga de historial)
- /unban: Revoca el baneo de un usuario mediante su ID
- /timeout: Aísla temporalmente a un miembro (sistema nativo de Discord)
- /untimeout: Remueve el aislamiento previo de un miembro
- /warn: Aplica y registra una advertencia en la base de datos
- /warnings: Consulta el historial de sanciones e infracciones de un usuario
- /clear: Elimina mensajes masivamente en el canal actual (con filtro opcional)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import database.queries as queries
from utils.checks import can_moderate_member, is_staff_or_admin
from utils.embeds import EmbedBuilder, EmbedColors


class AdminCog(commands.Cog, name="Administración"):
    """Comandos de administración, sanciones disciplinarias y auditoría."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ==========================================================================
    # UTILIDAD INTERNA: CANAL DE AUDITORÍA (MOD-LOGS)
    # ==========================================================================

    async def send_mod_log(self, guild: discord.Guild, embed: discord.Embed) -> None:
        """Envía un embed descriptivo al canal de mod-logs configurado para el servidor."""
        settings = await queries.get_guild_settings(guild.id)
        if not settings or not settings.get("mod_logs_channel_id"):
            return

        channel = guild.get_channel(settings["mod_logs_channel_id"])
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass  # El bot no tiene permisos de envío en ese canal

    # ==========================================================================
    # 1. COMANDO /setup admin
    # ==========================================================================

    @app_commands.command(
        name="setup_admin",
        description="Configura el canal de logs de moderación y el rol de Staff del servidor.",
    )
    @app_commands.describe(
        canal_logs="Canal de texto donde se registrarán las sanciones y acciones del staff.",
        rol_staff="Rol otorgado a los moderadores/administradores (opcional).",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_admin_command(
        self,
        interaction: discord.Interaction,
        canal_logs: discord.TextChannel,
        rol_staff: Optional[discord.Role] = None,
    ) -> None:
        """Guarda en la base de datos la configuración del canal de auditoría y rol staff."""
        guild = interaction.guild
        if not guild:
            return

        # Guardar en base de datos
        await queries.update_guild_setting(guild.id, "mod_logs_channel_id", canal_logs.id)
        if rol_staff:
            await queries.update_guild_setting(guild.id, "staff_role_id", rol_staff.id)

        desc = f"• **Canal de Auditoría (ModLogs):** {canal_logs.mention}\n"
        if rol_staff:
            desc += f"• **Rol de Staff:** {rol_staff.mention}\n"

        embed = EmbedBuilder.success("Módulo de Administración Configurado", desc)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==========================================================================
    # 2. COMANDO /warn
    # ==========================================================================

    @app_commands.command(name="warn", description="Aplica y registra una advertencia formal a un miembro.")
    @app_commands.describe(
        miembro="El usuario al que deseas advertir.",
        motivo="Razón clara de la advertencia.",
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_command(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
        motivo: str,
    ) -> None:
        """Registra una sanción de tipo WARN en SQLite y notifica al usuario."""
        moderator = interaction.user
        guild = interaction.guild
        if not isinstance(moderator, discord.Member) or not guild:
            return

        # Comprobación de jerarquía
        can_mod, msg = can_moderate_member(moderator, miembro)
        if not can_mod:
            await interaction.response.send_message(embed=EmbedBuilder.error("Acción Denegada", msg), ephemeral=True)
            return

        # Registrar en la base de datos
        infraction_id = await queries.add_infraction(
            guild_id=guild.id,
            user_id=miembro.id,
            moderator_id=moderator.id,
            action_type="WARN",
            reason=motivo,
        )

        # Contar total de sanciones
        history = await queries.get_user_infractions(guild.id, miembro.id)
        total_warns = sum(1 for inf in history if inf["action_type"] == "WARN")

        # Notificar por mensaje directo (DM) al infractor
        try:
            dm_embed = EmbedBuilder.warning(
                title=f"Has recibido una advertencia en {guild.name}",
                description=f"**Motivo:** {motivo}\n**Moderador:** {moderator.mention}\n**Total de Advertencias:** {total_warns}",
            )
            await miembro.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # El usuario tiene los MD cerrados

        # Respuesta al moderador
        confirm_embed = EmbedBuilder.success(
            title="Miembro Advertido",
            description=f"Se ha registrado la advertencia #{infraction_id} para {miembro.mention}.\n**Motivo:** {motivo}\n**Advertencias acumuladas:** `{total_warns}`",
        )
        await interaction.response.send_message(embed=confirm_embed)

        # Registro en canal de logs
        log_embed = EmbedBuilder.warning(
            title="⚠️ Sanción Aplicada: Advertencia (WARN)",
            description=(
                f"• **Usuario:** {miembro.mention} (`{miembro.id}`)\n"
                f"• **Moderador:** {moderator.mention} (`{moderator.id}`)\n"
                f"• **Motivo:** {motivo}\n"
                f"• **Infracción ID:** `#{infraction_id}`\n"
                f"• **Total Warns:** `{total_warns}`"
            ),
        )
        log_embed.set_thumbnail(url=miembro.display_avatar.url)
        await self.send_mod_log(guild, log_embed)

    # ==========================================================================
    # 3. COMANDO /warnings
    # ==========================================================================

    @app_commands.command(name="warnings", description="Consulta el historial disciplinario de un miembro.")
    @app_commands.describe(miembro="El usuario del cual deseas consultar el historial.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings_command(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
    ) -> None:
        """Muestra una lista paginada o resumida de las infracciones del usuario."""
        guild = interaction.guild
        if not guild:
            return

        history = await queries.get_user_infractions(guild.id, miembro.id)
        if not history:
            await interaction.response.send_message(
                embed=EmbedBuilder.info(
                    "Historial Limpio",
                    f"{miembro.mention} no registra ninguna sanción en este servidor.",
                ),
                ephemeral=True,
            )
            return

        embed = EmbedBuilder.base(
            title=f"📋 Historial de Sanciones: {miembro.display_name}",
            color=EmbedColors.PRIMARY,
        )
        embed.set_thumbnail(url=miembro.display_avatar.url)

        # Mostrar las últimas 10 sanciones
        recent = history[:10]
        for inf in recent:
            mod_str = f"<@{inf['moderator_id']}>"
            fecha_str = inf.get("created_at", "N/A")
            embed.add_field(
                name=f"#{inf['id']} • {inf['action_type']} ({fecha_str})",
                value=f"**Motivo:** {inf['reason']}\n**Por:** {mod_str}",
                inline=False,
            )

        if len(history) > 10:
            embed.set_footer(text=f"Mostrando las 10 más recientes de un total de {len(history)} sanciones.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==========================================================================
    # 4. COMANDO /timeout (Mute nativo de Discord)
    # ==========================================================================

    @app_commands.command(name="timeout", description="Aísla (mutea) temporalmente a un miembro usando el sistema nativo.")
    @app_commands.describe(
        miembro="El usuario a aislar.",
        minutos="Duración del aislamiento en minutos (máximo 40320 = 28 días).",
        motivo="Razón del aislamiento.",
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_command(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
        minutos: int,
        motivo: Optional[str] = "Sin motivo especificado",
    ) -> None:
        """Aplica un aislamiento temporal utilizando Member.timeout."""
        moderator = interaction.user
        guild = interaction.guild
        if not isinstance(moderator, discord.Member) or not guild:
            return

        if minutos <= 0 or minutos > 40320:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Duración Inválida", "La duración debe ser mayor a 0 y menor a 40320 minutos (28 días)."),
                ephemeral=True,
            )
            return

        can_mod, msg = can_moderate_member(moderator, miembro)
        if not can_mod:
            await interaction.response.send_message(embed=EmbedBuilder.error("Acción Denegada", msg), ephemeral=True)
            return

        duracion = timedelta(minutes=minutos)
        motivo_final = motivo or "Sin motivo especificado"

        # Aplicar el timeout en la API de Discord
        try:
            await miembro.timeout(duracion, reason=f"{motivo_final} (Por: {moderator.display_name})")
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Error de Permisos", "No tengo permisos suficientes para aislar a este miembro."),
                ephemeral=True,
            )
            return

        # Registrar en la base de datos
        await queries.add_infraction(guild.id, miembro.id, moderator.id, "MUTE", f"Aislamiento por {minutos}m: {motivo_final}")

        # Notificar por DM
        try:
            await miembro.send(
                embed=EmbedBuilder.warning(
                    title=f"Has sido aislado en {guild.name}",
                    description=f"**Duración:** {minutos} minutos\n**Motivo:** {motivo_final}\n**Moderador:** {moderator.mention}",
                )
            )
        except discord.Forbidden:
            pass

        confirm_embed = EmbedBuilder.success(
            title="Miembro Aislado",
            description=f"{miembro.mention} ha sido aislado por `{minutos}` minutos.\n**Motivo:** {motivo_final}",
        )
        await interaction.response.send_message(embed=confirm_embed)

        # Log
        log_embed = EmbedBuilder.warning(
            title="🔇 Sanción Aplicada: Aislamiento (TIMEOUT)",
            description=(
                f"• **Usuario:** {miembro.mention} (`{miembro.id}`)\n"
                f"• **Moderador:** {moderator.mention} (`{moderator.id}`)\n"
                f"• **Duración:** `{minutos}` minutos\n"
                f"• **Motivo:** {motivo_final}"
            ),
        )
        log_embed.set_thumbnail(url=miembro.display_avatar.url)
        await self.send_mod_log(guild, log_embed)

    # ==========================================================================
    # 5. COMANDO /untimeout
    # ==========================================================================

    @app_commands.command(name="untimeout", description="Remueve el aislamiento temporal previo de un miembro.")
    @app_commands.describe(
        miembro="El usuario al que deseas retirar el aislamiento.",
        motivo="Razón del levantamiento de la sanción.",
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout_command(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
        motivo: Optional[str] = "Aislamiento revocado por moderación",
    ) -> None:
        """Remueve el timeout de un miembro pasándole None a member.timeout."""
        moderator = interaction.user
        guild = interaction.guild
        if not isinstance(moderator, discord.Member) or not guild:
            return

        if not miembro.is_timed_out():
            await interaction.response.send_message(
                embed=EmbedBuilder.warning("No Aislado", f"{miembro.mention} no se encuentra actualmente aislado."),
                ephemeral=True,
            )
            return

        can_mod, msg = can_moderate_member(moderator, miembro)
        if not can_mod:
            await interaction.response.send_message(embed=EmbedBuilder.error("Acción Denegada", msg), ephemeral=True)
            return

        motivo_final = motivo or "Aislamiento revocado por moderación"
        await miembro.timeout(None, reason=f"{motivo_final} (Por: {moderator.display_name})")

        confirm_embed = EmbedBuilder.success(
            title="Aislamiento Removido",
            description=f"Se ha levantado el aislamiento a {miembro.mention}.\n**Motivo:** {motivo_final}",
        )
        await interaction.response.send_message(embed=confirm_embed)

        log_embed = EmbedBuilder.info(
            title="🔊 Sanción Revocada: Fin de Aislamiento",
            description=(
                f"• **Usuario:** {miembro.mention} (`{miembro.id}`)\n"
                f"• **Moderador:** {moderator.mention} (`{moderator.id}`)\n"
                f"• **Motivo:** {motivo_final}"
            ),
        )
        await self.send_mod_log(guild, log_embed)

    # ==========================================================================
    # 6. COMANDO /kick
    # ==========================================================================

    @app_commands.command(name="kick", description="Expulsa a un miembro del servidor.")
    @app_commands.describe(
        miembro="El miembro a expulsar.",
        motivo="Razón de la expulsión.",
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_command(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
        motivo: Optional[str] = "Sin motivo especificado",
    ) -> None:
        """Expulsa a un miembro tras comprobar la jerarquía de roles."""
        moderator = interaction.user
        guild = interaction.guild
        if not isinstance(moderator, discord.Member) or not guild:
            return

        can_mod, msg = can_moderate_member(moderator, miembro)
        if not can_mod:
            await interaction.response.send_message(embed=EmbedBuilder.error("Acción Denegada", msg), ephemeral=True)
            return

        motivo_final = motivo or "Sin motivo especificado"

        # Notificar al miembro antes de expulsar
        try:
            await miembro.send(
                embed=EmbedBuilder.error(
                    title=f"Has sido expulsado de {guild.name}",
                    description=f"**Motivo:** {motivo_final}\n**Moderador:** {moderator.mention}",
                )
            )
        except discord.Forbidden:
            pass

        # Expulsar
        try:
            await miembro.kick(reason=f"{motivo_final} (Por: {moderator.display_name})")
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Error de Permisos", "No poseo permisos para expulsar a este usuario."),
                ephemeral=True,
            )
            return

        # Registrar en la base de datos
        await queries.add_infraction(guild.id, miembro.id, moderator.id, "KICK", motivo_final)

        confirm_embed = EmbedBuilder.success(
            title="Miembro Expulsado",
            description=f"{miembro.mention} (`{miembro.id}`) ha sido expulsado del servidor.\n**Motivo:** {motivo_final}",
        )
        await interaction.response.send_message(embed=confirm_embed)

        log_embed = EmbedBuilder.error(
            title="🚪 Miembro Expulsado (KICK)",
            description=(
                f"• **Usuario:** {miembro.name} (`{miembro.id}`)\n"
                f"• **Moderador:** {moderator.mention} (`{moderator.id}`)\n"
                f"• **Motivo:** {motivo_final}"
            ),
        )
        log_embed.set_thumbnail(url=miembro.display_avatar.url)
        await self.send_mod_log(guild, log_embed)

    # ==========================================================================
    # 7. COMANDO /ban
    # ==========================================================================

    @app_commands.command(name="ban", description="Banea permanentemente o con purga de mensajes a un miembro.")
    @app_commands.describe(
        miembro="El miembro a banear.",
        motivo="Razón del baneo.",
        borrar_dias="Días de historial de mensajes a eliminar (0 a 7, defecto: 1).",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member,
        motivo: Optional[str] = "Sin motivo especificado",
        borrar_dias: Optional[app_commands.Range[int, 0, 7]] = 1,
    ) -> None:
        """Banea al miembro de forma permanente en el servidor."""
        moderator = interaction.user
        guild = interaction.guild
        if not isinstance(moderator, discord.Member) or not guild:
            return

        can_mod, msg = can_moderate_member(moderator, miembro)
        if not can_mod:
            await interaction.response.send_message(embed=EmbedBuilder.error("Acción Denegada", msg), ephemeral=True)
            return

        motivo_final = motivo or "Sin motivo especificado"
        delete_days = borrar_dias if borrar_dias is not None else 1

        # Notificar al miembro antes de banear
        try:
            await miembro.send(
                embed=EmbedBuilder.error(
                    title=f"Has sido baneado de {guild.name}",
                    description=f"**Motivo:** {motivo_final}\n**Moderador:** {moderator.mention}",
                )
            )
        except discord.Forbidden:
            pass

        # Ejecutar baneo
        try:
            await miembro.ban(
                delete_message_days=delete_days,
                reason=f"{motivo_final} (Por: {moderator.display_name})",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Error de Permisos", "No poseo permisos jerárquicos para banear a este usuario."),
                ephemeral=True,
            )
            return

        # Registrar en la base de datos
        await queries.add_infraction(guild.id, miembro.id, moderator.id, "BAN", motivo_final)

        confirm_embed = EmbedBuilder.success(
            title="Miembro Baneado",
            description=f"{miembro.mention} (`{miembro.id}`) ha sido baneado.\n**Motivo:** {motivo_final}\n**Purga de mensajes:** `{delete_days} día(s)`",
        )
        await interaction.response.send_message(embed=confirm_embed)

        log_embed = EmbedBuilder.error(
            title="🔨 Miembro Baneado (BAN)",
            description=(
                f"• **Usuario:** {miembro.name} (`{miembro.id}`)\n"
                f"• **Moderador:** {moderator.mention} (`{moderator.id}`)\n"
                f"• **Motivo:** {motivo_final}\n"
                f"• **Mensajes eliminados:** `{delete_days}` días"
            ),
        )
        log_embed.set_thumbnail(url=miembro.display_avatar.url)
        await self.send_mod_log(guild, log_embed)

    # ==========================================================================
    # 8. COMANDO /unban
    # ==========================================================================

    @app_commands.command(name="unban", description="Revoca el baneo de un usuario utilizando su ID de Discord.")
    @app_commands.describe(
        user_id="El ID numérico del usuario baneado.",
        motivo="Razón del desbaneo.",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_command(
        self,
        interaction: discord.Interaction,
        user_id: str,
        motivo: Optional[str] = "Baneo revocado por administración",
    ) -> None:
        """Busca en la lista de baneos del servidor y remueve la sanción."""
        guild = interaction.guild
        moderator = interaction.user
        if not guild or not isinstance(moderator, discord.Member):
            return

        try:
            target_id = int(user_id.strip())
        except ValueError:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("ID Inválido", "El ID de usuario debe ser una secuencia numérica."),
                ephemeral=True,
            )
            return

        # Verificar si está en la lista de baneos
        try:
            ban_entry = await guild.fetch_ban(discord.Object(id=target_id))
        except discord.NotFound:
            await interaction.response.send_message(
                embed=EmbedBuilder.warning("No Encontrado", f"El usuario con ID `{target_id}` no está baneado de este servidor."),
                ephemeral=True,
            )
            return
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Permisos Insuficientes", "No tengo permisos para ver o modificar la lista de baneos."),
                ephemeral=True,
            )
            return

        motivo_final = motivo or "Baneo revocado por administración"
        await guild.unban(ban_entry.user, reason=f"{motivo_final} (Por: {moderator.display_name})")

        confirm_embed = EmbedBuilder.success(
            title="Usuario Desbaneado",
            description=f"Se ha revocado el baneo a **{ban_entry.user.name}** (`{target_id}`).\n**Motivo:** {motivo_final}",
        )
        await interaction.response.send_message(embed=confirm_embed)

        log_embed = EmbedBuilder.info(
            title="🔓 Baneo Revocado (UNBAN)",
            description=(
                f"• **Usuario:** {ban_entry.user.name} (`{target_id}`)\n"
                f"• **Moderador:** {moderator.mention} (`{moderator.id}`)\n"
                f"• **Motivo:** {motivo_final}"
            ),
        )
        await self.send_mod_log(guild, log_embed)

    # ==========================================================================
    # 9. COMANDO /clear (Purga de mensajes)
    # ==========================================================================

    @app_commands.command(name="clear", description="Elimina una cantidad determinada de mensajes del canal actual.")
    @app_commands.describe(
        cantidad="Número de mensajes a eliminar (entre 1 y 100).",
        miembro="Opcional: filtrar para eliminar solo mensajes de este usuario.",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_command(
        self,
        interaction: discord.Interaction,
        cantidad: app_commands.Range[int, 1, 100],
        miembro: Optional[discord.Member] = None,
    ) -> None:
        """Purga mensajes recientes del canal, con filtro opcional por autor."""
        channel = interaction.channel
        guild = interaction.guild
        moderator = interaction.user
        if not isinstance(channel, discord.TextChannel) or not guild:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Canal No Válido", "Este comando solo puede ejecutarse en canales de texto."),
                ephemeral=True,
            )
            return

        # Aplazar respuesta para evitar expiración de la interacción mientras Discord borra los mensajes
        await interaction.response.defer(ephemeral=True)

        def check_filter(msg: discord.Message) -> bool:
            if miembro is not None:
                return msg.author.id == miembro.id
            return True

        # Discord no permite purgar mensajes con más de 14 días de antigüedad vía API bulk_delete
        limit_date = datetime.now(timezone.utc) - timedelta(days=14)

        def check_filter(msg: discord.Message) -> bool:
            # Omitir mensajes con más de 14 días para evitar fallo en bulk_delete
            if msg.created_at <= limit_date:
                return False
            if miembro is not None:
                return msg.author.id == miembro.id
            return True

        try:
            # oldest_first=False garantiza que la eliminación comience desde el mensaje más reciente hacia el más antiguo
            deleted = await channel.purge(
                limit=cantidad,
                check=check_filter,
                oldest_first=False,
            )
        except discord.Forbidden:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Permisos Faltantes", "No tengo permisos de `Gestionar Mensajes` en este canal."),
                ephemeral=True,
            )
            return

        total_borrados = len(deleted)
        filtro_str = f" de {miembro.mention}" if miembro else ""
        embed = EmbedBuilder.success(
            title="Mensajes Eliminados",
            description=f"Se eliminaron `{total_borrados}` mensaje(s){filtro_str} (del más reciente al más antiguo).",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Log
        log_embed = EmbedBuilder.info(
            title="🧹 Purga de Mensajes (CLEAR)",
            description=(
                f"• **Canal:** {channel.mention}\n"
                f"• **Moderador:** {moderator.mention} (`{moderator.id}`)\n"
                f"• **Cantidad eliminada:** `{total_borrados}` mensajes\n"
                f"• **Filtro de usuario:** {miembro.mention if miembro else 'Ninguno (todos)'}"
            ),
        )
        await self.send_mod_log(guild, log_embed)

    # ==========================================================================
    # AUDITORÍA DE ACCIONES RIESGOSAS EN EL SERVIDOR (LISTENERS DE EVENTOS)
    # ==========================================================================

    async def _get_audit_executor(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction,
        target_id: Optional[int] = None,
    ) -> Optional[discord.User]:
        """Consulta los Audit Logs de Discord para identificar al moderador que ejecutó la acción."""
        if not guild.me.guild_permissions.view_audit_log:
            return None

        try:
            async for entry in guild.audit_logs(limit=4, action=action):
                # Comprobar si la acción ocurrió en los últimos 20 segundos
                delta_sec = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if delta_sec <= 20:
                    if target_id is None or (entry.target and getattr(entry.target, "id", None) == target_id):
                        return entry.user
        except (discord.Forbidden, discord.HTTPException):
            pass
        return None

    # --- 1. AUDITORÍA DE CANALES ---

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Audita la creación de canales en el servidor."""
        guild = channel.guild
        executor = await self._get_audit_executor(guild, discord.AuditLogAction.channel_create, channel.id)
        mod_str = executor.mention if executor else "Desconocido / No disponible"

        log_embed = EmbedBuilder.warning(
            title="📁 Canal Creado",
            description=(
                f"• **Canal:** {channel.name} (`{channel.id}`)\n"
                f"• **Tipo:** `{channel.type}`\n"
                f"• **Categoría:** {channel.category.name if channel.category else 'Ninguna'}\n"
                f"• **Responsable:** {mod_str}"
            ),
        )
        await self.send_mod_log(guild, log_embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Audita la eliminación de canales en el servidor."""
        guild = channel.guild
        executor = await self._get_audit_executor(guild, discord.AuditLogAction.channel_delete, channel.id)
        mod_str = executor.mention if executor else "Desconocido / No disponible"

        log_embed = EmbedBuilder.error(
            title="🗑️ Canal Eliminado",
            description=(
                f"• **Canal:** `#{channel.name}` (`{channel.id}`)\n"
                f"• **Tipo:** `{channel.type}`\n"
                f"• **Categoría:** {channel.category.name if channel.category else 'Ninguna'}\n"
                f"• **Responsable:** {mod_str}"
            ),
        )
        await self.send_mod_log(guild, log_embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel,
    ) -> None:
        """Audita cambios críticos en canales (nombre o permisos/overwrites)."""
        guild = after.guild
        cambios = []

        if before.name != after.name:
            cambios.append(f"• **Nombre:** `{before.name}` ➔ `{after.name}`")

        # Comprobar cambios en permisos (Permission Overwrites)
        if before.overwrites != after.overwrites:
            cambios.append("• **Permisos:** Se modificaron los permisos o roles asignados a este canal.")

        if not cambios:
            return

        executor = await self._get_audit_executor(guild, discord.AuditLogAction.channel_update, after.id)
        mod_str = executor.mention if executor else "Desconocido / No disponible"

        log_embed = EmbedBuilder.warning(
            title="⚠️ Canal Modificado",
            description=(
                f"• **Canal:** {after.name} (`{after.id}`)\n"
                f"• **Responsable:** {mod_str}\n"
                f"**Detalles del cambio:**\n" + "\n".join(cambios)
            ),
        )
        await self.send_mod_log(guild, log_embed)

    # --- 2. AUDITORÍA DE ROLES ---

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """Audita la creación de un nuevo rol."""
        guild = role.guild
        executor = await self._get_audit_executor(guild, discord.AuditLogAction.role_create, role.id)
        mod_str = executor.mention if executor else "Desconocido / No disponible"

        log_embed = EmbedBuilder.warning(
            title="🎭 Rol Creado",
            description=(
                f"• **Rol:** {role.mention} (`{role.name}`)\n"
                f"• **ID:** `{role.id}`\n"
                f"• **Color:** `{role.color}`\n"
                f"• **Responsable:** {mod_str}"
            ),
        )
        await self.send_mod_log(guild, log_embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """Audita la eliminación de un rol."""
        guild = role.guild
        executor = await self._get_audit_executor(guild, discord.AuditLogAction.role_delete, role.id)
        mod_str = executor.mention if executor else "Desconocido / No disponible"

        log_embed = EmbedBuilder.error(
            title="🗑️ Rol Eliminado",
            description=(
                f"• **Rol:** `{role.name}` (`{role.id}`)\n"
                f"• **Responsable:** {mod_str}"
            ),
        )
        await self.send_mod_log(guild, log_embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        """Audita modificaciones críticas de permisos en roles (alerta de seguridad si otorga permisos peligrosos)."""
        guild = after.guild
        cambios = []
        es_riesgo_critico = False

        if before.name != after.name:
            cambios.append(f"• **Nombre:** `{before.name}` ➔ `{after.name}`")

        # Lista de permisos de alto riesgo
        critical_perms = [
            ("administrator", "👑 Administrador"),
            ("manage_guild", "⚙️ Gestionar Servidor"),
            ("manage_roles", "🎭 Gestionar Roles"),
            ("manage_channels", "📁 Gestionar Canales"),
            ("ban_members", "🔨 Banear Miembros"),
            ("kick_members", "🚪 Expulsar Miembros"),
            ("mention_everyone", "📢 Mencionar @everyone"),
        ]

        for perm_attr, perm_name in critical_perms:
            before_val = getattr(before.permissions, perm_attr)
            after_val = getattr(after.permissions, perm_attr)
            if not before_val and after_val:
                cambios.append(f"• 🔴 **Permiso Otorgado:** `{perm_name}`")
                es_riesgo_critico = True
            elif before_val and not after_val:
                cambios.append(f"• 🟢 **Permiso Revocado:** `{perm_name}`")

        if not cambios:
            return

        executor = await self._get_audit_executor(guild, discord.AuditLogAction.role_update, after.id)
        mod_str = executor.mention if executor else "Desconocido / No disponible"

        titulo = "🚨 ALERTA: Permisos Peligrosos Otorgados a Rol" if es_riesgo_critico else "🎭 Rol Modificado"
        color = EmbedColors.ERROR if es_riesgo_critico else EmbedColors.WARNING

        log_embed = EmbedBuilder.base(
            title=titulo,
            description=(
                f"• **Rol:** {after.mention} (`{after.name}`)\n"
                f"• **Responsable:** {mod_str}\n"
                f"**Cambios detectados:**\n" + "\n".join(cambios)
            ),
            color=color,
        )
        await self.send_mod_log(guild, log_embed)

    # --- 3. AUDITORÍA DE MIEMBROS (ROLES Y SANCIONES EXTERNAS) ---

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Audita cuando a un miembro se le asignan o remueven roles."""
        guild = after.guild
        if before.roles == after.roles:
            return

        added_roles = [r for r in after.roles if r not in before.roles]
        removed_roles = [r for r in before.roles if r not in after.roles]

        if not added_roles and not removed_roles:
            return

        executor = await self._get_audit_executor(guild, discord.AuditLogAction.member_role_update, after.id)
        mod_str = executor.mention if executor else "Desconocido / No disponible"

        desc_lines = [
            f"• **Miembro:** {after.mention} (`{after.name}`)",
            f"• **Responsable:** {mod_str}",
        ]

        es_peligroso = False
        if added_roles:
            roles_str = ", ".join(r.mention for r in added_roles)
            desc_lines.append(f"• ➕ **Roles Añadidos:** {roles_str}")
            # Alerta si se otorgó un rol con administrador
            if any(r.permissions.administrator for r in added_roles):
                es_peligroso = True
                desc_lines.append("⚠️ **¡Atención!** Se ha otorgado un rol con permisos de **ADMINISTRADOR**.")

        if removed_roles:
            roles_str = ", ".join(r.mention for r in removed_roles)
            desc_lines.append(f"• ➖ **Roles Removidos:** {roles_str}")

        titulo = "🚨 Asignación de Rol Administrativo" if es_peligroso else "👥 Roles de Miembro Actualizados"
        color = EmbedColors.ERROR if es_peligroso else EmbedColors.INFO

        log_embed = EmbedBuilder.base(
            title=titulo,
            description="\n".join(desc_lines),
            color=color,
        )
        log_embed.set_thumbnail(url=after.display_avatar.url)
        await self.send_mod_log(guild, log_embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User | discord.Member) -> None:
        """Audita baneos realizados directamente en Discord (externos o manuales)."""
        executor = await self._get_audit_executor(guild, discord.AuditLogAction.ban, user.id)
        # Si el ejecutor fue este mismo bot, ya se envió el log a través de /ban
        if executor and executor.id == self.bot.user.id:
            return

        mod_str = executor.mention if executor else "Manual / Desconocido"
        log_embed = EmbedBuilder.error(
            title="🔨 Baneo Detectado (Discord Audit)",
            description=(
                f"• **Usuario:** {user.name} (`{user.id}`)\n"
                f"• **Responsable:** {mod_str}\n"
                f"• **Origen:** Sanción aplicada directamente desde Discord."
            ),
        )
        log_embed.set_thumbnail(url=user.display_avatar.url)
        await self.send_mod_log(guild, log_embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """Audita desbaneos realizados directamente en Discord (externos o manuales)."""
        executor = await self._get_audit_executor(guild, discord.AuditLogAction.unban, user.id)
        if executor and executor.id == self.bot.user.id:
            return

        mod_str = executor.mention if executor else "Manual / Desconocido"
        log_embed = EmbedBuilder.info(
            title="🔓 Desbaneo Detectado (Discord Audit)",
            description=(
                f"• **Usuario:** {user.name} (`{user.id}`)\n"
                f"• **Responsable:** {mod_str}\n"
                f"• **Origen:** Revocación aplicada directamente desde Discord."
            ),
        )
        await self.send_mod_log(guild, log_embed)


async def setup(bot: commands.Bot) -> None:
    """Función de entrada para registrar el Cog de Administración."""
    await bot.add_cog(AdminCog(bot))

