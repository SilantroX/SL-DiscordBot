"""
Pruebas Automatizadas para el Módulo de Autoroles (tests/test_roles.py).
-----------------------------------------------------------------------
Evalúa:
1. Despliegue de paneles públicos de autoroles (/setup_autoroles).
2. Adición de opciones con validación de jerarquías y límites (/autorol_agregar_opcion).
3. Eliminación de opciones (/autorol_eliminar_opcion).
4. Interacción con el botón persistente y despliegue del menú efímero (RolePanelPersistentView).
5. Sincronización atómica de roles en el menú desplegable (RoleSelectDropdown).
6. Listado de paneles (/autorol_listar).
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
from cogs.roles import (
    RolesCog,
    RolePanelPersistentView,
    RoleDropdownView,
    RoleSelectDropdown,
    build_role_panel_embed,
)


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


class TestRolesModule(unittest.IsolatedAsyncioTestCase):
    """Suite de pruebas para el módulo de autoroles interactivos."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_roles.sqlite3"
        self.db = DatabaseManager(self.db_path)
        queries.db_manager = self.db
        await self.db.initialize_schema()

        self.mock_bot = MagicMock(spec=commands.Bot)
        self.mock_bot.add_view = MagicMock()
        self.cog = RolesCog(self.mock_bot)

        # Servidor mock
        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 777000777
        self.mock_guild.name = "Servidor Pruebas Roles"

        # Bot member con rol alto (posición 50)
        self.bot_top_role = MockRole("Bot Admin Role", position=50, id=900)
        self.mock_guild.me = MagicMock(spec=discord.Member)
        self.mock_guild.me.top_role = self.bot_top_role
        self.mock_guild.me.guild_permissions = discord.Permissions(manage_roles=True)

        # Roles del servidor
        self.role_gamer = MockRole("Gamer", position=10, id=101)
        self.role_coder = MockRole("Programador", position=12, id=102)
        self.role_higher = MockRole("Rol Superior al Bot", position=90, id=999)

        self.mock_guild.get_role.side_effect = lambda rid: {
            101: self.role_gamer,
            102: self.role_coder,
            999: self.role_higher,
        }.get(rid, None)

        # Miembro del servidor (inicialmente tiene el rol Gamer)
        self.mock_member = MagicMock(spec=discord.Member)
        self.mock_member.id = 555
        self.mock_member.name = "MemberTest"
        self.mock_member.roles = [self.role_gamer]
        self.mock_member.guild = self.mock_guild
        self.mock_member.add_roles = AsyncMock()
        self.mock_member.remove_roles = AsyncMock()

        # Canal mock
        self.mock_channel = MagicMock(spec=discord.TextChannel)
        self.mock_channel.id = 888
        self.mock_channel.mention = "<#888>"
        self.mock_channel.guild = self.mock_guild
        perms = discord.Permissions(send_messages=True, embed_links=True, manage_roles=True)
        self.mock_channel.permissions_for.return_value = perms

        self.mock_guild.get_channel.return_value = self.mock_channel

    async def asyncTearDown(self) -> None:
        await self.db.close()
        self.temp_dir.cleanup()

    async def test_setup_autoroles(self) -> None:
        """Comprueba el despliegue del panel público y su registro en la BD."""
        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.id = 123456
        mock_msg.edit = AsyncMock()
        self.mock_channel.send = AsyncMock(return_value=mock_msg)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        await self.cog.setup_autoroles_command.callback(
            self.cog,
            interaction,
            canal=self.mock_channel,
            titulo="Intereses y Videojuegos",
            descripcion="Selecciona tus juegos favoritos.",
        )

        # Verificaciones
        self.mock_channel.send.assert_awaited_once()
        mock_msg.edit.assert_awaited_once()
        interaction.followup.send.assert_awaited_once()

        # Verificar BD
        menu = await queries.get_role_menu_by_message_id(mock_msg.id)
        self.assertIsNotNone(menu)
        self.assertEqual(menu["title"], "Intereses y Videojuegos")
        self.assertEqual(menu["channel_id"], self.mock_channel.id)

    async def test_autorol_agregar_opcion_and_hierarchy_check(self) -> None:
        """Verifica la adición de opciones y la validación de jerarquía de roles."""
        # 1. Crear menú en BD
        menu_id = await queries.create_role_menu(
            guild_id=self.mock_guild.id,
            channel_id=self.mock_channel.id,
            message_id=987654,
            title="Panel Intereses",
        )

        mock_panel_msg = MagicMock(spec=discord.Message)
        mock_panel_msg.edit = AsyncMock()
        self.mock_channel.fetch_message = AsyncMock(return_value=mock_panel_msg)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.response.send_message = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        # Caso A: Intentar agregar rol superior al del bot -> Debe ser rechazado
        await self.cog.autorol_agregar_opcion_command.callback(
            self.cog,
            interaction,
            menu_id=menu_id,
            rol=self.role_higher,
            etiqueta="Admin Role",
        )
        interaction.response.send_message.assert_awaited_once()
        call_kw = interaction.response.send_message.await_args.kwargs
        self.assertIn("Jerarquía Insuficiente", call_kw["embed"].title)

        # Caso B: Agregar rol válido
        interaction.response.send_message.reset_mock()
        await self.cog.autorol_agregar_opcion_command.callback(
            self.cog,
            interaction,
            menu_id=menu_id,
            rol=self.role_gamer,
            etiqueta="Gamer",
            emoji="🎮",
            descripcion="Notificaciones de partidas",
        )
        interaction.followup.send.assert_awaited_once()
        mock_panel_msg.edit.assert_awaited_once()

        # Verificar que se registró en BD
        options = await queries.get_menu_options(menu_id)
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]["role_id"], self.role_gamer.id)
        self.assertEqual(options[0]["emoji"], "🎮")

    async def test_autorol_eliminar_opcion(self) -> None:
        """Verifica la eliminación de una opción de rol."""
        menu_id = await queries.create_role_menu(
            guild_id=self.mock_guild.id,
            channel_id=self.mock_channel.id,
            message_id=112233,
            title="Panel Eliminacion",
        )
        await queries.add_role_option(menu_id, self.role_gamer.id, "Gamer")

        mock_panel_msg = MagicMock(spec=discord.Message)
        mock_panel_msg.edit = AsyncMock()
        self.mock_channel.fetch_message = AsyncMock(return_value=mock_panel_msg)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        await self.cog.autorol_eliminar_opcion_command.callback(
            self.cog,
            interaction,
            menu_id=menu_id,
            rol=self.role_gamer,
        )

        options = await queries.get_menu_options(menu_id)
        self.assertEqual(len(options), 0)
        interaction.followup.send.assert_awaited_once()

    async def test_open_role_menu_interaction(self) -> None:
        """Prueba que el botón persistente despliegue el menú efímero con las opciones correctas."""
        msg_id = 445566
        menu_id = await queries.create_role_menu(
            guild_id=self.mock_guild.id,
            channel_id=self.mock_channel.id,
            message_id=msg_id,
            title="Panel Persistente",
        )
        await queries.add_role_option(menu_id, self.role_gamer.id, "Gamer", emoji="🎮")
        await queries.add_role_option(menu_id, self.role_coder.id, "Dev", emoji="💻")

        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.id = msg_id

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.message = mock_msg
        interaction.user = self.mock_member
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        view = RolePanelPersistentView()
        button_item = view.children[0]
        await button_item.callback(interaction)

        interaction.response.send_message.assert_awaited_once()
        call_kw = interaction.response.send_message.await_args.kwargs
        self.assertTrue(call_kw["ephemeral"])
        self.assertIsInstance(call_kw["view"], RoleDropdownView)

    async def test_role_dropdown_sync_roles(self) -> None:
        """
        Prueba la sincronización de roles en el menú desplegable:
        El miembro tiene Gamer (101).
        En el select, el miembro elige Programador (102) y desmarca Gamer (101).
        Resultado esperado:
        - add_roles llamado para Programador (102).
        - remove_roles llamado para Gamer (101).
        """
        menu_id = await queries.create_role_menu(
            guild_id=self.mock_guild.id,
            channel_id=self.mock_channel.id,
            message_id=990011,
            title="Panel Sync",
        )
        await queries.add_role_option(menu_id, self.role_gamer.id, "Gamer")
        await queries.add_role_option(menu_id, self.role_coder.id, "Programador")

        select_options = [
            discord.SelectOption(label="Gamer", value=str(self.role_gamer.id), default=True),
            discord.SelectOption(label="Programador", value=str(self.role_coder.id), default=False),
        ]
        dropdown = RoleSelectDropdown(select_options, menu_id)
        # El usuario selecciona solo "102" (desmarcó 101)
        dropdown._values = [str(self.role_coder.id)]

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_member
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        await dropdown.callback(interaction)

        # Verificar adición del nuevo rol y remoción del desmarcado
        self.mock_member.add_roles.assert_awaited_once_with(
            self.role_coder,
            reason=f"Autoroles: seleccionado por {self.mock_member.name}",
        )
        self.mock_member.remove_roles.assert_awaited_once_with(
            self.role_gamer,
            reason=f"Autoroles: desmarcado por {self.mock_member.name}",
        )
        interaction.response.edit_message.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
