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


async def claim_ticket(channel_id: int, staff_id: int) -> None:
    """Asigna un ticket a un miembro del staff."""
    query = "UPDATE tickets SET claimed_by = ? WHERE channel_id = ?;"
    await db_manager.execute(query, (staff_id, channel_id))


async def get_open_ticket_by_user(guild_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Verifica si el usuario ya tiene un ticket actualmente abierto en el servidor."""
    query = "SELECT * FROM tickets WHERE guild_id = ? AND user_id = ? AND status = 'OPEN';"
    row = await db_manager.fetch_one(query, (guild_id, user_id))
    return dict(row) if row else None



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


async def get_suggestion(suggestion_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una sugerencia a partir de su ID secuencial."""
    query = "SELECT * FROM suggestions WHERE suggestion_id = ?;"
    row = await db_manager.fetch_one(query, (suggestion_id,))
    return dict(row) if row else None


async def get_suggestion_by_message_id(message_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una sugerencia a partir del ID de su mensaje en Discord."""
    query = "SELECT * FROM suggestions WHERE message_id = ?;"
    row = await db_manager.fetch_one(query, (message_id,))
    return dict(row) if row else None


async def record_suggestion_vote(
    suggestion_id: int,
    user_id: int,
    vote_type: int,
) -> tuple[int, int, str]:
    """
    Registra, actualiza o remueve el voto de un usuario en una sugerencia.
    - Si el usuario vuelve a presionar el mismo botón: remueve su voto (toggle).
    - Si el usuario presiona el botón opuesto: cambia su voto (switch).
    - Si el usuario no había votado: registra el voto (add).

    Retorna: (upvotes_totales, downvotes_totales, accion_realizada: 'added' | 'removed' | 'switched')
    """
    check_query = "SELECT vote_type FROM suggestion_votes WHERE suggestion_id = ? AND user_id = ?;"
    existing = await db_manager.fetch_one(check_query, (suggestion_id, user_id))

    if existing:
        current_type = existing["vote_type"]
        if current_type == vote_type:
            # Eliminar voto
            await db_manager.execute(
                "DELETE FROM suggestion_votes WHERE suggestion_id = ? AND user_id = ?;",
                (suggestion_id, user_id),
            )
            action = "removed"
        else:
            # Cambiar voto
            await db_manager.execute(
                "UPDATE suggestion_votes SET vote_type = ? WHERE suggestion_id = ? AND user_id = ?;",
                (vote_type, suggestion_id, user_id),
            )
            action = "switched"
    else:
        # Añadir nuevo voto
        await db_manager.execute(
            "INSERT INTO suggestion_votes (suggestion_id, user_id, vote_type) VALUES (?, ?, ?);",
            (suggestion_id, user_id, vote_type),
        )
        action = "added"

    # Recalcular conteos totales de votos
    count_query = """
    SELECT
        COUNT(CASE WHEN vote_type = 1 THEN 1 END) AS up,
        COUNT(CASE WHEN vote_type = -1 THEN 1 END) AS down
    FROM suggestion_votes
    WHERE suggestion_id = ?;
    """
    counts = await db_manager.fetch_one(count_query, (suggestion_id,))
    upvotes = counts["up"] if counts else 0
    downvotes = counts["down"] if counts else 0

    # Actualizar la fila en suggestions para lecturas rápidas
    await db_manager.execute(
        "UPDATE suggestions SET upvotes = ?, downvotes = ? WHERE suggestion_id = ?;",
        (upvotes, downvotes, suggestion_id),
    )

    return upvotes, downvotes, action


async def update_suggestion_status(
    suggestion_id: int,
    status: str,
    staff_comment: Optional[str],
    reviewed_by: int
) -> Optional[Dict[str, Any]]:
    """Actualiza el estado de una sugerencia (APPROVED, REJECTED, IN_PROGRESS) y retorna la fila actualizada."""
    query = """
    UPDATE suggestions
    SET status = ?, staff_comment = ?, reviewed_by = ?
    WHERE suggestion_id = ?;
    """
    await db_manager.execute(query, (status.upper(), staff_comment, reviewed_by, suggestion_id))
    return await get_suggestion(suggestion_id)


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


async def get_role_menu(menu_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene la información de un menú de autoroles por su ID."""
    query = "SELECT * FROM role_menus WHERE menu_id = ?;"
    row = await db_manager.fetch_one(query, (menu_id,))
    return dict(row) if row else None


async def get_role_menu_by_message_id(message_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene la información de un menú de autoroles por el ID de su mensaje."""
    query = "SELECT * FROM role_menus WHERE message_id = ?;"
    row = await db_manager.fetch_one(query, (message_id,))
    return dict(row) if row else None


async def get_menu_options(menu_id: int) -> List[Dict[str, Any]]:
    """Obtiene todas las opciones de roles asociadas a un menú de autoroles."""
    query = "SELECT * FROM role_options WHERE menu_id = ? ORDER BY option_id ASC;"
    rows = await db_manager.fetch_all(query, (menu_id,))
    return [dict(r) for r in rows]


async def delete_role_option_by_role(menu_id: int, role_id: int) -> None:
    """Elimina una opción de rol de un menú específico."""
    query = "DELETE FROM role_options WHERE menu_id = ? AND role_id = ?;"
    await db_manager.execute(query, (menu_id, role_id))


async def delete_role_menu(menu_id: int) -> None:
    """Elimina un panel de autoroles y todas sus opciones asociadas (ON DELETE CASCADE)."""
    query = "DELETE FROM role_menus WHERE menu_id = ?;"
    await db_manager.execute(query, (menu_id,))


async def get_role_menus_by_guild(guild_id: int) -> List[Dict[str, Any]]:
    """Obtiene todos los paneles de autoroles configurados en un servidor."""
    query = "SELECT * FROM role_menus WHERE guild_id = ? ORDER BY menu_id DESC;"
    rows = await db_manager.fetch_all(query, (guild_id,))
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


async def get_announcements_by_guild(guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Obtiene el historial de los últimos anuncios publicados en el servidor."""
    query = """
    SELECT * FROM announcements
    WHERE guild_id = ?
    ORDER BY created_at DESC
    LIMIT ?;
    """
    rows = await db_manager.fetch_all(query, (guild_id, limit))
    return [dict(r) for r in rows]
