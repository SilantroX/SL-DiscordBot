"""
Gestor de Conexión a Base de Datos (database/connection.py).
------------------------------------------------------------
Maneja el ciclo de vida de la base de datos relacional SQLite de manera completamente asíncrona
utilizando la librería aiosqlite, garantizando transacciones seguras (ACID) y ejecución de migraciones.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger("bot.database")

# Esquema DDL para inicializar todas las tablas del sistema
SCHEMA_DDL = """
-- Habilitar claves foráneas en SQLite
PRAGMA foreign_keys = ON;

-- 1. Tabla de configuración por servidor
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    mod_logs_channel_id INTEGER,
    ticket_category_id INTEGER,
    ticket_logs_channel_id INTEGER,
    suggestions_channel_id INTEGER,
    roles_channel_id INTEGER,
    announcements_channel_id INTEGER,
    staff_role_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de infracciones y moderación (Warn, Mute, Kick, Ban)
CREATE TABLE IF NOT EXISTS infractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    action_type TEXT NOT NULL, -- 'WARN', 'MUTE', 'KICK', 'BAN'
    reason TEXT DEFAULT 'Sin motivo especificado',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla de tickets de soporte
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    claimed_by INTEGER,
    status TEXT NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'CLOSED'
    subject TEXT NOT NULL,
    transcript_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- 4. Tabla de sugerencias de la comunidad
CREATE TABLE IF NOT EXISTS suggestions (
    suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    message_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED', 'IN_PROGRESS'
    staff_comment TEXT,
    reviewed_by INTEGER,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4.1 Tabla de votos individuales en sugerencias
CREATE TABLE IF NOT EXISTS suggestion_votes (
    suggestion_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    vote_type INTEGER NOT NULL, -- 1 para UP (+1), -1 para DOWN (-1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (suggestion_id, user_id),
    FOREIGN KEY (suggestion_id) REFERENCES suggestions (suggestion_id) ON DELETE CASCADE
);

-- 5. Tabla de paneles de autoroles
CREATE TABLE IF NOT EXISTS role_menus (
    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Opciones de roles asignables en cada menú
CREATE TABLE IF NOT EXISTS role_options (
    option_id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    emoji TEXT,
    description TEXT,
    FOREIGN KEY (menu_id) REFERENCES role_menus (menu_id) ON DELETE CASCADE
);

-- 7. Historial de anuncios enviados
CREATE TABLE IF NOT EXISTS announcements (
    announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    target_channel_id INTEGER NOT NULL,
    published_message_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    mention_type TEXT DEFAULT 'none', -- 'none', '@here', '@everyone', 'role_id'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class DatabaseManager:
    """Administrador asíncrono para operaciones sobre la base de datos SQLite."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            # Ruta predeterminada en la raíz del proyecto
            self.db_path = Path(__file__).resolve().parent.parent / "bot_database.sqlite3"
        else:
            self.db_path = Path(db_path)

        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> aiosqlite.Connection:
        """Establece la conexión asíncrona a la base de datos y habilita foreign keys."""
        if self._connection is None:
            logger.info("Abriendo conexión a la base de datos SQLite: %s", self.db_path)
            self._connection = await aiosqlite.connect(self.db_path)
            # Habilitar nombres de columnas accesibles como diccionarios (Row factory)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA foreign_keys = ON;")
            await self._connection.commit()
        return self._connection

    async def close(self) -> None:
        """Cierra la conexión activa a la base de datos."""
        if self._connection is not None:
            logger.info("Cerrando conexión a la base de datos SQLite...")
            await self._connection.close()
            self._connection = None

    async def initialize_schema(self) -> None:
        """Ejecuta los scripts DDL para crear las tablas necesarias si no existen."""
        db = await self.connect()
        logger.info("Inicializando esquema de base de datos...")
        await db.executescript(SCHEMA_DDL)
        await db.commit()
        logger.info("✅ Esquema de base de datos inicializado con éxito.")

    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Ejecuta una sentencia SQL (INSERT, UPDATE, DELETE) y confirma los cambios."""
        db = await self.connect()
        async with db.cursor() as cursor:
            await cursor.execute(query, parameters)
            await db.commit()
            return cursor

    async def fetch_one(self, query: str, parameters: tuple = ()) -> Optional[aiosqlite.Row]:
        """Obtiene un único registro que coincida con la consulta."""
        db = await self.connect()
        async with db.execute(query, parameters) as cursor:
            return await cursor.fetchone()

    async def fetch_all(self, query: str, parameters: tuple = ()) -> list[aiosqlite.Row]:
        """Obtiene todos los registros que coincidan con la consulta."""
        db = await self.connect()
        async with db.execute(query, parameters) as cursor:
            rows = await cursor.fetchall()
            return list(rows)


# Instancia singleton del DatabaseManager
db_manager = DatabaseManager()
