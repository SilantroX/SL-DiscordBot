"""
Punto de Entrada Principal del Bot de Discord (main.py).
--------------------------------------------------------
Versión: 0.0.0
Inicializa el cliente de Discord, configura los intents privilegiados, inicializa
la base de datos SQLite, carga dinámicamente todos los Cogs y sincroniza el árbol
de comandos Slash (app_commands).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import config
from database.connection import db_manager
from utils.embeds import EmbedBuilder

# Configuración del sistema de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bot.main")


class DiscordBot(commands.Bot):
    """Subclase personalizada de commands.Bot con ciclo de vida asíncrono avanzado."""

    def __init__(self) -> None:
        # Configuración de Gateway Intents (Privileged Intents deben estar activados en Developer Portal)
        intents = discord.Intents.default()
        intents.members = True          # Requerido para moderación, autoroles y menciones
        intents.message_content = True  # Requerido para leer contenido de mensajes y comandos

        super().__init__(
            command_prefix=config.command_prefix if config else "!",
            intents=intents,
            help_command=None,  # Usamos nuestro propio comando slash /help
        )

    async def setup_hook(self) -> None:
        """Gancho asíncrono ejecutado antes de que el bot inicie la sesión en Discord."""
        logger.info("--- INICIANDO CICLO DE SETUP ASÍNCRONO ---")

        # 1. Inicialización de la Base de Datos SQLite
        try:
            await db_manager.initialize_schema()
        except Exception as exc:
            logger.critical("Error fatal al inicializar la base de datos: %s", exc)
            raise

        # 2. Carga dinámica de todos los módulos en la carpeta 'cogs/'
        cogs_dir = Path(__file__).resolve().parent / "cogs"
        if cogs_dir.exists():
            for file in cogs_dir.glob("*.py"):
                if file.name.startswith("__"):
                    continue
                cog_name = f"cogs.{file.stem}"
                try:
                    await self.load_extension(cog_name)
                    logger.info("🧩 Cog cargado exitosamente: %s", cog_name)
                except Exception as exc:
                    logger.error("❌ Error al cargar el cog %s: %s", cog_name, exc, exc_info=True)

        # 3. Sincronización del árbol de comandos Slash
        try:
            if config and config.guild_id:
                guild_obj = discord.Object(id=config.guild_id)
                self.tree.copy_global_to(guild=guild_obj)
                synced = await self.tree.sync(guild=guild_obj)
                logger.info(
                    "⚡ Sincronización instantánea en Servidor de Pruebas (ID: %s): %d comandos registrados.",
                    config.guild_id,
                    len(synced),
                )
            else:
                synced = await self.tree.sync()
                logger.info("🌐 Sincronización Global de comandos Slash: %d comandos registrados.", len(synced))
        except Exception as exc:
            logger.error("Error al sincronizar comandos Slash: %s", exc)

    async def on_ready(self) -> None:
        """Evento emitido cuando el bot se ha conectado y autenticado con éxito."""
        user = self.user
        if user:
            logger.info("==================================================")
            logger.info("🎉 Bot conectado con éxito como: %s (ID: %s)", user.name, user.id)
            logger.info("🌐 Conectado a %d servidor(es)", len(self.guilds))
            logger.info("⚡ Latencia actual: %.2f ms", self.bot_latency_ms)
            logger.info("==================================================")

        # Establecer presencia visual personalizada y motivadora
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="SilantroLabs • Innovando el futuro 🚀 (/help)",
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    @property
    def bot_latency_ms(self) -> float:
        """Retorna la latencia en milisegundos."""
        return round(self.latency * 1000, 2)

    async def close(self) -> None:
        """Garantiza el cierre limpio de la base de datos al apagar el bot."""
        logger.info("Cerrando sesión y liberando recursos...")
        await db_manager.close()
        await super().close()


# Instancia del bot
bot = DiscordBot()


# ==============================================================================
# MANEJADOR GLOBAL DE ERRORES PARA COMANDOS SLASH
# ==============================================================================

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    """Captura errores ocurridos durante la ejecución de cualquier comando Slash."""
    if isinstance(error, app_commands.MissingPermissions):
        missing = ", ".join(f"`{perm}`" for perm in error.missing_permissions)
        embed = EmbedBuilder.error(
            title="Permisos Insuficientes",
            description=f"No dispones de los permisos requeridos para usar este comando:\n{missing}",
        )
    elif isinstance(error, app_commands.BotMissingPermissions):
        missing = ", ".join(f"`{perm}`" for perm in error.missing_permissions)
        embed = EmbedBuilder.error(
            title="Permisos Faltantes en el Bot",
            description=f"Necesito los siguientes permisos en el servidor para ejecutar esta acción:\n{missing}",
        )
    elif isinstance(error, app_commands.CommandOnCooldown):
        embed = EmbedBuilder.warning(
            title="Comando en Enfriamiento",
            description=f"Por favor espera `{error.retry_after:.1f}s` antes de volver a usar este comando.",
        )
    elif isinstance(error, app_commands.CheckFailure):
        embed = EmbedBuilder.error(
            title="Acceso Denegado",
            description=str(error) or "No cumples con las condiciones requeridas para ejecutar este comando.",
        )
    else:
        logger.error("Error no controlado en comando slash: %s", error, exc_info=True)
        embed = EmbedBuilder.error(
            title="Error Inesperado",
            description="Ha ocurrido un error interno al procesar este comando. Por favor contacta al administrador.",
        )

    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================================================================
# FUNCIÓN PRINCIPAL DE ARRANQUE
# ==============================================================================

def main() -> None:
    """Función de arranque que valida la configuración y ejecuta el bot."""
    if config is None:
        print("\n" + "=" * 70)
        print("❌ ERROR AL INICIAR EL BOT:")
        print("No se encontró un archivo '.env' válido o el 'DISCORD_TOKEN' está vacío.")
        print("1. Copia '.env.example' como '.env':")
        print("   copy .env.example .env")
        print("2. Abre '.env' y coloca el Token de tu bot.")
        print("=" * 70 + "\n")
        sys.exit(1)

    try:
        bot.run(config.token, log_handler=None)
    except discord.LoginFailure:
        logger.critical("❌ Token de Discord no válido. Verifica tu archivo .env.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Cierre manual detectado (Ctrl+C). Apagando bot...")


if __name__ == "__main__":
    main()
