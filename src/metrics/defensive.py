"""
src/metrics/defensive.py
Motor Métrico de Fase Defensiva y Geometría Computacional 360:
- PPDA (Passes Allowed per Defensive Action)
- Compacidad Defensiva (Convex Hull 360 en m^2 via scipy.spatial.ConvexHull)
- Teselación de Voronoi y Triangulación de Delaunay sobre freeze_frames 360
- Asfixia Espacial en Presión (jugadores propios en radio de 3m del portador rival)
- Comportamiento tras pérdida (Reacción inmediata <= 6s vs Repliegue ordenado)
"""

import math
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

import numpy as np
from scipy.spatial import ConvexHull, Delaunay, Voronoi

from src.config import (
    PITCH_LENGTH,
    PITCH_WIDTH,
    AREA_YARD2_TO_M2,
    PPDA_MAX_RIVAL_X,
    PRESSURE_SUFFOCATION_RADIUS_SB,
    PRESSURE_ACTION_TYPES,
    DEFENSIVE_EVENT_TYPES,
)


def compute_polygon_clip_box(poly: List[Tuple[float, float]]) -> List[List[float]]:
    """Recorta un polígono convexo al rectángulo de la cancha [0, 120] x [0, 80] mediante Sutherland-Hodgman."""
    def clip_edge(pts, edge_fn, intersect_fn):
        if not pts:
            return []
        out = []
        s = pts[-1]
        for e in pts:
            if edge_fn(e):
                if not edge_fn(s):
                    out.append(intersect_fn(s, e))
                out.append(e)
            elif edge_fn(s):
                out.append(intersect_fn(s, e))
            s = e
        return out

    pts = list(poly)
    # Left x >= 0
    pts = clip_edge(
        pts,
        lambda p: p[0] >= 0.0,
        lambda s, e: (0.0, s[1] + (e[1] - s[1]) * (0.0 - s[0]) / ((e[0] - s[0]) or 1e-9)),
    )
    # Right x <= 120
    pts = clip_edge(
        pts,
        lambda p: p[0] <= PITCH_LENGTH,
        lambda s, e: (PITCH_LENGTH, s[1] + (e[1] - s[1]) * (PITCH_LENGTH - s[0]) / ((e[0] - s[0]) or 1e-9)),
    )
    # Top y >= 0
    pts = clip_edge(
        pts,
        lambda p: p[1] >= 0.0,
        lambda s, e: (s[0] + (e[0] - s[0]) * (0.0 - s[1]) / ((e[1] - s[1]) or 1e-9), 0.0),
    )
    # Bottom y <= 80
    pts = clip_edge(
        pts,
        lambda p: p[1] <= PITCH_WIDTH,
        lambda s, e: (s[0] + (e[0] - s[0]) * (PITCH_WIDTH - s[1]) / ((e[1] - s[1]) or 1e-9), PITCH_WIDTH),
    )
    return [[round(p[0], 2), round(p[1], 2)] for p in pts]


def compute_360_geometry_snapshot(
    freeze_frame: List[Dict[str, Any]],
    exclude_corner_taker: bool = False,
) -> Dict[str, Any]:
    """
    Calcula la geometría computacional completa sobre un freeze_frame 360:
    1. Convex Hull de los defensores/jugadores de campo del target_team (área en m^2 y vértices).
       Excluye cobradores en el banderín de córner para no distorsionar el polígono del bloque en el área.
    2. Triangulación de Delaunay entre los jugadores del target_team.
    3. Teselación de Voronoi finita (recortada a [0,120]x[0,80]) para todos los jugadores visibles.
    """
    def _is_corner_flag_taker(pt: Dict[str, Any]) -> bool:
        tx = pt.get("target_x", 60.0)
        ty = pt.get("target_y", 40.0)
        if exclude_corner_taker and pt.get("actor", False):
            return True
        if tx >= 117.0 and (ty <= 3.5 or ty >= 76.5):
            return True
        if tx <= 3.0 and (ty <= 3.5 or ty >= 76.5):
            return True
        return False

    target_outfield = [
        pt for pt in freeze_frame
        if pt.get("is_target_team", False)
        and not pt.get("keeper", False)
        and not _is_corner_flag_taker(pt)
    ]

    if exclude_corner_taker:
        box_players = [
            pt for pt in target_outfield
            if 102.0 <= pt.get("target_x", 60.0) <= 119.5
            and 18.0 <= pt.get("target_y", 40.0) <= 62.0
        ]
        if len(box_players) >= 3:
            target_outfield = box_players

    hull_vertices: List[List[float]] = []
    hull_area_m2 = 0.0
    centroid_x, centroid_y = 60.0, 40.0
    width_m, length_m = 0.0, 0.0

    if len(target_outfield) >= 3:
        pts_arr = np.array([[pt["target_x"], pt["target_y"]] for pt in target_outfield], dtype=float)
        centroid_x = float(np.mean(pts_arr[:, 0]))
        centroid_y = float(np.mean(pts_arr[:, 1]))
        length_m = float((np.max(pts_arr[:, 0]) - np.min(pts_arr[:, 0])) * 0.9144)
        width_m = float((np.max(pts_arr[:, 1]) - np.min(pts_arr[:, 1])) * 0.9144)
        try:
            # En 2D, ConvexHull.volume de scipy retorna el área superficial del polígono convexo
            hull = ConvexHull(pts_arr)
            hull_area_m2 = round(float(hull.volume) * AREA_YARD2_TO_M2, 2)
            hull_vertices = [
                [round(float(pts_arr[idx, 0]), 2), round(float(pts_arr[idx, 1]), 2)]
                for idx in hull.vertices
            ]
        except Exception:
            pass

    # Triangulación de Delaunay sobre jugadores del target_team
    delaunay_edges: List[List[List[float]]] = []
    if len(target_outfield) >= 4:
        pts_arr = np.array([[pt["target_x"], pt["target_y"]] for pt in target_outfield], dtype=float)
        try:
            tri = Delaunay(pts_arr)
            edge_set = set()
            for simplex in tri.simplices:
                for i in range(3):
                    u, v = sorted((int(simplex[i]), int(simplex[(i + 1) % 3])))
                    edge_set.add((u, v))
            for u, v in edge_set:
                delaunay_edges.append([
                    [round(float(pts_arr[u, 0]), 2), round(float(pts_arr[u, 1]), 2)],
                    [round(float(pts_arr[v, 0]), 2), round(float(pts_arr[v, 1]), 2)],
                ])
        except Exception:
            pass

    # Teselación de Voronoi acotada añadiendo puntos espejo lejos de las bandas
    voronoi_cells: List[Dict[str, Any]] = []
    if len(freeze_frame) >= 4:
        real_pts = [[pt["target_x"], pt["target_y"]] for pt in freeze_frame]
        # Puntos fantasma lejanos para cerrar todas las regiones de los jugadores reales
        ghost_pts = [
            [-200.0, -200.0],
            [320.0, -200.0],
            [320.0, 280.0],
            [-200.0, 280.0],
            [60.0, -250.0],
            [60.0, 330.0],
            [-250.0, 40.0],
            [370.0, 40.0],
        ]
        all_pts = np.array(real_pts + ghost_pts, dtype=float)
        try:
            vor = Voronoi(all_pts)
            for idx, pt in enumerate(freeze_frame):
                reg_idx = vor.point_region[idx]
                region = vor.regions[reg_idx]
                if not region or -1 in region:
                    continue
                raw_poly = [(float(vor.vertices[v, 0]), float(vor.vertices[v, 1])) for v in region]
                clipped_poly = compute_polygon_clip_box(raw_poly)
                if len(clipped_poly) >= 3:
                    voronoi_cells.append({
                        "x": pt["target_x"],
                        "y": pt["target_y"],
                        "is_target_team": pt.get("is_target_team", False),
                        "actor": pt.get("actor", False),
                        "keeper": pt.get("keeper", False),
                        "polygon": clipped_poly,
                    })
        except Exception:
            pass

    return {
        "hull_area_m2": hull_area_m2,
        "hull_vertices": hull_vertices,
        "centroid_x": round(centroid_x, 2),
        "centroid_y": round(centroid_y, 2),
        "block_length_m": round(length_m, 1),
        "block_width_m": round(width_m, 1),
        "delaunay_edges": delaunay_edges,
        "voronoi_cells": voronoi_cells,
    }


def compute_defensive_metrics(
    events: List[Dict[str, Any]],
    matches_meta: List[Dict[str, Any]],
    framework_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calcula todas las métricas defensivas y espaciales 360 (Sección 6.2):
    - PPDA global, por partido y por intervalo de 15 min
    - Convex Hull 360 (compacidad en bloque bajo y medio) y snapshots geométricos
    - Asfixia espacial en presión (jugadores propios en radio de 3m del portador rival)
    - Altura de bloque y comportamiento tras pérdida
    """
    # 1. PPDA: Pases del rival permitidos en X <= 80 (para el rival, es decir x <= 80 en coord actor)
    # divididos por acciones defensivas propias en esa misma zona (target_x >= 40)
    rival_passes_allowed = 0
    own_def_actions_ppda_zone = 0

    ppda_by_match: Dict[int, List[int]] = defaultdict(lambda: [0, 0])  # [rival_passes, own_def_actions]
    ppda_by_time_bin: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    ppda_by_game_state: Dict[str, List[int]] = defaultdict(lambda: [0, 0])

    # Altura de acciones defensivas y mapa de recuperaciones
    def_action_xs: List[float] = []
    recovery_points: List[Dict[str, Any]] = []
    pressure_heatmap_grid = [[0 for _ in range(6)] for _ in range(4)]  # [y_bin 0..3][x_bin 0..5]

    # Asfixia espacial en presión (radio 3m ~ 3.28 yardas sobre el portador rival)
    suffocation_counts: List[int] = []

    # Compacidad Convex Hull 360 en bloque bajo y medio
    low_block_hull_areas: List[float] = []
    mid_block_hull_areas: List[float] = []
    high_block_hull_areas: List[float] = []
    candidate_snapshots_by_match: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    from src.config import get_player_clean_name

    for ev in events:
        mid = ev["match_id"]
        is_target = ev["is_target_team"]
        ev_type = ev["type"]
        tb = ev["time_bin"]
        gs = ev["game_state"]

        # Pases del rival en X <= 80 (en coordenadas del rival)
        if not is_target and ev_type == "Pass" and ev["x"] is not None:
            if ev["x"] <= PPDA_MAX_RIVAL_X:
                rival_passes_allowed += 1
                ppda_by_match[mid][0] += 1
                ppda_by_time_bin[tb][0] += 1
                ppda_by_game_state[gs][0] += 1

        # Acciones defensivas del target_team
        if is_target and ev_type in PRESSURE_ACTION_TYPES and ev["target_x"] is not None:
            tx, ty = ev["target_x"], ev["target_y"]
            def_action_xs.append(tx)

            if ty is not None:
                xb = min(5, max(0, int(tx / 20.0)))
                yb = min(3, max(0, int(ty / 20.0)))
                pressure_heatmap_grid[yb][xb] += 1

            # Zona PPDA: X <= 80 para el rival equivale a target_x >= 40 para el target_team
            # Para PPDA estándar de cuerpo técnico, contabilizamos intervenciones defensivas directas
            # (Duel, Interception, Foul Committed, Block, o Pressure de contra-presión)
            is_ppda_def_action = (
                ev_type in ("Duel", "Interception", "Foul Committed", "Block")
                or (ev_type == "Pressure" and ev.get("counterpress"))
            )
            if tx >= (PITCH_LENGTH - PPDA_MAX_RIVAL_X) and is_ppda_def_action:
                own_def_actions_ppda_zone += 1
                ppda_by_match[mid][1] += 1
                ppda_by_time_bin[tb][1] += 1
                ppda_by_game_state[gs][1] += 1

        # Recuperaciones de balón
        if is_target and ev_type in ("Ball Recovery", "Interception") and ev["target_x"] is not None:
            recovery_points.append({
                "match_id": mid,
                "minute": ev["minute"],
                "type": ev_type,
                "player": get_player_clean_name(ev["player_name"]),
                "x": ev["target_x"],
                "y": ev["target_y"],
                "game_state": gs,
            })

        # Evaluar Asfixia Espacial (radio 3m) y Convex Hull 360 cuando el equipo defiende
        is_defensive_moment = (is_target and ev_type in DEFENSIVE_EVENT_TYPES) or (
            not is_target and ev["under_pressure"] and ev_type in ("Pass", "Carry", "Dispossessed", "Miscontrol")
        )
        if is_defensive_moment and ev["has_360"] and ev["freeze_frame"] and ev["target_x"] is not None:
            ball_x, ball_y = ev["target_x"], ev["target_y"]
            ff = ev["freeze_frame"]

            # 1) Asfixia espacial: defensores de target_team dentro de 3 metros (3.28 yardas SB) del balón
            nearby_defenders = 0
            target_def_pts = []
            for pt in ff:
                if pt.get("is_target_team", False) and not pt.get("keeper", False):
                    dx = pt["target_x"] - ball_x
                    dy = pt["target_y"] - ball_y
                    dist = math.hypot(dx, dy)
                    if dist <= PRESSURE_SUFFOCATION_RADIUS_SB:
                        nearby_defenders += 1
                    target_def_pts.append((pt["target_x"], pt["target_y"]))

            if (is_target and ev_type == "Pressure") or (not is_target and ev["under_pressure"]):
                suffocation_counts.append(nearby_defenders)

            # 2) Convex Hull 360 cuando hay al menos 5 jugadores de campo del target_team visibles
            if len(target_def_pts) >= 5:
                pts_np = np.array(target_def_pts, dtype=float)
                mean_x = float(np.mean(pts_np[:, 0]))
                try:
                    hull = ConvexHull(pts_np)
                    area_m2 = float(hull.volume) * AREA_YARD2_TO_M2
                    if 35.0 <= area_m2 <= 1400.0:
                        if mean_x < 45.0:
                            low_block_hull_areas.append(area_m2)
                        elif mean_x <= 75.0:
                            mid_block_hull_areas.append(area_m2)
                        else:
                            high_block_hull_areas.append(area_m2)

                        # Candidatos para el visualizador: actor propio (is_target), minuto >= 5,
                        # >= 7 defensores visibles y área representativa del bloque (380..560 m2)
                        if (
                            is_target
                            and ev.get("player_name")
                            and ev["minute"] >= 5
                            and len(target_def_pts) >= 7
                            and 380.0 <= area_m2 <= 560.0
                            and len(candidate_snapshots_by_match[mid]) < 3
                        ):
                            block_type = (
                                "Bloque Bajo"
                                if mean_x < 45.0
                                else ("Bloque Medio" if mean_x <= 75.0 else "Presión Alta")
                            )
                            candidate_snapshots_by_match[mid].append({
                                "event_id": ev["id"],
                                "match_id": mid,
                                "opponent": ev["opponent"],
                                "match_date": ev["match_date"],
                                "minute": ev["minute"],
                                "second": ev["second"],
                                "event_type": ev_type,
                                "block_type": block_type,
                                "player_name": get_player_clean_name(ev["player_name"]),
                                "ball_x": ball_x,
                                "ball_y": ball_y,
                                "suffocation_3m": nearby_defenders,
                                "visible_defenders": len(target_def_pts),
                                "area_m2_raw": area_m2,
                                "game_state": gs,
                                "freeze_frame": ff,
                                "visible_area": ev["visible_area"],
                            })
                except Exception:
                    pass

    global_ppda = round(rival_passes_allowed / max(1, own_def_actions_ppda_zone), 2)
    avg_def_height_x = round(sum(def_action_xs) / max(1, len(def_action_xs)), 1)
    avg_recovery_x = round(
        sum(r["x"] for r in recovery_points) / max(1, len(recovery_points)), 1
    )
    avg_suffocation_3m = round(sum(suffocation_counts) / max(1, len(suffocation_counts)), 2)

    low_block_hull_avg = round(sum(low_block_hull_areas) / max(1, len(low_block_hull_areas)), 1)
    mid_block_hull_avg = round(sum(mid_block_hull_areas) / max(1, len(mid_block_hull_areas)), 1)
    high_block_hull_avg = round(sum(high_block_hull_areas) / max(1, len(high_block_hull_areas)), 1)
    combined_low_mid = low_block_hull_areas + mid_block_hull_areas
    overall_hull_avg = round(sum(combined_low_mid) / max(1, len(combined_low_mid)), 1)
    total_hull_frames_evaluated = len(low_block_hull_areas) + len(mid_block_hull_areas) + len(high_block_hull_areas)

    # Seleccionar 1 snapshot representativo por partido distinto (ordenados por cercanía al área promedio global)
    representative_candidates: List[Dict[str, Any]] = []
    for mid, cands in candidate_snapshots_by_match.items():
        cands.sort(key=lambda c: abs(c["area_m2_raw"] - overall_hull_avg))
        representative_candidates.append(cands[0])

    representative_candidates.sort(key=lambda c: abs(c["area_m2_raw"] - overall_hull_avg))
    defensive_360_snapshots: List[Dict[str, Any]] = []
    for cand in representative_candidates[:15]:
        cand_copy = {k: v for k, v in cand.items() if k != "area_m2_raw"}
        cand_copy["geometry"] = compute_360_geometry_snapshot(cand["freeze_frame"])
        defensive_360_snapshots.append(cand_copy)

    # PPDA por partido
    match_ppda_list = []
    for m in matches_meta:
        mid = m["match_id"]
        rp, da = ppda_by_match[mid]
        match_ppda_list.append({
            "match_id": mid,
            "match_date": m["match_date"],
            "opponent": m["opponent"],
            "venue": m["venue"],
            "result": m["result"],
            "ppda": round(rp / max(1, da), 2),
            "rival_passes": rp,
            "defensive_actions": da,
        })

    # PPDA por intervalo de 15 min
    ppda_timeline = []
    for tb in ("0-15", "15-30", "30-45", "45-60", "60-75", "75+"):
        rp, da = ppda_by_time_bin[tb]
        ppda_timeline.append({
            "time_bin": tb,
            "ppda": round(rp / max(1, da), 2),
            "rival_passes": rp,
            "defensive_actions": da,
        })

    # Comportamiento tras pérdida (Counterpress <=6s vs Repliegue ordenado)
    pressure_evs = framework_data.get("pressure_events", [])
    cp_actions = sum(1 for p in pressure_evs if "Counterpress" in (p.get("subtype") or ""))
    high_press_actions = sum(1 for p in pressure_evs if p.get("subtype") == "High Press (X>=80)")
    total_press_phase = max(1, len(pressure_evs))

    return {
        "kpis": {
            "ppda_global": global_ppda,
            "defensive_line_height_x": avg_def_height_x,
            "avg_recovery_height_x": avg_recovery_x,
            "convex_hull_low_mid_m2": overall_hull_avg,
            "convex_hull_low_block_m2": low_block_hull_avg,
            "convex_hull_mid_block_m2": mid_block_hull_avg,
            "convex_hull_high_press_m2": high_block_hull_avg,
            "convex_hull_frames_total": total_hull_frames_evaluated,
            "pressure_suffocation_3m": avg_suffocation_3m,
            "total_pressure_phase_events": len(pressure_evs),
            "counterpress_events_6s": cp_actions,
            "high_press_events_x80": high_press_actions,
            "counterpress_share_pct": round((cp_actions / total_press_phase) * 100.0, 1),
        },
        "ppda_by_match": match_ppda_list,
        "ppda_by_time_bin": ppda_timeline,
        "pressure_heatmap_grid_4x6": pressure_heatmap_grid,
        "recoveries_sample": recovery_points[:120],
        "defensive_360_snapshots": defensive_360_snapshots,
    }
