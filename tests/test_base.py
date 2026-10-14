"""
Suite de Pruebas Automatizadas para la Arquitectura Base (tests/test_base.py).
-----------------------------------------------------------------------------
Valida el funcionamiento de:
1. Capa de Base de Datos SQLite (Conexión asíncrona, DDL de 7 tablas y operaciones CRUD).
2. Constructor de Embeds (utils/embeds.py).
3. Verificaciones de Jerarquía y Permisos (utils/checks.py).
4. Inicialización y registro del Cog General (cogs/general.py).
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
from discord.ext import commands

from database.connection import DatabaseManager
import database.queries as queries
from utils.embeds import EmbedBuilder, EmbedColors
from utils.checks import can_moderate_member, is_staff_or_admin
from cogs.general import GeneralCog


class TestBaseArchitecture(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias e integración de la arquitectura base del bot."""

    async def asyncSetUp(self) -> None:
        """Crea una base de datos SQLite temporal en disco para cada prueba."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_bot.sqlite3"

        # Inicializar DatabaseManager con la BD temporal
        self.db = DatabaseManager(self.db_path)
        queries.db_manager = self.db  # Apuntar las queries a la base de pruebas

    async def asyncTearDown(self) -> None:
        """Cierra la conexión y elimina los archivos temporales."""
        await self.db.close()
        self.temp_dir.cleanup()

    # ==========================================================================
    # 1. PRUEBAS DE BASE DE DATOS
    # ==========================================================================

    async def test_01_schema_initialization(self) -> None:
        """Verifica que las 7 tablas del sistema se creen correctamente."""
        await self.db.initialize_schema()
        conn = await self.db.connect()

        async with conn.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
            rows = await cursor.fetchall()
            table_names = {r[0] for r in rows}

        expected_tables = {
            "guild_settings",
            "infractions",
            "tickets",
            "suggestions",
            "role_menus",
            "role_options",
            "announcements",
        }
        self.assertTrue(expected_tables.issubset(table_names), f"Faltan tablas. Encontradas: {table_names}")

    async def test_02_guild_settings_crud(self) -> None:
        """Prueba insertar y recuperar configuraciones del servidor."""
        await self.db.initialize_schema()
        guild_id = 9876543210

        # Inicialmente no existe
        settings = await queries.get_guild_settings(guild_id)
        self.assertIsNone(settings)

        # Actualizar canal de mod-logs
        await queries.update_guild_setting(guild_id, "mod_logs_channel_id", 111222333)
        settings = await queries.get_guild_settings(guild_id)
        self.assertIsNotNone(settings)
        self.assertEqual(settings["mod_logs_channel_id"], 111222333)

        # Actualizar canal de anuncios
        await queries.update_guild_setting(guild_id, "announcements_channel_id", 444555666)
        settings = await queries.get_guild_settings(guild_id)
        self.assertEqual(settings["announcements_channel_id"], 444555666)
        self.assertEqual(settings["mod_logs_channel_id"], 111222333)

    async def test_03_infractions_crud(self) -> None:
        """Prueba registrar sanciones en el historial del usuario."""
        await self.db.initialize_schema()
        guild_id = 12345
        user_id = 67890
        mod_id = 11111

        infraction_id = await queries.add_infraction(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=mod_id,
            action_type="WARN",
            reason="Spam en canal general",
        )
        self.assertGreater(infraction_id, 0)

        history = await queries.get_user_infractions(guild_id, user_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["action_type"], "WARN")
        self.assertEqual(history[0]["reason"], "Spam en canal general")

    async def test_04_tickets_and_suggestions_crud(self) -> None:
        """Prueba las operaciones básicas de tickets y sugerencias."""
        await self.db.initialize_schema()
        guild_id = 100
        user_id = 200

        # Crear ticket
        t_id = await queries.create_ticket(guild_id, channel_id=3001, user_id=user_id, subject="Ayuda con rol")
        self.assertGreater(t_id, 0)

        t_data = await queries.get_ticket_by_channel(3001)
        self.assertIsNotNone(t_data)
        self.assertEqual(t_data["status"], "OPEN")

        # Cerrar ticket
        await queries.close_ticket(channel_id=3001, transcript_url="https://logs.local/transcript.html")
        t_data = await queries.get_ticket_by_channel(3001)
        self.assertEqual(t_data["status"], "CLOSED")
        self.assertEqual(t_data["transcript_url"], "https://logs.local/transcript.html")

        # Crear sugerencia
        s_id = await queries.create_suggestion(guild_id, message_id=5001, user_id=user_id, content="Añadir canal de arte")
        self.assertGreater(s_id, 0)

        # Actualizar sugerencia
        await queries.update_suggestion_status(s_id, status="APPROVED", staff_comment="Excelente idea", reviewed_by=999)
        conn = await self.db.connect()
        async with conn.execute("SELECT * FROM suggestions WHERE suggestion_id = ?;", (s_id,)) as cur:
            s_row = await cur.fetchone()
            self.assertEqual(s_row["status"], "APPROVED")
            self.assertEqual(s_row["staff_comment"], "Excelente idea")

    async def test_05_announcements_and_roles_crud(self) -> None:
        """Prueba el registro de anuncios y paneles de autoroles."""
        await self.db.initialize_schema()
        guild_id = 500

        # Autoroles
        menu_id = await queries.create_role_menu(guild_id, channel_id=601, message_id=701, title="Elige tus juegos")
        self.assertGreater(menu_id, 0)
        opt_id = await queries.add_role_option(menu_id, role_id=888, label="Minecraft", emoji="⛏️", description="Avisos del servidor")
        self.assertGreater(opt_id, 0)
        options = await queries.get_menu_options(menu_id)
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]["label"], "Minecraft")

        # Anuncios
        ann_id = await queries.log_announcement(
            guild_id=guild_id,
            author_id=123,
            target_channel_id=901,
            published_message_id=902,
            title="Evento de fin de semana",
            content="Los esperamos a las 18:00 UTC",
            mention_type="@everyone",
        )
        self.assertGreater(ann_id, 0)

    # ==========================================================================
    # 2. PRUEBAS DE UTILIDADES (EmbedBuilder y Checks)
    # ==========================================================================

    def test_06_embed_builder(self) -> None:
        """Valida que EmbedBuilder construya los embeds con colores y footers correctos."""
        embed_success = EmbedBuilder.success("Operación Exitosa", "Se aplicó el cambio.")
        self.assertEqual(embed_success.color, EmbedColors.SUCCESS)
        self.assertIn("Operación Exitosa", embed_success.title or "")
        self.assertIn("Bot Discord", embed_success.footer.text or "")

        embed_error = EmbedBuilder.error("Error Grave", "Fallo de conexión.")
        self.assertEqual(embed_error.color, EmbedColors.ERROR)

        embed_ann = EmbedBuilder.announcement("Gran Novedad", "Texto del anuncio", image_url="https://img.com/banner.png")
        self.assertEqual(embed_ann.color, EmbedColors.ANNOUNCEMENT)
        self.assertEqual(embed_ann.image.url, "https://img.com/banner.png")

    def test_07_role_hierarchy_checks(self) -> None:
        """Prueba las reglas de jerarquía entre miembros de Discord."""
        # Clase auxiliar para emular roles comparables por su posición
        class MockRole:
            def __init__(self, name: str, position: int):
                self.name = name
                self.position = position

            def __le__(self, other: MockRole) -> bool:
                return self.position <= other.position

            def __lt__(self, other: MockRole) -> bool:
                return self.position < other.position

            def __ge__(self, other: MockRole) -> bool:
                return self.position >= other.position

            def __gt__(self, other: MockRole) -> bool:
                return self.position > other.position

        # Mock de Servidor
        mock_guild = MagicMock(spec=discord.Guild)
        mock_guild.owner_id = 1000

        # Roles con diferentes posiciones
        role_high = MockRole("Admin", 10)
        role_mid = MockRole("Mod", 5)
        role_low = MockRole("Usuario", 1)

        # Miembros
        mod = MagicMock(spec=discord.Member)
        mod.id = 2000
        mod.guild = mock_guild
        mod.top_role = role_high

        target = MagicMock(spec=discord.Member)
        target.id = 3000
        target.guild = mock_guild
        target.top_role = role_low

        bot_member = MagicMock(spec=discord.Member)
        bot_member.id = 4000
        bot_member.top_role = role_high
        mock_guild.me = bot_member

        # Caso 1: Mod (10) vs Usuario (1) con Bot (10) -> Válido
        allowed, msg = can_moderate_member(mod, target)
        self.assertTrue(allowed, msg)

        # Caso 2: Auto-sanción -> Denegado
        allowed, msg = can_moderate_member(mod, mod)
        self.assertFalse(allowed)
        self.assertIn("a ti mismo", msg)

        # Caso 3: Mod intenta sancionar al dueño -> Denegado
        owner = MagicMock(spec=discord.Member)
        owner.id = 1000
        owner.guild = mock_guild
        allowed, msg = can_moderate_member(mod, owner)
        self.assertFalse(allowed)
        self.assertIn("dueño del servidor", msg)

        # Caso 4: Objetivo con rol superior al moderador -> Denegado
        mod_inferior = MagicMock(spec=discord.Member)
        mod_inferior.id = 2001
        mod_inferior.guild = mock_guild
        mod_inferior.top_role = role_mid

        target_superior = MagicMock(spec=discord.Member)
        target_superior.id = 3001
        target_superior.guild = mock_guild
        target_superior.top_role = role_high

        allowed, msg = can_moderate_member(mod_inferior, target_superior)
        self.assertFalse(allowed)
        self.assertIn("no tiene suficiente jerarquía", msg)

    # ==========================================================================
    # 3. PRUEBAS DEL COG GENERAL (/ping, /info, /help)
    # ==========================================================================

    async def test_08_general_cog_ping_interaction(self) -> None:
        """Prueba que el comando /ping responda correctamente a una interacción."""
        await self.db.initialize_schema()

        # Mock del bot
        mock_bot = MagicMock(spec=commands.Bot)
        mock_bot.latency = 0.045  # 45 ms

        cog = GeneralCog(mock_bot)

        # Mock de discord.Interaction
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response = MagicMock()
        mock_interaction.response.send_message = AsyncMock()

        # Ejecutar el comando ping
        await cog.ping_command.callback(cog, mock_interaction)

        # Verificar que se llamó a send_message con un embed
        mock_interaction.response.send_message.assert_called_once()
        _, kwargs = mock_interaction.response.send_message.call_args
        self.assertIn("embed", kwargs)
        embed = kwargs["embed"]
        self.assertIn("Pong!", embed.title or "")
        self.assertTrue(kwargs.get("ephemeral"))


if __name__ == "__main__":
    unittest.main()
