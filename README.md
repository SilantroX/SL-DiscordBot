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

El proyecto cuenta con un diagrama visual completo en formato **Draw.io** y **Mermaid**:
* **Abrir en Draw.io Web:** [Ver diagrama en app.diagrams.net](https://app.diagrams.net/?grid=1&pv=0#R5V3fd6I61%2F5b3gvW6lzUpaCtXiJix3f80VftnG%2BuuiKkyhkgngDt9Pz1X3YSEJDW6LTVOnPOaiWEBLOf7L2fnZ1UMyzN6P8KfE2vP2IaeSTUjJ6m641anf1kpTh0iOuFS1F8N%2B9ftuGG0dcMW6ubmmEFvx48H7OqKxLFohpar2uuh5YUBVEtxLFoCi1xKCuYYeyxu49e%2FMxumANRofAGerNWFy8hOtLr8L9hyXbZRYgCLJuj%2FyRejJ04oYjdgDb7fvI3idiHLmHd13te5BDqQieNmp5%2BOc8Vzy9IfOmKGpeIOqtyr2nfwa8bitarEXExjJj7Sw7WVV026D7LEj0tWdK0k8amYOb9K9%2B8kVZLPBdHhYoxIX7srYuFDglD9j0LZYhS8lSs9kD8Yq9rNvhbBTMH%2Bdulf3luvJKl7fRrwI2v2Fuu0q6b6Z0Fcn4uKUlC2aGmGw%2Fth84DErcDlDYm60cr5JKnXNH2QKfDTQmT3Uu3NzKxsO%2FnhCn66e%2F%2FYDYGNMNpsa1Xm%2FvP5SXAbjCESg3NgF%2B3Q3Nu9ifTEVz0BjNrMmWt1n8ALCdz9pMV2OwXe3Tvt42wc%2B%2BmqOazB%2FmJlKbWr2udvta2tE690LNtTWY%2FZnN7xD5fmLcD3vwVCtaa0YXXGQ7s8Xz2RUoqfk7hET15gY9CdtV9WrGZNlsjB249senAylYx0yBGj33rLtMFvkV8QvmDRqt91errUE7COFf%2BwP%2Bx8iim5CfO3Wlet3SrKZ%2BYyVdo8JqIxnLmGGxIuhx02JW32byVN9v8y0iFEuNfL0q38Rr8tmY%2BJgGOKegW2WJTIvq5ePm0mT%2FNK1m2yk0dPS1Ecs4us5aVcMvqSDDsjZkkovcBDhaYbkNGv%2FLZC3YX7MMSPkgMdRqa2WRV76IEUY%2Fwtvvs58hj7VCSPsYKN0%2BmTdG0ZBDGmCKmtixD65pI6DHQHTSmAQblPAe7EVIPLmxQfsT9juNI6vAoWWAmNpewIStDs4iC3dD5Ngoz3CoBqTQX3w8powip5iakMsOSh9T1URHFJiYbRGVAdTSrrjk9rdPSWoCkiXhc4sqa%2ByQgTB7MSoRq6HKCJwCW1UWiFRQkDCoAVQwgW4XkiTUmcOUz051RAxQTHHDkZXA7a3A1Phu65Nd%2BWDwrwMsxtLYF2MqRPP0GxfgZvWo5O5dZuztnAjaYm0EVnP2FZxOaqqUL%2FMQkxIklRxmDkr8CzIUYeV94f9DH1%2Bn0dt3VRU7D%2BTiI0Lf0ykUB42LRpuX9FQTiGZ5jdSOrH1vd1SsQ2TAqENn6WETuTrzYV8dvsS5mLttXWsrwnNFNfwQc7%2BL2n%2BnX8Yh9Mmt1iQ6h8iQ9q90CL3wyPpB9GbbRM81d2Bf779qwPgP7am6nX80To1%2BAmgcfkUDdWFoaYF2Hh2qrVzU9BZqQPWVBH8LptT0UgabqByQmyCM%2FmOUDAvazJyfsmSU8S30fBaBLpyEGWzl5DdyfP9p9ZR45cfnDC%2FZzQNE8pZx7N64Z5pVVWTqZ90rbGhVQ%2FGA1tisSGQd%2FJAtly9pu51mbLR%2BWOqyGGQlTQqfUdg%2FT8R%2FOaPP2zX1%2F0H3od4VZHIxvJg%2F2V2s0cgaTcwZQ%2B1MiaD5T12SG1gEzOPnfgIkJlAQYwAtEaPSvx0q%2BqKFnimYefFl410VCvPlDhOOYBAvJo0jwCI4m025lRxIumB%2B5wFHuLvAx5hEHibxGQcAw5WJWVOENREu0go%2Fuq0cY8EJzO%2BpmAqKDWVaQhcvGScyayeyrsJ715iZU223L6jSroHpttNrdsrXWN%2B29zv8dFtJ1vQjpKnJnXldguv2xmFYP2hkCVkNwJttm934wZipHrwtkGOKXqSlF60S7uZa0LCZodYf9UX8yvbPsvrg%2FUmuzkogicJffYqIbrna99uYLXLgU5lCPN8ioxgeyUKfbMBrNXViorZtN8%2FozsNASCTWrQJ6W5UFuppTh8JqbSfjB9SuCxmXNzZgfI37cxRVkEPCrREDZXRSICcM%2Bf2cqOLuIiY9EmfXrodRmF09ozA4kJnPUKmsE7O5tk%2BiWK8y88dzWThYlhgEuNXQ28zE9%2F6LQxT%2Bm6wDcuM%2FIEeohBvhrGSBGlmLeS3cptMKD2JJ%2FRmz3e9AhfFonCoq6qYiLI7H%2FgAW%2BAW721FhrTziwgzXJyhwCc8AmIEaHvIBOl1ETLqQucpyEeerKOrtMiaaapg4XrAWMOFRFX9SshNGPdh9fUjnA7rIT%2FwsQtvtqAHlK4mYeiCIJ%2BXBuRB2hAf5HX%2BGIXohkgOmx2nO%2BQLnuoibqrBYZZC%2F2Tw06y6yY0m%2Bp337D2cKvPu9jLiQyqnIiTuaBdAyaoXeutw3Hd%2BO76Y8WCvZsGzsY%2Flw87pntFJ2W%2BWlbSCJqdFms%2Fsp%2BHDJllUS4iqv74iEOP4eP6yYIL3tqutWVNN75Bvkem5hnVIUs8HD6gxHWkAOd62Z04ZWm5XYIefD%2BpQjT2t2D6SsMlAqK6vcRNsrIa5yn45HiAEsPp0jBbAMRTW9R0M%2F8QRjUQGJFSVBTDVhvro4ckOyyjGnc4ZDmfZU4aEqqXNcPLhLFCipj3SuNyAcyuY6JH1BjaQrFICgiHFUQwrTPz6JqIyHWgn3kXTBlCfrVRnnipaS8qjkyFXa43gcGdCShae3x1%2BCWC4YSM2BWvil2bnDrod8ZkjAfoCVsXEY5i6nIQq4Xjl%2FC6PkSVXplOOixPVoVLHEYAMjhAkW86bKzlMm4x29budlRcMY3KWv0%2BGA1Z3%2BDV44FAjnidsl7BHmq%2FClfEKLnTOGrpvbnSqjAkLHdqpMYRgm9zfOnTOy%2B9avOFZRUuHbZ8k9vu7KrG30lnpSudTbx3pTPce5btq7eFPdlm02nM%2FgTbVKFq7Sm6rSXUf0ppig1dIL2bJNID48ajPJlvkq5xn4ymACrAdama3dK77U82B6KQOhsl6Ss%2Bk38pwAGFgE47ZCQ8bsxCrxP2mMdrRhHbmwvOxk17UWMKAJyZhQ7g4Efkb0cIToCKBR8a9ODzUhfiJYYQnwHasXrYGSukCKnNlahXSW48iMQy%2FRD1lwroAoaZF6BbOpBsTHMpsdAcEMdaxAji03Tvhqx5z2SPMBKqAQomEcJlUSPb6%2Bsbd24zuN9VJvnppKDpqaOgEN8kkQo7JSLYvmcgIilvWrZqBumNjn8NQTFZsCYMhCHK0SRnrR%2BcKhtd0zyhBzXM9ILvIyKxd5wQ43WH3P3uq9y7saMgh3Px3fjQfOr3haMuhT7WtBAgssVKNW6m0zAjB0RvwVuQ%2FoDByb70GRDhnv5IMXenUazXbqWCkhtmMYznW6QeGkXbHSQq%2FrNIe6bbfnET0xJmFYHZustqu%2Biaimr7i924E3yTVi%2FCV6sjMdQSBaBi65FmWSzmF6%2F4n3N3C4%2BzLY7K336qdVKcjjMW6AzY7pUOGndfLet8iQKsUbpbPHuDtja2WXLVV3jocX3M%2B%2F4yI5GCc%2FLSxt38F5gmCC9fXbsTRkmoJvD9d40nPF5I1m%2FDgR51HEiXysut9cbk6sJaQ2wR6cl8Hs3iQOSbAQ118y0PqJF5PLCEoPnWM9LWgVkVVF609sczBAC61W3quCeSOBG9Kg5Al2CUecVfeJqxhxFIcn1NB8Lsb8Qrh%2FsLY%2BxD59woVi4GCPGM9hz8dvianGpwTVvn1FuYepuPtIOIxQQFe5%2FPDvBZh6SQt9mkRbUzp%2Fo%2FuR3ece5cXo3vlzDHrgvV5ggJ%2FfdAJhtRjcadaKvcKOytxxP9mmnvy2tg9Ov%2FWspv6zLWebm3vsViN74qR9vvIW8yqn76pqEfYRnT5AjVr%2BjW8GK%2Fhv2cEpSrT9G3aTWCxbKriNQhnKVQHr01dEig9lx7scmm1lQFVWaOkE3Kvv16qAz%2FHoOkeP4vJGvoL6vWsc88cFTAW9jxOP%2FrziUByZoqWUa4jC73P6vOUggyHO7zvRL7SGjpn0X2mwbomVLXG43oRc3dL93YD97PtwfmH2aAfW%2FoXnDGIFFFc5na2jBfw5ileqWUO%2BaOVPwsP0%2Bi08JT6A3lJ0C4YQ5efHSqXBjDd0YPHYs%2FV%2BykIisnT2x20yE1uospQ1nMfQhdP9%2BBJSF3sHTVIeAYIN83NCECQXLbdDkMfy7zDfKpfXVTcenXEEpVFUaaEjxeXBAjk5WNJH4optUsI7vYUDXTksH8kiCQVIeWcirpcCWERmoDWosJCvdbZ4axXhVr%2FexJtRabiPizel3XdNQfuYwEO%2FALZXjsEFkDNFI54lPTP3V7%2BIwbnVSidpfJHNBzQmjwKRGaKTOYkvD7gr7xh4MlUAVbnx%2B%2BB%2BrT0eOfZ0fMdTijeDccd6fy7TrW%2FIFM8XOPX5aBgv6YIyFeOsS0tOX07CQpLp6cSVu7dLBytCZwXJRjQJXVlUPguVOZ8LLIe9fO7gR%2FiUITPTMXkqvtARzu0xTlwmudNEfxeRmAcWSemEq5%2BKpDzueZmUzrM7J5E0TlgkpWHfkEgavz51eShao7%2F77MeEX9y82xI1P16eb%2B%2F0f6%2F0CifznLr0dhn9q72OfmlT0HtHv7QN%2FJzG%2F3qv419advje8S9sHDmn0W%2FtV%2FekCbxfG%2F3SYrFzGv%2F2ftFf9CffO%2F7FvM2pD%2F%2BujmQuRdkfTZ270fjdljzYg1NZlZ1UEGdRZhvSzOVRPjCkcCqzKtiDI%2FkrcsiN9oYkVvlcwDnKQnqQubhfljU4KSEVBLEppny8%2FBzFtAev8pekkR%2FvDWlk0eRPIonKyrzaG39HTDaR%2B5Nu%2BTr8bvo35sQN%2BQD%2FK3em838%3D)
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
