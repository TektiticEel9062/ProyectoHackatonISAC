"""
src/config.py
Constantes globales, coordenadas y parámetros del Framework Analítico Formal.
"""

from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

# Dimensiones estándar StatsBomb
PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0

# Conversión aproximada de unidades StatsBomb (yardas) a metros para cálculos de área / distancia
YARD_TO_METER = 0.9144
AREA_YARD2_TO_M2 = YARD_TO_METER ** 2  # ~0.836127 m^2 por yarda^2

# 5.2 Definición Formal de Objetos
POSSESSION_MIN_PASSES = 3
POSSESSION_MIN_DURATION_SEC = 5.0

HIGH_PRESS_X_THRESHOLD = 80.0
COUNTERPRESS_WINDOW_SEC = 6.0

DEFENSIVE_EVENT_TYPES = {
    "Pressure",
    "Foul Committed",
    "Duel",
    "Interception",
    "Block",
    "Ball Recovery",
}

PRESSURE_ACTION_TYPES = {
    "Pressure",
    "Foul Committed",
    "Duel",
    "Interception",
    "Block",
}

# Transición Defensiva -> Ofensiva (Contraataque)
TRANSITION_ORIGIN_MAX_X = 60.0
TRANSITION_END_MIN_X = 80.0
TRANSITION_MAX_DURATION_SEC = 10.0
TRANSITION_MAX_PASSES = 4

# Segmentación Temporal (Intervalos de 15 min)
TIME_BINS = [
    (0, 15, "0-15"),
    (15, 30, "15-30"),
    (30, 45, "30-45"),
    (45, 60, "45-60"),
    (60, 75, "60-75"),
    (75, 130, "75+"),
]

# 6.1 Fase Ofensiva
PROGRESSIVE_PASS_FRACTION = 0.25  # 25% más cerca de la línea de meta rival (X=120, Y=40)
FINAL_THIRD_X = 80.0

# 6.2 Fase Defensiva
PPDA_MAX_RIVAL_X = 80.0  # X <= 80 para el rival equivalen a X >= 40 en coordenadas propias
PRESSURE_SUFFOCATION_RADIUS_M = 3.0
PRESSURE_SUFFOCATION_RADIUS_SB = PRESSURE_SUFFOCATION_RADIUS_M / YARD_TO_METER  # ~3.28 yardas

# 6.3 Consistencia y Adaptabilidad Táctica (Grilla 6x4 para Divergencia KL)
KL_GRID_X_BINS = 6
KL_GRID_Y_BINS = 4
KL_EPSILON = 1e-6

# 6.5 Balón Parado (ABP) - Área chica
SIX_YARD_BOX_MIN_X = 114.0
SIX_YARD_BOX_MIN_Y = 30.0
SIX_YARD_BOX_MAX_Y = 50.0

# 6.6 Simulación Monte Carlo
MONTE_CARLO_ITERATIONS = 10000
RANDOM_SEED = 42

# 7.1 Paleta de Colores (Dark Mode Táctico)
THEME_COLORS = {
    "bg": "#0B0F19",
    "surface": "#111827",
    "border": "#1F2937",
    "offensive": "#00F5D4",
    "defensive": "#F59E0B",
    "risk": "#F43F5E",
    "advanced360": "#8B5CF6",
    "pitchLines": "#334155",
}

# Diccionario de nombres deportivos conocidos (evita extraer el apellido materno en nombres hispanos)
PLAYER_SHORT_NAMES = {
    "Luis Ángel Malagón Velázquez": "Malagón",
    "Rodolfo Damian Cota Robles": "R. Cota",
    "Sebastián Enzo Cáceres Ramos": "S. Cáceres",
    "Israel Reyes Romero": "I. Reyes",
    "Ramón Juárez Del Castillo": "R. Juárez",
    "Igor Lichnovsky Osorio": "Lichnovsky",
    "Miguel Ángel Vázquez García": "M. Vázquez",
    "Néstor Alejandro Araujo Razo": "N. Araujo",
    "Cristian Alexis Borja González": "C. Borja",
    "Cristian Yonathan Calderón Del Real": "C. Calderón",
    "Kevin Nahin Álvarez Campos": "K. Álvarez",
    "Dagoberto Espinoza Acosta": "D. Espinoza",
    "Aaron Mejía Montoya": "A. Mejía",
    "Álvaro Fidalgo Fernández": "Fidalgo",
    "Jonathan dos Santos Ramírez": "J. dos Santos",
    "Erick Daniel Sánchez Ocegueda": "E. Sánchez",
    "Rodrigo Dourado Cunha": "R. Dourado",
    "Alan Jhosué Cervantes Martín del Campo": "A. Cervantes",
    "Richard Rafael Sánchez Guerrero": "R. Sánchez",
    "Raphael Cavalcante Veiga": "R. Veiga",
    "Vinícius Moreira de Lima": "V. Lima",
    "Diego Alfonso Valdés Contreras": "D. Valdés",
    "Alejandro Zendejas Saavedra": "Zendejas",
    "Paul Brian Rodríguez Bravo": "B. Rodríguez",
    "Allan Irénée Saint-Maximin": "Saint-Maximin",
    "Isaías Violante Romero": "I. Violante",
    "Alexis Hazael Gutiérrez Torres": "A. Gutiérrez",
    "Javairô Joreno Faustino Dilrosun": "Dilrosun",
    "Henry Josué Martín Mex": "H. Martín",
    "Rodrigo Sebastián Aguirre Soto": "R. Aguirre",
    "José Raúl Zúñiga Murillo": "R. Zúñiga",
    "Víctor Alejandro Dávila Zavala": "V. Dávila",
    "Patricio Salas": "P. Salas",
    "Illian Gerardo Hernández Vargas": "I. Hernández",
}

PLAYER_CLEAN_NAMES = {
    "Luis Ángel Malagón Velázquez": "Luis Ángel Malagón",
    "Rodolfo Damian Cota Robles": "Rodolfo Cota",
    "Sebastián Enzo Cáceres Ramos": "Sebastián Cáceres",
    "Israel Reyes Romero": "Israel Reyes",
    "Ramón Juárez Del Castillo": "Ramón Juárez",
    "Igor Lichnovsky Osorio": "Igor Lichnovsky",
    "Miguel Ángel Vázquez García": "Miguel Vázquez",
    "Néstor Alejandro Araujo Razo": "Néstor Araujo",
    "Cristian Alexis Borja González": "Cristian Borja",
    "Cristian Yonathan Calderón Del Real": "Cristian Calderón",
    "Kevin Nahin Álvarez Campos": "Kevin Álvarez",
    "Dagoberto Espinoza Acosta": "Dagoberto Espinoza",
    "Aaron Mejía Montoya": "Aaron Mejía",
    "Álvaro Fidalgo Fernández": "Álvaro Fidalgo",
    "Jonathan dos Santos Ramírez": "Jonathan dos Santos",
    "Erick Daniel Sánchez Ocegueda": "Erick Sánchez",
    "Rodrigo Dourado Cunha": "Rodrigo Dourado",
    "Alan Jhosué Cervantes Martín del Campo": "Alan Cervantes",
    "Richard Rafael Sánchez Guerrero": "Richard Sánchez",
    "Raphael Cavalcante Veiga": "Raphael Veiga",
    "Vinícius Moreira de Lima": "Vinícius Lima",
    "Diego Alfonso Valdés Contreras": "Diego Valdés",
    "Alejandro Zendejas Saavedra": "Alejandro Zendejas",
    "Paul Brian Rodríguez Bravo": "Brian Rodríguez",
    "Allan Irénée Saint-Maximin": "Allan Saint-Maximin",
    "Isaías Violante Romero": "Isaías Violante",
    "Alexis Hazael Gutiérrez Torres": "Alexis Gutiérrez",
    "Javairô Joreno Faustino Dilrosun": "Javairô Dilrosun",
    "Henry Josué Martín Mex": "Henry Martín",
    "Rodrigo Sebastián Aguirre Soto": "Rodrigo Aguirre",
    "José Raúl Zúñiga Murillo": "Raúl Zúñiga",
    "Víctor Alejandro Dávila Zavala": "Víctor Dávila",
    "Patricio Salas": "Patricio Salas",
    "Illian Gerardo Hernández Vargas": "Illian Hernández",
}


def get_player_short_name(full_name: str) -> str:
    """Retorna el nombre corto deportivo para pizarras (evitando el apellido materno)."""
    if not full_name:
        return "Jugador"
    if full_name in PLAYER_SHORT_NAMES:
        return PLAYER_SHORT_NAMES[full_name]
    parts = full_name.strip().split()
    if len(parts) <= 2:
        return parts[-1]
    # En nombres hispanos de 3 o 4 palabras (Nombre [SegundoNombre] ApellidoPaterno ApellidoMaterno),
    # el apellido deportivo suele ser el penúltimo token (ej. "Erick Daniel Sánchez Ocegueda" -> "E. Sánchez")
    if parts[-2].lower() in ("del", "de", "da", "dos", "van", "von"):
        return f"{parts[0][0]}. {' '.join(parts[-2:])}"
    return f"{parts[0][0]}. {parts[-2]}"


def get_player_clean_name(full_name: str) -> str:
    """Retorna el nombre deportivo completo (Nombre + Primer Apellido)."""
    if not full_name:
        return "Jugador"
    if full_name in PLAYER_CLEAN_NAMES:
        return PLAYER_CLEAN_NAMES[full_name]
    parts = full_name.strip().split()
    if len(parts) <= 2:
        return full_name
    return f"{parts[0]} {parts[-2]}"

