"""
src/metrics/set_pieces.py
Laboratorio de Balón Parado - ABP Ofensivo y Defensivo con Ocupación Espacial 360 (Sección 6.5):
- Clasificación de entregas: Primer palo, Segundo palo, Frontal / Punto penal, Jugada corta
- Sobrecarga espacial 360 en el área chica (X >= 114, 30 <= Y <= 50)
- Conversión a remate y xG en ABP ofensivo vs vulnerabilidad en ABP defensivo
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict

from src.config import (
    SIX_YARD_BOX_MIN_X,
    SIX_YARD_BOX_MIN_Y,
    SIX_YARD_BOX_MAX_Y,
    get_player_clean_name,
)


def classify_corner_delivery(start_x: float, start_y: float, end_x: float, end_y: float, length: float) -> str:
    """
    Clasifica la rutina de tiro de esquina (en coordenadas del ejecutante X -> 120, Y in [0,80]):
    - Jugada Corta: longitud < 16 yd o end_x < 102 o fuera del área (end_y < 18 o end_y > 62)
    - Primer Palo: envío al poste cercano al saque (diferencia en Y respecto a la esquina <= 42 yd y X >= 111)
    - Segundo Palo: envío pasado hacia el poste lejano
    - Frontal / Punto Penal: zona central entre X in [102, 113] y Y in [30, 50]
    """
    if length is not None and length < 16.0:
        return "Jugada Corta"
    if end_x is None or end_y is None:
        return "Frontal / Penal"
    if end_x < 101.0 or end_y < 18.0 or end_y > 62.0:
        return "Jugada Corta"

    from_top_left = (start_y or 0.0) < 40.0
    if end_x >= 111.5:
        if from_top_left:
            if end_y <= 38.5:
                return "Primer Palo"
            elif end_y >= 42.5:
                return "Segundo Palo"
        else:
            if end_y >= 41.5:
                return "Primer Palo"
            elif end_y <= 37.5:
                return "Segundo Palo"

    if (from_top_left and end_y >= 45.0) or (not from_top_left and end_y <= 35.0):
        return "Segundo Palo"
    if (from_top_left and end_y <= 34.0) or (not from_top_left and end_y >= 46.0):
        return "Primer Palo"

    return "Frontal / Penal"


def compute_set_pieces_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula métricas de Balón Parado (ABP) ofensivo y defensivo (Sección 6.5).
    """
    # Agrupar posesiones para saber si un córner o tiro libre culminó en disparo / xG / gol
    poss_shots: Dict[Tuple[int, int], Dict[str, Any]] = defaultdict(
        lambda: {"shots": 0, "xg": 0.0, "goals": 0}
    )
    for ev in events:
        if ev["type"] == "Shot":
            key = (ev["match_id"], ev["possession"])
            poss_shots[key]["shots"] += 1
            poss_shots[key]["xg"] += ev["shot_xg"]
            if ev["is_goal"]:
                poss_shots[key]["goals"] += 1

    off_zones: Dict[str, Dict[str, Any]] = {
        z: {"count": 0, "shots": 0, "xg": 0.0, "goals": 0, "att_6yd_sum": 0, "def_6yd_sum": 0, "frames_360": 0}
        for z in ("Primer Palo", "Segundo Palo", "Frontal / Penal", "Jugada Corta")
    }
    def_zones: Dict[str, Dict[str, Any]] = {
        z: {"count": 0, "shots_conceded": 0, "xg_conceded": 0.0, "goals_conceded": 0, "att_6yd_sum": 0, "def_6yd_sum": 0, "frames_360": 0}
        for z in ("Primer Palo", "Segundo Palo", "Frontal / Penal", "Jugada Corta")
    }

    off_corner_deliveries: List[Dict[str, Any]] = []
    def_corner_deliveries: List[Dict[str, Any]] = []
    corner_360_samples: List[Dict[str, Any]] = []

    free_kick_stats = {
        "offensive_fk_passes": 0,
        "offensive_fk_shots": 0,
        "offensive_fk_xg": 0.0,
        "defensive_fk_shots_conceded": 0,
        "defensive_fk_xg_conceded": 0.0,
    }

    for ev in events:
        mid = ev["match_id"]
        pid = ev["possession"]
        is_target = ev["is_target_team"]
        ev_type = ev["type"]
        pass_type = ev.get("pass_type")
        play_pattern = ev.get("play_pattern", "")

        # Estadísticas de Tiros Libres (From Free Kick)
        if play_pattern == "From Free Kick":
            if ev_type == "Pass" and pass_type == "Free Kick" and is_target:
                free_kick_stats["offensive_fk_passes"] += 1
            elif ev_type == "Shot":
                if is_target:
                    free_kick_stats["offensive_fk_shots"] += 1
                    free_kick_stats["offensive_fk_xg"] = round(free_kick_stats["offensive_fk_xg"] + ev["shot_xg"], 3)
                else:
                    free_kick_stats["defensive_fk_shots_conceded"] += 1
                    free_kick_stats["defensive_fk_xg_conceded"] = round(
                        free_kick_stats["defensive_fk_xg_conceded"] + ev["shot_xg"], 3
                    )

        # Analizar saques de esquina (Pass con pass_type == "Corner")
        if ev_type == "Pass" and pass_type == "Corner":
            sx, sy = ev["x"], ev["y"]
            ex, ey = ev["end_x"], ev["end_y"]
            zone = classify_corner_delivery(sx, sy, ex, ey, ev.get("pass_length"))

            # Resultado de la posesión del córner
            p_res = poss_shots[(mid, pid)]
            led_to_shot = 1 if p_res["shots"] > 0 else 0
            seq_xg = p_res["xg"]
            seq_goals = p_res["goals"]

            # Evaluar Sobrecarga Espacial 360 en el área chica (X >= 114, 30 <= Y <= 50 en coords del lanzador)
            att_in_6yd = 0
            def_in_6yd = 0
            has_ff = bool(ev["has_360"] and ev["freeze_frame"])
            if has_ff:
                for pt in ev["freeze_frame"]:
                    # pt["x"], pt["y"] están en coordenadas relativas al lanzador del córner (X -> 120)
                    px, py = pt["x"], pt["y"]
                    if px >= SIX_YARD_BOX_MIN_X and SIX_YARD_BOX_MIN_Y <= py <= SIX_YARD_BOX_MAX_Y:
                        if pt.get("teammate", False):
                            att_in_6yd += 1
                        elif not pt.get("keeper", False):
                            def_in_6yd += 1

            if is_target:
                z_obj = off_zones[zone]
                z_obj["count"] += 1
                z_obj["shots"] += led_to_shot
                z_obj["xg"] = round(z_obj["xg"] + seq_xg, 3)
                z_obj["goals"] += seq_goals
                if has_ff:
                    z_obj["att_6yd_sum"] += att_in_6yd
                    z_obj["def_6yd_sum"] += def_in_6yd
                    z_obj["frames_360"] += 1

                off_corner_deliveries.append({
                    "id": ev["id"],
                    "match_id": mid,
                    "opponent": ev["opponent"],
                    "minute": ev["minute"],
                    "taker": get_player_clean_name(ev["player_name"]),
                    "recipient": get_player_clean_name(ev["pass_recipient"]) if ev.get("pass_recipient") else None,
                    "zone": zone,
                    "start_x": ev["target_x"],
                    "start_y": ev["target_y"],
                    "end_x": ev["target_end_x"],
                    "end_y": ev["target_end_y"],
                    "led_to_shot": bool(led_to_shot),
                    "xg": round(seq_xg, 3),
                    "att_in_6yd": att_in_6yd,
                    "def_in_6yd": def_in_6yd,
                })

                if has_ff and zone != "Jugada Corta" and len(ev["freeze_frame"]) >= 8 and len(corner_360_samples) < 35:
                    box_att_count = sum(
                        1 for pt in ev["freeze_frame"]
                        if pt.get("is_target_team", False)
                        and not pt.get("keeper", False)
                        and not pt.get("actor", False)
                        and 102.0 <= pt.get("target_x", 60.0) <= 119.5
                        and 18.0 <= pt.get("target_y", 40.0) <= 62.0
                    )
                    if box_att_count >= 4:
                        corner_360_samples.append({
                            "event_id": ev["id"],
                            "match_id": mid,
                            "opponent": ev["opponent"],
                            "minute": ev["minute"],
                            "side": "Ofensivo",
                            "zone": zone,
                            "taker": get_player_clean_name(ev["player_name"]),
                            "start_x": ev["target_x"],
                            "start_y": ev["target_y"],
                            "end_x": ev["target_end_x"],
                            "end_y": ev["target_end_y"],
                            "att_in_6yd": att_in_6yd,
                            "def_in_6yd": def_in_6yd,
                            "led_to_shot": bool(led_to_shot),
                            "xg": round(seq_xg, 3),
                            "freeze_frame": ev["freeze_frame"],
                        })
            else:
                z_obj = def_zones[zone]
                z_obj["count"] += 1
                z_obj["shots_conceded"] += led_to_shot
                z_obj["xg_conceded"] = round(z_obj["xg_conceded"] + seq_xg, 3)
                z_obj["goals_conceded"] += seq_goals
                if has_ff:
                    z_obj["att_6yd_sum"] += att_in_6yd
                    z_obj["def_6yd_sum"] += def_in_6yd
                    z_obj["frames_360"] += 1

                # Para visualización en media cancha de recepción o en coordenadas del lanzador rival
                def_corner_deliveries.append({
                    "id": ev["id"],
                    "match_id": mid,
                    "opponent": ev["opponent"],
                    "minute": ev["minute"],
                    "zone": zone,
                    "start_x": sx,
                    "start_y": sy,
                    "end_x": ex,
                    "end_y": ey,
                    "led_to_shot": bool(led_to_shot),
                    "xg_conceded": round(seq_xg, 3),
                    "att_in_6yd": att_in_6yd,
                    "def_in_6yd": def_in_6yd,
                })

    # Formatear resúmenes por zona con promedios de sobrecarga 360 en el área chica
    off_summary = []
    tot_off_corners = sum(v["count"] for v in off_zones.values())
    tot_off_xg = sum(v["xg"] for v in off_zones.values())
    tot_off_shots = sum(v["shots"] for v in off_zones.values())

    for z_name, v in off_zones.items():
        n_f = max(1, v["frames_360"])
        c = v["count"]
        off_summary.append({
            "zone": z_name,
            "count": c,
            "share_pct": round((c / max(1, tot_off_corners)) * 100.0, 1),
            "shots_generated": v["shots"],
            "shot_conversion_pct": round((v["shots"] / max(1, c)) * 100.0, 1),
            "xg_total": round(v["xg"], 2),
            "goals": v["goals"],
            "avg_attackers_6yd": round(v["att_6yd_sum"] / n_f, 2),
            "avg_defenders_6yd": round(v["def_6yd_sum"] / n_f, 2),
            "overload_ratio_6yd": round(v["att_6yd_sum"] / max(1, v["def_6yd_sum"]), 2),
        })

    def_summary = []
    tot_def_corners = sum(v["count"] for v in def_zones.values())
    tot_def_xg = sum(v["xg_conceded"] for v in def_zones.values())
    tot_def_shots = sum(v["shots_conceded"] for v in def_zones.values())

    for z_name, v in def_zones.items():
        n_f = max(1, v["frames_360"])
        c = v["count"]
        def_summary.append({
            "zone": z_name,
            "count": c,
            "share_pct": round((c / max(1, tot_def_corners)) * 100.0, 1),
            "shots_conceded": v["shots_conceded"],
            "shot_conceded_pct": round((v["shots_conceded"] / max(1, c)) * 100.0, 1),
            "xg_conceded": round(v["xg_conceded"], 2),
            "goals_conceded": v["goals_conceded"],
            "avg_rival_attackers_6yd": round(v["att_6yd_sum"] / n_f, 2),
            "avg_own_defenders_6yd": round(v["def_6yd_sum"] / n_f, 2),
        })

    return {
        "kpis": {
            "offensive_corners_total": tot_off_corners,
            "offensive_corners_shots": tot_off_shots,
            "offensive_corners_xg": round(tot_off_xg, 2),
            "defensive_corners_total": tot_def_corners,
            "defensive_corners_shots_conceded": tot_def_shots,
            "defensive_corners_xg_conceded": round(tot_def_xg, 2),
            **free_kick_stats,
        },
        "offensive_by_zone": off_summary,
        "defensive_by_zone": def_summary,
        "offensive_deliveries": off_corner_deliveries[:80],
        "defensive_deliveries": def_corner_deliveries[:80],
        "corner_360_samples": corner_360_samples,
    }
