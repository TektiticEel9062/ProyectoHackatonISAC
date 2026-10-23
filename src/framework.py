"""
src/framework.py
Segmentador del Framework Analítico Formal:
1. Posesiones Válidas (Pases completados >= 3 OR Delta t >= 5.0s)
2. Fases de Presión (Tercio ofensivo X >= 80 OR <= 6s tras pérdida de balón)
3. Transiciones Defensiva -> Ofensiva / Contraataques (Recuperación X <= 60 -> Remate o X >= 80 en < 10s y <= 4 pases)
4. Estados de Partido (Game State: Winning, Drawing, Losing y bines de 15 min)
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict

from src.config import (
    POSSESSION_MIN_PASSES,
    POSSESSION_MIN_DURATION_SEC,
    HIGH_PRESS_X_THRESHOLD,
    COUNTERPRESS_WINDOW_SEC,
    PRESSURE_ACTION_TYPES,
    TRANSITION_ORIGIN_MAX_X,
    TRANSITION_END_MIN_X,
    TRANSITION_MAX_DURATION_SEC,
    TRANSITION_MAX_PASSES,
    get_player_clean_name,
)


def segment_framework_objects(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aplica las definiciones axiomáticas del Framework Analítico sobre la lista de eventos normalizados.
    Enriquece los eventos in-place con banderas formales y retorna el catálogo estructurado de objetos:
      - possessions: Lista de todas las posesiones con indicador is_valid_possession
      - valid_target_possessions: Posesiones válidas del target_team
      - pressure_events: Eventos de Fase de Presión del target_team (alta o tras pérdida <=6s)
      - transitions: Contraataques válidos del target_team
      - game_state_summary: Distribución de eventos y posesiones por Game State y ventana de 15m
    """
    # Agrupar eventos por (match_id, possession)
    poss_groups: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
    events_by_match: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    for ev in events:
        mid = ev["match_id"]
        pid = ev["possession"]
        poss_groups[(mid, pid)].append(ev)
        events_by_match[mid].append(ev)

    # 1. Detectar instantes de pérdida de balón del target_team por partido para el axioma de 6s
    loss_timestamps_by_match: Dict[int, List[float]] = defaultdict(list)
    for mid, m_evs in events_by_match.items():
        prev_target_poss = False
        for ev in m_evs:
            curr_target_poss = ev["is_target_possession"]
            # Si la posesión cambia de target_team al rival, o hay Dispossessed/Miscontrol/ pase fallido
            if prev_target_poss and not curr_target_poss:
                loss_timestamps_by_match[mid].append(ev["abs_seconds"])
            elif ev["is_target_team"] and ev["type"] in ("Dispossessed", "Miscontrol"):
                loss_timestamps_by_match[mid].append(ev["abs_seconds"])
            elif ev["is_target_team"] and ev["type"] == "Pass" and not ev["pass_completed"]:
                loss_timestamps_by_match[mid].append(ev["abs_seconds"])
            prev_target_poss = curr_target_poss

    # 2. Evaluar Fases de Presión (Axioma 5.2.2) sobre eventos defensivos del target_team
    pressure_events: List[Dict[str, Any]] = []
    for ev in events:
        is_press_phase = False
        press_subtype = None
        if ev["is_target_team"] and ev["type"] in PRESSURE_ACTION_TYPES:
            tx = ev["target_x"]
            # Condición A: Tercio ofensivo (X >= 80)
            in_high_zone = (tx is not None and tx >= HIGH_PRESS_X_THRESHOLD)
            # Condición B: Dentro de los primeros 6 segundos posteriores a una pérdida (contra-presión inmediata)
            t_ev = ev["abs_seconds"]
            losses = loss_timestamps_by_match.get(ev["match_id"], [])
            in_6s_window = bool(ev.get("counterpress")) or any(
                0.0 <= (t_ev - t_loss) <= COUNTERPRESS_WINDOW_SEC for t_loss in losses
            )

            if in_high_zone or in_6s_window:
                is_press_phase = True
                if in_high_zone and in_6s_window:
                    press_subtype = "High Counterpress"
                elif in_6s_window:
                    press_subtype = "Counterpress (<=6s)"
                else:
                    press_subtype = "High Press (X>=80)"
                pressure_events.append({
                    "event_id": ev["id"],
                    "match_id": ev["match_id"],
                    "minute": ev["minute"],
                    "second": ev["second"],
                    "type": ev["type"],
                    "subtype": press_subtype,
                    "player_name": ev["player_name"],
                    "x": tx,
                    "y": ev["target_y"],
                    "game_state": ev["game_state"],
                    "time_bin": ev["time_bin"],
                })

        ev["is_pressure_phase"] = is_press_phase
        ev["pressure_subtype"] = press_subtype

    # 3. Evaluar Posesiones (Axioma 5.2.1) y Transiciones Defensiva -> Ofensiva (Axioma 5.2.3)
    possessions: List[Dict[str, Any]] = []
    valid_target_possessions: List[Dict[str, Any]] = []
    transitions: List[Dict[str, Any]] = []

    for (mid, pid), p_evs in poss_groups.items():
        if not p_evs:
            continue
        is_target_poss = p_evs[0]["is_target_possession"]
        team_evs = [e for e in p_evs if e["is_target_team"] == is_target_poss]
        if not team_evs:
            team_evs = p_evs

        t_start = p_evs[0]["abs_seconds"]
        t_end = p_evs[-1]["abs_seconds"] + p_evs[-1].get("duration", 0.0)
        delta_t = max(0.0, round(t_end - t_start, 2))

        completed_passes = sum(
            1 for e in team_evs if e["type"] == "Pass" and e["pass_completed"]
        )
        total_passes = sum(1 for e in team_evs if e["type"] == "Pass")

        # Axioma 5.2.1: Pases completados >= 3 OR Delta t >= 5.0 segundos
        is_valid_poss = (completed_passes >= POSSESSION_MIN_PASSES) or (delta_t >= POSSESSION_MIN_DURATION_SEC)

        # Coordenadas de inicio y fin de la secuencia en referencia target_team
        coords_evs = [e for e in team_evs if e["target_x"] is not None and e["target_y"] is not None]
        start_x = coords_evs[0]["target_x"] if coords_evs else None
        start_y = coords_evs[0]["target_y"] if coords_evs else None

        last_ev = coords_evs[-1] if coords_evs else None
        end_x = (
            last_ev["target_end_x"]
            if (last_ev and last_ev["target_end_x"] is not None)
            else (last_ev["target_x"] if last_ev else None)
        )
        end_y = (
            last_ev["target_end_y"]
            if (last_ev and last_ev["target_end_y"] is not None)
            else (last_ev["target_y"] if last_ev else None)
        )

        max_x_reached = max(
            [
                max(e["target_x"] or 0.0, e["target_end_x"] or 0.0)
                for e in coords_evs
            ],
            default=0.0,
        )

        has_shot = any(e["type"] == "Shot" for e in team_evs)
        has_goal = any(e["is_goal"] for e in team_evs)
        seq_xg = round(sum(e["shot_xg"] for e in team_evs if e["type"] == "Shot"), 4)
        seq_obv = round(sum(e["obv_total_net"] for e in team_evs), 4)

        for e in p_evs:
            e["is_valid_possession"] = is_valid_poss

        poss_record = {
            "match_id": mid,
            "possession_id": pid,
            "is_target_possession": is_target_poss,
            "is_valid": is_valid_poss,
            "game_state": p_evs[0]["game_state"],
            "time_bin": p_evs[0]["time_bin"],
            "minute": p_evs[0]["minute"],
            "duration_sec": delta_t,
            "completed_passes": completed_passes,
            "total_passes": total_passes,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "max_x": round(max_x_reached, 2),
            "has_shot": has_shot,
            "has_goal": has_goal,
            "xg": seq_xg,
            "obv": seq_obv,
            "play_pattern": p_evs[0]["play_pattern"],
        }
        possessions.append(poss_record)
        if is_target_poss and is_valid_poss:
            valid_target_possessions.append(poss_record)

        # Evaluar Axioma 5.2.3: Transición Defensiva a Ofensiva (Contraataque) del target_team
        # Inicia con recuperación en campo propio (X <= 60) y culmina en remate o ingreso a X >= 80
        # en < 10 segundos y con <= 4 pases.
        if is_target_poss and coords_evs:
            first_ev = coords_evs[0]
            origin_x = first_ev["target_x"]
            # Excluir saques de banda, córners, tiros libres o saque de centro como "recuperación"
            is_open_recovery = first_ev["play_pattern"] in (
                "Regular Play",
                "From Counter",
                "From Keeper",
            ) and first_ev["type"] in (
                "Ball Recovery",
                "Interception",
                "Duel",
                "Pass",
                "Carry",
                "Ball Receipt*",
                "Block",
                "Clearance",
            )

            if is_open_recovery and origin_x is not None and origin_x <= TRANSITION_ORIGIN_MAX_X:
                # 1) Verificar si dentro de < 10s y <= 4 pases la secuencia ingresa a X >= 80 o genera un remate
                passes_to_entry = 0
                reached_transition = False
                entry_idx = -1

                for idx_ev, e in enumerate(team_evs):
                    dt_ev = e["abs_seconds"] - t_start
                    if dt_ev >= TRANSITION_MAX_DURATION_SEC:
                        break
                    if e["type"] == "Pass":
                        passes_to_entry += 1
                    if passes_to_entry > TRANSITION_MAX_PASSES:
                        break

                    ex = e["target_end_x"] if e["target_end_x"] is not None else e["target_x"]
                    if e["type"] == "Shot" or (ex is not None and ex >= TRANSITION_END_MIN_X) or (e["target_x"] is not None and e["target_x"] >= TRANSITION_END_MIN_X):
                        reached_transition = True
                        entry_idx = idx_ev
                        break

                if reached_transition and entry_idx >= 0:
                    # 2) Extender la trayectoria hasta el remate de contraataque (si ocurre en <= 15.0s desde la recuperación)
                    # o hasta el último toque en tercio ofensivo dentro de la ventana de <= 15.0s (evitando reciclajes atrás)
                    shot_indices = [
                        i for i, e in enumerate(team_evs)
                        if e["type"] == "Shot" and (e["abs_seconds"] - t_start) <= 15.0
                    ]
                    if shot_indices:
                        final_idx = shot_indices[-1]
                    else:
                        final_idx = entry_idx
                        for i in range(entry_idx + 1, len(team_evs)):
                            ev_next = team_evs[i]
                            if (ev_next["abs_seconds"] - t_start) > 15.0:
                                break
                            nx_start = ev_next["target_x"]
                            nx_end = ev_next["target_end_x"] if ev_next["target_end_x"] is not None else nx_start
                            # Detener si el balón recicla hacia atrás fuera del último tercio (X < 78.0)
                            if (nx_start is not None and nx_start < 78.0) or (nx_end is not None and nx_end < 78.0):
                                break
                            final_idx = i

                    culmination_ev = team_evs[final_idx]
                    path_points = [[round(origin_x, 2), round(first_ev["target_y"], 2)]]

                    def _add_path_pt(px, py):
                        if px is None or py is None:
                            return
                        rpt = [round(float(px), 2), round(float(py), 2)]
                        if not path_points or (abs(path_points[-1][0] - rpt[0]) > 0.2 or abs(path_points[-1][1] - rpt[1]) > 0.2):
                            path_points.append(rpt)

                    total_trans_passes = 0
                    trans_evs = team_evs[: final_idx + 1]
                    for e in trans_evs:
                        if e["type"] == "Pass":
                            total_trans_passes += 1
                        _add_path_pt(e["target_x"], e["target_y"])
                        # Si el evento final es un Shot, terminar el path en la ubicación del disparo (target_x, target_y)
                        # para que coincida exactamente con shots_map
                        if e is culmination_ev and e["type"] == "Shot":
                            break
                        ex = e["target_end_x"] if e["target_end_x"] is not None else e["target_x"]
                        ey = e["target_end_y"] if e["target_end_y"] is not None else e["target_y"]
                        if e is culmination_ev and ex is not None and ex < 78.0:
                            break
                        _add_path_pt(ex, ey)

                    trans_has_shot = any(e["type"] == "Shot" for e in trans_evs)
                    trans_has_goal = any(e["is_goal"] for e in trans_evs)
                    trans_xg = round(sum(e["shot_xg"] for e in trans_evs if e["type"] == "Shot"), 4)
                    trans_obv = round(sum(e["obv_total_net"] for e in trans_evs), 4)

                    if len(path_points) >= 2 and path_points[-1][0] >= 78.0:
                        trans_dt = round(min(15.0, max(0.5, culmination_ev["abs_seconds"] - t_start)), 2)
                        transitions.append({
                            "match_id": mid,
                            "possession_id": pid,
                            "minute": culmination_ev["minute"] if culmination_ev["type"] == "Shot" else first_ev["minute"],
                            "second": culmination_ev["second"] if culmination_ev["type"] == "Shot" else first_ev["second"],
                            "game_state": first_ev["game_state"],
                            "time_bin": first_ev["time_bin"],
                            "origin_x": path_points[0][0],
                            "origin_y": path_points[0][1],
                            "end_x": path_points[-1][0],
                            "end_y": path_points[-1][1],
                            "duration_sec": trans_dt,
                            "passes_count": passes_to_entry,
                            "total_passes_in_sequence": total_trans_passes,
                            "ended_in_shot": trans_has_shot,
                            "ended_in_goal": trans_has_goal,
                            "xg": trans_xg,
                            "obv": trans_obv,
                            "initiator": get_player_clean_name(first_ev["player_name"]),
                            "finisher": get_player_clean_name(culmination_ev["player_name"]),
                            "path": path_points,
                        })

    # 4. Resumen por Game State y Segmentación Temporal (Axioma 5.2.4)
    gs_counts: Dict[str, Dict[str, Any]] = {
        "Winning": {"events": 0, "valid_possessions": 0, "pressure_actions": 0, "transitions": 0, "xg_for": 0.0, "xg_against": 0.0},
        "Drawing": {"events": 0, "valid_possessions": 0, "pressure_actions": 0, "transitions": 0, "xg_for": 0.0, "xg_against": 0.0},
        "Losing": {"events": 0, "valid_possessions": 0, "pressure_actions": 0, "transitions": 0, "xg_for": 0.0, "xg_against": 0.0},
    }
    time_bin_counts: Dict[str, Dict[str, Any]] = {
        tb: {"events": 0, "valid_possessions": 0, "pressure_actions": 0, "transitions": 0, "xg_for": 0.0, "xg_against": 0.0}
        for tb in ("0-15", "15-30", "30-45", "45-60", "60-75", "75+")
    }

    for ev in events:
        gs = ev["game_state"]
        tb = ev["time_bin"]
        if ev["is_target_team"]:
            gs_counts[gs]["events"] += 1
            time_bin_counts[tb]["events"] += 1
            if ev["type"] == "Shot":
                gs_counts[gs]["xg_for"] = round(gs_counts[gs]["xg_for"] + ev["shot_xg"], 3)
                time_bin_counts[tb]["xg_for"] = round(time_bin_counts[tb]["xg_for"] + ev["shot_xg"], 3)
        else:
            if ev["type"] == "Shot":
                gs_counts[gs]["xg_against"] = round(gs_counts[gs]["xg_against"] + ev["shot_xg"], 3)
                time_bin_counts[tb]["xg_against"] = round(time_bin_counts[tb]["xg_against"] + ev["shot_xg"], 3)

    for vp in valid_target_possessions:
        gs_counts[vp["game_state"]]["valid_possessions"] += 1
        time_bin_counts[vp["time_bin"]]["valid_possessions"] += 1

    for pe in pressure_events:
        gs_counts[pe["game_state"]]["pressure_actions"] += 1
        time_bin_counts[pe["time_bin"]]["pressure_actions"] += 1

    for tr in transitions:
        gs_counts[tr["game_state"]]["transitions"] += 1
        time_bin_counts[tr["time_bin"]]["transitions"] += 1

    return {
        "possessions": possessions,
        "valid_target_possessions": valid_target_possessions,
        "pressure_events": pressure_events,
        "transitions": transitions,
        "game_state_summary": gs_counts,
        "time_bin_summary": time_bin_counts,
    }
