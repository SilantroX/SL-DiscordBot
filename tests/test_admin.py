"""
Pruebas Automatizadas para el Módulo de Administración (tests/test_admin.py).
----------------------------------------------------------------------------
Evalúa:
1. Configuración del canal de auditoría (/setup_admin).
2. Flujo disciplinario de advertencias (/warn y /warnings).
3. Acciones de aislamiento (/timeout y /untimeout).
4. Acciones de expulsión y baneo (/kick, /ban, /unban).
5. Purga de mensajes (/clear).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
from discord.ext import commands

from database.connection import DatabaseManager
import database.queries as queries
from cogs.admin import AdminCog


class MockRole:
    """Clase auxiliar para emular roles jerárquicos comparables."""
    def __init__(self, name: str, position: int, id: int = 1, managed: bool = False):
        self.name = name
        self.position = position
        self.id = id
        self.managed = managed
        self.mention = f"<@&{id}>"

    def is_default(self) -> bool:
        return False

    def __le__(self, other: MockRole) -> bool:
        return self.position <= other.position

    def __lt__(self, other: MockRole) -> bool:
        return self.position < other.position

    def __ge__(self, other: MockRole) -> bool:
        return self.position >= other.position

    def __gt__(self, other: MockRole) -> bool:
        return self.position > other.position


class TestAdminModule(unittest.IsolatedAsyncioTestCase):
    """Suite de pruebas para el módulo de administración."""

    async def asyncSetUp(self) -> None:
        """Configuración de base de datos temporal y mocks del bot."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_admin.sqlite3"
        self.db = DatabaseManager(self.db_path)
        queries.db_manager = self.db
        await self.db.initialize_schema()

        self.mock_bot = MagicMock(spec=commands.Bot)
        self.cog = AdminCog(self.mock_bot)

        # Configuración común del Guild
        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 123456789
        self.mock_guild.name = "Servidor de Pruebas"
        self.mock_guild.owner_id = 9999

        # Miembro Bot con rol alto
        self.bot_member = MagicMock(spec=discord.Member)
        self.bot_member.id = 8888
        self.bot_member.top_role = MockRole("Bot Role", 20)
        self.mock_guild.me = self.bot_member

        # Moderador con rol medio-alto
        self.moderator = MagicMock(spec=discord.Member)
        self.moderator.id = 1111
        self.moderator.display_name = "StaffUser"
        self.moderator.mention = "<@1111>"
        self.moderator.top_role = MockRole("Staff", 10)
        self.moderator.guild = self.mock_guild

        # Infractor con rol bajo
        self.target = MagicMock(spec=discord.Member)
        self.target.id = 2222
        self.target.name = "BadUser"
        self.target.display_name = "BadUser"
        self.target.mention = "<@2222>"
        self.target.top_role = MockRole("Miembro", 1)
        self.target.guild = self.mock_guild
        self.target.send = AsyncMock()
        self.target.kick = AsyncMock()
        self.target.ban = AsyncMock()
        self.target.timeout = AsyncMock()
        self.target.is_timed_out = MagicMock(return_value=True)

    async def asyncTearDown(self) -> None:
        await self.db.close()
        self.temp_dir.cleanup()

    def _create_interaction(self) -> MagicMock:
        """Genera un mock de discord.Interaction con responses asíncronas."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.moderator
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        return interaction

    async def test_01_setup_admin(self) -> None:
        """Prueba que /setup_admin guarde la configuración del canal de logs y rol."""
        interaction = self._create_interaction()
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.id = 55555
        mock_channel.mention = "<#55555>"

        mock_role = MockRole("ModRole", 10, id=77777)
        mock_role.mention = "<@&77777>"

        await self.cog.setup_admin_command.callback(self.cog, interaction, mock_channel, mock_role)

        settings = await queries.get_guild_settings(self.mock_guild.id)
        self.assertIsNotNone(settings)
        self.assertEqual(settings["mod_logs_channel_id"], 55555)
        self.assertEqual(settings["staff_role_id"], 77777)
        interaction.response.send_message.assert_called_once()

    async def test_02_warn_and_warnings(self) -> None:
        """Prueba aplicar una advertencia (/warn) y consultar el historial (/warnings)."""
        interaction = self._create_interaction()

        # 1. Aplicar warn
        await self.cog.warn_command.callback(self.cog, interaction, self.target, "Lenguaje inadecuado")
        self.target.send.assert_called_once()
        interaction.response.send_message.assert_called_once()

        # 2. Consultar historial
        interaction_hist = self._create_interaction()
        await self.cog.warnings_command.callback(self.cog, interaction_hist, self.target)
        interaction_hist.response.send_message.assert_called_once()
        _, kwargs = interaction_hist.response.send_message.call_args
        embed = kwargs["embed"]
        self.assertIn("Historial de Sanciones", embed.title or "")
        self.assertEqual(len(embed.fields), 1)

    async def test_03_timeout_and_untimeout(self) -> None:
        """Prueba aislar (/timeout) y desaislar (/untimeout) a un miembro."""
        interaction = self._create_interaction()

        # Aplicar timeout de 15 minutos
        await self.cog.timeout_command.callback(self.cog, interaction, self.target, minutos=15, motivo="Spam continuo")
        self.target.timeout.assert_called_once()

        # Levantar timeout
        interaction_un = self._create_interaction()
        await self.cog.untimeout_command.callback(self.cog, interaction_un, self.target, motivo="Perdón aceptado")
        # Segundo llamado a timeout con None
        self.assertEqual(self.target.timeout.call_count, 2)
        self.assertIsNone(self.target.timeout.call_args[0][0])

    async def test_04_kick_and_ban(self) -> None:
        """Prueba expulsar (/kick) y banear (/ban) con registro en BD."""
        interaction_kick = self._create_interaction()
        await self.cog.kick_command.callback(self.cog, interaction_kick, self.target, motivo="Comportamiento tóxico")
        self.target.kick.assert_called_once()

        interaction_ban = self._create_interaction()
        await self.cog.ban_command.callback(self.cog, interaction_ban, self.target, motivo="Ataque raid", borrar_dias=2)
        self.target.ban.assert_called_once()
        self.assertEqual(self.target.ban.call_args[1]["delete_message_days"], 2)

        # Verificar historial en BD
        history = await queries.get_user_infractions(self.mock_guild.id, self.target.id)
        action_types = [h["action_type"] for h in history]
        self.assertIn("KICK", action_types)
        self.assertIn("BAN", action_types)

    async def test_05_clear_command_newest_first(self) -> None:
        """Prueba que /clear purgue de más reciente a más antiguo (oldest_first=False)."""
        interaction = self._create_interaction()
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.id = 66666
        mock_channel.mention = "<#66666>"
        mock_channel.purge = AsyncMock(return_value=[MagicMock(), MagicMock()])
        interaction.channel = mock_channel

        await self.cog.clear_command.callback(self.cog, interaction, cantidad=20, miembro=None)

        mock_channel.purge.assert_called_once()
        _, kwargs = mock_channel.purge.call_args
        self.assertEqual(kwargs.get("limit"), 20)
        self.assertFalse(kwargs.get("oldest_first"), "oldest_first debe ser False para borrar de reciente a antiguo")

    async def test_06_audit_channel_and_role_listeners(self) -> None:
        """Prueba que los listeners de auditoría capturen creación de canales y cambios de rol."""
        self.cog.send_mod_log = AsyncMock()

        # 1. Creación de canal
        mock_ch = MagicMock(spec=discord.TextChannel)
        mock_ch.name = "anuncios-staff"
        mock_ch.id = 99901
        mock_ch.type = discord.ChannelType.text
        mock_ch.category = None
        mock_ch.guild = self.mock_guild

        await self.cog.on_guild_channel_create(mock_ch)
        self.cog.send_mod_log.assert_called_once()

        # 2. Modificación de rol con permiso peligroso (Administrator)
        self.cog.send_mod_log.reset_mock()
        role_before = MagicMock(spec=discord.Role)
        role_before.name = "Moderador"
        role_before.permissions = discord.Permissions(moderate_members=True)

        role_after = MagicMock(spec=discord.Role)
        role_after.name = "Moderador"
        role_after.mention = "<@&555>"
        role_after.guild = self.mock_guild
        role_after.permissions = discord.Permissions(administrator=True, moderate_members=True)

        await self.cog.on_guild_role_update(role_before, role_after)
        self.cog.send_mod_log.assert_called_once()
        _, kwargs = self.cog.send_mod_log.call_args
        embed = self.cog.send_mod_log.call_args[0][1]
        self.assertIn("ALERTA", embed.title or "")

    # ==========================================================================
    # 7. PRUEBAS DE ASIGNACIÓN Y REMOCIÓN MASIVA DE ROLES (/role_add_all /role_remove_all)
    # ==========================================================================

    async def test_07_role_add_all(self) -> None:
        """Prueba la asignación masiva de un rol a todos los miembros elegibles."""
        self.cog.send_mod_log = AsyncMock()

        # Rol a asignar (posición 5, menor que el bot que tiene posición 20)
        target_role = MockRole("Comunidad", position=5, id=555)

        # Miembros del servidor
        m1 = MagicMock(spec=discord.Member)
        m1.id = 1001
        m1.name = "Human1"
        m1.bot = False
        m1.roles = []
        m1.add_roles = AsyncMock()

        m2 = MagicMock(spec=discord.Member)
        m2.id = 1002
        m2.name = "Human2"
        m2.bot = False
        m2.roles = [target_role]  # Ya tiene el rol
        m2.add_roles = AsyncMock()

        m3_bot = MagicMock(spec=discord.Member)
        m3_bot.id = 1003
        m3_bot.name = "BotUser"
        m3_bot.bot = True  # Es bot
        m3_bot.roles = []
        m3_bot.add_roles = AsyncMock()

        self.mock_guild.members = [m1, m2, m3_bot]

        # Caso A: Jerarquía insuficiente del bot (rol con posición 25 > bot posición 20)
        high_role = MockRole("Rol Alto", position=25, id=777)
        interaction_fail = self._create_interaction()
        await self.cog.role_add_all_command.callback(self.cog, interaction_fail, high_role)
        interaction_fail.response.send_message.assert_awaited_once()
        self.assertIn("Jerarquía Insuficiente", interaction_fail.response.send_message.await_args.kwargs["embed"].title)

        # Caso B: Asignación masiva exitosa ignorando bots
        interaction_success = self._create_interaction()
        await self.cog.role_add_all_command.callback(self.cog, interaction_success, target_role, ignorar_bots=True)

        # Solo m1 debe haber recibido el rol (m2 ya lo tenía, m3 es bot)
        m1.add_roles.assert_awaited_once_with(target_role, reason=f"Asignación masiva por {self.moderator.name}")
        m2.add_roles.assert_not_awaited()
        m3_bot.add_roles.assert_not_awaited()

        interaction_success.followup.send.assert_awaited_once()
        call_kw = interaction_success.followup.send.await_args.kwargs
        self.assertIn("Completada", call_kw["embed"].title)
        self.cog.send_mod_log.assert_awaited_once()

    async def test_08_role_remove_all(self) -> None:
        """Prueba la remoción masiva de un rol de todos los miembros del servidor."""
        self.cog.send_mod_log = AsyncMock()
        target_role = MockRole("VIP Expirado", position=5, id=555)

        m1 = MagicMock(spec=discord.Member)
        m1.id = 2001
        m1.name = "UserWithRole"
        m1.bot = False
        m1.roles = [target_role]
        m1.remove_roles = AsyncMock()

        m2 = MagicMock(spec=discord.Member)
        m2.id = 2002
        m2.name = "UserWithoutRole"
        m2.bot = False
        m2.roles = []
        m2.remove_roles = AsyncMock()

        self.mock_guild.members = [m1, m2]

        interaction = self._create_interaction()
        await self.cog.role_remove_all_command.callback(self.cog, interaction, target_role, ignorar_bots=True)

        m1.remove_roles.assert_awaited_once_with(target_role, reason=f"Remoción masiva por {self.moderator.name}")
        m2.remove_roles.assert_not_awaited()
        interaction.followup.send.assert_awaited_once()
        self.cog.send_mod_log.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()

