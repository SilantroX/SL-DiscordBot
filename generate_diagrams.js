const fs = require('fs');
const path = require('path');
const pako = require('C:/Users/silan/AppData/Roaming/npm/node_modules/@drawio/mcp/node_modules/pako');

// 1. Mermaid Source Definition with 5 modules + mass roles + multicanal announcements + persistent storage
const mermaidContent = `flowchart TD
    classDef discord fill:#5865F2,stroke:#4752C4,stroke-width:2px,color:#fff;
    classDef botCore fill:#2C2F33,stroke:#23272A,stroke-width:2px,color:#fff;
    classDef admin fill:#ED4245,stroke:#C03537,stroke-width:2px,color:#fff;
    classDef tickets fill:#57F287,stroke:#3BA55D,stroke-width:2px,color:#000;
    classDef sug fill:#FEE75C,stroke:#D8C34E,stroke-width:2px,color:#000;
    classDef roles fill:#EB459E,stroke:#B22E73,stroke-width:2px,color:#fff;
    classDef news fill:#FFA500,stroke:#CC8400,stroke-width:2px,color:#000;
    classDef db fill:#99AAB5,stroke:#7289DA,stroke-width:2px,color:#000;

    subgraph PlataformaDiscord ["🌐 Discord API & Clientes"]
        User["👤 Usuario / Miembro"]:::discord
        Staff["🛡️ Moderador / Admin"]:::discord
        D_API["⚡ Discord Gateway & REST API"]:::discord
    end

    subgraph CoreBot ["🤖 Core del Bot (Python 3.13 / discord.py v2)"]
        Main["🚀 main.py / Client Setup"]:::botCore
        CogLoader["🧩 Gestor Dinámico de Cogs (31 Comandos)"]:::botCore
        DB[("💾 SQLite Database (aiosqlite)
• guild_settings
• infractions
• tickets
• suggestions & suggestion_votes
• role_menus & role_options
• announcements")]:::db
    end

    subgraph ModuloAdmin ["🛡️ 1. Módulo Administración & Moderación"]
        AdminCogs["Comandos Slash:
/kick, /ban, /unban, /timeout, /clear, /warn, /warnings,
/role_add_all, /role_remove_all"]:::admin
        RoleCheck{"¿Jerarquía & Permisos OK?
(bot.top_role > rol y mod.top_role > rol)"}:::admin
        ModLog["📝 Canal de Logs / Auditoría (#mod-logs)"]:::admin
        WarnSystem["⚠️ Registro de Sanciones en SQLite"]:::admin
    end

    subgraph ModuloTickets ["🎫 2. Módulo de Tickets de Soporte"]
        TicketPanel["📌 Panel Fijo (Persistent View)
Botón: '📩 Crear Ticket'"]:::tickets
        TicketModal["📝 Modal Interactivo (Asunto / Motivo)"]:::tickets
        ChannelCreate["🔒 Crear Canal Privado (ticket-user-id)
Permisos Aislados: Usuario + Staff + Bot"]:::tickets
        TicketControls["🎛️ Controles: Reclamar | Cerrar (2 pasos) | /ticket_add /ticket_remove"]:::tickets
        Transcript["📄 Generador Transcripción HTML Dark Mode"]:::tickets
    end

    subgraph ModuloSugerencias ["💡 3. Módulo de Sugerencias"]
        SugTrigger["Comando /sugerir o Formulario Modal"]:::sug
        SugEmbed["📊 Embed Dinámico en #sugerencias
Botones Voto: 👍 A favor | 👎 En contra"]:::sug
        StaffReview{"Evaluación del Staff (/responder_sugerencia)
(Aprobar / Rechazar / En Desarrollo)"}:::sug
        SugUpdated["🟢 Aprobada / 🔴 Rechazada / 🟡 Desarrollo
(Actualización Embed + Notificación DM)"]:::sug
    end

    subgraph ModuloRoles ["🎭 4. Módulo de Autoroles"]
        RoleSetup["Comando /setup_autoroles en #roles"]:::roles
        RolePanel["📌 Embed Fijo con Botón Persistente
[🎭 Seleccionar Roles]"]:::roles
        RoleSelectMenu["🔽 Menú Desplegable Efímero (StringSelect)
Multi-selección con Emojis y Descripción"]:::roles
        RoleApply["🔄 Sincronización Atómica de Roles"]:::roles
    end

    subgraph ModuloAnuncios ["📢 5. Módulo de Anuncios & Comunicados"]
        NewsCommand["Comando /anuncio (Canal Global)
Comando /anuncio_canal & /comunicado (Canal Específico)"]:::news
        NewsModal["📝 Modal: Título, Cuerpo Markdown, Mención (@everyone/@here), Banner"]:::news
        NewsPreview["👁️ Vista Previa Privada de Seguridad
Botones: [🚀 Publicar Anuncio] [❌ Cancelar]"]:::news
        NewsPublish["🌐 Publicación Oficial en Canal Destino
(#anuncios, #reglas, #bienvenida)"]:::news
    end

    %% Relaciones Gateway
    User -->|Interacciones UI| D_API
    Staff -->|Comandos Slash / Config| D_API
    D_API <--> Main
    Main --> CogLoader
    CogLoader --> AdminCogs
    CogLoader --> TicketPanel
    CogLoader --> SugTrigger
    CogLoader --> RoleSetup
    CogLoader --> NewsCommand
    Main <--> DB

    %% Flujos Administración
    AdminCogs --> RoleCheck
    RoleCheck -->|Permiso Válido| WarnSystem
    WarnSystem --> DB
    WarnSystem --> ModLog
    WarnSystem --> D_API

    %% Flujos Tickets
    TicketPanel -->|Clic Botón| TicketModal
    TicketModal --> ChannelCreate
    ChannelCreate --> TicketControls
    ChannelCreate --> DB
    TicketControls -->|Cerrar Ticket| Transcript
    Transcript --> DB
    Transcript --> ModLog

    %% Flujos Sugerencias
    SugTrigger --> SugEmbed
    SugEmbed --> DB
    SugEmbed --> StaffReview
    StaffReview --> SugUpdated
    SugUpdated --> DB

    %% Flujos Autoroles
    RoleSetup --> RolePanel
    RolePanel -->|Clic en Botón| RoleSelectMenu
    RoleSelectMenu --> RoleApply
    RoleApply --> DB
    RoleApply --> D_API

    %% Flujos Anuncios
    Staff --> NewsCommand
    NewsCommand --> NewsModal
    NewsModal --> NewsPreview
    NewsPreview -->|Confirmar [Publicar]| NewsPublish
    NewsPublish --> DB
    NewsPublish --> ModLog
    NewsPublish --> D_API
`;

// Helper: Compress data using pako deflateRaw and encode base64
function compressData(data) {
  const encoded = encodeURIComponent(data);
  const compressed = pako.deflateRaw(encoded);
  return Buffer.from(compressed).toString('base64');
}

// 2. Build Draw.io URL for Mermaid
const compressedMermaid = compressData(mermaidContent);
const createObj = {
  type: 'mermaid',
  compressed: true,
  data: compressedMermaid,
  version: '12'
};
const drawioMermaidUrl = 'https://app.diagrams.net/?grid=0&pv=0#create=' + encodeURIComponent(JSON.stringify(createObj));

// 3. Native XML Draw.io Format (complete with 5 modules arranged in clean grid)
const drawioXml = `<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" agent="Antigravity AI" version="24.0.0">
  <diagram name="Arquitectura y Flujos Bot Discord v1.2.0" id="bot-discord-arch">
    <mxGraphModel dx="1600" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1800" pageHeight="1400" background="#f8f9fa" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- FILA 1: PLATAFORMA DISCORD Y BOT CORE -->
        <mxCell id="sec_discord" value="🌐 DISCORD ECOSYSTEM (API &amp; CLIENTS)" style="swimlane;whiteSpace=wrap;html=1;fillColor=#5865F2;fontColor=#ffffff;strokeColor=#4752C4;fontStyle=1;startSize=30;rounded=1;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="460" height="260" as="geometry"/>
        </mxCell>
        <mxCell id="usr_member" value="&lt;b&gt;👤 Usuario / Miembro&lt;/b&gt;&lt;br&gt;Interactúa con botones de roles, tickets y sugerencias" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#5865F2;" vertex="1" parent="sec_discord">
          <mxGeometry x="20" y="50" width="200" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="usr_staff" value="&lt;b&gt;🛡️ Staff / Administrador&lt;/b&gt;&lt;br&gt;Comandos Slash, modera, atiende tickets y publica anuncios" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#5865F2;" vertex="1" parent="sec_discord">
          <mxGeometry x="240" y="50" width="200" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="discord_gw" value="&lt;b&gt;⚡ Discord Gateway &amp;amp; REST API&lt;/b&gt;&lt;br&gt;WebSockets (eventos en tiempo real) + HTTP REST (roles, mensajes, canales)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ebedef;strokeColor=#4752C4;fontStyle=0;" vertex="1" parent="sec_discord">
          <mxGeometry x="20" y="150" width="420" height="80" as="geometry"/>
        </mxCell>

        <mxCell id="sec_core" value="🤖 BOT ENGINE (PYTHON 3.13 / DISCORD.PY v2 / RAILWAY &amp; DOCKER)" style="swimlane;whiteSpace=wrap;html=1;fillColor=#2C2F33;fontColor=#ffffff;strokeColor=#23272A;fontStyle=1;startSize=30;rounded=1;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="540" y="40" width="560" height="260" as="geometry"/>
        </mxCell>
        <mxCell id="core_main" value="&lt;b&gt;🚀 main.py&lt;/b&gt;&lt;br&gt;• Bot Class Initialization&lt;br&gt;• Slash Command Tree (31 comandos)&lt;br&gt;• Dynamic Cog Loader" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2C2F33;" vertex="1" parent="sec_core">
          <mxGeometry x="20" y="50" width="240" height="80" as="geometry"/>
        </mxCell>
        <mxCell id="core_config" value="&lt;b&gt;⚙️ Config / Env / Storage&lt;/b&gt;&lt;br&gt;• DISCORD_TOKEN, GUILD_ID&lt;br&gt;• Volumen Persistente (/app/data)&lt;br&gt;• Railway / Docker Compose" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#2C2F33;" vertex="1" parent="sec_core">
          <mxGeometry x="290" y="50" width="240" height="80" as="geometry"/>
        </mxCell>
        <mxCell id="core_db" value="&lt;b&gt;💾 SQLite DB (aiosqlite)&lt;/b&gt;&lt;br&gt;Tablas: guild_settings, infractions, tickets, suggestions, suggestion_votes, role_menus, role_options, announcements" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#99AAB5;strokeColor=#7289DA;fontStyle=0;fontColor=#000000;" vertex="1" parent="sec_core">
          <mxGeometry x="50" y="150" width="470" height="90" as="geometry"/>
        </mxCell>

        <!-- FILA 2: MÓDULOS 1, 2, 3 -->
        <!-- MÓDULO 1: ADMINISTRACIÓN -->
        <mxCell id="sec_admin" value="🛡️ 1. ADMINISTRACIÓN &amp; ROLES MASIVOS (cogs/admin.py)" style="swimlane;whiteSpace=wrap;html=1;fillColor=#ED4245;fontColor=#ffffff;strokeColor=#C03537;fontStyle=1;startSize=30;rounded=1;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="350" width="350" height="320" as="geometry"/>
        </mxCell>
        <mxCell id="adm_cmd" value="&lt;b&gt;Comandos Slash:&lt;/b&gt;&lt;br&gt;/kick, /ban, /unban, /timeout, /clear, /warn, /warnings, /role_add_all, /role_remove_all" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ED4245;" vertex="1" parent="sec_admin">
          <mxGeometry x="15" y="45" width="160" height="75" as="geometry"/>
        </mxCell>
        <mxCell id="adm_check" value="&lt;b&gt;¿Jerarquía OK?&lt;/b&gt;&lt;br&gt;Bot &amp;gt; Rol &amp;gt; Target" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2f2;strokeColor=#ED4245;" vertex="1" parent="sec_admin">
          <mxGeometry x="15" y="135" width="160" height="85" as="geometry"/>
        </mxCell>
        <mxCell id="adm_exec" value="&lt;b&gt;Aplicar Sanción / Rol&lt;/b&gt;&lt;br&gt;REST API + Anti Rate-Limits" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ED4245;" vertex="1" parent="sec_admin">
          <mxGeometry x="195" y="140" width="140" height="75" as="geometry"/>
        </mxCell>
        <mxCell id="adm_log" value="&lt;b&gt;📝 ModLog &amp;amp; DB&lt;/b&gt;&lt;br&gt;Historial en SQLite y Embed a #mod-logs" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ED4245;" vertex="1" parent="sec_admin">
          <mxGeometry x="70" y="245" width="210" height="55" as="geometry"/>
        </mxCell>

        <!-- MÓDULO 2: TICKETS -->
        <mxCell id="sec_tickets" value="🎫 2. TICKETS DE SOPORTE (cogs/tickets.py)" style="swimlane;whiteSpace=wrap;html=1;fillColor=#57F287;fontColor=#000000;strokeColor=#3BA55D;fontStyle=1;startSize=30;rounded=1;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="420" y="350" width="370" height="320" as="geometry"/>
        </mxCell>
        <mxCell id="tkt_panel" value="&lt;b&gt;Panel Fijo Persistente&lt;/b&gt;&lt;br&gt;Botón: [📩 Crear Ticket]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#57F287;" vertex="1" parent="sec_tickets">
          <mxGeometry x="20" y="50" width="150" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="tkt_modal" value="&lt;b&gt;Modal Formulario&lt;/b&gt;&lt;br&gt;Asunto y Descripción" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#57F287;" vertex="1" parent="sec_tickets">
          <mxGeometry x="190" y="50" width="160" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="tkt_channel" value="&lt;b&gt;🔒 Canal Privado #ticket&lt;/b&gt;&lt;br&gt;Permisos: Autor + Staff" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#57F287;" vertex="1" parent="sec_tickets">
          <mxGeometry x="20" y="135" width="150" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="tkt_actions" value="&lt;b&gt;Controles Ticket&lt;/b&gt;&lt;br&gt;[Reclamar] [Cerrar en 2 pasos]&lt;br&gt;/ticket_add, /ticket_remove" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#57F287;" vertex="1" parent="sec_tickets">
          <mxGeometry x="190" y="135" width="160" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="tkt_close" value="&lt;b&gt;Cierre &amp;amp; Transcripción HTML&lt;/b&gt;&lt;br&gt;Exporta HTML estilo Discord a #logs" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#57F287;" vertex="1" parent="sec_tickets">
          <mxGeometry x="75" y="240" width="220" height="55" as="geometry"/>
        </mxCell>

        <!-- MÓDULO 3: SUGERENCIAS -->
        <mxCell id="sec_sug" value="💡 3. SUGERENCIAS COMUNITARIAS (cogs/suggestions.py)" style="swimlane;whiteSpace=wrap;html=1;fillColor=#FEE75C;fontColor=#000000;strokeColor=#D8C34E;fontStyle=1;startSize=30;rounded=1;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="820" y="350" width="360" height="320" as="geometry"/>
        </mxCell>
        <mxCell id="sug_cmd" value="&lt;b&gt;Envío de Sugerencia&lt;/b&gt;&lt;br&gt;/sugerir &amp;lt;contenido&amp;gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FEE75C;" vertex="1" parent="sec_sug">
          <mxGeometry x="20" y="50" width="150" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="sug_embed" value="&lt;b&gt;Embed con Votación&lt;/b&gt;&lt;br&gt;Botones: [👍 Si] [👎 No]&lt;br&gt;Toggle y Switch de voto" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FEE75C;" vertex="1" parent="sec_sug">
          <mxGeometry x="190" y="50" width="150" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="sug_review" value="&lt;b&gt;Revisión Staff&lt;/b&gt;&lt;br&gt;/responder_sugerencia&lt;br&gt;[Aprobar] [Rechazar] [Dev]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FEE75C;" vertex="1" parent="sec_sug">
          <mxGeometry x="20" y="135" width="150" height="75" as="geometry"/>
        </mxCell>
        <mxCell id="sug_state" value="&lt;b&gt;Actualización Embed&lt;/b&gt;&lt;br&gt;Color (🟢/🔴/🟡) + DM usuario" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FEE75C;" vertex="1" parent="sec_sug">
          <mxGeometry x="190" y="135" width="150" height="75" as="geometry"/>
        </mxCell>
        <mxCell id="sug_db" value="&lt;b&gt;Persistencia en DB&lt;/b&gt;&lt;br&gt;Tablas suggestions y suggestion_votes" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FEE75C;" vertex="1" parent="sec_sug">
          <mxGeometry x="85" y="245" width="190" height="55" as="geometry"/>
        </mxCell>

        <!-- FILA 3: MÓDULOS 4 Y 5 -->
        <!-- MÓDULO 4: AUTOROLES -->
        <mxCell id="sec_roles" value="🎭 4. AUTOROLES &amp;amp; MENÚ SELECT (cogs/roles.py)" style="swimlane;whiteSpace=wrap;html=1;fillColor=#EB459E;fontColor=#ffffff;strokeColor=#B22E73;fontStyle=1;startSize=30;rounded=1;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="40" y="700" width="460" height="320" as="geometry"/>
        </mxCell>
        <mxCell id="rol_setup" value="&lt;b&gt;Setup por Staff&lt;/b&gt;&lt;br&gt;/setup_autoroles en #roles" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#EB459E;fontColor=#000000;" vertex="1" parent="sec_roles">
          <mxGeometry x="20" y="50" width="190" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="rol_panel" value="&lt;b&gt;Panel con Botón Fijo&lt;/b&gt;&lt;br&gt;Embed visual: [🎭 Elegir Roles]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#EB459E;fontColor=#000000;" vertex="1" parent="sec_roles">
          <mxGeometry x="240" y="50" width="190" height="60" as="geometry"/>
        </mxCell>
        <mxCell id="rol_menu" value="&lt;b&gt;Menú Desplegable Efímero&lt;/b&gt;&lt;br&gt;discord.ui.Select (StringSelect)&lt;br&gt;Multi-selección y auto-marcación" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#EB459E;fontColor=#000000;" vertex="1" parent="sec_roles">
          <mxGeometry x="20" y="140" width="200" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="rol_apply" value="&lt;b&gt;Sincronización Atómica&lt;/b&gt;&lt;br&gt;member.add_roles() / remove_roles()" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#EB459E;fontColor=#000000;" vertex="1" parent="sec_roles">
          <mxGeometry x="240" y="140" width="200" height="70" as="geometry"/>
        </mxCell>
        <mxCell id="rol_db" value="&lt;b&gt;Persistencia en DB&lt;/b&gt;&lt;br&gt;Tablas role_menus y role_options" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#EB459E;fontColor=#000000;" vertex="1" parent="sec_roles">
          <mxGeometry x="120" y="240" width="220" height="55" as="geometry"/>
        </mxCell>

        <!-- MÓDULO 5: ANUNCIOS MULTICANAL -->
        <mxCell id="sec_news" value="📢 5. ANUNCIOS Y COMUNICADOS MULTICANAL (cogs/announcements.py)" style="swimlane;whiteSpace=wrap;html=1;fillColor=#FFA500;fontColor=#000000;strokeColor=#CC8400;fontStyle=1;startSize=30;rounded=1;arcSize=8;" vertex="1" parent="1">
          <mxGeometry x="540" y="700" width="640" height="320" as="geometry"/>
        </mxCell>
        <mxCell id="news_cmd" value="&lt;b&gt;1. Comandos Slash&lt;/b&gt;&lt;br&gt;/anuncio (Canal General)&lt;br&gt;/anuncio_canal y /comunicado (Destino Personalizado)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FFA500;" vertex="1" parent="sec_news">
          <mxGeometry x="20" y="50" width="180" height="75" as="geometry"/>
        </mxCell>
        <mxCell id="news_modal" value="&lt;b&gt;2. Modal Formulario&lt;/b&gt;&lt;br&gt;• Título&lt;br&gt;• Mensaje Markdown (hasta 3000 chars)&lt;br&gt;• Mención (@everyone / @here / none)&lt;br&gt;• URL Imagen / Banner" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FFA500;" vertex="1" parent="sec_news">
          <mxGeometry x="220" y="50" width="190" height="85" as="geometry"/>
        </mxCell>
        <mxCell id="news_preview" value="&lt;b&gt;3. Vista Previa Privada&lt;/b&gt;&lt;br&gt;Muestra Embed en canal privado con botones:&lt;br&gt;[🚀 Publicar Anuncio] [❌ Cancelar]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FFA500;" vertex="1" parent="sec_news">
          <mxGeometry x="430" y="50" width="190" height="85" as="geometry"/>
        </mxCell>
        <mxCell id="news_publish" value="&lt;b&gt;4. Publicación en Canal Destino&lt;/b&gt;&lt;br&gt;Publica Embed oficial en #anuncios o canales específicos (#reglas, #bienvenida)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FFA500;" vertex="1" parent="sec_news">
          <mxGeometry x="80" y="170" width="280" height="65" as="geometry"/>
        </mxCell>
        <mxCell id="news_log" value="&lt;b&gt;5. Confirmación y Registro&lt;/b&gt;&lt;br&gt;Guarda en DB (announcements) y emite auditoría en #mod-logs" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#FFA500;" vertex="1" parent="sec_news">
          <mxGeometry x="380" y="170" width="240" height="65" as="geometry"/>
        </mxCell>

        <!-- CONECTORES GLOBALES -->
        <mxCell id="c1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=2;strokeColor=#5865F2;" edge="1" source="usr_member" target="discord_gw" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=2;strokeColor=#5865F2;" edge="1" source="usr_staff" target="discord_gw" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c3" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=2;strokeColor=#2C2F33;" edge="1" source="discord_gw" target="core_main" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c4" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=2;strokeColor=#2C2F33;" edge="1" source="core_main" target="core_db" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- CONEXIONES COGS -->
        <mxCell id="c5" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#ED4245;" edge="1" source="core_main" target="adm_cmd" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c6" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#57F287;" edge="1" source="core_main" target="tkt_panel" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c7" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#FEE75C;" edge="1" source="core_main" target="sug_cmd" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c8" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#EB459E;" edge="1" source="core_main" target="rol_setup" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="c9" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#FFA500;" edge="1" source="core_main" target="news_cmd" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- CONECTORES ANUNCIOS INTERNOS -->
        <mxCell id="cn1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#CC8400;" edge="1" source="news_cmd" target="news_modal" parent="sec_news">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="cn2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#CC8400;" edge="1" source="news_modal" target="news_preview" parent="sec_news">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="cn3" value="Publicar" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#CC8400;" edge="1" source="news_preview" target="news_publish" parent="sec_news">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="cn4" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#CC8400;" edge="1" source="news_publish" target="news_log" parent="sec_news">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;

// Direct Draw.io URL using raw GitHub URL (#U) to avoid atob/base64 length and encoding errors
const rawGithubUrl = 'https://raw.githubusercontent.com/SilantroX/SL-DiscordBot/master/bot_arquitectura_y_flujos.drawio';
const drawioEditorUrl = 'https://app.diagrams.net/?grid=1#U' + encodeURIComponent(rawGithubUrl);
const drawioViewerUrl = 'https://viewer.diagrams.net/?highlight=0000ff&edit=_blank&layers=1&nav=1&title=bot_arquitectura_y_flujos.drawio#U' + encodeURIComponent(rawGithubUrl);

// Write files to workspace
const ws = 'c:/Users/silan/OneDrive/Documentos/Bot Discord';
fs.writeFileSync(path.join(ws, 'bot_arquitectura_y_flujos.drawio'), drawioXml, 'utf-8');
fs.writeFileSync(path.join(ws, 'drawio_links.txt'), 
  '=== ENLACES OFICIALES DRAW.IO (SilantroLabs Discord Bot v1.2.0) ===\n\n' +
  '1. EDITOR WEB INTERACTIVO (Draw.io Online vía GitHub Direct):\n' + drawioEditorUrl + '\n\n' +
  '2. VISUALIZADOR INTERACTIVO (Viewer con zoom, navegación y botón editar):\n' + drawioViewerUrl + '\n\n' +
  '3. ARCHIVO LOCAL (Sin conexión):\n' +
  '   - Abrir app.diagrams.net -> "Open Existing Diagram" -> Seleccionar bot_arquitectura_y_flujos.drawio\n' +
  '   - O abrir directamente en Draw.io Desktop / VS Code Draw.io extension.\n',
  'utf-8'
);

console.log('--- GENERACIÓN COMPLETADA CON ÉXITO ---');
console.log('URL Draw.io Editor:', drawioEditorUrl);
console.log('URL Draw.io Viewer:', drawioViewerUrl);

