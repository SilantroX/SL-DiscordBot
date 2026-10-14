# 🤖 Bot de Discord Modular en Python (discord.py v2)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-v2.4%2B-5865F2.svg)](https://github.com/Rapptz/discord.py)
[![Database](https://img.shields.io/badge/database-SQLite%20(aiosqlite)-99AAB5.svg)](https://github.com/omnilib/aiosqlite)
[![Version](https://img.shields.io/badge/version-0.0.0-green.svg)](#versiones)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

Un bot de Discord profesional, modular, escalable y completamente tipado, diseñado con **Python 3.10+**, **discord.py v2** y una base de datos relacional asíncrona con **SQLite**.

---

## 🌟 Módulos Principales del Bot

1. **🛡️ Administración y Moderación:**
   * Comandos slash para moderación: `/kick`, `/ban`, `/unban`, `/timeout` (aislamiento nativo), `/warn`, `/warnings` y purga masiva de mensajes `/clear`.
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

5. **📢 Anuncios desde Canal Privado:**
   * Comando `/anuncio` ejecutado en el canal privado de administración.
   * Modal de redacción para título, contenido en Markdown, menciones (`@everyone`, `@here` o ninguna) y banner opcional.
   * **Vista previa de seguridad (Preview)** con botones `[🚀 Publicar]` y `[❌ Cancelar]` para evitar errores públicos.
   * Replicación inmediata en el canal público `#anuncios`.

---

## 📐 Diagrama de Arquitectura

El proyecto cuenta con un diagrama visual completo en formato **Draw.io** y **Mermaid**:
* **Abrir en Draw.io Web:** [Ver diagrama en app.diagrams.net](https://app.diagrams.net/?grid=1&pv=0#R5V1Zd%2BK4Ev4t98HnpB%2FCMTYk8GiMSXOHJTeQWZ5yhFFA3bbFeMnSv%2F6qJNnYxmlEOiyhe%2BYkWJYlo%2FpU9VWVpGimrZm9F9%2FTDP0JhxGhgWZ2NcOo13T2k5XiwKVzEixE8f20d9mCG2ZPMx1NtzTT9l8eiYdZ1SWNYlENrVa1OUGLEPlRLcCxaAotcCArWEFM2N0nEr%2ByG1ZfVCi8gdGo6eIlREeGDv%2BbtmyXXQTIx7K58N%2BExNiNkxCxG9Bmz0u%2B0Yh96FDWvd4lkUvDueiHzMVjMxpfzsWNSxS6y3JnaZf%2By02IVsshnWMYqPmLHKMrXQ7S%2FFWWGGnJIkw7qa8LJuSHfOF6Wi0hcxwVKsaUejFZFQtdGgTs6xXKUBjS52K1R%2BoVe12xMd8omLjI2yz9i8zjpSxtpV8DbnzFZLFMu26kd2bI%2Fb4IaRLIDjXDfGw9th%2BRuO2jtDFZP1qiOX3OFW0OdDrcIWUie%2Bv2WiY29rycMEU%2Fvd0fzMYgzOBZbOunzf3n8hLQ1h9Apbpmwq%2FbgTW1euO7IVx0%2BxN7fMda1f8BNI6n7CcrcNgv9ujObxth92GeB%2FMT8hIpTa2na%2B2e1rK1tl7o2bHHk38mU2fIPl9Yt33e%2FBXyV5rZgdcZ9J3RdPJFSip%2BTeERPRPfQwG76jwv2QSbrJALt57ZdGBly5gpDrPLvnWHqQDPph4N%2BYNms3XV7BlQToM4V%2F7I%2F7HyKA7pd5y707huGnZDPjGRr1DnNVEYy5ljsiHpcNDhubzN5q282eJfRuqRGL%2B8Kd36z%2BC3MfMx9XEcgkqRLTYkol%2BLl8%2Fr%2BdO4kmXL3NQx0kIk5%2Bwia1kJt6yOBMPOmEmi8MHH%2FgyHm5Axrjz2gp0Z%2B7CADxJD7bpmNVjV%2ByhBIaG87R77OSSsnZCmj7HC9ZNpU2Fa0g9iHCKmtmxT61hI6DHQHTSmAQblPAe7EVIPLmxQfsT9juNI6vAoWWAmNpewIStDs4iC3dD5Ngoz3CoBqTQX3w8powip5iakMsOSh9T1URHFJiYbRGVAdTSrrjk9rdPSWoCkiXhc4sqa%2ByQgTB7MSoRq6HKCJwCW1UWiFRQkDCoAVQwgW4XkiTUmcOUz051RAxQTHHDkZXA7a3A1Phu65Nd%2BWDwrwMsxtLYF2MqRPP0GxfgZvWo5O5dZuztnAjaYm0EVnP2FZxOaqqUL%2FMQkxIklRxmDkr8CzIUYeV94f9DH1%2Bn0dt3VRU7D%2BTiI0Lf0ykUB42LRpuX9FQTiGZ5jdSOrH1vd1SsQ2TAqENn6WETuTrzYV8dvsS5mLttXWsrwnNFNfwQc7%2BL2n%2BnX8Yh9Mmt1iQ6h8iQ9q90CL3wyPpB9GbbRM81d2Bf779qwPgP7am6nX80To1%2BAmgcfkUDdWFoaYF2Hh2qrVzU9BZqQPWVBH8LptT0UgabqByQmyCM%2FmOUDAvazJyfsmSU8S30fBaBLpyEGWzl5DdyfP9p9ZR45cfnDC%2FZzQNE8pZx7N64Z5pVVWTqZ90rbGhVQ%2FGA1tisSGQd%2FJAtly9pu51mbLR%2BWOqyGGQlTQqfUdg%2FT8R%2FOaPP2zX1%2F0H3od4VZHIxvJg%2F2V2s0cgaTcwZQ%2B1MiaD5T12SG1gEzOPnfgIkJlAQYwAtEaPSvx0q%2BqKFnimYefFl410VCvPlDhOOYBAvJo0jwCI4m025lRxIumB%2B5wFHuLvAx5hEHibxGQcAw5WJWVOENREu0go%2Fuq0cY8EJzO%2BpmAqKDWVaQhcvGScyayeyrsJ715iZU223L6jSroHpttNrdsrXWN%2B29zv8dFtJ1vQjpKnJnXldguv2xmFYP2hkCVkNwJttm934wZipHrwtkGOKXqSlF60S7uZa0LCZodYf9UX8yvbPsvrg%2FUmuzkogicJffYqIbrna99uYLXLgU5lCPN8ioxgeyUKfbMBrNXViorZtN8%2FozsNASCTWrQJ6W5UFuppTh8JqbSfjB9SuCxmXNzZgfI37cxRVkEPCrREDZXRSICcM%2Bf2cqOLuIiY9EmfXrodRmF09ozA4kJnPUKmsE7O5tk%2BiWK8y88dzWThYlhgEuNXQ28zE9%2F6LQxT%2Bm6wDcuM%2FIEeohBvhrGSBGlmLeS3cptMKD2JJ%2FRmz3e9AhfFonCoq6qYiLI7H%2FgAW%2BAW721FhrTziwgzXJyhwCc8AmIEaHvIBOl1ETLqQucpyEeerKOrtMiaaapg4XrAWMOFRFX9SshNGPdh9fUjnA7rIT%2FwsQtvtqAHlK4mYeiCIJ%2BXBuRB2hAf5HX%2BGIXohkgOmx2nO%2BQLnuoibqrBYZZC%2F2Tw06y6yY0m%2Bp337D2cKvPu9jLiQyqnIiTuaBdAyaoXeutw3Hd%2BO76Y8WCvZsGzsY%2Flw87pntFJ2W%2BWlbSCJqdFms%2Fsp%2BHDJllUS4iqv74iEOP4eP6yYIL3tqutWVNN75Bvkem5hnVIUs8HD6gxHWkAOd62Z04ZWm5XYIefD%2BpQjT2t2D6SsMlAqK6vcRNsrIa5yn45HiAEsPp0jBbAMRTW9R0M%2F8QRjUQGJFSVBTDVhvro4ckOyyjGnc4ZDmfZU4aEqqXNcPLhLFCipj3SuNyAcyuY6JH1BjaQrFICgiHFUQwrTPz6JqIyHWgn3kXTBlCfrVRnnipaS8qjkyFXa43gcGdCShae3x1%2BCWC4YSM2BWvil2bnDrod8ZkjAfoCVsXEY5i6nIQq4Xjl%2FC6PkSVXplOOixPVoVLHEYAMjhAkW86bKzlMm4x29budlRcMY3KWv0%2BGA1Z3%2BDV44FAjnidsl7BHmq%2FClfEKLnTOGrpvbnSqjAkLHdqpMYRgm9zfOnTOy%2B9avOFZRUuHbZ8k9vu7KrG30lnpSudTbx3pTPce5btq7eFPdlm02nM%2FgTbVKFq7Sm6rSXUf0ppig1dIL2bJNID48ajPJlvkq5xn4ymACrAdama3dK77U82B6KQOhsl6Ss%2Bk38pwAGFgE47ZCQ8bsxCrxP2mMdrRhHbmwvOxk17UWMKAJyZhQ7g4Efkb0cIToCKBR8a9ODzUhfiJYYQnwHasXrYGSukCKnNlahXSW48iMQy%2FRD1lwroAoaZF6BbOpBsTHMpsdAcEMdaxAji03Tvhqx5z2SPMBKqAQomEcJlUSPb6%2Bsbd24zuN9VJvnppKDpqaOgEN8kkQo7JSLYvmcgIilvWrZqBumNjn8NQTFZsCYMhCHK0SRnrR%2BcKhtd0zyhBzXM9ILvIyKxd5wQ43WH3P3uq9y7saMgh3Px3fjQfOr3haMuhT7WtBAgssVKNW6m0zAjB0RvwVuQ%2FoDByb70GRDhnv5IMXenUazXbqWCkhtmMYznW6QeGkXbHSQq%2FrNIe6bbfnET0xJmFYHZustqu%2Biaimr7i924E3yTVi%2FCV6sjMdQSBaBi65FmWSzmF6%2F4n3N3C4%2BzLY7K336qdVKcjjMW6AzY7pUOGndfLet8iQKsUbpbPHuDtja2WXLVV3jocX3M%2B%2F4yI5GCc%2FLSxt38F5gmCC9fXbsTRkmoJvD9d40nPF5I1m%2FDgR51HEiXysut9cbk6sJaQ2wR6cl8Hs3iQOSbAQ118y0PqJF5PLCEoPnWM9LWgVkVVF609sczBAC61W3quCeSOBG9Kg5Al2CUecVfeJqxhxFIcn1NB8Lsb8Qrh%2FsLY%2BxD59woVi4GCPGM9hz8dvianGpwTVvn1FuYepuPtIOIxQQFe5%2FPDvBZh6SQt9mkRbUzp%2Fo%2FuR3ece5cXo3vlzDHrgvV5ggJ%2FfdAJhtRjcadaKvcKOytxxP9mmnvy2tg9Ov%2FWspv6zLWebm3vsViN74qR9vvIW8yqn76pqEfYRnT5AjVr%2BjW8GK%2Fhv2cEpSrT9G3aTWCxbKriNQhnKVQHr01dEig9lx7scmm1lQFVWaOkE3Kvv16qAz%2FHoOkeP4vJGvoL6vWsc88cFTAW9jxOP%2FrziUByZoqWUa4jC73P6vOUggyHO7zvRL7SGjpn0X2mwbomVLXG43oRc3dL93YD97PtwfmH2aAfW%2FoXnDGIFFFc5na2jBfw5ileqWUO%2BaOVPwsP0%2Bi08JT6A3lJ0C4YQ5efHSqXBjDd0YPHYs%2FV%2BykIisnT2x20yE1uospQ1nMfQhdP9%2BBJSF3sHTVIeAYIN83NCECQXLbdDkMfy7zDfKpfXVTcenXEEpVFUaaEjxeXBAjk5WNJH4optUsI7vYUDXTksH8kiCQVIeWcirpcCWERmoDWosJCvdbZ4axXhVr%2FexJtRabiPizel3XdNQfuYwEO%2FALZXjsEFkDNFI54lPTP3V7%2BIwbnVSidpfJHNBzQmjwKRGaKTOYkvD7gr7xh4MlUAVbnx%2B%2BB%2BrT0eOfZ0fMdTijeDccd6fy7TrW%2FIFM8XOPX5aBgv6YIyFeOsS0tOX07CQpLp6cSVu7dLBytCZwXJRjQJXVlUPguVOZ8LLIe9fO7gR%2FiUITPTMXkqvtARzu0xTlwmudNEfxeRmAcWSemEq5%2BKpDzueZmUzrM7J5E0TlgkpWHfkEgavz51eShao7%2F77MeEX9y82xI1P16eb%2B%2F0f6%2F0CifznLr0dhn9q72OfmlT0HtHv7QN%2FJzG%2F3qv419advje8S9sHDmn0W%2FtV%2FekCbxfG%2F3SYrFzGv%2F2ftFf9CffO%2F7FvM2pD%2F%2BujmQuRdkfTZ270fjdljzYg1NZlZ1UEGdRZhvSzOVRPjCkcCqzKtiDI%2FkrcsiN9oYkVvlcwDnKQnqQubhfljU4KSEVBLEppny8%2FBzFtAev8pekkR%2FvDWlk0eRPIonKyrzaG39HTDaR%2B5Nu%2BTr8bvo35sQN%2BQD%2FK3em838%3D)
* **Archivo local:** `bot_arquitectura_y_flujos.drawio`

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

## 🚀 Requisitos e Instalación Paso a Paso

### 1. Requisitos Previos
* **Python 3.10 o superior** instalado.
* **Git** instalado.
* Una cuenta de Discord y acceso al [Discord Developer Portal](https://discord.com/developers/applications).

### 2. Configurar la Aplicación en Discord Developer Portal
1. Ve a [Discord Developer Portal](https://discord.com/developers/applications) y haz clic en **New Application**.
2. Dale un nombre a tu bot (ej. `Antigravity Bot`).
3. Ve a la pestaña **Bot**:
   * Haz clic en **Reset Token** y copia el token generado (este será tu `DISCORD_TOKEN`).
   * Desplázate hacia abajo hasta **Privileged Gateway Intents** y activa:
     * ✅ **Presence Intent**
     * ✅ **Server Members Intent** (esencial para autoroles y moderación)
     * ✅ **Message Content Intent** (esencial para comandos y contenido de mensajes)
   * Haz clic en **Save Changes**.
4. Ve a la pestaña **OAuth2 -> URL Generator**:
   * En **SCOPES** marca: `bot` y `applications.commands`.
   * En **BOT PERMISSIONS** marca: `Administrator` (o permisos individuales de gestión de canales, mensajes, roles, baneo y expulsión).
   * Copia la URL generada al final e invita al bot a tu servidor de Discord.

### 3. Clonar e Instalar el Proyecto

```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd "Bot Discord"

# 2. Crear el entorno virtual
python -m venv .venv

# 3. Activar el entorno virtual
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En Linux / macOS:
source .venv/bin/activate

# 4. Instalar las dependencias
pip install -r requirements.txt
```

### 4. Configurar las Variables de Entorno

Copia el archivo de plantilla `.env.example` y renómbralo a `.env`:

```bash
# En Windows:
copy .env.example .env

# En Linux / macOS:
cp .env.example .env
```

Abre `.env` con tu editor de texto y completa:

```env
DISCORD_TOKEN=tu_token_secreto_aqui
GUILD_ID=123456789012345678   # ID de tu servidor para sincronización instantánea de comandos slash
COMMAND_PREFIX=!
DATABASE_PATH=bot_database.sqlite3
ENVIRONMENT=development
```

### 5. Iniciar el Bot

```bash
# Con el entorno virtual activado:
python main.py
```

Al iniciar por primera vez:
1. Se inicializará automáticamente la base de datos `bot_database.sqlite3` con las 7 tablas del sistema.
2. Se cargarán todos los cogs.
3. Se sincronizarán los comandos Slash (`/ping`, `/info`, `/help`).

---

## 📌 Versiones y Registro de Cambios (Changelog)

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
