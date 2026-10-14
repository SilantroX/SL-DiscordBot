# 📋 Plan de Arquitectura e Implementación: Bot de Discord en Python (v1.2.0)

Este documento define la arquitectura técnica, esquema de base de datos, flujos de trabajo y el roadmap completo de **SilantroLabs Bot**, un bot de Discord profesional, modular, escalable y tipado enfocado en **5 módulos esenciales** y **31 comandos slash**:
1. **Administración, Moderación y Gestión Masiva de Roles**
2. **Tickets de Soporte con Vistas Persistentes y Transcripciones HTML**
3. **Sugerencias Comunitarias con Votación Dinámica**
4. **Autoroles Interactivos (Botón Fijo + Menú Desplegable Efímero)**
5. **Anuncios y Comunicados Multicanal desde Canal Privado**

---

## 🛠️ 1. Stack Tecnológico

| Componente | Tecnología | Justificación |
|---|---|---|
| **Lenguaje** | Python 3.10 - 3.13+ | Tipado estático moderno (`typing`), sintaxis `match/case` y excelente rendimiento asíncrono. |
| **Librería Principal** | `discord.py` v2.4+ | Framework maduro con soporte completo para Slash Commands (`app_commands`), Vistas UI (`discord.ui.View`), Botones (`discord.ui.Button`), Menús desplegables (`discord.ui.Select`) y Modales (`discord.ui.Modal`). |
| **Base de Datos** | SQLite con `aiosqlite` | Asíncrono, liviano, sin dependencias de servidores externos, altamente portable y fiable con soporte ACID. |
| **Almacenamiento Persistente** | Railway Volume (`/app/data`) / Docker Volume | Garantiza persistencia total de la base de datos entre reinicios y redespliegues. |
| **Configuración** | `python-dotenv` | Manejo seguro de credenciales (Token, IDs de servidor) fuera del código fuente. |
| **Contenedores & Despliegue** | Dockerfile (`python:3.13-slim`), Docker Compose, Procfile | Agnóstico a la infraestructura, operable en local, VPS y nube. |
| **Diagramación** | Draw.io | Arquitectura visual disponible online y en archivo local `.drawio`. |

---

## 📐 Diagrama de Arquitectura
* **Editor Web Interactivo:** [Abrir en app.diagrams.net](https://app.diagrams.net/?grid=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2FSilantroX%2FSL-DiscordBot%2Fmaster%2Fbot_arquitectura_y_flujos.drawio)
* **Visualizador Interactivo:** [Ver en viewer.diagrams.net](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1&title=bot_arquitectura_y_flujos.drawio#Uhttps%3A%2F%2Fraw.githubusercontent.com%2FSilantroX%2FSL-DiscordBot%2Fmaster%2Fbot_arquitectura_y_flujos.drawio)
* **Archivo local:** `bot_arquitectura_y_flujos.drawio` (arrastrar a [app.diagrams.net](https://app.diagrams.net) o abrir con la extensión Draw.io de VS Code / Draw.io Desktop)

---

## 📁 2. Estructura del Proyecto

```text
Bot Discord/
├── .dockerignore                 # Exclusiones de construcción Docker
├── .env                          # Tokens y claves secretas (IGNORADO EN GIT)
├── .env.example                  # Plantilla de configuración
├── .gitignore                    # Reglas de exclusión de Git (blindado)
├── Dockerfile                    # Contenedor optimizado en Python 3.13-slim
├── LICENSE                       # Licencia MIT oficial de SilantroLabs
├── PLAN_ESTRUCTURADO_BOT.md      # Este documento maestro
├── Procfile                      # Declaración de proceso worker para Railway/Heroku
├── README.md                     # Documentación pública y guía de instalación
├── requirements.txt              # Dependencias fijadas (UTF-8, conditional audioop-lts)
├── main.py                       # Punto de entrada, inicio del bot y carga de cogs
├── config.py                     # Carga de variables de entorno y validaciones tipadas
├── bot_arquitectura_y_flujos.drawio # Diagrama nativo editable en Draw.io
├── generate_diagrams.js          # Generador de compresión y URLs de Draw.io
├── docker-compose.yml            # Orquestación con volumen Docker persistente
├── database/
│   ├── __init__.py
│   ├── connection.py             # Pool asíncrono SQLite (aiosqlite) con soporte para volúmenes
│   └── queries.py                # Consultas SQL reutilizables y transacciones CRUD
├── cogs/
│   ├── __init__.py
│   ├── general.py                # Diagnóstico (/ping, /help, /info) - 3 comandos
│   ├── admin.py                  # Moderación, auditoría y roles masivos - 11 comandos
│   ├── tickets.py                # Sistema de soporte interactivo (Modals, Buttons) - 4 comandos
│   ├── suggestions.py            # Sistema de sugerencias y votaciones - 4 comandos
│   ├── roles.py                  # Autoroles interactivos con menús desplegables - 4 comandos
│   └── announcements.py          # Anuncios globales y multicanal - 5 comandos
├── utils/
│   ├── __init__.py
│   ├── embeds.py                 # Generador estandarizado de Discord Embeds
│   ├── checks.py                 # Decoradores de comprobación de permisos y jerarquías
│   └── transcript.py             # Motor generador de transcripciones HTML estilo Dark Mode
└── tests/
    ├── __init__.py
    ├── test_base.py              # Pruebas de DB, Embeds, Jerarquía y General (8 tests)
    ├── test_admin.py             # Pruebas de moderación y asignación masiva de roles (8 tests)
    ├── test_tickets.py           # Pruebas de ciclo de vida de tickets (5 tests)
    ├── test_suggestions.py       # Pruebas de votaciones y resolución de sugerencias (6 tests)
    ├── test_roles.py             # Pruebas de autoroles y sincronización atómica (6 tests)
    └── test_announcements.py     # Pruebas de anuncios globales y multicanal (6 tests)
```

---

## 🗄️ 3. Esquema de Base de Datos Relacional (7 Tablas + 1 Subtabla)

```sql
PRAGMA foreign_keys = ON;

-- 1. Configuración por servidor
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

-- 2. Historial de sanciones y moderación
CREATE TABLE IF NOT EXISTS infractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    action_type TEXT NOT NULL, -- 'WARN', 'MUTE', 'KICK', 'BAN'
    reason TEXT DEFAULT 'Sin motivo especificado',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Estado y metadatos de tickets
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

-- 4. Sugerencias comunitarias
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

-- 4.1. Votos individuales en sugerencias (anti-duplicados y toggle)
CREATE TABLE IF NOT EXISTS suggestion_votes (
    suggestion_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    vote_type INTEGER NOT NULL, -- 1 (+1) o -1 (-1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (suggestion_id, user_id),
    FOREIGN KEY (suggestion_id) REFERENCES suggestions (suggestion_id) ON DELETE CASCADE
);

-- 5. Paneles de autoroles
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

-- 7. Historial de anuncios emitidos
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

## ⚙️ 4. Especificación Funcional de los 5 Módulos (31 Comandos)

### 🛡️ 4.1. Módulo de Administración y Moderación (11 Comandos)
* `/setup_admin <canal_logs> [rol_staff]`: Configuración inicial del canal de auditoría y rol de Staff.
* `/warn <miembro> <motivo>`: Registra una advertencia formal con DM al infractor.
* `/warnings <miembro>`: Consulta el historial acumulado de infracciones.
* `/timeout <miembro> <duracion> [motivo]`: Aislamiento temporal nativo (hasta 28 días).
* `/untimeout <miembro> [motivo]`: Retira la sanción de aislamiento antes de su expiración.
* `/kick <miembro> [motivo]`: Expulsión del servidor con validación de jerarquía.
* `/ban <miembro> [motivo] [borrar_dias]`: Baneo permanente con opción de purga de mensajes.
* `/unban <user_id> [motivo]`: Revoca el baneo de un usuario mediante su ID numérico.
* `/clear <cantidad>`: Purga de mensajes de más reciente a más antiguo (máximo 14 días de antigüedad).
* `/role_add_all <rol> [ignorar_bots]`: Asigna un rol a todos los miembros de forma iterativa y segura contra rate-limits.
* `/role_remove_all <rol> [ignorar_bots]`: Remueve un rol masivamente de todos los miembros.
* **Auditoría en tiempo real:** Registra eventos críticos (creación/eliminación/modificación de canales y roles con alertas rojas ante permisos peligrosos, actualizaciones de miembros y sanciones).

### 🎫 4.2. Módulo de Tickets de Soporte (4 Comandos)
* `/setup_tickets <categoria> <canal_logs>`: Configura la categoría contenedora y el canal de transcripciones.
* `/ticket_panel [titulo] [descripcion]`: Envía el panel visual con vista persistente y botón `[📩 Crear Ticket]`.
* `/ticket_add <usuario>`: Añade permisos de visualización a un usuario dentro del ticket activo.
* `/ticket_remove <usuario>`: Retira permisos de un usuario del ticket.
* **Flujo interactivo:** Formulario modal `TicketCreateModal` -> Canal privado aislado `ticket-usuario-id` -> Controles: `[🙋 Reclamar Ticket]`, `[🔒 Cerrar Ticket]` con confirmación en dos pasos -> Exportación de transcripción HTML estilo Dark Mode a `#mod-logs` y por DM al usuario.

### 💡 4.3. Módulo de Sugerencias (4 Comandos)
* `/setup_suggestions <canal>`: Asigna el canal público de sugerencias.
* `/sugerir <contenido>`: Envía una propuesta formateada con botones interactivos `[👍 A favor]` y `[👎 En contra]`.
* `/responder_sugerencia <id> <estado> [comentario]`: Staff resuelve la sugerencia (`APPROVED`, `REJECTED`, `IN_PROGRESS`) bloqueando votaciones y actualizando visualmente el embed.
* `/ver_sugerencia <id>`: Consulta el estado detallado de una propuesta.
* **Protecciones:** Prevención estricta de auto-voto, soporte para retirar voto (toggle) o cambiar de opinión (switch).

### 🎭 4.4. Módulo de Autoroles (4 Comandos)
* `/setup_autoroles <canal> <titulo> [descripcion]`: Despliega el panel público con botón `[🎭 Seleccionar Roles]`.
* `/autorol_agregar_opcion <menu_id> <rol> <etiqueta> [emoji] [descripcion]`: Agrega un rol configurable al selector.
* `/autorol_eliminar_opcion <opcion_id>`: Elimina una opción del menú interactivo.
* `/autorol_listar`: Lista todos los menús y roles registrados en la base de datos.
* **Menú efímero:** Al pulsar el botón, el usuario recibe un menú desplegable privado (`ephemeral=True`) con pre-selección automática (`default=True`) de los roles que ya posee y sincronización atómica en un solo paso.

### 📢 4.5. Módulo de Anuncios y Comunicados Oficiales (5 Comandos)
* `/setup_anuncios <canal>`: Asigna el canal oficial por defecto para anuncios globales.
* `/anuncio [mencion]`: Redacta desde canal privado y difunde en el canal global `#anuncios`.
* `/anuncio_canal <canal> [mencion]`: Redacta y publica en **cualquier canal específico** (ej. `#reglas`, `#bienvenida`).
* `/comunicado <canal> [mencion]`: Alias de `/anuncio_canal` para normativas y comunicados institucionales.
* `/anuncios_historial [limite]`: Consulta administrativa del registro histórico de anuncios emitidos.
* **Seguridad:** Formulario modal (`AnnouncementModal`) -> Previsualización privada en canal de staff con botones `[🚀 Publicar Anuncio]` y `[❌ Cancelar]` -> Difusión con allowed mentions -> Auditoría en SQLite y `#mod-logs`.

### ⚙️ 4.6. Comandos Generales y Diagnóstico (3 Comandos)
* `/ping`: Comprueba la latencia del WebSocket de Discord y el tiempo de respuesta de SQLite.
* `/info`: Estadísticas de tiempo activo (uptime), versión de Python, versión de discord.py y servidores.
* `/help`: Guía interactiva y completa con la sintaxis de todos los 31 comandos del bot.

---

## 🚀 5. Métodos de Despliegue

1. **Railway (Nube 24/7 con Volumen Persistente)**:
   * Volumen persistente montado en `/app/data`.
   * Variable `DATABASE_PATH=/app/data/bot_database.sqlite3`.
   * Transferencia de datos con `railway volume files upload ./bot_database.sqlite3 /bot_database.sqlite3`.
2. **Docker Compose (VPS propio / NAS)**:
   * `docker compose up -d --build` utilizando volumen Docker nombrado `bot_data:/app/data`.
3. **Local / VPS Tradicional (Python Nativo)**:
   * Entorno virtual `.venv`, `pip install -r requirements.txt`, `.env` y `python main.py`.
