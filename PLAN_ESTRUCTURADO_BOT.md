# 📋 Plan de Arquitectura e Implementación: Bot de Discord en Python

Este documento define la arquitectura técnica, esquema de base de datos, flujos de trabajo y el roadmap paso a paso para desarrollar un bot de Discord profesional, modular y escalable enfocado en **5 módulos esenciales**:
1. **Administración y Moderación**
2. **Tickets de Soporte**
3. **Sugerencias con Votación**
4. **Autoroles Interactivos (Botón + Select Menu)**
5. **Anuncios Globales desde Canal Privado**

---

## 🛠️ 1. Stack Tecnológico Recomendado

| Componente | Tecnología | Justificación |
|---|---|---|
| **Lenguaje** | Python 3.10+ | Tipado estático moderno (`typing`), sintaxis `match/case` y excelente rendimiento asíncrono. |
| **Librería Principal** | `discord.py` v2.4+ | Framework maduro con soporte completo para Slash Commands (`app_commands`), Vistas UI (`discord.ui.View`), Botones (`discord.ui.Button`), Menús desplegables (`discord.ui.Select`) y Modales (`discord.ui.Modal`). |
| **Base de Datos** | SQLite con `aiosqlite` | Asíncrono, liviano, sin dependencias de servidores externos para comenzar, altamente portable y fiable con soporte ACID. |
| **Configuración** | `python-dotenv` | Manejo seguro de credenciales (Token, IDs de servidor) fuera del código fuente. |
| **Transcripciones** | `chat-exporter` / HTML custom | Generación de transcripciones visuales completas de los canales de tickets cerrados para auditoría. |

---

## 📁 2. Estructura del Proyecto

Organización modular basada en **Cogs** (patrón recomendado por `discord.py`):

```text
Bot Discord/
├── .env                          # Tokens y claves secretas
├── .gitignore                    # Ignora .env, __pycache__, .db
├── requirements.txt              # Dependencias del proyecto
├── main.py                       # Punto de entrada, inicio del bot y carga de cogs
├── config.py                     # Carga de variables de entorno y validaciones
├── database/
│   ├── __init__.py
│   ├── connection.py             # Pool y contexto asíncrono de conexión SQLite
│   └── queries.py                # Consultas SQL reutilizables y migraciones
├── cogs/
│   ├── __init__.py
│   ├── admin.py                  # Comandos de moderación, control de sanciones y logs
│   ├── tickets.py                # Sistema de soporte interactivo (Modals, Buttons, Canales)
│   ├── suggestions.py            # Sistema de sugerencias, votaciones y resolución
│   ├── roles.py                  # Sistema de autoroles con embeds, botones y menús select
│   ├── announcements.py          # Creación y replicación de anuncios desde canal privado
│   └── general.py                # Comandos informativos (/ping, /help, /info)
└── utils/
    ├── __init__.py
    ├── embeds.py                 # Generador estandarizado de Discord Embeds
    ├── checks.py                 # Decoradores de comprobación de permisos y jerarquías
    └── transcript.py             # Lógica para exportar el chat del ticket a archivo
```

---

## 🗄️ 3. Esquema de Base de Datos Relacional

Se implementarán las siguientes tablas en SQLite:

```sql
-- Configuración general por servidor
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    mod_logs_channel_id INTEGER,
    ticket_category_id INTEGER,
    ticket_logs_channel_id INTEGER,
    suggestions_channel_id INTEGER,
    roles_channel_id INTEGER,
    announcements_channel_id INTEGER, -- Canal público global de anuncios
    staff_role_id INTEGER
);

-- Historial de advertencias y sanciones
CREATE TABLE IF NOT EXISTS infractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    action_type TEXT NOT NULL, -- 'WARN', 'MUTE', 'KICK', 'BAN'
    reason TEXT DEFAULT 'Sin motivo especificado',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Estado y metadatos de tickets
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

-- Sugerencias de la comunidad
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

-- Paneles de Autoroles
CREATE TABLE IF NOT EXISTS role_menus (
    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT
);

-- Opciones de roles asignables en cada panel
CREATE TABLE IF NOT EXISTS role_options (
    option_id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    emoji TEXT,
    description TEXT,
    FOREIGN KEY (menu_id) REFERENCES role_menus (menu_id) ON DELETE CASCADE
);

-- Historial de Anuncios publicados
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
```

---

## ⚙️ 4. Especificación Funcional de los 5 Módulos

### 🛡️ 4.1. Módulo de Administración y Moderación
* **Comandos Slash**:
  * `/kick <miembro> [motivo]`
  * `/ban <miembro> [motivo] [días_mensajes]`
  * `/unban <user_id> [motivo]`
  * `/timeout <miembro> <duración> [motivo]`
  * `/warn <miembro> <motivo>` y `/warnings <miembro>`
  * `/clear <cantidad>`
  * `/setup admin <canal_logs> <rol_staff>`
* **Seguridad y Jerarquía**:
  * Comprobaciones: `author.top_role > target.top_role` y `bot.top_role > target.top_role`.
* **Auditoría**:
  * Envío automático de Embed con detalle de cada sanción a `#mod-logs`.

---

### 🎫 4.2. Módulo de Tickets de Soporte
* **Panel de Creación (Vistas Persistentes)**:
  * `/setup tickets <categoría> <canal_logs>` crea un embed con botón fijo `[📩 Abrir Ticket]`.
* **Modal de Solicitud**:
  * Formulario emergente solicitando Asunto y Detalle.
* **Canal Privado Dinámico**:
  * Canal `ticket-nombre-id` con permisos restringidos exclusivamente a: Usuario solicitante + Rol Staff + Bot.
* **Controles Internos**:
  * Botones: `🔒 Cerrar Ticket` (con confirmación), `🙋 Reclamar Ticket` y `📄 Transcripción`.
* **Cierre & Transcripción**:
  * Exporta el historial a HTML/TXT, envía copia al usuario por DM y al canal de logs de tickets, y elimina el canal tras 5 segundos.

---

### 💡 4.3. Módulo de Sugerencias
* **Envío**: Comando `/sugerir <texto>` o botón modal en `#sugerencias`.
* **Embed Público de Sugerencia**:
  * Muestra avatar, autor, estado (`🟡 PENDIENTE`) y botones interactivos de votación `[👍 Votar A Favor]` y `[👎 Votar En Contra]`.
  * Previene votos duplicados del mismo usuario.
* **Resolución del Staff**:
  * Comando `/sugerencia responder <id> <estado> <motivo>`.
  * Actualiza dinámicamente el Embed original (cambia color a verde/rojo/morado, desactiva botones y añade nota del staff).
  * Envía aviso por DM al creador de la sugerencia.

---

### 🎭 4.4. Módulo de Autoroles (Selector Interactivo de Roles)
* **Panel Público**:
  * Comando `/setup autoroles <canal> <título>` genera un embed con botón persistente `[🎭 Seleccionar Roles]`.
* **Menú Desplegable Efímero**:
  * Al pulsar el botón, el bot responde con un mensaje efímero (`ephemeral=True`, visible solo para el usuario).
  * Despliega un `discord.ui.Select (StringSelect)` con soporte multi-selección, emojis y descripciones.
* **Sincronización Automática**:
  * Compara roles actuales y aplica adición (`member.add_roles()`) o remoción (`member.remove_roles()`).
  * Valida que el rol esté por debajo del bot en la jerarquía.
  * Muestra confirmación instantánea: *"✅ Roles actualizados: +Notificaciones, -Eventos"*.

---

### 📢 4.5. Módulo de Anuncios (Replicación Segura desde Canal Privado)
* **Objetivo**: Permitir a los administradores redactar, previsualizar y enviar anuncios oficiales al canal público `#anuncios` desde un canal privado de staff, evitando errores públicos.
* **Flujo de Ejecución**:
  1. **Comando en Privado**:
     * El administrador ejecuta `/anuncio` dentro del canal de administración o staff privado.
  2. **Modal Formulario de Redacción**:
     * El bot abre un modal emergente con los campos:
       * *Título del Anuncio* (ej: "¡Mantenimiento Programado y Novedades!").
       * *Contenido / Mensaje* (cuerpo principal con soporte completo para markdown, negritas, listas y enlaces).
       * *Mención* (opciones: `Ninguna`, `@here`, `@everyone` o rol específico).
       * *URL de Imagen / Banner* (opcional, para incluir imágenes de cabecera en el anuncio).
  3. **Vista Previa de Seguridad (Preview)**:
     * El bot genera en el canal privado un mensaje idéntico a cómo se verá el anuncio final.
     * Añade una vista interactiva con dos botones:
       * `[🚀 Publicar Anuncio]`
       * `[❌ Cancelar]`
  4. **Replicación y Publicación en Canal Global**:
     * Al confirmar, el bot envía el embed y la mención correspondiente al canal configurado en `/setup anuncios <#canal-anuncios>`.
     * Se utiliza `allowed_mentions` de forma estricta para evitar pings no deseados si no fueron solicitados explícitamente.
  5. **Confirmación y Auditoría**:
     * El mensaje privado de vista previa se actualiza indicando: *"✅ Anuncio publicado con éxito en #anuncios ([Ir al mensaje](url))"*.
     * Se almacena el registro en la tabla `announcements` y se envía un log a `#mod-logs`.

---

## 🗺️ 5. Roadmap de Implementación por Fases

```
[Fase 1: Setup & Core] ──> [Fase 2: Admin & Logs] ──> [Fase 3: Tickets] ──> [Fase 4: Sugerencias] ──> [Fase 5: Autoroles] ──> [Fase 6: Anuncios] ──> [Fase 7: Testing & Despliegue]
```

1. **Fase 1 — Setup y Arquitectura Base**:
   * Creación de la aplicación en el [Discord Developer Portal](https://discord.com/developers/applications).
   * Activación de los **Privileged Gateway Intents** (`Server Members Intent` y `Message Content Intent`).
   * Configuración del entorno virtual de Python, instalación de librerías (`discord.py`, `aiosqlite`, `python-dotenv`).
   * Creación del esqueleto `main.py`, cargador dinámico de Cogs y la conexión SQLite asíncrona.
2. **Fase 2 — Cogs de Administración**:
   * Implementación de comandos `/kick`, `/ban`, `/unban`, `/timeout`, `/warn`, `/clear`.
   * Verificaciones de jerarquía y canal de auditoría `#mod-logs`.
3. **Fase 3 — Cogs de Tickets**:
   * Vistas persistentes, formulario modal y canales privados dinámicos con `overwrites`.
   * Botones de control y generación de transcripciones a archivo.
4. **Fase 4 — Cogs de Sugerencias**:
   * Formulario `/sugerir`, embeds dinámicos con botones de votación y panel de resolución de staff.
5. **Fase 5 — Cogs de Autoroles**:
   * Panel fijo con botón persistente y menú desplegable (`StringSelect`) efímero multi-selección.
6. **Fase 6 — Cogs de Anuncios**:
   * Comando `/anuncio` en canal privado, modal de redacción, vista previa con confirmación y replicación en `#anuncios`.
7. **Fase 7 — Pruebas, Manejo de Errores y Despliegue**:
   * Manejador global de excepciones (`on_app_command_error`) y preparación para despliegue 24/7.
