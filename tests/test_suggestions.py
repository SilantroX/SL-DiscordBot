"""
Pruebas Automatizadas para el Módulo de Sugerencias (tests/test_suggestions.py).
--------------------------------------------------------------------------------
Evalúa:
1. Configuración del canal oficial (/setup_suggestions).
2. Publicación de sugerencias (/sugerir) y validación de longitud.
3. Mecánica de votos persistentes (voto único, toggle, switch, prevención de auto-voto).
4. Resolución por parte del Staff (/responder_sugerencia) y desactivación de botones.
5. Consulta de sugerencias (/ver_sugerencia).
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
from utils.embeds import EmbedBuilder
from cogs.suggestions import SuggestionsCog, SuggestionVoteView


class TestSuggestionsModule(unittest.IsolatedAsyncioTestCase):
    """Suite completa de pruebas para el módulo de sugerencias."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_sug.sqlite3"
        self.db = DatabaseManager(self.db_path)
        queries.db_manager = self.db
        await self.db.initialize_schema()

        self.mock_bot = MagicMock(spec=commands.Bot)
        self.mock_bot.add_view = MagicMock()
        self.mock_bot.fetch_user = AsyncMock()
        self.cog = SuggestionsCog(self.mock_bot)

        # Servidor mock
        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 555555555
        self.mock_guild.name = "Servidor Pruebas Sugerencias"
        self.mock_guild.me = MagicMock(spec=discord.Member)

        # Usuarios mock
        self.author_user = MagicMock(spec=discord.Member)
        self.author_user.id = 111000111
        self.author_user.name = "Sugeridor"
        self.author_user.display_name = "Sugeridor"
        self.author_user.mention = "<@111000111>"
        self.author_user.display_avatar = MagicMock(url="https://img.com/sugeridor.png")
        self.author_user.guild = self.mock_guild
        self.author_user.send = AsyncMock()

        self.voter_user = MagicMock(spec=discord.Member)
        self.voter_user.id = 222000222
        self.voter_user.name = "Votante"
        self.voter_user.display_name = "Votante"
        self.voter_user.mention = "<@222000222>"
        self.voter_user.guild = self.mock_guild

        self.staff_user = MagicMock(spec=discord.Member)
        self.staff_user.id = 999000999
        self.staff_user.name = "StaffUser"
        self.staff_user.display_name = "StaffUser"
        self.staff_user.mention = "<@999000999>"
        self.staff_user.guild_permissions = discord.Permissions(administrator=True)
        self.staff_user.guild = self.mock_guild

        # Canal de sugerencias
        self.mock_channel = MagicMock(spec=discord.TextChannel)
        self.mock_channel.id = 888888888
        self.mock_channel.name = "sugerencias"
        self.mock_channel.mention = "<#888888888>"
        self.mock_channel.guild = self.mock_guild

        perms = discord.Permissions(send_messages=True, embed_links=True)
        self.mock_channel.permissions_for.return_value = perms

        self.mock_guild.get_channel.return_value = self.mock_channel
        self.mock_guild.get_member.side_effect = lambda uid: {
            self.author_user.id: self.author_user,
            self.voter_user.id: self.voter_user,
            self.staff_user.id: self.staff_user,
        }.get(uid, None)

    async def asyncTearDown(self) -> None:
        await self.db.close()
        self.temp_dir.cleanup()

    async def test_setup_suggestions(self) -> None:
        """Verifica la configuración del canal oficial de sugerencias."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.staff_user
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await self.cog.setup_suggestions_command.callback(self.cog, interaction, self.mock_channel)

        settings = await queries.get_guild_settings(self.mock_guild.id)
        self.assertIsNotNone(settings)
        self.assertEqual(settings["suggestions_channel_id"], self.mock_channel.id)
        interaction.response.send_message.assert_awaited_once()

    async def test_sugerir_validation_short_text(self) -> None:
        """Comprueba que se rechacen textos demasiado cortos (< 10 caracteres)."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.author_user
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await self.cog.sugerir_command.callback(self.cog, interaction, "hola")

        interaction.response.send_message.assert_awaited_once()
        call_kwargs = interaction.response.send_message.await_args.kwargs
        self.assertIn("Demasiado Corto", call_kwargs["embed"].title)

    async def test_sugerir_successful_flow(self) -> None:
        """Evalúa el flujo completo de publicación de una sugerencia en el canal oficial."""
        # 1. Configurar canal
        await queries.update_guild_setting(self.mock_guild.id, "suggestions_channel_id", self.mock_channel.id)

        # Mock del mensaje enviado al canal
        mock_sent_msg = MagicMock(spec=discord.Message)
        mock_sent_msg.id = 777777777
        mock_sent_msg.jump_url = "https://discord.com/channels/1/2/3"
        mock_sent_msg.edit = AsyncMock()
        self.mock_channel.send = AsyncMock(return_value=mock_sent_msg)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.author_user
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        suggestion_text = "Implementar un canal de debates semanales de tecnología."
        await self.cog.sugerir_command.callback(self.cog, interaction, suggestion_text)

        # Verificaciones
        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        self.mock_channel.send.assert_awaited_once()
        mock_sent_msg.edit.assert_awaited_once()
        interaction.followup.send.assert_awaited_once()

        # Comprobar registro en BD
        sug = await queries.get_suggestion_by_message_id(mock_sent_msg.id)
        self.assertIsNotNone(sug)
        self.assertEqual(sug["user_id"], self.author_user.id)
        self.assertEqual(sug["content"], suggestion_text)
        self.assertEqual(sug["status"], "PENDING")
        self.assertEqual(sug["upvotes"], 0)
        self.assertEqual(sug["downvotes"], 0)

    async def test_voting_mechanics(self) -> None:
        """Prueba toda la lógica de votación: prevención de auto-voto, toggle, switch y votos múltiples."""
        # Crear sugerencia en base de datos
        msg_id = 999111999
        sug_id = await queries.create_suggestion(
            guild_id=self.mock_guild.id,
            message_id=msg_id,
            user_id=self.author_user.id,
            content="Añadir más emojis personalizados al servidor.",
        )

        view = SuggestionVoteView()
        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.id = msg_id
        mock_msg.edit = AsyncMock()

        # Caso 1: El autor intenta votar en su propia sugerencia
        author_interaction = MagicMock(spec=discord.Interaction)
        author_interaction.guild = self.mock_guild
        author_interaction.message = mock_msg
        author_interaction.user = self.author_user
        author_interaction.response = MagicMock()
        author_interaction.response.send_message = AsyncMock()

        await view._handle_vote(author_interaction, vote_type=1)
        author_interaction.response.send_message.assert_awaited_once()
        call_kw = author_interaction.response.send_message.await_args.kwargs
        self.assertIn("No puedes votar en tu propia sugerencia", call_kw["embed"].description)

        # Caso 2: Otro usuario vota a favor (+1)
        voter_interaction = MagicMock(spec=discord.Interaction)
        voter_interaction.guild = self.mock_guild
        voter_interaction.message = mock_msg
        voter_interaction.user = self.voter_user
        voter_interaction.response = MagicMock()
        voter_interaction.response.send_message = AsyncMock()

        await view._handle_vote(voter_interaction, vote_type=1)
        mock_msg.edit.assert_awaited_once()

        sug = await queries.get_suggestion(sug_id)
        self.assertEqual(sug["upvotes"], 1)
        self.assertEqual(sug["downvotes"], 0)

        # Caso 3: El mismo votante presiona otra vez a favor (+1) -> Toggle / Retirar voto
        mock_msg.edit.reset_mock()
        await view._handle_vote(voter_interaction, vote_type=1)
        sug = await queries.get_suggestion(sug_id)
        self.assertEqual(sug["upvotes"], 0)
        self.assertEqual(sug["downvotes"], 0)

        # Caso 4: Votar en contra (-1) y luego cambiar a favor (+1) -> Switch
        await view._handle_vote(voter_interaction, vote_type=-1)
        sug = await queries.get_suggestion(sug_id)
        self.assertEqual(sug["upvotes"], 0)
        self.assertEqual(sug["downvotes"], 1)

        await view._handle_vote(voter_interaction, vote_type=1)
        sug = await queries.get_suggestion(sug_id)
        self.assertEqual(sug["upvotes"], 1)
        self.assertEqual(sug["downvotes"], 0)

    async def test_responder_sugerencia_staff(self) -> None:
        """Verifica la resolución de sugerencias por el Staff (Aprobada, Rechazada, En Progreso)."""
        await queries.update_guild_setting(self.mock_guild.id, "suggestions_channel_id", self.mock_channel.id)

        msg_id = 444333222
        sug_id = await queries.create_suggestion(
            guild_id=self.mock_guild.id,
            message_id=msg_id,
            user_id=self.author_user.id,
            content="Organizar torneos mensuales de videojuegos.",
        )

        mock_target_msg = MagicMock(spec=discord.Message)
        mock_target_msg.edit = AsyncMock()
        self.mock_channel.fetch_message = AsyncMock(return_value=mock_target_msg)

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.user = self.staff_user
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        choice_approved = app_commands.Choice(name="Aprobada", value="APPROVED")
        await self.cog.responder_sugerencia_command.callback(
            self.cog,
            interaction,
            id=sug_id,
            estado=choice_approved,
            comentario="¡Excelente idea! Comenzaremos con el torneo el próximo fin de semana.",
        )

        # Verificaciones en BD
        sug = await queries.get_suggestion(sug_id)
        self.assertEqual(sug["status"], "APPROVED")
        self.assertEqual(sug["reviewed_by"], self.staff_user.id)
        self.assertIn("Excelente idea", sug["staff_comment"])

        # Verificación de edición del mensaje y notificación al autor
        mock_target_msg.edit.assert_awaited_once()
        self.author_user.send.assert_awaited_once()
        interaction.followup.send.assert_awaited_once()

    async def test_ver_sugerencia(self) -> None:
        """Evalúa la consulta de una sugerencia existente mediante /ver_sugerencia."""
        sug_id = await queries.create_suggestion(
            guild_id=self.mock_guild.id,
            message_id=123123123,
            user_id=self.author_user.id,
            content="Crear un canal exclusivo para recursos de programación.",
        )

        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.mock_guild
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()

        await self.cog.ver_sugerencia_command.callback(self.cog, interaction, id=sug_id)

        interaction.response.send_message.assert_awaited_once()
        call_kw = interaction.response.send_message.await_args.kwargs
        self.assertIn(f"Sugerencia #{sug_id}", call_kw["embed"].title)


if __name__ == "__main__":
    unittest.main()
