# ⚽ La Historia de un Entrenador a través de los Datos — StatsBomb 360

> **Hackathon ISAC 2026** · Sistema End-to-End de Inteligencia Táctica, Geometría Computacional 360 y Simulación Estocástica  
> **Sujeto de Estudio Autodescubierto:** **Club América** — **DT: André Soares Jardine** (Liga MX 2025/2026 · 37 partidos · 121,369 eventos · 108,144 instantáneas 360)

---

## 📋 1. Resumen Ejecutivo

Este proyecto construye un sistema analítico **end-to-end** que ingesta y normaliza datos de eventos (**StatsBomb v8**) y datos espaciales de cámara (**StatsBomb 360 v2**) para reconstruir, cuantificar y comunicar el modelo de juego de un director técnico a lo largo de toda una temporada.

El sistema ofrece una **estrategia de entrega dual**:
1. **Aplicación Web Interactiva Full-Stack:** Backend en **FastAPI** (`http://127.0.0.1:8000`) + Frontend en **React + Vite + Tailwind CSS** (`http://localhost:5188`).
2. **Reporte Autónomo en Archivo Único (`Reporte_Tactico_StatsBomb360.html`):** Bundle 100% *standalone* compilado con `vite-plugin-singlefile` y datos precalculados inyectados (`window.__PRECALCULATED_DATA__`), ejecutable sin servidor ni conexión a internet en cualquier navegador moderno.

---

## 🏆 2. Alineación con Criterios de Evaluación (100%)

| Criterio | Peso | Implementación en este Proyecto |
| :--- | :---: | :--- |
| **1. Innovación** | **25%** | • **Geometría Computacional 360:** Teselación de Voronoi recortada al campo ($[0,120]\times[0,80]$), Triangulación de Delaunay, Polígono de Compacidad Defensiva (*Convex Hull* en $\text{m}^2$) e **Índice de Ruptura de Líneas 360** por corredor interpolado.<br>• **Teoría de Grafos:** Redes de pases dirigidas $G=(V,E)$ con cálculo de *Betweenness Centrality*, *Degree Centrality*, *PageRank* y densidad estructural.<br>• **Modelado Estocástico Monte Carlo:** $10,000$ iteraciones por partido agrupando rebotes por posesión para estimar distribución de marcadores, varianza e intervalos de confianza del $95\%$ en Puntos Esperados ($xPoints$).<br>• **Teoría de la Información:** Divergencia de Kullback-Leibler ($D_{KL}$) sobre grillas espaciales $6\times 4$ para medir mutación táctica por contexto (*Ganando vs. Perdiendo*, *Local vs. Visitante*, *1T vs. 2T*). |
| **2. Comunicación y Engagement** | **25%** | • **Navegación en 3 Vistas por Perfil:**<br>  1. *Scrollytelling ("La Historia del Entrenador")*: Narrativa guiada en 5 capítulos con pizarra vectorial fija (*sticky pitch*) que se transforma en tiempo real.<br>  2. *Resumen Cuerpo Técnico*: Jerga 100% futbolística sin fricción matemática.<br>  3. *Deep-Dive Analítico*: Trazabilidad formal, axiomas, visualizador geométrico 360 y distribuciones.<br>• **Leyendas Semánticas Dinámicas:** El pie de pizarra actualiza automáticamente su codificación de colores según la capa activa en cancha. |
| **3. Accionabilidad** | **25%** | • **Plan de Partido / Scouting Report:** 3 claves accionables para **potenciar al propio equipo** y 3 claves tácticas para un **rival que busque neutralizarlo**, respaldadas por métricas de OBV, grafos y PPDA.<br>• **Impacto de Sustituciones Ajustado por *Game State*:** Descuenta el sesgo de estado del marcador ($\Delta xG_{\text{ajustado}}$) y aplica *Empirical Bayes Shrinkage* para identificar a los verdaderos revulsivos desde la banca.<br>• **Laboratorio de Balón Parado (ABP 360):** Clasificación de rutinas de córner y medición de sobrecarga en área chica ($X \ge 114, 30 \le Y \le 50$). |
| **4. Metodología y Visualización** | **25%** | • **Framework Analítico Formal:** Definiciones axiomáticas auditables con conteo exacto de instancias detectadas y módulo fuente.<br>• **Sistema de Diseño *Dark Mode Táctico* (`#0B0F19`):** Alto contraste semántico, paleta amigable para daltonismo y micro-anotaciones vectoriales en cancha (`120×80`). |

---

## 🗂️ 3. Arquitectura del Repositorio

```text
├── README.md
├── gemini.md                         # Especificación técnica y directrices del sistema
├── requirements.txt                  # Dependencias de Python (FastAPI, NumPy, SciPy, Scikit-Learn, NetworkX)
├── package.json                      # Scripts globales de desarrollo y compilación
├── Reporte_Tactico_StatsBomb360.html # Entregable autónomo single-file (100% offline)
├── data/
│   ├── raw/                          # JSONs crudos de StatsBomb (ignorados en Git por licencia)
│   └── processed/                    # Manifiesto y payloads JSON estructurados para API y exportación
├── src/
│   ├── config.py                     # Constantes espaciales, umbrales del framework y normalizador de nombres
│   ├── discovery.py                  # Autodescubrimiento agnóstico de equipo, DT, partidos e integridad 360
│   ├── ingestion.py                  # Normalización espacial (X -> 120) y cruce con freeze_frames 360
│   ├── framework.py                  # Segmentador formal: Posesiones, Presión, Transiciones y Game States
│   ├── pipeline.py                   # Orquestador end-to-end (Discovery -> Métricas -> JSONs -> HTML)
│   ├── metrics/
│   │   ├── offensive.py              # xG, OBV, pases progresivos, Field Tilt, Ruptura 360 y Grafos
│   │   ├── defensive.py              # PPDA, altura de bloque, Voronoi, Delaunay, Convex Hull 360 y asfixia 3m
│   │   ├── context.py                # Divergencia de Kullback-Leibler (D_KL) en grillas 6x4
│   │   ├── players.py                # Once estructural 4-2-3-1, PCA + K-Means y sustituciones ajustadas
│   │   ├── set_pieces.py             # Laboratorio ABP ofensivo/defensivo y ocupación espacial 360
│   │   └── simulation.py             # Motor Monte Carlo (10,000 iteraciones/partido por posesión)
│   └── api/
│       ├── main.py                   # Servidor FastAPI (/api/summary, /scrollytelling, /tactical-staff, /deep-dive)
│       └── exporters.py              # Compilador e inyector del archivo único Reporte_Tactico_StatsBomb360.html
└── frontend/
    ├── index.html
    ├── vite.config.js                # Configurado con vite-plugin-singlefile y puerto 5188
    ├── tailwind.config.js            # Tokens de diseño Dark Mode Táctico
    └── src/
        ├── App.jsx                   # Layout global y selector de las 3 vistas
        ├── components/
        │   ├── Header.jsx            # Navegación de vistas, KPIs rápidos y botón de exportación HTML
        │   ├── PitchSVG.jsx          # Cancha vectorial interactiva 120x80 con leyenda semántica dinámica
        │   ├── FreezeFrame360.jsx    # Renderizador SVG de Voronoi, Delaunay, Convex Hull y cono de cámara
        │   └── ExportModal.jsx       # Modal de descarga del reporte autónomo
        ├── views/
        │   ├── ScrollytellingView.jsx # Vista 1: Narrativa interactiva en 5 capítulos con sticky pitch
        │   ├── TacticalStaffView.jsx  # Vista 2: Pizarra de fases, gestión de plantilla, ABP y Plan de Partido
        │   └── DeepDiveView.jsx       # Vista 3: Matriz de axiomas, visor 360, grafos, PCA, KL y Monte Carlo
        └── utils/
            └── dataClient.js         # Cliente dual: consume FastAPI en vivo o window.__PRECALCULATED_DATA__ en HTML
```

---

## 📐 4. Framework Analítico Formal y Formulación Matemática

Todas las coordenadas se estandarizan a la convención **StatsBomb** ($X \in [0, 120]$, $Y \in [0, 80]$), orientando siempre el ataque del equipo objetivo de izquierda a derecha ($X \rightarrow 120$) y convirtiendo áreas geométricas a metros cuadrados ($1\text{ yd}^2 = 0.836127\text{ m}^2$).

1. **Posesión Válida (`src/framework.py`):**
   $$\text{Pases completados} \ge 3 \quad \lor \quad \Delta t \ge 5.0\text{ s}$$
   *(Detectadas: **2,888** posesiones válidas · **78.1** por partido).*

2. **Fase de Presión y Contra-presión Tras Pérdida (`src/framework.py`):**
   $$\text{Acción} \in \{\text{Pressure, Foul, Duel, Interception, Block}\} \quad \land \quad \left(X \ge 80 \;\lor\; \Delta t_{\text{pérdida}} \le 6.0\text{ s}\right)$$
   *(Detectadas: **3,131** acciones · **84.6** por partido).*

3. **Transición Defensiva $\rightarrow$ Ofensiva / Contraataque (`src/framework.py`):**
   Secuencia iniciada con recuperación en campo propio ($X_{\text{origen}} \le 60$) que alcanza zona de finalización ($X \ge 80$) o remate en $< 10.0\text{ s}$ y $\le 4$ pases, extendiendo su polilínea hasta el remate o último toque ofensivo dentro de una ventana máxima de $15.0\text{ s}$.
   *(Detectadas: **337** transiciones rápidas · **9.11** por partido).*

4. **Pase Progresivo e Índice de Ruptura de Líneas 360 (`src/metrics/offensive.py`):**
   $$(120 - X_{\text{fin}}) \le 0.75\,(120 - X_{\text{ini}}) \quad \land \quad X_{\text{fin}} > 60$$
   Un pase con `freeze_frame` 360 rompe líneas si supera en el eje longitudinal $X_{\text{ini}} < X_d < X_{\text{fin}}$ al menos a un defensor rival ubicado dentro del corredor activo de pase ($\text{dist}_{\perp}(d, \overline{AB}) \le 12.5\text{ yd}$).

5. **Compacidad Defensiva Convex Hull 360 (`src/metrics/defensive.py`):**
   $$\text{Área}_{\text{Hull}} = \text{ConvexHull}\left(\{(x_i, y_i) \mid i \in \text{Defensores}_{360}\}\right).\text{volume} \times 0.836127\text{ m}^2/\text{yd}^2$$
   *(Evaluadas: **13,846** instantáneas defensivas 360 · **374.2 frames/partido** · Compacidad media en bloque bajo/medio: **494.6 m²**).*

6. **Divergencia de Kullback-Leibler Espacial (`src/metrics/context.py`):**
   Sobre una grilla discretizada de $6 \times 4 = 24$ zonas espaciales $z$:
   $$D_{KL}(P \parallel Q) = \sum_{z=1}^{24} P(z) \ln\left(\frac{P(z)}{Q(z) + \epsilon}\right)$$

7. **Simulación Estocástica Monte Carlo con Agrupación por Posesión (`src/metrics/simulation.py`):**
   Para impedir que rebotes en una misma jugada sumen múltiples goles en una iteración, la probabilidad de gol de cada posesión con disparo $k$ se modela como:
   $$P(\text{Gol en posesión } k) = 1 - \prod_{i \in k} \left(1 - \text{xG}_i\right)$$
   Sobre $10,000$ iteraciones por partido se calcula $\mathbb{E}[\text{Points}] = 3\,P(\text{Win}) + 1\,P(\text{Draw})$.

---

## 🚀 5. Instalación y Ejecución

### Requisitos Previos
- **Python** `3.10+`
- **Node.js** `18+` y `npm`

### Paso 1: Configurar Entorno Python
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

*(Opcional)* Si deseas volver a descargar los datos crudos desde la API de StatsBomb, crea un archivo `.env` en la raíz:
```ini
STATSBOMB_USER=tu_usuario
STATSBOMB_PASSWORD=tu_password
```

### Paso 2: Ejecutar el Pipeline Analítico Completo
Si deseas recalcular todas las métricas desde `data/raw/`, regenerar los JSONs en `data/processed/` y compilar `Reporte_Tactico_StatsBomb360.html`:
```powershell
.\.venv\Scripts\python.exe -m src.pipeline
```

### Paso 3: Levantar los Servidores (Modo Desarrollo / Demo en Vivo)

**Terminal 1 — Backend FastAPI (`http://127.0.0.1:8000`):**
```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend React + Vite (`http://localhost:5188`):**
```powershell
cd frontend
npm install
npm run dev
```

### Paso 4: Uso del Reporte Autónomo Sin Servidor
Abre directamente el archivo [`Reporte_Tactico_StatsBomb360.html`](./Reporte_Tactico_StatsBomb360.html) haciendo doble clic en cualquier navegador. Contiene todas las vistas, gráficos, filtros e instantáneas 360 embebidas para funcionar **100% offline**.
