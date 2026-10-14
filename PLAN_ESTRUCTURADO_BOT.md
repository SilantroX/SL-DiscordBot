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
| **Diagramación** | Draw.io & Mermaid | Arquitectura visual disponible online y en archivo local `.drawio`. |

---

## 📐 Diagrama de Arquitectura
* **Editor Web Interactivo:** [Abrir en app.diagrams.net](https://app.diagrams.net/?grid=1&pv=0#R5V3fd6I61%2F5b3gvW6lzUpaCtXiJix3f80VftnG%2BuuiKkyhkgngDt9Pz1X3YSEJDW6LTVOnPOaiWEBLOf7L2fnZ1UMyzN6P8KfE2vP2IaeSTUjJ6m641anf1kpTh0iOuFS1F8N%2B9ftuGG0dcMW6ubmmEFvx48H7OqKxLFohpar2uuh5YUBVEtxLFoCi1xKCuYYeyxu49e%2FMxumANRofAGerNWFy8hOtLr8L9hyXbZRYgCLJuj%2FyRejJ04oYjdgDb7fvI3idiHLmHd13te5BDqQieNmp5%2BOc8Vzy9IfOmKGpeIOqtyr2nfwa8bitarEXExjJj7Sw7WVV026D7LEj0tWdK0k8amYOb9K9%2B8kVZLPBdHhYoxIX7srYuFDglD9j0LZYhS8lSs9kD8Yq9rNvhbBTMH%2Bdulf3luvJKl7fRrwI2v2Fuu0q6b6Z0Fcn4uKUlC2aGmGw%2Fth84DErcDlDYm60cr5JKnXNH2QKfDTQmT3Uu3NzKxsO%2FnhCn66e%2F%2FYDYGNMNpsa1Xm%2FvP5SXAbjCESg3NgF%2B3Q3Nu9ifTEVz0BjNrMmWt1n8ALCdz9pMV2OwXe3Tvt42wc%2B%2BmqOazB%2FmJlKbWr2udvta2tE690LNtTWY%2FZnN7xD5fmLcD3vwVCtaa0YXXGQ7s8Xz2RUoqfk7hET15gY9CdtV9WrGZNlsjB249senAylYx0yBGj33rLtMFvkV8QvmDRqt91errUE7COFf%2BwP%2Bx8iim5CfO3Wlet3SrKZ%2BYyVdo8JqIxnLmGGxIuhx02JW32byVN9v8y0iFEuNfL0q38Rr8tmY%2BJgGOKegW2WJTIvq5ePm0mT%2FNK1m2yk0dPS1Ecs4us5aVcMvqSDDsjZkkovcBDhaYbkNGv%2FLZC3YX7MMSPkgMdRqa2WRV76IEUY%2Fwtvvs58hj7VCSPsYKN0%2BmTdG0ZBDGmCKmtixD65pI6DHQHTSmAQblPAe7EVIPLmxQfsT9juNI6vAoWWAmNpewIStDs4iC3dD5Ngoz3CoBqTQX3w8powip5iakMsOSh9T1URHFJiYbRGVAdTSrrjk9rdPSWoCkiXhc4sqa%2ByQgTB7MSoRq6HKCJwCW1UWiFRQkDCoAVQwgW4XkiTUmcOUz051RAxQTHHDkZXA7a3A1Phu65Nd%2BWDwrwMsxtLYF2MqRPP0GxfgZvWo5O5dZuztnAjaYm0EVnP2FZxOaqqUL%2FMQkxIklRxmDkr8CzIUYeV94f9DH1%2Bn0dt3VRU7D%2BTiI0Lf0ykUB42LRpuX9FQTiGZ5jdSOrH1vd1SsQ2TAqENn6WETuTrzYV8dvsS5mLttXWsrwnNFNfwQc7%2BL2n%2BnX8Yh9Mmt1iQ6h8iQ9q90CL3wyPpB9GbbRM81d2Bf779qwPgP7am6nX80To1%2BAmgcfkUDdWFoaYF2Hh2qrVzU9BZqQPWVBH8LptT0UgabqByQmyCM%2FmOUDAvazJyfsmSU8S30fBaBLpyEGWzl5DdyfP9p9ZR45cfnDC%2FZzQNE8pZx7N64Z5pVVWTqZ90rbGhVQ%2FGA1tisSGQd%2FJAtly9pu51mbLR%2BWOqyGGQlTQqfUdg%2FT8R%2FOaPP2zX1%2F0H3od4VZHIxvJg%2F2V2s0cgaTcwZQ%2B1MiaD5T12SG1gEzOPnfgIkJlAQYwAtEaPSvx0q%2BqKFnimYefFl410VCvPlDhOOYBAvJo0jwCI4m025lRxIumB%2B5wFHuLvAx5hEHibxGQcAw5WJWVOENREu0go%2Fuq0cY8EJzO%2BpmAqKDWVaQhcvGScyayeyrsJ715iZU223L6jSroHpttNrdsrXWN%2B29zv8dFtJ1vQjpKnJnXldguv2xmFYP2hkCVkNwJttm934wZipHrwtkGOKXqSlF60S7uZa0LCZodYf9UX8yvbPsvrg%2FUmuzkogicJffYqIbrna99uYLXLgU5lCPN8ioxgeyUKfbMBrNXViorZtN8%2FozsNASCTWrQJ6W5UFuppTh8JqbSfjB9SuCxmXNzZgfI37cxRVkEPCrREDZXRSICcM%2Bf2cqOLuIiY9EmfXrodRmF09ozA4kJnPUKmsE7O5tk%2BiWK8y88dzWThYlhgEuNXQ28zE9%2F6LQxT%2Bm6wDcuM%2FIEeohBvhrGSBGlmLeS3cptMKD2JJ%2FRmz3e9AhfFonCoq6qYiLI7H%2FgAW%2BAW721FhrTziwgzXJyhwCc8AmIEaHvIBOl1ETLqQucpyEeerKOrtMiaaapg4XrAWMOFRFX9SshNGPdh9fUjnA7rIT%2FwsQtvtqAHlK4mYeiCIJ%2BXBuRB2hAf5HX%2BGIXohkgOmx2nO%2BQLnuoibqrBYZZC%2F2Tw06y6yY0m%2Bp337D2cKvPu9jLiQyqnIiTuaBdAyaoXeutw3Hd%2BO76Y8WCvZsGzsY%2Flw87pntFJ2W%2BWlbSCJqdFms%2Fsp%2BHDJllUS4iqv74iEOP4eP6yYIL3tqutWVNN75Bvkem5hnVIUs8HD6gxHWkAOd62Z04ZWm5XYIefD%2BpQjT2t2D6SsMlAqK6vcRNsrIa5yn45HiAEsPp0jBbAMRTW9R0M%2F8QRjUQGJFSVBTDVhvro4ckOyyjGnc4ZDmfZU4aEqqXNcPLhLFCipj3SuNyAcyuY6JH1BjaQrFICgiHFUQwrTPz6JqIyHWgn3kXTBlCfrVRnnipaS8qjkyFXa43gcGdCShae3x1%2BCWC4YSM2BWvil2bnDrod8ZkjAfoCVsXEY5i6nIQq4Xjl%2FC6PkSVXplOOixPVoVLHEYAMjhAkW86bKzlMm4x29budlRcMY3KWv0%2BGA1Z3%2BDV44FAjnidsl7BHmq%2FClfEKLnTOGrpvbnSqjAkLHdqpMYRgm9zfOnTOy%2B9avOFZRUuHbZ8k9vu7KrG30lnpSudTbx3pTPce5btq7eFPdlm02nM%2FgTbVKFq7Sm6rSXUf0ppig1dIL2bJNID48ajPJlvkq5xn4ymACrAdama3dK77U82B6KQOhsl6Ss%2Bk38pwAGFgE47ZCQ8bsxCrxP2mMdrRhHbmwvOxk17UWMKAJyZhQ7g4Efkb0cIToCKBR8a9ODzUhfiJYYQnwHasXrYGSukCKnNlahXSW48iMQy%2FRD1lwroAoaZF6BbOpBsTHMpsdAcEMdaxAji03Tvhqx5z2SPMBKqAQomEcJlUSPb6%2Bsbd24zuN9VJvnppKDpqaOgEN8kkQo7JSLYvmcgIilvWrZqBumNjn8NQTFZsCYMhCHK0SRnrR%2BcKhtd0zyhBzXM9ILvIyKxd5wQ43WH3P3uq9y7saMgh3Px3fjQfOr3haMuhT7WtBAgssVKNW6m0zAjB0RvwVuQ%2FoDByb70GRDhnv5IMXenUazXbqWCkhtmMYznW6QeGkXbHSQq%2FrNIe6bbfnET0xJmFYHZustqu%2Biaimr7i924E3yTVi%2FCV6sjMdQSBaBi65FmWSzmF6%2F4n3N3C4%2BzLY7K336qdVKcjjMW6AzY7pUOGndfLet8iQKsUbpbPHuDtja2WXLVV3jocX3M%2B%2F4yI5GCc%2FLSxt38F5gmCC9fXbsTRkmoJvD9d40nPF5I1m%2FDgR51HEiXysut9cbk6sJaQ2wR6cl8Hs3iQOSbAQ118y0PqJF5PLCEoPnWM9LWgVkVVF609sczBAC61W3quCeSOBG9Kg5Al2CUecVfeJqxhxFIcn1NB8Lsb8Qrh%2FsLY%2BxD59woVi4GCPGM9hz8dvianGpwTVvn1FuYepuPtIOIxQQFe5%2FPDvBZh6SQt9mkRbUzp%2Fo%2FuR3ece5cXo3vlzDHrgvV5ggJ%2FfdAJhtRjcadaKvcKOytxxP9mmnvy2tg9Ov%2FWspv6zLWebm3vsViN74qR9vvIW8yqn76pqEfYRnT5AjVr%2BjW8GK%2Fhv2cEpSrT9G3aTWCxbKriNQhnKVQHr01dEig9lx7scmm1lQFVWaOkE3Kvv16qAz%2FHoOkeP4vJGvoL6vWsc88cFTAW9jxOP%2FrziUByZoqWUa4jC73P6vOUggyHO7zvRL7SGjpn0X2mwbomVLXG43oRc3dL93YD97PtwfmH2aAfW%2FoXnDGIFFFc5na2jBfw5ileqWUO%2BaOVPwsP0%2Bi08JT6A3lJ0C4YQ5efHSqXBjDd0YPHYs%2FV%2BykIisnT2x20yE1uospQ1nMfQhdP9%2BBJSF3sHTVIeAYIN83NCECQXLbdDkMfy7zDfKpfXVTcenXEEpVFUaaEjxeXBAjk5WNJH4optUsI7vYUDXTksH8kiCQVIeWcirpcCWERmoDWosJCvdbZ4axXhVr%2FexJtRabiPizel3XdNQfuYwEO%2FALZXjsEFkDNFI54lPTP3V7%2BIwbnVSidpfJHNBzQmjwKRGaKTOYkvD7gr7xh4MlUAVbnx%2B%2BB%2BrT0eOfZ0fMdTijeDccd6fy7TrW%2FIFM8XOPX5aBgv6YIyFeOsS0tOX07CQpLp6cSVu7dLBytCZwXJRjQJXVlUPguVOZ8LLIe9fO7gR%2FiUITPTMXkqvtARzu0xTlwmudNEfxeRmAcWSemEq5%2BKpDzueZmUzrM7J5E0TlgkpWHfkEgavz51eShao7%2F77MeEX9y82xI1P16eb%2B%2F0f6%2F0CifznLr0dhn9q72OfmlT0HtHv7QN%2FJzG%2F3qv419advje8S9sHDmn0W%2FtV%2FekCbxfG%2F3SYrFzGv%2F2ftFf9CffO%2F7FvM2pD%2F%2BujmQuRdkfTZ270fjdljzYg1NZlZ1UEGdRZhvSzOVRPjCkcCqzKtiDI%2FkrcsiN9oYkVvlcwDnKQnqQubhfljU4KSEVBLEppny8%2FBzFtAev8pekkR%2FvDWlk0eRPIonKyrzaG39HTDaR%2B5Nu%2BTr8bvo35sQN%2BQD%2FK3em838%3D)
* **Archivo local:** `bot_arquitectura_y_flujos.drawio`

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
├── bot_flujos.mmd                # Diagrama en sintaxis Mermaid
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
