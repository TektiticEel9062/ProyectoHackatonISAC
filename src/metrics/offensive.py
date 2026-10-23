"""
src/metrics/offensive.py
Motor Métrico de Fase Ofensiva, Progresión, Índice de Ruptura de Líneas 360 y Teoría de Grafos en Redes de Pases.
"""

import math
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter

try:
    import networkx as nx
except ImportError:
    nx = None

from src.config import (
    PITCH_LENGTH,
    PITCH_WIDTH,
    PROGRESSIVE_PASS_FRACTION,
    FINAL_THIRD_X,
    get_player_short_name,
    get_player_clean_name,
)


def is_progressive_pass(start_x: float, start_y: float, end_x: float, end_y: float) -> bool:
    """
    6.1 Pases Progresivos:
    Pases completados hacia campo rival que avanzan el balón al menos un 25% más cerca
    de la línea de meta rival (X=120) respecto a su punto de origen.
    """
    if start_x is None or end_x is None or end_x <= start_x:
        return False
    # Debe terminar en campo rival (X > 60)
    if end_x <= 60.0:
        return False
    dist_origin = PITCH_LENGTH - start_x
    dist_end = PITCH_LENGTH - end_x
    if dist_origin <= 1.0:
        return False
    advance_ratio = (dist_origin - dist_end) / dist_origin
    return advance_ratio >= PROGRESSIVE_PASS_FRACTION


def count_360_broken_defenders(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    freeze_frame: List[Dict[str, Any]],
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    6.1 Índice de Ruptura de Líneas 360 (Innovación):
    Cuenta la cantidad de defensores rivales de campo superados en el eje X entre el pasador y el receptor
    que se encontraban dentro del corredor/cono defensivo activo del pase (distancia lateral <= 12 yd
    respecto a la trayectoria interpolada del envío), acotado físicamente a <= 9 jugadores de campo.
    """
    if not freeze_frame or start_x is None or end_x is None or end_x <= (start_x + 1.5):
        return 0, []

    dx_span = end_x - start_x
    dy_span = end_y - start_y

    bypassed_defenders = []
    seen_coords = set()
    for pt in freeze_frame:
        if pt.get("is_target_team", False) or pt.get("keeper", False):
            continue
        dx = pt.get("target_x")
        dy = pt.get("target_y")
        if dx is None or dy is None:
            continue
        # Evitar detecciones duplicadas en el mismo frame
        coord_key = (round(dx, 1), round(dy, 1))
        if coord_key in seen_coords:
            continue

        # 1. Superado longitudinalmente en el eje X entre pasador y receptor
        if (start_x + 1.0) < dx < (end_x - 0.5):
            # 2. Interpolación de la coordenada Y del pase a la altura X = dx (corredor activo +-12.5 yd)
            ratio_x = (dx - start_x) / dx_span
            interp_y = start_y + ratio_x * dy_span
            if abs(dy - interp_y) <= 12.5:
                seen_coords.add(coord_key)
                bypassed_defenders.append(pt)
                if len(bypassed_defenders) >= 9:
                    break

    return len(bypassed_defenders), bypassed_defenders


def compute_passing_network(events: List[Dict[str, Any]], min_passes_edge: int = 12) -> Dict[str, Any]:
    """
    Teoría de Grafos en Redes de Pases:
    Construye el grafo dirigido ponderado G=(V,E), calcula ubicación media (x,y),
    Betweenness Centrality, grado ponderado y densidad de red.
    """
    player_locs: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    player_positions: Dict[str, Counter] = defaultdict(Counter)
    pair_counts: Counter = Counter()
    pair_obv: Dict[Tuple[str, str], float] = defaultdict(float)
    pair_prog: Counter = Counter()

    for ev in events:
        if not ev["is_target_team"]:
            continue
        p_name = ev.get("player_name")
        if p_name and ev["target_x"] is not None and ev["target_y"] is not None:
            player_locs[p_name].append((ev["target_x"], ev["target_y"]))
            if ev.get("position_name"):
                player_positions[p_name][ev["position_name"]] += 1

        if ev["type"] == "Pass" and ev["pass_completed"]:
            rec_name = ev.get("pass_recipient")
            if p_name and rec_name and p_name != rec_name:
                pair_counts[(p_name, rec_name)] += 1
                pair_obv[(p_name, rec_name)] += ev.get("obv_total_net", 0.0)
                if ev.get("is_progressive_pass"):
                    pair_prog[(p_name, rec_name)] += 1

    # Seleccionar los 14 jugadores con mayor participación en pases para la red principal
    player_touch_counts = {p: len(locs) for p, locs in player_locs.items()}
    top_players = [
        p for p, _ in sorted(player_touch_counts.items(), key=lambda kv: kv[1], reverse=True)[:14]
    ]
    top_set = set(top_players)

    nodes_map: Dict[str, Dict[str, Any]] = {}
    for p in top_players:
        locs = player_locs[p]
        avg_x = sum(pt[0] for pt in locs) / len(locs) if locs else 60.0
        avg_y = sum(pt[1] for pt in locs) / len(locs) if locs else 40.0
        pos_label = player_positions[p].most_common(1)[0][0] if player_positions[p] else "Midfielder"
        clean_p = get_player_clean_name(p)
        nodes_map[p] = {
            "id": p,
            "name": clean_p,
            "full_name": p,
            "short_name": get_player_short_name(p),
            "x": round(avg_x, 2),
            "y": round(avg_y, 2),
            "position": pos_label,
            "touches": len(locs),
            "betweenness_centrality": 0.0,
            "degree_centrality": 0.0,
            "pagerank": 0.0,
            "passes_sent": 0,
            "passes_received": 0,
        }

    edges: List[Dict[str, Any]] = []
    for (u, v), w in pair_counts.items():
        if u in top_set and v in top_set:
            nodes_map[u]["passes_sent"] += w
            nodes_map[v]["passes_received"] += w
            if w >= min_passes_edge:
                edges.append({
                    "source": nodes_map[u]["name"],
                    "target": nodes_map[v]["name"],
                    "source_raw": u,
                    "target_raw": v,
                    "source_x": nodes_map[u]["x"],
                    "source_y": nodes_map[u]["y"],
                    "target_x": nodes_map[v]["x"],
                    "target_y": nodes_map[v]["y"],
                    "weight": w,
                    "progressive_count": pair_prog[(u, v)],
                    "obv_net": round(pair_obv[(u, v)], 3),
                })

    density = 0.0
    if nx is not None and len(top_players) > 1:
        G = nx.DiGraph()
        for p in top_players:
            G.add_node(p)
        for e in edges:
            # En camino más corto, distancia inversamente proporcional al flujo de pases
            G.add_edge(e["source_raw"], e["target_raw"], weight=e["weight"], distance=1.0 / max(1.0, float(e["weight"])))

        density = round(nx.density(G), 4)
        bw = nx.betweenness_centrality(G, weight="distance", normalized=True)
        deg = nx.degree_centrality(G)
        try:
            pr = nx.pagerank(G, weight="weight")
        except Exception:
            pr = {p: 1.0 / len(top_players) for p in top_players}

        for p in top_players:
            nodes_map[p]["betweenness_centrality"] = round(float(bw.get(p, 0.0)), 4)
            nodes_map[p]["degree_centrality"] = round(float(deg.get(p, 0.0)), 4)
            nodes_map[p]["pagerank"] = round(float(pr.get(p, 0.0)), 4)

    nodes_list = sorted(nodes_map.values(), key=lambda x: x["betweenness_centrality"], reverse=True)
    edges.sort(key=lambda x: x["weight"], reverse=True)

    max_bw_player = nodes_list[0]["name"] if nodes_list else "N/A"
    max_bw_val = nodes_list[0]["betweenness_centrality"] if nodes_list else 0.0

    return {
        "nodes": nodes_list,
        "edges": edges,
        "network_density": density,
        "hub_player": max_bw_player,
        "hub_betweenness": max_bw_val,
    }


def compute_offensive_metrics(events: List[Dict[str, Any]], matches_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula todas las métricas de la fase ofensiva y de progresión (Sección 6.1):
    - Pases progresivos
    - Field Tilt global y por partido
    - Índice de Ruptura de Líneas 360 y mejores jugadas 360
    - Salida de balón (corta vs larga), carriles de progresión y mapa de tiros
    - Red de pases y métricas de teoría de grafos
    """
    total_passes_target = 0
    completed_passes_target = 0
    progressive_passes_count = 0
    progressive_carries_count = 0

    # Field Tilt: Pases exitosos en el tercio final de cada equipo (X >= 80 en coordenadas del actor)
    target_final_third_passes = 0
    opponent_final_third_passes = 0
    ft_by_match: Dict[int, List[ int ]] = defaultdict(lambda: [0, 0])  # [target_ft, opp_ft]

    # Ruptura de líneas 360
    passes_with_360 = 0
    line_breaking_passes_count = 0
    total_defenders_broken = 0
    line_breaking_examples: List[Dict[str, Any]] = []

    # Salida desde tercio propio (X < 40)
    buildup_short_total = 0
    buildup_short_comp = 0
    buildup_short_obv = 0.0
    buildup_long_total = 0
    buildup_long_comp = 0
    buildup_long_obv = 0.0

    # Carriles de progresión (Izquierdo Y<26.67, Central 26.67..53.33, Derecho Y>53.33)
    lanes = {
        "left": {"passes": 0, "progressive": 0, "obv": 0.0, "label": "Carril Izquierdo (Y < 26.7)"},
        "center": {"passes": 0, "progressive": 0, "obv": 0.0, "label": "Carril Central (26.7 ≤ Y ≤ 53.3)"},
        "right": {"passes": 0, "progressive": 0, "obv": 0.0, "label": "Carril Derecho (Y > 53.3)"},
    }

    # Disparos y xG / OBV
    shots_list: List[Dict[str, Any]] = []
    total_xg_for = 0.0
    total_xg_against = 0.0
    total_goals_for = 0
    total_goals_against = 0
    total_obv_net = 0.0
    progressive_pass_vectors: List[Dict[str, Any]] = []

    for ev in events:
        mid = ev["match_id"]
        is_target = ev["is_target_team"]
        ev_type = ev["type"]

        # Contabilizar Field Tilt en tercio final de cada equipo (x >= 80 en coord del actor)
        if ev_type == "Pass" and ev["pass_completed"] and ev["x"] is not None:
            if ev["x"] >= FINAL_THIRD_X:
                if is_target:
                    target_final_third_passes += 1
                    ft_by_match[mid][0] += 1
                else:
                    opponent_final_third_passes += 1
                    ft_by_match[mid][1] += 1

        if not is_target:
            if ev_type == "Shot":
                total_xg_against += ev["shot_xg"]
                if ev["is_goal"]:
                    total_goals_against += 1
            continue

        total_obv_net += ev["obv_total_net"]

        # Evaluar Conducciones Progresivas
        if ev_type == "Carry" and ev["target_x"] is not None and ev["target_end_x"] is not None:
            if is_progressive_pass(ev["target_x"], ev["target_y"], ev["target_end_x"], ev["target_end_y"]):
                progressive_carries_count += 1
                ev["is_progressive_carry"] = True
            else:
                ev["is_progressive_carry"] = False

        # Evaluar Pases
        if ev_type == "Pass":
            total_passes_target += 1
            sx, sy = ev["target_x"], ev["target_y"]
            ex, ey = ev["target_end_x"], ev["target_end_y"]

            # Salida de fondo (origen X < 40)
            if sx is not None and sx < 40.0 and ev["pass_length"] is not None:
                if ev["pass_length"] < 28.0:
                    buildup_short_total += 1
                    if ev["pass_completed"]:
                        buildup_short_comp += 1
                    buildup_short_obv += ev["obv_total_net"]
                else:
                    buildup_long_total += 1
                    if ev["pass_completed"]:
                        buildup_long_comp += 1
                    buildup_long_obv += ev["obv_total_net"]

            if ev["pass_completed"] and sx is not None and sy is not None and ex is not None and ey is not None:
                completed_passes_target += 1
                prog = is_progressive_pass(sx, sy, ex, ey)
                ev["is_progressive_pass"] = prog

                # Clasificar carril según coordenada media Y
                mid_y = 0.5 * (sy + ey)
                lane_key = "left" if mid_y < 26.67 else ("right" if mid_y > 53.33 else "center")
                lanes[lane_key]["passes"] += 1
                lanes[lane_key]["obv"] = round(lanes[lane_key]["obv"] + ev["obv_total_net"], 4)

                if prog:
                    progressive_passes_count += 1
                    lanes[lane_key]["progressive"] += 1

                # Evaluar Índice de Ruptura de Líneas 360
                if ev["has_360"] and ev["freeze_frame"]:
                    passes_with_360 += 1
                    n_broken, broken_list = count_360_broken_defenders(
                        sx, sy, ex, ey, ev["freeze_frame"]
                    )
                    is_lb = bool(ev["line_breaking_pass_360"]) or (n_broken >= 2 and prog)
                    ev["defenders_broken_360"] = n_broken
                    if is_lb and n_broken >= 1:
                        line_breaking_passes_count += 1
                        total_defenders_broken += n_broken
                        # Solo destacar en el catálogo 360 pases progresivos que sumen valor positivo (OBV > 0.02)
                        if prog and n_broken >= 2 and ev["obv_total_net"] > 0.02 and len(ev["freeze_frame"]) >= 8:
                            line_breaking_examples.append({
                                "event_id": ev["id"],
                                "match_id": mid,
                                "opponent": ev["opponent"],
                                "match_date": ev["match_date"],
                                "minute": ev["minute"],
                                "second": ev["second"],
                                "player_name": get_player_clean_name(ev["player_name"]),
                                "recipient_name": get_player_clean_name(ev["pass_recipient"]),
                                "start_x": sx,
                                "start_y": sy,
                                "end_x": ex,
                                "end_y": ey,
                                "defenders_broken": n_broken,
                                "obv_net": round(ev["obv_total_net"], 4),
                                "game_state": ev["game_state"],
                                "freeze_frame": ev["freeze_frame"],
                                "visible_area": ev["visible_area"],
                            })

                # Filtrar progressive_pass_vectors exigiendo que cumplan estrictamente el axioma del 25%
                # tanto en X como en distancia euclidiana a portería (120, 40), con avance >= 8 yd y >= 1 defensor superado
                dist_goal_ini = math.hypot(PITCH_LENGTH - sx, 40.0 - sy)
                dist_goal_end = math.hypot(PITCH_LENGTH - ex, 40.0 - ey)
                strict_25_goal = dist_goal_end <= 0.75 * dist_goal_ini
                if (
                    prog
                    and strict_25_goal
                    and (ex - sx) >= 8.0
                    and (ev.get("defenders_broken_360") or 0) >= 1
                    and ev["obv_total_net"] > 0.015
                ):
                    progressive_pass_vectors.append({
                        "start_x": sx,
                        "start_y": sy,
                        "end_x": ex,
                        "end_y": ey,
                        "player": get_player_clean_name(ev["player_name"]),
                        "recipient": get_player_clean_name(ev["pass_recipient"]),
                        "obv": round(ev["obv_total_net"], 4),
                        "broken_defenders": ev.get("defenders_broken_360", 0),
                    })
            else:
                ev["is_progressive_pass"] = False

        # Evaluar Disparos
        if ev_type == "Shot" and ev["target_x"] is not None and ev["target_y"] is not None:
            total_xg_for += ev["shot_xg"]
            if ev["is_goal"]:
                total_goals_for += 1
            shots_list.append({
                "id": ev["id"],
                "match_id": mid,
                "opponent": ev["opponent"],
                "minute": ev["minute"],
                "player_name": get_player_clean_name(ev["player_name"]),
                "x": ev["target_x"],
                "y": ev["target_y"],
                "end_x": ev["target_end_x"],
                "end_y": ev["target_end_y"],
                "xg": round(ev["shot_xg"], 4),
                "is_goal": ev["is_goal"],
                "outcome": ev["shot_outcome"],
                "game_state": ev["game_state"],
                "play_pattern": ev["play_pattern"],
            })

    # Ordenar ejemplos 360 de ruptura de líneas priorizando el pase insignia de Zendejas a Aguirre vs Santos Laguna
    # (ab561f3c-2df1-5535-9591-ca058fe89b5d) y luego por mayor impacto OBV positivo + defensores superados
    line_breaking_examples.sort(
        key=lambda item: (
            100.0 if item["event_id"] == "ab561f3c-2df1-5535-9591-ca058fe89b5d" else 0.0,
            item["obv_net"] + item["defenders_broken"] * 0.04,
        ),
        reverse=True,
    )
    progressive_pass_vectors.sort(key=lambda item: item["obv"], reverse=True)

    total_ft_passes = target_final_third_passes + opponent_final_third_passes
    field_tilt_pct = round((target_final_third_passes / total_ft_passes) * 100.0, 2) if total_ft_passes > 0 else 50.0

    match_field_tilt = []
    for m in matches_meta:
        mid = m["match_id"]
        tf, of = ft_by_match[mid]
        tot = tf + of
        ft_val = round((tf / tot) * 100.0, 1) if tot > 0 else 50.0
        match_field_tilt.append({
            "match_id": mid,
            "match_date": m["match_date"],
            "opponent": m["opponent"],
            "venue": m["venue"],
            "result": m["result"],
            "field_tilt": ft_val,
            "target_final_third_passes": tf,
            "opponent_final_third_passes": of,
        })

    n_matches = max(1, len(matches_meta))
    passing_network = compute_passing_network(events)

    return {
        "kpis": {
            "total_passes": total_passes_target,
            "completed_passes": completed_passes_target,
            "pass_accuracy_pct": round((completed_passes_target / max(1, total_passes_target)) * 100.0, 1),
            "progressive_passes_total": progressive_passes_count,
            "progressive_passes_per_match": round(progressive_passes_count / n_matches, 1),
            "progressive_carries_total": progressive_carries_count,
            "progressive_carries_per_match": round(progressive_carries_count / n_matches, 1),
            "field_tilt_pct": field_tilt_pct,
            "line_breaking_passes_360_total": line_breaking_passes_count,
            "line_breaking_passes_360_per_match": round(line_breaking_passes_count / n_matches, 1),
            "avg_defenders_broken_per_lb_pass": round(
                total_defenders_broken / max(1, line_breaking_passes_count), 2
            ),
            "xg_for_total": round(total_xg_for, 2),
            "xg_for_per_match": round(total_xg_for / n_matches, 2),
            "goals_for_total": total_goals_for,
            "obv_net_total": round(total_obv_net, 2),
            "obv_net_per_match": round(total_obv_net / n_matches, 2),
        },
        "buildup_profile": {
            "short_passes_total": buildup_short_total,
            "short_passes_completed": buildup_short_comp,
            "short_accuracy_pct": round((buildup_short_comp / max(1, buildup_short_total)) * 100.0, 1),
            "short_obv_net": round(buildup_short_obv, 2),
            "long_passes_total": buildup_long_total,
            "long_passes_completed": buildup_long_comp,
            "long_accuracy_pct": round((buildup_long_comp / max(1, buildup_long_total)) * 100.0, 1),
            "long_obv_net": round(buildup_long_obv, 2),
            "short_ratio_pct": round(
                (buildup_short_total / max(1, buildup_short_total + buildup_long_total)) * 100.0, 1
            ),
        },
        "progression_lanes": lanes,
        "field_tilt_by_match": match_field_tilt,
        "top_progressive_vectors": progressive_pass_vectors[:85],
        "top_line_breaking_360": line_breaking_examples[:18],
        "shots_map": shots_list,
        "passing_network": passing_network,
    }
