# 🤖 SilantroLabs Bot — Bot de Discord Modular en Python (discord.py v2)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-v2.4%2B-5865F2.svg)](https://github.com/Rapptz/discord.py)
[![Database](https://img.shields.io/badge/database-SQLite%20(aiosqlite)-99AAB5.svg)](https://github.com/omnilib/aiosqlite)
[![Version](https://img.shields.io/badge/version-1.2.0-green.svg)](#versiones)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

**SilantroLabs Bot** es un bot de Discord profesional, modular, escalable y completamente tipado, diseñado con **Python 3.10+**, **discord.py v2** y una base de datos relacional asíncrona con **SQLite**.

---

## 🌟 Módulos Principales del Bot

1. **🛡️ Administración y Moderación:**
   * Comandos slash para moderación: `/kick`, `/ban`, `/unban`, `/timeout` (aislamiento nativo), `/warn`, `/warnings`, purga de mensajes `/clear`, y gestión masiva de roles (`/role_add_all`, `/role_remove_all`).
   * Verificación obligatoria de jerarquía de roles para evitar que moderadores sancionen a usuarios con roles iguales o superiores.
   * Registro automático y detallado de cada acción en un canal de auditoría `#mod-logs`.

2. **🎫 Tickets de Soporte:**
   * Panel de apertura fijado mediante Vistas Persistentes (`discord.ui.View` con `timeout=None`) que funcionan incluso tras reiniciar el bot.
   * Formulario modal emergente (`discord.ui.Modal`) para solicitar motivo y asunto de forma estructurada.
   * Creación dinámica de canales privados (`ticket-usuario-id`) restringidos exclusivamente al creador, rol de Staff y el bot.
   * Controles dentro del ticket: Reclamar atención por parte de un miembro del staff, cierre seguro y exportación completa de la transcripción del chat.

3. **💡 Sugerencias de la Comunidad:**
   * Envío de sugerencias mediante comando `/sugerir` o botón en canal público.
   * Embed dinámico con contadores en vivo de votos a favor (`👍`) y en contra (`👎`) con prevención de voto duplicado.
   * Panel de resolución de staff para aprobar, rechazar o marcar en desarrollo las propuestas, con notificación por DM al usuario.

4. **🎭 Autoroles Interactivos (Role Selector):**
   * Panel visual fijo con botón interactivo `[🎭 Seleccionar Roles]`.
   * Menú desplegable efímero (`discord.ui.Select` / `StringSelect`) visible solo para el usuario (`ephemeral=True`), evitando saturar el canal.
   * Selección múltiple con emojis y descripciones.
   * Sincronización automática de roles con verificación de jerarquía.

5. **📢 Anuncios y Comunicados Oficiales:**
   * Comando `/anuncio [mencion]`: Apertura de modal desde canal privado y difusión en el canal público configurado `#anuncios`.
   * Comando `/anuncio_canal <canal> [mencion]` (o alias `/comunicado <canal> [mencion]`): Permite redactar y publicar comunicados oficiales, normas o mensajes institucionales en **cualquier canal específico** (ej. `#reglas`, `#bienvenida`, `#noticias`).
   * Modal interactivo de redacción con soporte para Markdown enriquecido, menciones y banner visual.
   * **Vista previa de seguridad (Preview)** con botones `[🚀 Publicar]` y `[❌ Cancelar]` antes de emitir públicamente.
   * Auditoría de publicaciones en `#mod-logs` y consulta histórica con `/anuncios_historial`.

---

## ⌨️ Referencia de Comandos (31 Comandos Slash)

| Módulo | Comando | Descripción |
|---|---|---|
| **🛡️ Admin** | `/setup_admin <logs> [staff]` | Configura el canal de auditoría `#mod-logs` y rol de Staff |
| **🛡️ Admin** | `/warn <usuario> <motivo>` | Registra una advertencia formal con notificación por DM |
| **🛡️ Admin** | `/warnings <usuario>` | Consulta el historial de infracciones y advertencias |
| **🛡️ Admin** | `/timeout <usuario> <duracion> [motivo]` | Aplica aislamiento temporal nativo (hasta 28 días) |
| **🛡️ Admin** | `/untimeout <usuario> [motivo]` | Retira el aislamiento temporal a un miembro |
| **🛡️ Admin** | `/kick <usuario> [motivo]` | Expulsa a un miembro con validación de jerarquía |
| **🛡️ Admin** | `/ban <usuario> [motivo] [borrar_dias]` | Banea permanentemente con opción de purga de historial |
| **🛡️ Admin** | `/unban <user_id> [motivo]` | Revoca el baneo de un usuario mediante su ID numérico |
| **🛡️ Admin** | `/clear <cantidad>` | Purga mensajes recientes (últimos 14 días) cronológicamente |
| **🛡️ Admin** | `/role_add_all <rol> [ignorar_bots]` | Asigna un rol a todos los miembros de forma segura |
| **🛡️ Admin** | `/role_remove_all <rol> [ignorar_bots]` | Remueve un rol masivamente de todos los miembros |
| **🎫 Tickets** | `/setup_tickets <categoria> <logs>` | Configura categoría de tickets y canal de transcripciones |
| **🎫 Tickets** | `/ticket_panel [titulo] [desc]` | Despliega el panel público fijo con botón `[📩 Crear Ticket]` |
| **🎫 Tickets** | `/ticket_add <usuario>` | Concede acceso a un miembro dentro de un ticket activo |
| **🎫 Tickets** | `/ticket_remove <usuario>` | Revoca el acceso de un miembro del ticket |
| **💡 Sugerencias** | `/setup_suggestions <canal>` | Asigna el canal público de sugerencias |
| **💡 Sugerencias** | `/sugerir <contenido>` | Publica una propuesta comunitaria con botones 👍 / 👎 |
| **💡 Sugerencias** | `/responder_sugerencia <id> <estado> [nota]` | Staff aprueba, rechaza o marca en desarrollo una propuesta |
| **💡 Sugerencias** | `/ver_sugerencia <id>` | Consulta el estado detallado de una sugerencia |
| **🎭 Autoroles** | `/setup_autoroles <canal> <titulo> [desc]` | Crea un panel público con botón `[🎭 Seleccionar Roles]` |
| **🎭 Autoroles** | `/autorol_agregar_opcion <menu> <rol> <lbl> [emoji]` | Añade una opción de rol con emoji y descripción al menú |
| **🎭 Autoroles** | `/autorol_eliminar_opcion <opcion_id>` | Elimina una opción de rol del selector interactivo |
| **🎭 Autoroles** | `/autorol_listar` | Lista todos los menús y roles configurados en la base de datos |
| **📢 Anuncios** | `/setup_anuncios <canal>` | Configura el canal público oficial de comunicados globales |
| **📢 Anuncios** | `/anuncio [mencion]` | Redacta desde canal privado y publica en el canal global |
| **📢 Anuncios** | `/anuncio_canal <canal> [mencion]` | Publica un anuncio o comunicado en cualquier canal específico |
| **📢 Anuncios** | `/comunicado <canal> [mencion]` | Alias directo para publicar comunicados en canales específicos |
| **📢 Anuncios** | `/anuncios_historial [limite]` | Muestra el registro histórico de anuncios emitidos |
| **⚙️ General** | `/ping` | Mide la latencia del WebSocket de Discord y de SQLite |
| **⚙️ General** | `/info` | Estadísticas técnicas, servidores, usuarios y tiempo activo |
| **⚙️ General** | `/help` | Despliega la guía interactiva completa del bot |

---

## 📐 Diagrama de Arquitectura

* **Editor interactivo online:** [Abrir en app.diagrams.net](https://app.diagrams.net/?grid=1#Uhttps%3A%2F%2Fraw.githubusercontent.com%2FSilantroX%2FSL-DiscordBot%2Fmaster%2Fbot_arquitectura_y_flujos.drawio)
* **Visualizador interactivo:** [Ver en viewer.diagrams.net](https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1&title=bot_arquitectura_y_flujos.drawio#Uhttps%3A%2F%2Fraw.githubusercontent.com%2FSilantroX%2FSL-DiscordBot%2Fmaster%2Fbot_arquitectura_y_flujos.drawio)
* **Archivo local:** `bot_arquitectura_y_flujos.drawio` (se puede arrastrar a [app.diagrams.net](https://app.diagrams.net) o abrir en la extensión Draw.io de VS Code / Draw.io Desktop)

---

## 📁 Estructura del Proyecto

```text
Bot Discord/
├── .env                          # Variables de entorno y Token (IGNORADO EN GIT)
├── .env.example                  # Plantilla de configuración
├── .gitignore                    # Reglas de exclusión de Git
├── requirements.txt              # Dependencias de Python fijadas
├── main.py                       # Punto de entrada principal y carga de Cogs
├── config.py                     # Carga y validación tipada del .env
├── bot_arquitectura_y_flujos.drawio # Diagrama nativo editable en Draw.io
├── PLAN_ESTRUCTURADO_BOT.md      # Documento maestro de arquitectura y flujos
├── database/
│   ├── __init__.py
│   ├── connection.py             # Administrador de conexión SQLite asíncrona (aiosqlite)
│   └── queries.py                # Consultas SQL reutilizables (CRUD)
├── cogs/
│   ├── __init__.py
│   ├── general.py                # Comandos de diagnóstico (/ping, /info, /help)
│   ├── admin.py                  # Moderación, sanciones y logs (Módulo 1)
│   ├── tickets.py                # Tickets interactivos con vistas persistentes (Módulo 2)
│   ├── suggestions.py            # Sugerencias y votaciones de comunidad (Módulo 3)
│   ├── roles.py                  # Autoroles interactivos con menús select (Módulo 4)
│   └── announcements.py          # Creación y replicación de anuncios (Módulo 5)
└── utils/
    ├── __init__.py
    ├── embeds.py                 # Generador estándar de Discord Embeds
    └── checks.py                 # Funciones de validación de jerarquías y permisos
```

---

## 🚀 Métodos de Despliegue y Ejecución

El bot está diseñado para ser totalmente agnóstico a la plataforma: funciona en un entorno local, en cualquier servidor VPS tradicional (Linux/Windows), en contenedores Docker y en plataformas de nube modernas como Railway.

### Requisitos Previos Comunes
1. Una cuenta de Discord y acceso al [Discord Developer Portal](https://discord.com/developers/applications).
2. **Privileged Gateway Intents** activados en la pestaña **Bot**:
   * ✅ **Presence Intent**
   * ✅ **Server Members Intent** (esencial para autoroles, asignación masiva y moderación)
   * ✅ **Message Content Intent** (esencial para comandos y contenido de mensajes)
3. Invitar al bot a tu servidor mediante **OAuth2 -> URL Generator** con scopes `bot` y `applications.commands` (y permisos de Administrador o gestión de roles, canales y moderación).

---

### Opción A: Despliegue en la Nube 24/7 con Railway (Recomendado para Producción)

Railway permite mantener el bot activo 24/7 sin necesidad de mantener encendida una computadora propia.

#### 1. Conectar Repositorio o Usar Railway CLI
* Puedes crear un proyecto en [Railway.app](https://railway.com/) conectando directamente tu repositorio de GitHub, o usar el CLI de Railway:
  ```bash
  npm i -g @railway/cli
  railway login
  railway link
  ```

#### 2. Configurar Variables de Entorno en Railway
En la pestaña **Variables** de tu servicio en Railway, agrega:
* `DISCORD_TOKEN`: Tu token de bot de Discord.
* `GUILD_ID`: ID del servidor para sincronización instantánea (opcional).
* `COMMAND_PREFIX`: `!` (o el prefijo deseado).
* `ENVIRONMENT`: `production`.
* `DATABASE_PATH`: `/app/data/bot_database.sqlite3`.

#### 3. Añadir Volumen Persistente (Imprescindible para SQLite)
> [!IMPORTANT]
> Los contenedores en la nube son efímeros por defecto: si el bot se reinicia o se despliega una nueva versión, cualquier cambio en la base de datos se perdería si no se usa un volumen persistente.

1. En la pestaña del servicio en Railway, ve a **Settings** o **Volumes** y haz clic en **Add Volume**.
2. Asigna la ruta de montaje (Mount Path): `/app/data`.
3. *(Opcional)* Si ya tienes datos locales y quieres migrarlos a Railway:
   ```bash
   # Agregar tu clave SSH a Railway (requerido para transferencia de archivos)
   railway ssh keys add
   # Subir tu base de datos local al volumen persistente
   railway volume files upload ./bot_database.sqlite3 /bot_database.sqlite3
   ```
4. El bot se iniciará automáticamente mediante el `Dockerfile` / `Procfile` y mantendrá los datos permanentemente seguros.

---

### Opción B: Despliegue con Docker y Docker Compose (Ideal para VPS propio)

Si cuentas con tu propio servidor VPS (Ubuntu, Debian, CentOS, etc.) o NAS (Synology, Unraid):

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd "Bot Discord"
   ```

2. **Crear archivo `.env`:**
   ```bash
   cp .env.example .env
   # Edita .env con tu editor favorito y coloca tu DISCORD_TOKEN
   ```

3. **Iniciar con Docker Compose:**
   ```bash
   docker compose up -d --build
   ```
   * El archivo [`docker-compose.yml`](docker-compose.yml) creará automáticamente un volumen persistente de Docker llamado `bot_data` montado en `/app/data`, asegurando que la base de datos SQLite sobreviva a cualquier reinicio o actualización de imagen.

4. **Ver registros en tiempo real:**
   ```bash
   docker compose logs -f
   ```

5. **Detener el bot:**
   ```bash
   docker compose down
   ```

---

### Opción C: Ejecución Local / VPS Tradicional (Python Nativo)

Si prefieres correr el bot directamente en tu máquina o en un VPS sin contenedores:

1. **Requisitos:**
   * Python 3.10 o superior (compatible hasta Python 3.13+).
   * Git.

2. **Crear y activar entorno virtual:**
   ```bash
   # Crear el entorno virtual
   python -m venv .venv

   # Activar en Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # O en Linux / macOS:
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar el archivo `.env`:**
   ```bash
   # Windows:
   copy .env.example .env
   # Linux / macOS:
   cp .env.example .env
   ```
   Edita `.env` y define tu `DISCORD_TOKEN`. La base de datos se creará de forma predeterminada como `bot_database.sqlite3` en la misma carpeta del proyecto.

5. **Iniciar el bot:**
   ```bash
   python main.py
   ```

6. **Ejecutar suite de pruebas unitarias (37 pruebas):**
   ```bash
   python -m unittest discover tests -v
   ```

---

## 📌 Versiones y Registro de Cambios (Changelog)

* **v1.2.0**: **Anuncios Multicanal y Comunicados Institucionales**.
  - Comando `/anuncio_canal <canal> [mencion]`: Permite a moderadores y staff publicar anuncios institucionales en cualquier canal específico (`#reglas`, `#bienvenida`, etc.).
  - Comando `/comunicado <canal> [mencion]`: Alias complementario orientado a redacción y difusión de normativas y comunicados.
  - Validación de permisos del bot en el canal especificado (`send_messages` y `embed_links`) para prevenir fallos antes de enviar el formulario modal.
  - Vista previa interactiva adaptada mostrando el canal destino en el embed de borrador.
  - Auditoría de publicaciones vinculadas al canal destino en SQLite y en `#mod-logs`.
  - Cobertura completa de pruebas unitarias ampliada a 39 pruebas automáticas.

* **v1.1.0**: **Gestión Masiva de Roles en Administración**.
  - Comando `/role_add_all <rol> [ignorar_bots]`: Asigna un rol de forma iterativa y segura a todos los miembros del servidor.
  - Comando `/role_remove_all <rol> [ignorar_bots]`: Remueve un rol masivamente de todos los miembros del servidor.
  - Validación estricta de jerarquía (`guild.me.top_role > rol` y `moderator.top_role > rol`), protección para `@everyone` y roles administrados.
  - Prevención de rate-limits de Discord mediante pausas asíncronas automáticas y aplazamiento de interacción (`defer`).
  - Filtro opcional para omitir cuentas de bots (`ignorar_bots=True` por defecto).
  - Registro de auditoría detallado en `#mod-logs` con conteo de éxitos, omisiones y fallos.
  - Cobertura completa de pruebas unitarias (`tests/test_admin.py`).

* **v1.0.0**: **Lanzamiento Oficial & Branding SilantroLabs**.
  - Personalización completa de identidad visual corporativa para SilantroLabs.
  - Presencia motivadora en Discord: `SilantroLabs • Innovando el futuro 🚀 (/help)`.
  - Estandarización de footers en todos los Embeds: `SilantroLabs • Discord Bot`.
  - Transcripciones HTML oficiales con firma de SilantroLabs.

* **v0.5.0**: **Módulo 5 - Anuncios con Replicación desde Canal Privado**.
  - Comando `/setup_anuncios <canal>`: Configuración del canal oficial global para difusión de comunicados.
  - Comando `/anuncio [mencion]`: Apertura de formulario modal interactivo (`AnnouncementModal`) desde un canal privado de moderación para redactar título, contenido enriquecido (Markdown) y URL de banner.
  - Vista previa de seguridad (Preview): Genera el embed de previsualización idéntico al final con controles interactivos `[🚀 Publicar Anuncio]` y `[❌ Cancelar]`.
  - Replicación y difusión: Publica instantáneamente en el canal público oficial con menciones opcionales (`@everyone`, `@here` o ninguna).
  - Auditoría y trazabilidad: Registro del anuncio en SQLite (`announcements`) y en el canal de auditoría `#mod-logs`.
  - Comando `/anuncios_historial [limite]`: Consulta administrativa del registro histórico de anuncios emitidos.
  - Cobertura completa de pruebas unitarias (`tests/test_announcements.py`).

* **v0.4.0**: **Módulo 4 - Autoroles Interactivos**.
  - Comando `/setup_autoroles <canal> <titulo> [descripcion]`: Despliegue de paneles públicos con vista persistente `[🎭 Seleccionar Roles]`.
  - Menú desplegable efímero (`discord.ui.Select` / `StringSelect`): Menú multi-selección (`min_values=0, max_values=N`) visible de forma privada solo para el usuario (`ephemeral=True`), evitando inundar el canal.
  - Pre-selección visual automática: Muestra los roles que el usuario ya posee marcados por defecto con `default=True`.
  - Sincronización atómica de roles: Detecta y ejecuta en una sola interacción los roles a otorgar y los roles desmarcados a revocar.
  - Validación estricta de jerarquía (`bot.top_role > rol`) para prevenir errores de permisos de Discord, junto a bloqueos de seguridad para `@everyone` y roles administrados por bots/integraciones.
  - Comandos administrativos `/autorol_agregar_opcion`, `/autorol_eliminar_opcion` y `/autorol_listar`, con actualización en tiempo real del embed público.
  - Cobertura completa de pruebas unitarias (`tests/test_roles.py`).

* **v0.3.0**: **Módulo 3 - Sugerencias y Votaciones Comunitarias**.
  - Comando `/setup_suggestions <canal>`: Asignación oficial del canal de sugerencias con validación de permisos.
  - Comando `/sugerir <texto>`: Envío estructurado de sugerencias con embeds dinámicos y botones de votación.
  - Vistas interactivas persistentes (`SuggestionVoteView`): Botones `[👍 A favor]` y `[👎 En contra]` que sobreviven a reinicios.
  - Lógica anti-trampas: Prevención estricta de auto-voto (el autor no puede votar su propuesta) y soporte para retirar voto (toggle) o cambiar de sentido (switch).
  - Tabla `suggestion_votes` en SQLite para persistencia y auditoría de votos individuales.
  - Comando de Staff `/responder_sugerencia <id> <estado> [comentario]`: Aprobación, Rechazo o Desarrollo con desactivación de botones y actualización visual del embed.
  - Notificaciones privadas por DM al autor cuando su sugerencia es resuelta.
  - Comando de consulta `/ver_sugerencia <id>`.
  - Cobertura completa de pruebas unitarias (`tests/test_suggestions.py`).

* **v0.2.0**: **Módulo 2 - Tickets de Soporte**.
  - Vistas persistentes (`TicketPanelPersistentView` y `TicketControlView`).
  - Formularios emergentes (`TicketCreateModal`).
  - Canales privados automáticos con permisos aislados (`ticket-usuario-id`).
  - Motor de transcripciones HTML estilo Discord Dark Mode (`utils/transcript.py`).
  - Controles: Reclamar atención, Cierre en 2 pasos, `/ticket_add` y `/ticket_remove`.

* **v0.1.1**: **Mejoras de Seguridad y Moderación en Admin**.
  - Corrección de orden cronológico en `/clear` (eliminación de más nuevo a más antiguo, filtrado de mensajes menores a 14 días).
  - Monitor de eventos críticos de auditoría en tiempo real (`on_guild_channel_create`, `on_guild_channel_delete`, `on_guild_channel_update`, `on_guild_role_create`, `on_guild_role_delete`, `on_guild_role_update` con alerta roja ante permisos peligrosos como Administrador, `on_member_update` ante asignación de roles, `on_member_ban`, `on_member_unban`).

* **v0.1.0**: **Módulo 1 - Administración y Moderación**.
  - Comandos slash `/setup_admin`, `/warn`, `/warnings`, `/timeout`, `/untimeout`, `/kick`, `/ban`, `/unban`.
  - Validación estricta de jerarquía de roles de Discord.
  - Registro de sanciones e historial en SQLite.

* **v0.0.0**: Inicialización del proyecto, arquitectura base, conexión asíncrona SQLite (`aiosqlite`), cargador dinámico de Cogs, utilidades de embeds y jerarquías, comandos `/ping`, `/info` y `/help`, integración con Draw.io y Git.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
