"""
Comprobaciones de Permisos y Jerarquía de Roles (utils/checks.py).
-----------------------------------------------------------------
Proporciona funciones para validar si un moderador o el propio bot
tienen la jerarquía y permisos suficientes para sancionar o gestionar a un miembro.
"""

from __future__ import annotations

from typing import Tuple
import discord


def can_moderate_member(moderator: discord.Member, target: discord.Member) -> Tuple[bool, str]:
    """
    Verifica las reglas de jerarquía de roles de Discord:
    1. El moderador no puede auto-sancionarse.
    2. El objetivo no puede ser el dueño del servidor (Guild Owner).
    3. El rol más alto del moderador debe ser superior al del objetivo.
    4. El rol más alto del bot debe ser superior al del objetivo.
    """
    if moderator.id == target.id:
        return False, "No puedes aplicarte sanciones o acciones de moderación a ti mismo."

    if target.guild.owner_id == target.id:
        return False, "No es posible aplicar acciones de moderación al dueño del servidor."

    # Comprobación de jerarquía del moderador
    if moderator.top_role <= target.top_role and moderator.id != target.guild.owner_id:
        return (
            False,
            f"Tu rol ({moderator.top_role.name}) no tiene suficiente jerarquía sobre {target.mention} ({target.top_role.name}).",
        )

    # Comprobación de jerarquía del propio bot
    bot_member = target.guild.me
    if bot_member.top_role <= target.top_role:
        return (
            False,
            f"Mi rol más alto ({bot_member.top_role.name}) está por debajo o igual al rol de {target.mention}. Sube mi rol en los ajustes del servidor.",
        )

    return True, "Jerarquía válida."


def is_staff_or_admin(member: discord.Member, staff_role_id: int | None = None) -> bool:
    """Verifica si un miembro cuenta con permisos de administrador o posee el rol de staff configurado."""
    if member.guild_permissions.administrator:
        return True

    if staff_role_id and any(role.id == staff_role_id for role in member.roles):
        return True

    return False
