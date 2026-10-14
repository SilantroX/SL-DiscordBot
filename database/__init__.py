"""
Módulo de Persistencia y Base de Datos (database).
--------------------------------------------------
Gestiona la conexión asíncrona a SQLite mediante aiosqlite, la inicialización de
las tablas del sistema y operaciones de lectura/escritura seguras.
"""

from .connection import DatabaseManager, db_manager

__all__ = ["DatabaseManager", "db_manager"]
