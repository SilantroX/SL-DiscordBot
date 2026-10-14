"""
Generador de Transcripciones de Chat (utils/transcript.py).
----------------------------------------------------------
Genera un archivo HTML interactivo con tema oscuro (estilo Discord) a partir del historial
de mensajes de un canal de tickets, incluyendo autores, avatares, marcas de tiempo y adjuntos.
"""

from __future__ import annotations

import html
import io
from datetime import datetime, timezone
import discord


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Transcripción: {channel_name}</title>
    <style>
        body {{
            background-color: #313338;
            color: #dbdee1;
            font-family: 'gg sans', 'Noto Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        .header {{
            background-color: #2b2d31;
            border-left: 4px solid #5865f2;
            padding: 16px 20px;
            border-radius: 6px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            margin: 0 0 8px 0;
            font-size: 20px;
            color: #f2f3f5;
        }}
        .header p {{
            margin: 4px 0;
            font-size: 13px;
            color: #949ba4;
        }}
        .messages {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .message {{
            display: flex;
            gap: 16px;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        .message:hover {{
            background-color: #2e3035;
        }}
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
        }}
        .content {{
            flex: 1;
        }}
        .meta {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 4px;
        }}
        .author {{
            font-weight: 600;
            color: #f2f3f5;
            font-size: 15px;
        }}
        .bot-badge {{
            background-color: #5865f2;
            color: #ffffff;
            font-size: 10px;
            font-weight: bold;
            padding: 1px 4px;
            border-radius: 3px;
            text-transform: uppercase;
        }}
        .timestamp {{
            font-size: 11px;
            color: #949ba4;
        }}
        .body {{
            font-size: 14px;
            line-height: 1.4;
            color: #dbdee1;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .attachment {{
            margin-top: 8px;
        }}
        .attachment a {{
            color: #00a8fc;
            text-decoration: none;
            font-size: 13px;
        }}
        .attachment a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: #80848e;
            border-top: 1px solid #3f4147;
            padding-top: 16px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎫 Transcripción Oficial: #{channel_name}</h1>
        <p><strong>Servidor:</strong> {guild_name}</p>
        <p><strong>Fecha de Exportación:</strong> {export_date} (UTC)</p>
        <p><strong>Total de Mensajes:</strong> {message_count}</p>
    </div>
    <div class="messages">
        {messages_html}
    </div>
    <div class="footer">
        Generado por Antigravity Bot • Sistema de Soporte y Tickets
    </div>
</body>
</html>
"""


async def generate_ticket_transcript(
    channel: discord.TextChannel,
    limit: int = 500,
) -> discord.File:
    """
    Lee los mensajes de un canal de texto y genera un archivo HTML con el historial formateado.
    Retorna un objeto discord.File listo para ser enviado en un canal o DM.
    """
    messages = []
    # Recorrer mensajes de más antiguo a más reciente para orden cronológico de lectura
    async for msg in channel.history(limit=limit, oldest_first=True):
        messages.append(msg)

    rendered_messages = []
    for msg in messages:
        author_name = html.escape(msg.author.display_name)
        avatar_url = msg.author.display_avatar.url if msg.author.display_avatar else ""
        time_str = msg.created_at.strftime("%d/%m/%Y %H:%M:%S")
        bot_badge = '<span class="bot-badge">BOT</span>' if msg.author.bot else ""
        content = html.escape(msg.clean_content) if msg.clean_content else "<em>(Sin texto o solo incrustación)</em>"

        # Procesar archivos adjuntos
        attachments_html = ""
        if msg.attachments:
            links = []
            for att in msg.attachments:
                att_name = html.escape(att.filename)
                links.append(f'<div class="attachment">📎 <a href="{att.url}" target="_blank">{att_name}</a></div>')
            attachments_html = "".join(links)

        msg_block = f"""
        <div class="message">
            <img class="avatar" src="{avatar_url}" alt="{author_name}">
            <div class="content">
                <div class="meta">
                    <span class="author">{author_name}</span>
                    {bot_badge}
                    <span class="timestamp">{time_str}</span>
                </div>
                <div class="body">{content}</div>
                {attachments_html}
            </div>
        </div>
        """
        rendered_messages.append(msg_block)

    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
    full_html = HTML_TEMPLATE.format(
        channel_name=html.escape(channel.name),
        guild_name=html.escape(channel.guild.name),
        export_date=now_str,
        message_count=len(messages),
        messages_html="".join(rendered_messages),
    )

    # Crear buffer en memoria
    buffer = io.BytesIO(full_html.encode("utf-8"))
    buffer.seek(0)
    filename = f"transcripcion-{channel.name}.html"

    return discord.File(fp=buffer, filename=filename)
