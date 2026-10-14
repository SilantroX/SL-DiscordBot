"""
Módulo de Configuración Centralizada (config.py).
------------------------------------------------
Este módulo se encarga de cargar y validar las variables de entorno definidas en el archivo .env,
proporcionando una interfaz tipada y segura para el resto de la aplicación.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env local
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


@dataclass(frozen=True)
class BotConfig:
    """Clase inmutable que almacena los parámetros de configuración del bot."""

    token: str
    guild_id: Optional[int]
    command_prefix: str
    database_path: Path
    environment: str

    @classmethod
    def load_from_env(cls) -> BotConfig:
        """Carga y valida los valores desde las variables de entorno del sistema."""
        raw_token = os.getenv("DISCORD_TOKEN", "").strip()

        # Validación del token (no debe estar vacío ni mantener el placeholder de ejemplo)
        if not raw_token or raw_token == "TU_TOKEN_SECRETO_AQUI":
            raise ValueError(
                "❌ ERROR DE CONFIGURACIÓN: No se ha configurado 'DISCORD_TOKEN'.\n"
                "Por favor, crea un archivo '.env' basado en '.env.example' y asigna tu token real de Discord."
            )

        # Parseo opcional del Guild ID
        raw_guild_id = os.getenv("GUILD_ID", "").strip()
        guild_id: Optional[int] = None
        if raw_guild_id:
            try:
                guild_id = int(raw_guild_id)
            except ValueError:
                print(f"⚠️ Advertencia: 'GUILD_ID' ({raw_guild_id}) no es un número entero válido. Se omitirá.")

        command_prefix = os.getenv("COMMAND_PREFIX", "!").strip() or "!"
        raw_db_path = os.getenv("DATABASE_PATH", "bot_database.sqlite3").strip()
        database_path = BASE_DIR / raw_db_path
        environment = os.getenv("ENVIRONMENT", "development").strip().lower()

        return cls(
            token=raw_token,
            guild_id=guild_id,
            command_prefix=command_prefix,
            database_path=database_path,
            environment=environment,
        )


# Instancia de configuración lista para ser importada por los módulos del bot
try:
    config = BotConfig.load_from_env()
except ValueError:
    # Para permitir importar el módulo durante pruebas o setup inicial sin fallar si el .env aún no existe
    config = None  # type: ignore
