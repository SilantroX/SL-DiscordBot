"""
Generador Estandarizado de Embeds (utils/embeds.py).
----------------------------------------------------
Proporciona una interfaz unificada para crear Discord Embeds consistentes,
con colores temáticos, marcas de tiempo y formatos uniformes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import discord


class EmbedColors:
    """Paleta de colores estándar para los embeds del bot."""
    PRIMARY = discord.Color.from_rgb(88, 101, 242)      # Blurple Discord
    SUCCESS = discord.Color.from_rgb(87, 242, 135)      # Verde Éxito
    WARNING = discord.Color.from_rgb(254, 231, 92)      # Amarillo Advertencia
    ERROR = discord.Color.from_rgb(237, 66, 69)         # Rojo Peligro / Error
    INFO = discord.Color.from_rgb(59, 165, 92)          # Verde Azulado Info
    ROLES = discord.Color.from_rgb(235, 69, 158)        # Fucsia / Roles
    ANNOUNCEMENT = discord.Color.from_rgb(255, 165, 0)  # Naranja Anuncios


class EmbedBuilder:
    """Constructor fluido y estático para crear Embeds de Discord."""

    @staticmethod
    def base(
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: discord.Color = EmbedColors.PRIMARY,
    ) -> discord.Embed:
        """Crea un embed básico con marca de tiempo UTC automática."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Bot Discord • Sistema Modular")
        return embed

    @staticmethod
    def success(title: str, description: str) -> discord.Embed:
        """Embed preconfigurado para acciones exitosas."""
        return EmbedBuilder.base(
            title=f"✅ {title}",
            description=description,
            color=EmbedColors.SUCCESS,
        )

    @staticmethod
    def error(title: str, description: str) -> discord.Embed:
        """Embed preconfigurado para errores o permisos denegados."""
        return EmbedBuilder.base(
            title=f"❌ {title}",
            description=description,
            color=EmbedColors.ERROR,
        )

    @staticmethod
    def warning(title: str, description: str) -> discord.Embed:
        """Embed preconfigurado para advertencias del sistema."""
        return EmbedBuilder.base(
            title=f"⚠️ {title}",
            description=description,
            color=EmbedColors.WARNING,
        )

    @staticmethod
    def info(title: str, description: str) -> discord.Embed:
        """Embed preconfigurado para mensajes informativos."""
        return EmbedBuilder.base(
            title=f"ℹ️ {title}",
            description=description,
            color=EmbedColors.PRIMARY,
        )

    @staticmethod
    def announcement(
        title: str,
        content: str,
        author: Optional[discord.Member] = None,
        image_url: Optional[str] = None,
    ) -> discord.Embed:
        """Embed estilizado para anuncios globales del servidor."""
        embed = EmbedBuilder.base(
            title=title,
            description=content,
            color=EmbedColors.ANNOUNCEMENT,
        )
        if author:
            embed.set_author(
                name=author.display_name,
                icon_url=author.display_avatar.url if author.display_avatar else None,
            )
        if image_url:
            embed.set_image(url=image_url)
        return embed
