"""
Módulo de Consultas y Operaciones de Base de Datos (database/queries.py).
-----------------------------------------------------------------------
Contiene funciones de alto nivel para interactuar con las tablas del sistema:
configuración, infracciones, tickets, sugerencias, autoroles y anuncios.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from .connection import db_manager


# ==============================================================================
# 1. CONFIGURACIÓN DEL SERVIDOR (guild_settings)
# ==============================================================================

async def get_guild_settings(guild_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene la fila de configuración para un servidor específico."""
    query = "SELECT * FROM guild_settings WHERE guild_id = ?;"
    row = await db_manager.fetch_one(query, (guild_id,))
    return dict(row) if row else None


async def update_guild_setting(guild_id: int, column: str, value: Any) -> None:
    """Actualiza o crea una columna de configuración para el servidor de forma segura."""
    valid_columns = {
        "mod_logs_channel_id",
        "ticket_category_id",
        "ticket_logs_channel_id",
        "suggestions_channel_id",
        "roles_channel_id",
        "announcements_channel_id",
        "staff_role_id",
    }
    if column not in valid_columns:
        raise ValueError(f"Columna de configuración inválida: '{column}'")

    # Inserta o actualiza mediante ON CONFLICT
    query = f"""
    INSERT INTO guild_settings (guild_id, {column})
    VALUES (?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET
        {column} = excluded.{column},
        updated_at = CURRENT_TIMESTAMP;
    """
    await db_manager.execute(query, (guild_id, value))


# ==============================================================================
# 2. INFRACCIONES Y MODERACIÓN (infractions)
# ==============================================================================

async def add_infraction(guild_id: int, user_id: int, moderator_id: int, action_type: str, reason: str) -> int:
    """Registra una nueva sanción (WARN, MUTE, KICK, BAN) en el historial del usuario."""
    query = """
    INSERT INTO infractions (guild_id, user_id, moderator_id, action_type, reason)
    VALUES (?, ?, ?, ?, ?);
    """
    cursor = await db_manager.execute(query, (guild_id, user_id, moderator_id, action_type.upper(), reason))
    return cursor.lastrowid or 0


async def get_user_infractions(guild_id: int, user_id: int) -> List[Dict[str, Any]]:
    """Obtiene el listado completo de infracciones registradas para un usuario en el servidor."""
    query = """
    SELECT * FROM infractions
    WHERE guild_id = ? AND user_id = ?
    ORDER BY created_at DESC;
    """
    rows = await db_manager.fetch_all(query, (guild_id, user_id))
    return [dict(r) for r in rows]


# ==============================================================================
# 3. TICKETS DE SOPORTE (tickets)
# ==============================================================================

async def create_ticket(guild_id: int, channel_id: int, user_id: int, subject: str) -> int:
    """Registra la apertura de un nuevo ticket de soporte."""
    query = """
    INSERT INTO tickets (guild_id, channel_id, user_id, subject, status)
    VALUES (?, ?, ?, ?, 'OPEN');
    """
    cursor = await db_manager.execute(query, (guild_id, channel_id, user_id, subject))
    return cursor.lastrowid or 0


async def get_ticket_by_channel(channel_id: int) -> Optional[Dict[str, Any]]:
    """Busca la información de un ticket por el ID de su canal de Discord."""
    query = "SELECT * FROM tickets WHERE channel_id = ?;"
    row = await db_manager.fetch_one(query, (channel_id,))
    return dict(row) if row else None


async def close_ticket(channel_id: int, transcript_url: Optional[str] = None) -> None:
    """Marca un ticket como cerrado y registra la fecha y URL de transcripción."""
    query = """
    UPDATE tickets
    SET status = 'CLOSED', closed_at = CURRENT_TIMESTAMP, transcript_url = ?
    WHERE channel_id = ?;
    """
    await db_manager.execute(query, (transcript_url, channel_id))


# ==============================================================================
# 4. SUGERENCIAS (suggestions)
# ==============================================================================

async def create_suggestion(guild_id: int, message_id: int, user_id: int, content: str) -> int:
    """Registra una nueva sugerencia enviada por un usuario."""
    query = """
    INSERT INTO suggestions (guild_id, message_id, user_id, content, status)
    VALUES (?, ?, ?, ?, 'PENDING');
    """
    cursor = await db_manager.execute(query, (guild_id, message_id, user_id, content))
    return cursor.lastrowid or 0


async def update_suggestion_status(
    suggestion_id: int,
    status: str,
    staff_comment: Optional[str],
    reviewed_by: int
) -> None:
    """Actualiza el estado de una sugerencia (APPROVED, REJECTED, IN_PROGRESS)."""
    query = """
    UPDATE suggestions
    SET status = ?, staff_comment = ?, reviewed_by = ?
    WHERE suggestion_id = ?;
    """
    await db_manager.execute(query, (status.upper(), staff_comment, reviewed_by, suggestion_id))


# ==============================================================================
# 5. AUTOROLES (role_menus & role_options)
# ==============================================================================

async def create_role_menu(guild_id: int, channel_id: int, message_id: int, title: str, description: Optional[str] = None) -> int:
    """Crea un nuevo registro para un panel de autoroles."""
    query = """
    INSERT INTO role_menus (guild_id, channel_id, message_id, title, description)
    VALUES (?, ?, ?, ?, ?);
    """
    cursor = await db_manager.execute(query, (guild_id, channel_id, message_id, title, description))
    return cursor.lastrowid or 0


async def add_role_option(menu_id: int, role_id: int, label: str, emoji: Optional[str] = None, description: Optional[str] = None) -> int:
    """Agrega una opción de rol seleccionable a un panel existente."""
    query = """
    INSERT INTO role_options (menu_id, role_id, label, emoji, description)
    VALUES (?, ?, ?, ?, ?);
    """
    cursor = await db_manager.execute(query, (menu_id, role_id, label, emoji, description))
    return cursor.lastrowid or 0


async def get_menu_options(menu_id: int) -> List[Dict[str, Any]]:
    """Obtiene todas las opciones de roles asociadas a un menú de autoroles."""
    query = "SELECT * FROM role_options WHERE menu_id = ?;"
    rows = await db_manager.fetch_all(query, (menu_id,))
    return [dict(r) for r in rows]


# ==============================================================================
# 6. ANUNCIOS (announcements)
# ==============================================================================

async def log_announcement(
    guild_id: int,
    author_id: int,
    target_channel_id: int,
    published_message_id: int,
    title: str,
    content: str,
    mention_type: str = "none"
) -> int:
    """Registra un anuncio oficial publicado en el canal global de anuncios."""
    query = """
    INSERT INTO announcements (guild_id, author_id, target_channel_id, published_message_id, title, content, mention_type)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    cursor = await db_manager.execute(query, (guild_id, author_id, target_channel_id, published_message_id, title, content, mention_type))
    return cursor.lastrowid or 0
