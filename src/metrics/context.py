"""
src/metrics/context.py
Consistencia y Adaptabilidad Táctica (Sección 6.3):
Cuantificación del cambio en la distribución espacial de pases mediante la
Divergencia de Kullback-Leibler sobre una grilla discretizada de 6x4 zonas.
"""

import math
from typing import Dict, List, Any, Tuple
import numpy as np

from src.config import (
    PITCH_LENGTH,
    PITCH_WIDTH,
    KL_GRID_X_BINS,
    KL_GRID_Y_BINS,
    KL_EPSILON,
)


def compute_spatial_grid_6x4(coords: List[Tuple[float, float]]) -> Tuple[np.ndarray, List[List[float]]]:
    """
    Calcula la distribución de probabilidad discreta P(z) sobre una grilla de 6x4 zonas
    (6 columnas a lo largo de X in [0,120], 4 filas a lo ancho de Y in [0,80]).
    Retorna el arreglo aplanado (24,) normalizado y la matriz 4x6 en porcentajes.
    """
    counts = np.zeros((KL_GRID_Y_BINS, KL_GRID_X_BINS), dtype=float)
    x_step = PITCH_LENGTH / KL_GRID_X_BINS  # 20.0
    y_step = PITCH_WIDTH / KL_GRID_Y_BINS   # 20.0

    for x, y in coords:
        xb = min(KL_GRID_X_BINS - 1, max(0, int(x / x_step)))
        yb = min(KL_GRID_Y_BINS - 1, max(0, int(y / y_step)))
        counts[yb, xb] += 1.0

    total = float(np.sum(counts))
    if total <= 0:
        prob = np.full((KL_GRID_Y_BINS, KL_GRID_X_BINS), 1.0 / (KL_GRID_X_BINS * KL_GRID_Y_BINS))
    else:
        prob = counts / total

    pct_matrix = [[round(float(prob[r, c] * 100.0), 2) for c in range(KL_GRID_X_BINS)] for r in range(KL_GRID_Y_BINS)]
    return prob.flatten(), pct_matrix


def kl_divergence(p: np.ndarray, q: np.ndarray, eps: float = KL_EPSILON) -> Tuple[float, List[List[float]]]:
    """
    Fórmula 6.3:
    D_KL(P || Q) = sum_{z in Zonas} P(z) * log( P(z) / (Q(z) + eps) )
    Retorna el valor escalar D_KL y la matriz 4x6 de contribución firmada por zona.
    """
    p_safe = np.clip(p, eps, 1.0)
    p_safe = p_safe / np.sum(p_safe)
    q_safe = np.clip(q, eps, 1.0)
    q_safe = q_safe / np.sum(q_safe)

    terms = p_safe * np.log(p_safe / (q_safe + eps))
    d_kl = float(max(0.0, np.sum(terms)))

    # Diferencial por celda P(z) - Q(z) en puntos porcentuales para visualización de mutación espacial
    diff_grid = ((p_safe - q_safe) * 100.0).reshape((KL_GRID_Y_BINS, KL_GRID_X_BINS))
    diff_matrix = [[round(float(diff_grid[r, c]), 2) for c in range(KL_GRID_X_BINS)] for r in range(KL_GRID_Y_BINS)]
    return round(d_kl, 4), diff_matrix


def compute_context_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula las distribuciones espaciales 6x4 y la Divergencia de Kullback-Leibler
    para los distintos contextos tácticos:
    - Game State: Winning vs Drawing vs Losing
    - Localía: Home (Local) vs Away (Visitante)
    - Mitad de partido: 1T (Period 1) vs 2T (Period 2)
    """
    pass_coords_by_gs: Dict[str, List[Tuple[float, float]]] = {
        "Winning": [],
        "Drawing": [],
        "Losing": [],
    }
    pass_coords_by_venue: Dict[str, List[Tuple[float, float]]] = {
        "Home": [],
        "Away": [],
    }
    pass_coords_by_period: Dict[str, List[Tuple[float, float]]] = {
        "1H": [],
        "2H": [],
    }
    all_target_passes: List[Tuple[float, float]] = []

    # Métricas de mutación táctica por Game State (altura media de pase, % pases largos, % pases en último tercio)
    gs_stats: Dict[str, Dict[str, float]] = {
        k: {"passes": 0, "sum_x": 0.0, "final_third": 0, "long_passes": 0, "progressive": 0, "obv": 0.0}
        for k in ("Winning", "Drawing", "Losing")
    }

    for ev in events:
        if not ev["is_target_team"] or ev["type"] != "Pass" or not ev["pass_completed"]:
            continue
        tx, ty = ev["target_x"], ev["target_y"]
        if tx is None or ty is None:
            continue

        pt = (tx, ty)
        all_target_passes.append(pt)
        gs = ev["game_state"]
        pass_coords_by_gs[gs].append(pt)

        venue_key = "Home" if ev["is_home"] else "Away"
        pass_coords_by_venue[venue_key].append(pt)

        period_key = "1H" if ev["period"] == 1 else "2H"
        pass_coords_by_period[period_key].append(pt)

        st = gs_stats[gs]
        st["passes"] += 1
        st["sum_x"] += tx
        if tx >= 80.0:
            st["final_third"] += 1
        if (ev.get("pass_length") or 0.0) >= 28.0:
            st["long_passes"] += 1
        if ev.get("is_progressive_pass"):
            st["progressive"] += 1
        st["obv"] += ev.get("obv_total_net", 0.0)

    p_base, grid_base = compute_spatial_grid_6x4(all_target_passes)
    p_win, grid_win = compute_spatial_grid_6x4(pass_coords_by_gs["Winning"])
    p_draw, grid_draw = compute_spatial_grid_6x4(pass_coords_by_gs["Drawing"])
    p_lose, grid_lose = compute_spatial_grid_6x4(pass_coords_by_gs["Losing"])

    p_home, grid_home = compute_spatial_grid_6x4(pass_coords_by_venue["Home"])
    p_away, grid_away = compute_spatial_grid_6x4(pass_coords_by_venue["Away"])

    p_1h, grid_1h = compute_spatial_grid_6x4(pass_coords_by_period["1H"])
    p_2h, grid_2h = compute_spatial_grid_6x4(pass_coords_by_period["2H"])

    kl_win_vs_lose, diff_win_lose = kl_divergence(p_lose, p_win)
    kl_draw_vs_lose, diff_draw_lose = kl_divergence(p_lose, p_draw)
    kl_win_vs_draw, diff_win_draw = kl_divergence(p_win, p_draw)
    kl_home_vs_away, diff_home_away = kl_divergence(p_home, p_away)
    kl_1h_vs_2h, diff_1h_2h = kl_divergence(p_2h, p_1h)

    # Perfil resumido por estado de partido para Capítulo 4 de Scrollytelling y Vista 2
    game_state_profiles = {}
    for gs, st in gs_stats.items():
        n_p = max(1, int(st["passes"]))
        game_state_profiles[gs] = {
            "completed_passes": int(st["passes"]),
            "avg_pass_x": round(st["sum_x"] / n_p, 1),
            "final_third_pct": round((st["final_third"] / n_p) * 100.0, 1),
            "long_pass_pct": round((st["long_passes"] / n_p) * 100.0, 1),
            "progressive_pct": round((st["progressive"] / n_p) * 100.0, 1),
            "obv_net": round(st["obv"], 2),
        }

    # Índice de Consistencia Táctica (0 a 100, mayor cuando D_KL es baja)
    mean_kl = (kl_win_vs_lose + kl_home_vs_away + kl_1h_vs_2h) / 3.0
    consistency_index = round(max(0.0, min(100.0, 100.0 * math.exp(-3.5 * mean_kl))), 1)

    return {
        "kpis": {
            "kl_losing_vs_winning": kl_win_vs_lose,
            "kl_losing_vs_drawing": kl_draw_vs_lose,
            "kl_winning_vs_drawing": kl_win_vs_draw,
            "kl_home_vs_away": kl_home_vs_away,
            "kl_2h_vs_1h": kl_1h_vs_2h,
            "tactical_consistency_index": consistency_index,
        },
        "grids_6x4_pct": {
            "Baseline": grid_base,
            "Winning": grid_win,
            "Drawing": grid_draw,
            "Losing": grid_lose,
            "Home": grid_home,
            "Away": grid_away,
            "1H": grid_1h,
            "2H": grid_2h,
        },
        "kl_diff_grids_6x4": {
            "Losing_minus_Winning": diff_win_lose,
            "Losing_minus_Drawing": diff_draw_lose,
            "Home_minus_Away": diff_home_away,
            "2H_minus_1H": diff_1h_2h,
        },
        "game_state_profiles": game_state_profiles,
    }
