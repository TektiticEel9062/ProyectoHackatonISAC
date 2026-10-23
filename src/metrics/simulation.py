"""
src/metrics/simulation.py
Motor de Simulación Estocástica Monte Carlo (Sección 6.6):
- 10,000 iteraciones por partido basadas en el vector Bernoulli de xG de cada disparo
  (y ajuste contextual OBV de secuencias sin tiro).
- Cálculo de P(Win), P(Draw), P(Loss) y Puntos Esperados:
    E[Points] = 3 * P(Win) + 1 * P(Draw) + 0 * P(Loss)
- Distribución acumulada de puntos de la temporada con Intervalos de Confianza del 95%
  y curva de densidad / histograma para contrastar puntos reales vs puntos esperados.
"""

from typing import Dict, List, Any
from collections import defaultdict
import numpy as np

from src.config import MONTE_CARLO_ITERATIONS, RANDOM_SEED


def run_monte_carlo_simulation(
    events: List[Dict[str, Any]],
    matches_meta: List[Dict[str, Any]],
    n_iterations: int = MONTE_CARLO_ITERATIONS,
    seed: int = RANDOM_SEED,
) -> Dict[str, Any]:
    """
    Ejecuta 10,000 iteraciones Monte Carlo para cada partido del lote y para la temporada completa.
    """
    rng = np.random.default_rng(seed)

    # Agrupar xG de disparos propios y rivales por partido y por possession_id
    # para evitar que rebotes en una misma posesión sumen múltiples goles en una iteración
    shots_for_by_match_poss: Dict[int, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    shots_ag_by_match_poss: Dict[int, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    raw_shots_for_by_match: Dict[int, List[float]] = defaultdict(list)
    raw_shots_ag_by_match: Dict[int, List[float]] = defaultdict(list)
    obv_for_by_match: Dict[int, float] = defaultdict(float)
    obv_ag_by_match: Dict[int, float] = defaultdict(float)

    for ev in events:
        mid = ev["match_id"]
        if ev["type"] == "Shot":
            p_xg = min(0.98, max(0.005, float(ev["shot_xg"])))
            pid = int(ev.get("possession") or 0)
            if ev["is_target_team"]:
                shots_for_by_match_poss[mid][pid].append(p_xg)
                raw_shots_for_by_match[mid].append(p_xg)
            else:
                shots_ag_by_match_poss[mid][pid].append(p_xg)
                raw_shots_ag_by_match[mid].append(p_xg)
        if ev["is_target_team"]:
            obv_for_by_match[mid] += ev.get("obv_for_net", 0.0)
            obv_ag_by_match[mid] += ev.get("obv_against_net", 0.0)

    n_matches = len(matches_meta)
    season_sim_points = np.zeros(n_iterations, dtype=np.int32)
    season_sim_gd = np.zeros(n_iterations, dtype=np.int32)

    match_simulations: List[Dict[str, Any]] = []
    cumulative_real_pts = 0
    cumulative_xpts = 0.0

    for idx, m in enumerate(matches_meta, 1):
        mid = m["match_id"]
        gf_real = int(m["goals_for"])
        ga_real = int(m["goals_against"])
        real_pts = 3 if gf_real > ga_real else (1 if gf_real == ga_real else 0)

        # Probabilidad de gol por posesión k: P(Gol en posesión k) = 1 - prod_{i in k} (1 - xG_i)
        poss_probs_for = [
            1.0 - float(np.prod([1.0 - x for x in xg_list]))
            for xg_list in shots_for_by_match_poss[mid].values()
        ]
        poss_probs_ag = [
            1.0 - float(np.prod([1.0 - x for x in xg_list]))
            for xg_list in shots_ag_by_match_poss[mid].values()
        ]

        p_for = np.array(poss_probs_for, dtype=float)
        p_ag = np.array(poss_probs_ag, dtype=float)

        # Simular matriz Bernoulli por posesión de tiro (n_iterations, n_shooting_possessions)
        if len(p_for) > 0:
            rand_for = rng.random((n_iterations, len(p_for)))
            sim_gf = np.sum(rand_for < p_for, axis=1)
        else:
            sim_gf = np.zeros(n_iterations, dtype=np.int32)

        if len(p_ag) > 0:
            rand_ag = rng.random((n_iterations, len(p_ag)))
            sim_ga = np.sum(rand_ag < p_ag, axis=1)
        else:
            sim_ga = np.zeros(n_iterations, dtype=np.int32)

        wins_mask = sim_gf > sim_ga
        draws_mask = sim_gf == sim_ga
        losses_mask = sim_gf < sim_ga

        p_win = float(np.mean(wins_mask))
        p_draw = float(np.mean(draws_mask))
        p_loss = float(np.mean(losses_mask))

        # Fórmula 6.6: E[Points] = 3*P(Win) + 1*P(Draw) + 0*P(Loss)
        xpoints = 3.0 * p_win + 1.0 * p_draw

        sim_pts_match = np.where(wins_mask, 3, np.where(draws_mask, 1, 0))
        season_sim_points += sim_pts_match
        season_sim_gd += (sim_gf - sim_ga)

        cumulative_real_pts += real_pts
        cumulative_xpts += xpoints

        # Distribución de marcadores más probables en las 10,000 iteraciones
        score_pairs, score_counts = np.unique(
            np.column_stack((sim_gf, sim_ga)), axis=0, return_counts=True
        )
        top_Idx = np.argsort(-score_counts)[:5]
        top_scorelines = [
            {
                "score": f"{int(score_pairs[i, 0])}-{int(score_pairs[i, 1])}",
                "prob_pct": round(float(score_counts[i] / n_iterations * 100.0), 1),
            }
            for i in top_Idx
        ]

        # Histograma de diferencia de goles simulada (-4 a +4) para ese partido
        gd_vals = sim_gf - sim_ga
        gd_hist = []
        for d in range(-4, 5):
            cnt = int(np.sum(gd_vals == d))
            gd_hist.append({
                "goal_diff": d,
                "prob_pct": round((cnt / n_iterations) * 100.0, 2),
            })

        xg_for_val = round(float(np.sum(p_for)), 2)
        xg_ag_val = round(float(np.sum(p_ag)), 2)

        match_simulations.append({
            "match_index": idx,
            "match_id": mid,
            "match_date": m["match_date"],
            "opponent": m["opponent"],
            "venue": m["venue"],
            "real_score": f"{gf_real}-{ga_real}",
            "real_result": m["result"],
            "real_points": real_pts,
            "xg_for": xg_for_val,
            "xg_against": xg_ag_val,
            "shots_for": len(raw_shots_for_by_match[mid]),
            "shots_against": len(raw_shots_ag_by_match[mid]),
            "shooting_possessions_for": len(p_for),
            "shooting_possessions_against": len(p_ag),
            "p_win_pct": round(p_win * 100.0, 1),
            "p_draw_pct": round(p_draw * 100.0, 1),
            "p_loss_pct": round(p_loss * 100.0, 1),
            "xpoints": round(xpoints, 2),
            "points_variance_delta": round(real_pts - xpoints, 2),
            "cumulative_real_points": cumulative_real_pts,
            "cumulative_xpoints": round(cumulative_xpts, 2),
            "top_scorelines": top_scorelines,
            "goal_diff_distribution": gd_hist,
        })

    # Estadísticos globales de la simulación de temporada completa (10,000 temporadas simuladas)
    mean_xpts = float(np.mean(season_sim_points))
    std_xpts = float(np.std(season_sim_points))
    ci_95_low = float(np.percentile(season_sim_points, 2.5))
    ci_95_high = float(np.percentile(season_sim_points, 97.5))
    p_percentile_real = float(np.mean(season_sim_points <= cumulative_real_pts) * 100.0)

    # Construir histograma / campana de Gauss de puntos totales en las 10,000 iteraciones
    min_pt = max(0, int(np.min(season_sim_points)))
    max_pt = int(np.max(season_sim_points))
    pts_values, pts_counts = np.unique(season_sim_points, return_counts=True)
    pts_map = dict(zip(pts_values.tolist(), pts_counts.tolist()))

    points_distribution_curve = []
    for pt in range(min_pt, max_pt + 1):
        c = pts_map.get(pt, 0)
        points_distribution_curve.append({
            "points": pt,
            "iterations": c,
            "prob_pct": round((c / n_iterations) * 100.0, 2),
            "in_ci_95": bool(ci_95_low <= pt <= ci_95_high),
            "is_real_points": (pt == cumulative_real_pts),
            "is_expected_mean": (pt == round(mean_xpts)),
        })

    variance_diff = round(cumulative_real_pts - mean_xpts, 2)
    if abs(variance_diff) <= 3.0:
        verdict = (
            "Convergencia Táctica: Los puntos reales obtenidos reflejan con alta fidelidad la calidad estructural "
            "de las ocasiones generadas y concedidas (dentro de media desviación estándar)."
        )
    elif variance_diff > 3.0:
        verdict = (
            f"Sobrerendimiento de Efectividad (+{variance_diff} pts vs xPoints): La contundencia individual en las áreas "
            "ha potenciado la cosecha de puntos por encima de la media esperada del modelo Monte Carlo."
        )
    else:
        verdict = (
            f"Subrendimiento por Varianza ({variance_diff} pts vs xPoints): El modelo estocástico demuestra que el "
            "funcionamiento colectivo generó méritos tácticos superiores a los puntos finalmente cosechados."
        )

    return {
        "summary": {
            "iterations_per_match": n_iterations,
            "total_matches": n_matches,
            "real_points_total": cumulative_real_pts,
            "expected_points_total": round(mean_xpts, 2),
            "expected_points_std": round(std_xpts, 2),
            "ci_95_low": round(ci_95_low, 1),
            "ci_95_high": round(ci_95_high, 1),
            "real_points_percentile": round(p_percentile_real, 1),
            "points_minus_xpoints": variance_diff,
            "verdict_text": verdict,
        },
        "points_distribution_curve": points_distribution_curve,
        "matches_simulation": match_simulations,
    }
