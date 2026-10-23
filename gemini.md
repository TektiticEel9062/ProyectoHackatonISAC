# GEMINI.md - Especificación Técnica y Directriz para Antigravity

## 1. Visión General del Proyecto
- **Proyecto:** "La Historia de un Entrenador a través de los Datos"
- **Insumo Principal:** Datos de eventos de StatsBomb y datos espaciales StatsBomb 360 correspondientes a múltiples partidos de un mismo equipo bajo un mismo director técnico.
- **Objetivo Central:** Construir un sistema end-to-end que procese los datos de eventos y 360, modele el comportamiento táctico en fase ofensiva, defensiva, transiciones, balón parado y uso de plantilla, y lo comunique mediante una aplicación web en **React** con backend en **FastAPI**.
- **Entregable Dual:**
  1. Aplicación web interactiva completa (FastAPI + React).
  2. Reporte exportable autónomo en un único archivo `.html` auto-contenido (bundle que incluye datos embebidos e interactividad completa sin dependencias externas ni servidor activo).

---

## 2. Alineación con Criterios de Evaluación (100%)

| Criterio | Peso | Implementación en este Proyecto |
| :--- | :--- | :--- |
| **Innovación** | 25% | - Geometría computacional sobre `freeze_frames` 360 (Teselación de Voronoi, Triangulación de Delaunay y Convex Hull).<br>- Teoría de grafos para redes de pases dinámicas.<br>- Modelado estocástico Monte Carlo (10,000 iteraciones) para evaluar varianza y puntos esperados ($xPoints$).<br>- Cuantificación de consistencia táctica mediante Divergencia de Kullback-Leibler. |
| **Comunicación y Engagement** | 25% | - Estructura de navegación en 3 vistas diferenciadas por perfil de usuario.<br>- Vista principal de **Scrollytelling** con narrativa guiada y pizarra SVG interactiva fija (*sticky pitch*).<br>- Jerga adaptada: separación estricta entre lenguaje futbolístico y formulación matemática. |
| **Accionabilidad** | 25% | - Módulo de "Plan de Partido / Scouting Report" con KPIs orientados a decisiones de banquillo.<br>- Análisis de impacto cuantitativo de sustituciones y ajustes por contexto de partido ($Game\ State$, localía, minuto).<br>- Diagnóstico de vulnerabilidad y eficacia en jugadas a balón parado (ABP). |
| **Metodología y Visualización** | 25% | - **Framework Analítico Formal** documentado con trazabilidad matemática de cada objeto.<br>- Diseño UI Dark Mode Táctico (`#0B0F19`) con alto contraste semántico y visualizaciones autoexplicativas sin sesgo.<br>- Paleta daltónico-amigable y micro-anotaciones en cancha. |

---

## 3. Arquitectura del Repositorio

```text
├── GEMINI.md
├── requirements.txt
├── package.json
├── data/
│   ├── raw/                      # Ingesta de JSONs de StatsBomb (events, 360, lineups, matches)
│   └── processed/                # Archivos Parquet intermedios y JSONs finales estructurados
├── src/
│   ├── config.py                 # Constantes globales, coordenadas y parámetros del framework
│   ├── discovery.py              # Autodescubrimiento del equipo objetivo, entrenador y schema
│   ├── ingestion.py              # Parser y normalizador de eventos + 360 freeze frames
│   ├── framework.py              # Segmentador de objetos: Posesiones, Secuencias, Presión, Transiciones
│   ├── metrics/
│   │   ├── offensive.py          # xG, OBV, pases progresivos, Field Tilt, Ruptura de líneas 360
│   │   ├── defensive.py          # PPDA, altura de bloque, Convex Hull 360, densidad de presión
│   │   ├── context.py            # Variabilidad por marcador, localía, tiempo (Divergencia KL)
│   │   ├── players.py            # Clustering de roles tácticos (PCA/K-Means), impacto sustituciones
│   │   ├── set_pieces.py         # ABP ofensivo y defensivo con ocupación espacial 360
│   │   └── simulation.py         # Simulación Monte Carlo de partidos (xG/OBV a xPoints)
│   └── api/
│       ├── main.py               # Servidor FastAPI
│       └── exporters.py          # Generador del archivo HTML único interactivo
└── frontend/
    ├── index.html
    ├── vite.config.js            # Configurado con vite-plugin-singlefile
    ├── tailwind.config.js        # Tokens de diseño Dark Mode Táctico
    └── src/
        ├── App.jsx               # Enrutador de pestañas y layout global
        ├── components/
        │   ├── Header.jsx        # Barra superior con selector de vistas y botón de exportar HTML
        │   ├── PitchSVG.jsx      # Cancha vectorial interactiva (coordenadas StatsBomb 120x80)
        │   ├── FreezeFrame360.jsx# Renderizador de Voronoi y Convex Hull en eventos 360
        │   └── ExportModal.jsx   # Feedback de compilación y descarga de archivo único
        ├── views/
        │   ├── ScrollytellingView.jsx  # Vista 1: Narrativa interactiva guiada
        │   ├── TacticalStaffView.jsx   # Vista 2: Resumen para Cuerpo Técnico
        │   └── DeepDiveView.jsx        # Vista 3: Deep-Dive Analítico y Matemático
        └── utils/
            └── dataClient.js     # Cliente dual: API FastAPI en desarrollo / Inlined JSON en standalone
```

---

## 4. Módulo de Autodescubrimiento (`src/discovery.py`)

Antigravity debe implementar una rutina de inspección agnóstica que opere sobre cualquier estructura de carpetas dentro de `data/raw/`:

1. **Detección de Archivos:**
   - Buscar recursivamente archivos `.json`, `.parquet` o `.csv` asociados a `matches`, `events`, `lineups` y `three-sixty` / `360`.
2. **Identificación de Sujetos de Estudio:**
   - Contabilizar la frecuencia de aparición de cada equipo en los partidos disponibles.
   - Identificar automáticamente el **`target_team`** como el equipo presente en el 100% de los partidos del lote.
   - Extraer el nombre del **`target_coach`** desde los metadatos de partidos o alineaciones.
3. **Auditoría de Columnas y Capacidades:**
   - Verificar la presencia de métricas avanzadas nativas (`obv_total_net`, `shot_statsbomb_xg`). Si no existen, activar métodos analíticos basados en control espacial.
   - Validar la integridad del enlace entre `events.id` y `three_sixty.event_uuid`.
4. **Salida Estructurada:**
   - Generar `data/processed/metadata_manifest.json` con el resumen del equipo, partidos analizados, rivales, minutaje total y disponibilidad de datos 360.

---

## 5. Framework Analítico Formal (`src/config.py` & `src/framework.py`)

Para garantizar la coherencia metodológica interna, todas las funciones deben derivarse estrictamente de estos supuestos:

### 5.1. Normalización Espacial
- Todas las coordenadas se normalizan al estándar StatsBomb: $X \in [0, 120]$, $Y \in [0, 80]$.
- La dirección de ataque del `target_team` se estandariza de izquierda a derecha ($X \rightarrow 120$).

### 5.2. Definición Formal de Objetos
1. **Posesión:** Cadena de eventos consecutivos controlados por un mismo equipo. Se considera posesión válida si cumple:
   $$\text{Pases completados} \ge 3 \quad \lor \quad \Delta t \ge 5.0\text{ segundos}$$
2. **Fase de Presión:** Acciones defensivas (*Pressure*, *Foul Committed*, *Duel*, *Interception*, *Block*) ejecutadas:
   - En tercio ofensivo ($X \ge 80$).
   - O dentro de los primeros $6$ segundos posteriores a una pérdida de balón (contra-presión inmediata).
3. **Transición Defensiva a Ofensiva (Contraataque):** Secuencia que inicia con una recuperación en campo propio ($X \le 60$) y culmina en un remate o ingreso a zona de finalización ($X \ge 80$) en menos de $10$ segundos y con $\le 4$ pases.
4. **Estados de Partido ($Game\ State$):**
   - Ganando ($\Delta G > 0$), Empatando ($\Delta G = 0$), Perdiendo ($\Delta G < 0$).
   - Segmentación temporal por intervalos de $15$ minutos ($[0-15], [15-30], [30-45], [45-60], [60-75], [75+]$).

### 5.3. Alcance y Límites Explícitos
- Los datos de StatsBomb 360 se interpretan como **instantáneas discretas contextuales** (`freeze_frame`), circunscritas al cono de visión de la cámara en el instante del evento. No se infiere posicionamiento cinemático de jugadores fuera de cuadro.

---

## 6. Motor Métrico y Matemático (`src/metrics/`)

### 6.1. Fase Ofensiva y Progresión (`offensive.py`)
- **Pases Progresivos:** Pases completados hacia campo rival que avanzan el balón al menos un 25% más cerca de la línea de meta rival respecto a su punto de origen.
- **Field Tilt:** Porcentaje de pases completados en el tercio final ($X \ge 80$) respecto al total del partido:
  $$\text{Field Tilt} = \frac{\text{Pases exitosos propios en } X \ge 80}{\text{Pases exitosos totales de ambos equipos en } X \ge 80} \times 100$$
- **Índice de Ruptura de Líneas 360 (Innovación):** Para cada pase con `freeze_frame`, se cuenta la cantidad de defensores rivales superados en el eje $X$ entre el pasador y el receptor que se encontraban en el cono defensivo activo.

### 6.2. Fase Defensiva y Geometría 360 (`defensive.py`)
- **PPDA (Passes Allowed per Defensive Action):** Pases del rival permitidos en su propia mitad y tercio medio ($X \le 80$ para el rival) divididos por las acciones defensivas propias en dicha zona.
- **Compacidad Defensiva (Convex Hull 360):** Cálculo del área superficial ($m^2$) del polígono convexo delimitado por los defensores en momentos de bloque bajo y medio:
  $$\text{Área Convex Hull} = \text{ConvexHull}(\{(x_i, y_i) \mid i \in \text{Defensores en freeze frame}\}).\text{volume}$$
- **Asfixia Espacial en Presión:** Cantidad media de rivales en un radio de $3$ metros sobre el portador del balón rival durante eventos defensivos.

### 6.3. Consistencia y Adaptabilidad Táctica (`context.py`)
- **Divergencia de Identidad Táctica:** Cuantificar el cambio en la distribución espacial de pases ($P$) según el contexto ($Q$: ganando vs. perdiendo; local vs. visitante) mediante la Divergencia de Kullback-Leibler sobre una grilla espacial discretizada de $6 \times 4$ zonas:
  $$D_{KL}(P \parallel Q) = \sum_{z \in \text{Zonas}} P(z) \log\left(\frac{P(z)}{Q(z) + \epsilon}\right)$$

### 6.4. Uso de Jugadores y Dinámica de Plantilla (`players.py`)
- **Clustering de Roles (PCA + K-Means):** Clasificación no supervisada de jugadores basada en vectores de frecuencia de eventos normalizados por 90 minutos (conducciones progresivas, duelos aéreos, pases filtrados, presiones, recuperaciones).
- **Impacto de Sustituciones:** Medición del diferencial de xG generado vs. concedido por minuto ($\Delta xG_{diff}/min$) y cambio en posesión antes y después del minuto de cada cambio.

### 6.5. Balón Parado - ABP (`set_pieces.py`)
- Segmentación de córners y tiros libres en:
  - Tipo de entrega: Primer palo, segundo palo, frontal, jugada corta.
  - Sobrecarga espacial 360: Conteo de atacantes vs. defensores en el área chica ($X \ge 114, 30 \le Y \le 50$) al momento del saque.

### 6.6. Motor de Simulación Monte Carlo (`simulation.py`)
- Simulación de $10,000$ iteraciones por partido a partir del valor de $xG$ de cada disparo y probabilidades de gol esperadas por secuencia.
- Cálculo de la distribución de probabilidad de resultados ($Victoria, Empate, Derrota$) y cálculo de Puntos Esperados ($xPoints$):
  $$\mathbb{E}[\text{Points}] = 3 \cdot P(\text{Win}) + 1 \cdot P(\text{Draw}) + 0 \cdot P(\text{Loss})$$
- Demostración de varianza: ¿los resultados obtenidos reflejan la calidad táctica de las oportunidades creadas/concedidas o están sesgados por efectividad puntual?

---

## 7. Diseño del Frontend en React

### 7.1. Sistema de Diseño (Dark Mode Táctico)
- **Fondo General (`bg`):** `#0B0F19` (Obsidian Pitch)
- **Superficies / Paneles:** `#111827` con bordes `#1F2937`
- **Tipografía:** Sans-serif moderna y monoespaciada para métricas numéricas (`Inter` / `JetBrains Mono`).
- **Código de Color Semántico:**
  - **Fase Ofensiva / Progresión:** Neón Cian (`#00F5D4`)
  - **Fase Defensiva / Presión:** Ámbar Táctico (`#F59E0B`)
  - **Vulnerabilidad / Riesgo Rival:** Carmesí Neón (`#F43F5E`)
  - **Métricas Avanzadas 360 / Algorítmicas:** Violeta Eléctrico (`#8B5CF6`)
  - **Líneas de Cancha SVG:** Sutiles en `#334155`

### 7.2. Especificación de las Tres Vistas

#### Vista 1: Página Principal — Scrollytelling ("La Historia del Entrenador")
- **Layout:** Pantalla dividida. Panel izquierdo de lectura con tarjetas deslizantes; panel derecho fijo (*sticky*) con la cancha SVG dinámica interactiva.
- **Flujo de Capítulos:**
  1. *El ADN Inicial:* Presentación del entrenador, alineación táctica promedio y mapa de densidad base.
  2. *Construcción y Progresión:* La cancha anima los canales preferidos de salida de balón y resalta una jugada 360 de ruptura de líneas.
  3. *El Bloque sin Balón:* Transformación visual de la cancha hacia la fase defensiva; visualización del Convex Hull y la altura de la línea de presión.
  4. *Ajustes de Emergencia:* La cancha muestra la mutación táctica cuando el equipo se encuentra abajo en el marcador.
  5. *El Veredicto de la Simulación:* Gráfico interactivo que contrasta los puntos reales acumulados con la campana de Gauss de las simulaciones Monte Carlo.

#### Vista 2: Resumen para Cuerpo Técnico (Enfoque Cancha)
- **Lenguaje:** Estrictamente futbolístico, comprensible para entrenadores y directores deportivos.
- **Pizarra Táctica de Fases:**
  - Salida de fondo (corta vs. larga), carriles de progresión y zonas de remate.
  - Comportamiento tras pérdida (reacción inmediata vs. repliegue ordenado).
- **Gestión de Plantilla:**
  - Mapa de roles de jugadores en cancha (ej. Central Corrector, Lateral Largo, Interior Organizador).
  - Efectividad de las sustituciones: ¿Quién entra como revulsivo y qué impacto real tiene en el partido?
- **Laboratorio de Balón Parado (ABP):**
  - Gráfico de rutinas ofensivas de tiros de esquina y zonas de vulnerabilidad en córners concedidos.
- **Plan de Partido (Tarjetas Accionables):**
  - 3 claves para potenciar a este equipo.
  - 3 claves tácticas para un rival que busque neutralizarlo.

#### Vista 3: Deep-Dive Analítico (Enfoque Matemático / Data Science)
- **Documentación del Framework:** Matriz interactiva de definiciones lógicas y umbrales aplicados.
- **Visualizador Geométrico 360:**
  - Selector de eventos 360 con renderizado en tiempo real de Diagramas de Voronoi y polígonos de compacidad.
- **Teoría de Grafos en Redes de Pases:**
  - Métricas de intermediación (*Betweenness Centrality*) y densidad de red para cuantificar dependencia de futbolistas específicos.
- **Análisis de Distribuciones:**
  - Matrices de calor de la Divergencia de Kullback-Leibler por contexto de partido.
  - Histograma detallado de la simulación Monte Carlo de $10,000$ iteraciones por juego con intervalos de confianza del 95%.

---

## 8. Estrategia de Entrega Dual y Exportador Autónomo

El sistema debe operar de dos formas sin necesidad de escribir código duplicado:

1. **Modo Full-Stack (Desarrollo y Demo en Vivo):**
   - Backend en FastAPI sirviendo JSONs procesados en `/api/...`.
   - Frontend en React consumiendo los endpoints de manera reactiva.
2. **Modo Exportación HTML Autónomo (Botón en Header):**
   - El header de la aplicación en React contendrá un botón principal: **"Exportar Reporte HTML Único"**.
   - Al presionarlo, el backend toma el build compilado por Vite (usando `vite-plugin-singlefile`), inyecta los datos calculados en un script `window.__PRECALCULATED_DATA__` y emite un único archivo `Reporte_Tactico_StatsBomb360.html`.
   - Dicho archivo funcionará de manera 100% offline en cualquier navegador moderno, conservando toda la interactividad, tabs, gráficos y canchas SVG.

---

## 9. Instrucciones de Implementación para Antigravity

Al ejecutar este proyecto, Antigravity debe proceder en el siguiente orden secuencial:

1. **Paso 1 - Exploración y Pipeline:**
   - Crear `src/discovery.py` y correrlo sobre `data/raw/` para generar `metadata_manifest.json`.
   - Implementar `src/framework.py` y `src/metrics/` para generar la base procesada de eventos, métricas 360 y simulaciones.
2. **Paso 2 - Backend FastAPI:**
   - Crear los endpoints en `src/api/main.py` para servir:
     - `/api/summary` (metadatos del entrenador, partidos y KPIs globales).
     - `/api/scrollytelling` (capítulos secuenciales con estados de cancha).
     - `/api/tactical-staff` (datos tácticos, fases, roles y ABP).
     - `/api/deep-dive` (métricas matemáticas, Voronoi 360, grafos y Monte Carlo).
     - `/api/export-html` (generación y descarga del archivo único compilado).
3. **Paso 3 - Frontend React:**
   - Inicializar el proyecto con Vite y Tailwind CSS.
   - Configurar la paleta de colores Dark Mode Táctico en `tailwind.config.js`.
   - Construir los componentes modulares (`PitchSVG`, `FreezeFrame360`, `Header`) y las 3 vistas.
4. **Paso 4 - Validación de Coherencia:**
   - Verificar que ninguna métrica de la app contradiga los axiomas del Framework Analítico.
   - Confirmar que la exportación a archivo único `.html` abra de forma autónoma sin conexión a servidor.