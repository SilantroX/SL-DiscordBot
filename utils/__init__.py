"""
Módulo de Utilidades (utils).
-----------------------------
Contiene herramientas de apoyo compartidas: generadores de embeds estilizados,
verificadores de jerarquías y generadores de transcripciones.
"""

from .embeds import EmbedBuilder
from .checks import can_moderate_member, is_staff_or_admin

__all__ = ["EmbedBuilder", "can_moderate_member", "is_staff_or_admin"]
