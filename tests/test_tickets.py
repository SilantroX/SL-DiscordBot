"""
Pruebas Automatizadas para el Módulo de Tickets (tests/test_tickets.py).
----------------------------------------------------------------------
Evalúa:
1. Generación de transcripción en formato HTML (utils/transcript.py).
2. Configuración de categoría y canal de logs (/setup_tickets).
3. Despliegue del panel público (/ticket_panel).
4. Gestión de miembros en tickets (/ticket_add y /ticket_remove).
5. Interacción del formulario modal (TicketCreateModal) y controles (TicketControlView).
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
from utils.transcript import generate_ticket_transcript
from cogs.tickets import (
    TicketsCog,
    TicketCreateModal,
    TicketPanelPersistentView,
    TicketControlView,
)


class TestTicketsModule(unittest.IsolatedAsyncioTestCase):
    """Suite de pruebas para el módulo de tickets."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_tickets.sqlite3"
        self.db = DatabaseManager(self.db_path)
        queries.db_manager = self.db
        await self.db.initialize_schema()

        self.mock_bot = MagicMock(spec=commands.Bot)
        self.mock_bot.add_view = MagicMock()
        self.cog = TicketsCog(self.mock_bot)

        # Mocks de Discord
        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 111111111
        self.mock_guild.name = "Servidor Pruebas Tickets"
        self.mock_guild.default_role = MagicMock(spec=discord.Role)
        self.mock_guild.icon = None

        self.mock_user = MagicMock(spec=discord.Member)
        self.mock_user.id = 222222222
        self.mock_user.name = "TestUser"
        self.mock_user.display_name = "TestUser"
        self.mock_user.mention = "<@222222222>"
        self.mock_user.display_avatar = MagicMock(url="https://img.com/avatar.png")
        self.mock_user.guild = self.mock_guild

    async def asyncTearDown(self) -> None:
        await self.db.close()
        self.temp_dir.cleanup()

    def _create_interaction(self, user: Optional[discord.Member] = None) -> MagicMock:
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = user or self.mock_user
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.response.send_modal = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        return interaction

    # ==========================================================================
    # 1. PRUEBA DE TRANSCRIPCIONES HTML
    # ==========================================================================

    async def test_01_transcript_generation(self) -> None:
        """Verifica que el generador cree un archivo HTML válido con los mensajes."""
        mock_channel = MagicMock(spec=discord.TextChannel)
        mock_channel.name = "ticket-testuser-0001"
        mock_channel.guild = self.mock_guild

        # Mock de mensajes para history
        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.author = self.mock_user
        mock_msg.created_at = MagicMock()
        mock_msg.created_at.strftime = MagicMock(return_value="14/10/2026 12:00:00")
        mock_msg.clean_content = "Hola, necesito ayuda con mi rango."
        mock_msg.attachments = []

        async def mock_history(*args, **kwargs):
            yield mock_msg

        mock_channel.history = mock_history

        file_result = await generate_ticket_transcript(mock_channel)
        self.assertIsInstance(file_result, discord.File)
        self.assertTrue(file_result.filename.endswith(".html"))

        # Leer contenido del buffer
        html_content = file_result.fp.read().decode("utf-8")
        self.assertIn("Transcripción Oficial", html_content)
        self.assertIn("Hola, necesito ayuda con mi rango.", html_content)
        self.assertIn("TestUser", html_content)

    # ==========================================================================
    # 2. PRUEBA DE CONFIGURACIÓN Y PANEL
    # ==========================================================================

    async def test_02_setup_tickets(self) -> None:
        """Prueba /setup_tickets guardando categoría y canal de logs."""
        interaction = self._create_interaction()
        mock_cat = MagicMock(spec=discord.CategoryChannel)
        mock_cat.id = 333333333
        mock_cat.name = "Tickets Soporte"

        mock_logs = MagicMock(spec=discord.TextChannel)
        mock_logs.id = 444444444
        mock_logs.mention = "<#444444444>"

        await self.cog.setup_tickets_command.callback(self.cog, interaction, mock_cat, mock_logs)

        settings = await queries.get_guild_settings(self.mock_guild.id)
        self.assertEqual(settings["ticket_category_id"], 333333333)
        self.assertEqual(settings["ticket_logs_channel_id"], 444444444)
        interaction.response.send_message.assert_called_once()

    async def test_03_ticket_panel_deploy(self) -> None:
        """Prueba enviar el panel con la vista persistente."""
        interaction = self._create_interaction()
        mock_target = MagicMock(spec=discord.TextChannel)
        mock_target.send = AsyncMock()
        mock_target.mention = "<#555>"

        await self.cog.ticket_panel_command.callback(self.cog, interaction, canal=mock_target)

        mock_target.send.assert_called_once()
        _, kwargs = mock_target.send.call_args
        self.assertIsInstance(kwargs["view"], TicketPanelPersistentView)
        self.assertIn("embed", kwargs)

    # ==========================================================================
    # 3. PRUEBA DE MODAL Y CREACIÓN DE CANAL
    # ==========================================================================

    async def test_04_modal_submission_creates_channel(self) -> None:
        """Prueba que el modal cree el canal privado y lo inserte en la base de datos."""
        interaction = self._create_interaction()

        # Mock de canal creado
        mock_created_ch = MagicMock(spec=discord.TextChannel)
        mock_created_ch.id = 777888
        mock_created_ch.mention = "<#777888>"
        mock_created_ch.send = AsyncMock()
        self.mock_guild.create_text_channel = AsyncMock(return_value=mock_created_ch)

        modal = TicketCreateModal()
        modal.asunto._value = "Problema con Rol"
        modal.descripcion._value = "No he recibido mi rol de donador."

        await modal.on_submit(interaction)

        # Verificar que se creó el canal
        self.mock_guild.create_text_channel.assert_called_once()
        mock_created_ch.send.assert_called_once()

        # Verificar en base de datos
        ticket_row = await queries.get_ticket_by_channel(777888)
        self.assertIsNotNone(ticket_row)
        self.assertEqual(ticket_row["user_id"], self.mock_user.id)
        self.assertEqual(ticket_row["status"], "OPEN")
        self.assertEqual(ticket_row["subject"], "Problema con Rol")

    # ==========================================================================
    # 4. PRUEBA DE GESTIÓN DE MIEMBROS EN TICKET
    # ==========================================================================

    async def test_05_ticket_add_and_remove(self) -> None:
        """Prueba /ticket_add y /ticket_remove en un canal activo."""
        # Insertar ticket en base de datos para canal 999
        await queries.create_ticket(self.mock_guild.id, channel_id=999, user_id=self.mock_user.id, subject="Prueba")

        interaction = self._create_interaction()
        mock_ch = MagicMock(spec=discord.TextChannel)
        mock_ch.id = 999
        mock_ch.set_permissions = AsyncMock()
        interaction.channel = mock_ch

        target_member = MagicMock(spec=discord.Member)
        target_member.id = 333444
        target_member.mention = "<@333444>"

        # Agregar miembro
        await self.cog.ticket_add_command.callback(self.cog, interaction, target_member)
        mock_ch.set_permissions.assert_called_once()

        # Remover miembro
        interaction_rem = self._create_interaction()
        interaction_rem.channel = mock_ch
        await self.cog.ticket_remove_command.callback(self.cog, interaction_rem, target_member)
        self.assertEqual(mock_ch.set_permissions.call_count, 2)


if __name__ == "__main__":
    unittest.main()
