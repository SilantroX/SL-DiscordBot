"""
Módulo de Comandos Generales (cogs/general.py).
----------------------------------------------
Proporciona comandos de utilidad e información básica (/ping, /info, /help)
para verificar el estado del bot y de la base de datos en tiempo real.
"""

from __future__ import annotations

import sys
import time
import discord
from discord import app_commands
from discord.ext import commands

from database.connection import db_manager
from utils.embeds import EmbedBuilder, EmbedColors

# Versión del bot
BOT_VERSION = "0.0.0"


class GeneralCog(commands.Cog, name="General"):
    """Comandos informativos y de diagnóstico general."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="ping", description="Verifica la latencia del bot y la conexión a la base de datos.")
    async def ping_command(self, interaction: discord.Interaction) -> None:
        """Comprueba la latencia del WebSocket de Discord y mide el tiempo de respuesta de SQLite."""
        # Medir latencia de Discord
        ws_latency_ms = round(self.bot.latency * 1000, 2)

        # Medir latencia de la base de datos SQLite
        db_start = time.perf_counter()
        try:
            await db_manager.fetch_one("SELECT 1;")
            db_status = "🟢 Conectada"
            db_latency_ms = round((time.perf_counter() - db_start) * 1000, 2)
        except Exception as exc:
            db_status = f"🔴 Error: {exc}"
            db_latency_ms = -1

        embed = EmbedBuilder.base(
            title="🏓 Pong! - Estado del Sistema",
            color=EmbedColors.PRIMARY,
        )
        embed.add_field(name="⚡ Latencia Discord API", value=f"`{ws_latency_ms} ms`", inline=True)
        embed.add_field(name="💾 Base de Datos SQLite", value=f"{db_status} (`{db_latency_ms} ms`)", inline=True)
        embed.add_field(name="🏷️ Versión del Bot", value=f"`v{BOT_VERSION}`", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="info", description="Muestra información técnica, estadísticas y versión del bot.")
    async def info_command(self, interaction: discord.Interaction) -> None:
        """Proporciona detalles técnicos sobre el entorno de ejecución."""
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        embed = EmbedBuilder.base(
            title="🤖 Información y Estadísticas del Bot",
            description="Bot multipropósito modular para Discord programado en Python.",
            color=EmbedColors.PRIMARY,
        )
        embed.add_field(name="📌 Versión", value=f"`v{BOT_VERSION}`", inline=True)
        embed.add_field(name="🐍 Python", value=f"`{sys.version.split()[0]}`", inline=True)
        embed.add_field(name="📦 discord.py", value=f"`v{discord.__version__}`", inline=True)
        embed.add_field(name="⏱️ Tiempo Activo", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🌐 Servidores", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="👥 Usuarios en Caché", value=f"`{len(self.bot.users)}`", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Guía de módulos y comandos disponibles en el bot.")
    async def help_command(self, interaction: discord.Interaction) -> None:
        """Despliega una lista explicativa de los módulos que integran el bot."""
        embed = EmbedBuilder.base(
            title="📖 Menú de Ayuda y Módulos",
            description=(
                "Bienvenido al panel de ayuda. A continuación se detallan los módulos "
                "que conforman este bot:"
            ),
            color=EmbedColors.PRIMARY,
        )
        embed.add_field(
            name="🛡️ 1. Administración",
            value="`/kick`, `/ban`, `/unban`, `/timeout`, `/warn`, `/warnings`, `/clear`, `/setup admin`",
            inline=False,
        )
        embed.add_field(
            name="🎫 2. Tickets de Soporte",
            value="`/setup tickets`: Panel persistente con modales, canales dinámicos y transcripciones.",
            inline=False,
        )
        embed.add_field(
            name="💡 3. Sugerencias",
            value="`/sugerir <texto>`, `/sugerencia responder`: Embeds interactivos con votación 👍 / 👎.",
            inline=False,
        )
        embed.add_field(
            name="🎭 4. Autoroles",
            value="`/setup autoroles`: Selector de roles interactivo mediante botón y menú desplegable efímero.",
            inline=False,
        )
        embed.add_field(
            name="📢 5. Anuncios",
            value="`/anuncio`: Redacta en canal privado con vista previa y publica en el canal global de anuncios.",
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Función de entrada requerida por discord.py para registrar el Cog."""
    await bot.add_cog(GeneralCog(bot))
