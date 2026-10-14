"""
Pruebas Automatizadas para el Módulo de Anuncios (tests/test_announcements.py).
-------------------------------------------------------------------------------
Evalúa:
1. Configuración del canal oficial (/setup_anuncios).
2. Apertura del modal y generación de vista previa (/anuncio).
3. Confirmación de publicación y difusión en canal global con menciones.
4. Cancelación de borrador desde el canal privado.
5. Consulta del historial de anuncios (/anuncios_historial).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
from discord import app_commands
from discord.ext import commands

from database.connection import DatabaseManager
import database.queries as queries
from cogs.announcements import (
    AnnouncementsCog,
    AnnouncementModal,
    AnnouncementPreviewView,
)


class TestAnnouncementsModule(unittest.IsolatedAsyncioTestCase):
    """Suite de pruebas unitarias para el módulo de anuncios oficiales."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_announcements.sqlite3"
        self.db = DatabaseManager(self.db_path)
        queries.db_manager = self.db
        await self.db.initialize_schema()

        self.mock_bot = MagicMock(spec=commands.Bot)
        self.cog = AnnouncementsCog(self.mock_bot)

        # Servidor mock
        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 666000666
        self.mock_guild.name = "Servidor Pruebas Anuncios"

        # Staff User
        self.mock_staff = MagicMock(spec=discord.Member)
        self.mock_staff.id = 12345
        self.mock_staff.name = "StaffMember"
        self.mock_staff.display_name = "StaffMember"
        self.mock_staff.mention = "<@12345>"
        self.mock_staff.display_avatar = MagicMock(url="https://img.com/staff.png")
        self.mock_staff.guild_permissions = discord.Permissions(administrator=True)
        self.mock_staff.guild = self.mock_guild

        # Canales mock
        self.public_channel = MagicMock(spec=discord.TextChannel)
        self.public_channel.id = 7001
        self.public_channel.name = "anuncios-globales"
        self.public_channel.mention = "<#7001>"
        self.public_channel.guild = self.mock_guild
        self.public_channel.send = AsyncMock()

        self.mod_logs_channel = MagicMock(spec=discord.TextChannel)
        self.mod_logs_channel.id = 7002
        self.mod_logs_channel.name = "mod-logs"
        self.mod_logs_channel.mention = "<#7002>"
        self.mod_logs_channel.guild = self.mock_guild
        self.mod_logs_channel.send = AsyncMock()

        perms = discord.Permissions(send_messages=True, embed_links=True)
        self.public_channel.permissions_for.return_value = perms

        self.mock_guild.get_channel.side_effect = lambda cid: {
            7001: self.public_channel,
            7002: self.mod_logs_channel,
        }.get(cid, None)

        self.mock_guild.get_member.side_effect = lambda uid: {
            12345: self.mock_staff,
        }.get(uid, None)

    async def asyncTearDown(self) -> None:
        await self.db.close()
        self.temp_dir.cleanup()

    async def test_setup_anuncios(self) -> None:
        """Verifica la configuración del canal global de anuncios."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_staff
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await self.cog.setup_anuncios_command.callback(self.cog, interaction, self.public_channel)

        settings = await queries.get_guild_settings(self.mock_guild.id)
        self.assertIsNotNone(settings)
        self.assertEqual(settings["announcements_channel_id"], self.public_channel.id)
        interaction.response.send_message.assert_awaited_once()

    async def test_anuncio_modal_submission_creates_preview(self) -> None:
        """Comprueba que al enviar el modal se genere la vista previa con botones."""
        modal = AnnouncementModal(bot=self.mock_bot, mention_type="@here")
        modal.titulo._value = "Gran Actualización v1.0"
        modal.contenido._value = "Estamos felices de presentar las nuevas características del bot."
        modal.banner_url._value = "https://i.imgur.com/valido.png"

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_staff
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await modal.on_submit(interaction)

        interaction.response.send_message.assert_awaited_once()
        call_kw = interaction.response.send_message.await_args.kwargs
        self.assertIn("Vista Previa", call_kw["content"])
        self.assertIsInstance(call_kw["view"], AnnouncementPreviewView)
        self.assertEqual(call_kw["embed"].title, "Gran Actualización v1.0")

    async def test_anuncio_preview_confirm_publish(self) -> None:
        """Evalúa la publicación oficial: envío a canal global, logs en BD y #mod-logs."""
        # Configurar canales
        await queries.update_guild_setting(self.mock_guild.id, "announcements_channel_id", self.public_channel.id)
        await queries.update_guild_setting(self.mock_guild.id, "mod_logs_channel_id", self.mod_logs_channel.id)

        # Mock del mensaje publicado en Discord
        mock_published = MagicMock(spec=discord.Message)
        mock_published.id = 999888
        mock_published.jump_url = "https://discord.com/channels/1/2/999888"
        self.public_channel.send = AsyncMock(return_value=mock_published)

        preview_view = AnnouncementPreviewView(
            bot=self.mock_bot,
            title="Mantenimiento Programado",
            content="Los servidores se reiniciarán a las 12:00 UTC.",
            banner_url=None,
            mention_type="@everyone",
            author_id=self.mock_staff.id,
        )

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_staff
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        # Botón de confirmación (children[0])
        publish_btn = preview_view.children[0]
        await publish_btn.callback(interaction)

        # Verificaciones en el canal público
        self.public_channel.send.assert_awaited_once()
        pub_kwargs = self.public_channel.send.await_args.kwargs
        self.assertEqual(pub_kwargs["content"], "@everyone")
        self.assertEqual(pub_kwargs["embed"].title, "Mantenimiento Programado")

        # Verificación en base de datos
        history = await queries.get_announcements_by_guild(self.mock_guild.id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["title"], "Mantenimiento Programado")
        self.assertEqual(history[0]["mention_type"], "@everyone")
        self.assertEqual(history[0]["published_message_id"], 999888)

        # Verificación en #mod-logs
        self.mod_logs_channel.send.assert_awaited_once()

        # Verificación de edición del mensaje de vista previa
        interaction.response.edit_message.assert_awaited_once()

    async def test_anuncio_preview_cancel(self) -> None:
        """Comprueba que cancelar el anuncio descarte la publicación sin afectar el canal público."""
        preview_view = AnnouncementPreviewView(
            bot=self.mock_bot,
            title="Anuncio Cancelado",
            content="Este contenido nunca se publicará.",
            banner_url=None,
            mention_type="none",
            author_id=self.mock_staff.id,
        )

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_staff
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        # Botón de cancelar (children[1])
        cancel_btn = preview_view.children[1]
        await cancel_btn.callback(interaction)

        self.public_channel.send.assert_not_awaited()
        interaction.response.edit_message.assert_awaited_once()
        call_kw = interaction.response.edit_message.await_args.kwargs
        self.assertIn("Cancelada", call_kw["embed"].title)

    async def test_anuncios_historial(self) -> None:
        """Verifica la consulta del historial de anuncios mediante comando slash."""
        # Insertar registros en BD
        await queries.log_announcement(
            guild_id=self.mock_guild.id,
            author_id=self.mock_staff.id,
            target_channel_id=self.public_channel.id,
            published_message_id=111,
            title="Anuncio 1",
            content="Contenido 1",
            mention_type="none",
        )
        await queries.log_announcement(
            guild_id=self.mock_guild.id,
            author_id=self.mock_staff.id,
            target_channel_id=self.public_channel.id,
            published_message_id=222,
            title="Anuncio 2",
            content="Contenido 2",
            mention_type="@here",
        )

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_staff
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await self.cog.anuncios_historial_command.callback(self.cog, interaction, limite=5)

        interaction.response.send_message.assert_awaited_once()
        call_kw = interaction.response.send_message.await_args.kwargs
        self.assertEqual(len(call_kw["embed"].fields), 2)

    async def test_anuncio_canal_command_opens_modal(self) -> None:
        """Prueba que /anuncio_canal valide permisos y abra el modal con el canal destino."""
        rules_channel = MagicMock(spec=discord.TextChannel)
        rules_channel.id = 7003
        rules_channel.name = "reglas"
        rules_channel.mention = "<#7003>"
        rules_channel.permissions_for.return_value = discord.Permissions(send_messages=True, embed_links=True)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_staff
        interaction.response = MagicMock()
        interaction.response.send_modal = AsyncMock()

        await self.cog.anuncio_canal_command.callback(self.cog, interaction, canal=rules_channel)

        interaction.response.send_modal.assert_awaited_once()
        sent_modal = interaction.response.send_modal.await_args.args[0]
        self.assertIsInstance(sent_modal, AnnouncementModal)
        self.assertEqual(sent_modal.target_channel, rules_channel)

    async def test_anuncio_canal_confirm_publishes_to_specific_channel(self) -> None:
        """Comprueba que la confirmación de AnnouncementPreviewView con target_channel publique en ese canal."""
        rules_channel = MagicMock(spec=discord.TextChannel)
        rules_channel.id = 7003
        rules_channel.name = "reglas"
        rules_channel.mention = "<#7003>"
        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.id = 555666
        mock_msg.jump_url = "https://discord.com/channels/1/7003/555666"
        rules_channel.send = AsyncMock(return_value=mock_msg)

        preview_view = AnnouncementPreviewView(
            bot=self.mock_bot,
            title="Normas Oficiales del Servidor",
            content="1. Respeto mutuo.\n2. No spam.",
            banner_url=None,
            mention_type="none",
            author_id=self.mock_staff.id,
            target_channel=rules_channel,
        )

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.mock_staff
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        publish_btn = preview_view.children[0]
        await publish_btn.callback(interaction)

        rules_channel.send.assert_awaited_once()
        send_kwargs = rules_channel.send.await_args.kwargs
        self.assertEqual(send_kwargs["embed"].title, "Normas Oficiales del Servidor")

        # Verificación en BD
        history = await queries.get_announcements_by_guild(self.mock_guild.id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["target_channel_id"], 7003)


if __name__ == "__main__":
    unittest.main()
