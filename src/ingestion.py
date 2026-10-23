"""
src/ingestion.py
Parser y normalizador de eventos de StatsBomb + instantáneas espaciales 360 (freeze_frames).
Estandariza coordenadas (X in [0,120], Y in [0,80]) con dirección de ataque del target_team -> X=120,
calcula Game State (Ganando, Empatando, Perdiendo) y enlaza freeze_frames por event_uuid.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from src.config import (
    DATA_RAW_DIR,
    PITCH_LENGTH,
    PITCH_WIDTH,
    TIME_BINS,
)


def parse_timestamp_seconds(ts_str: Optional[str], period: int = 1, minute: int = 0, second: int = 0) -> float:
    """Convierte timestamp HH:MM:SS.mmm de StatsBomb a segundos acumulados del partido."""
    base_offset = 0.0
    if period == 2:
        base_offset = 45.0 * 60.0
    elif period == 3:
        base_offset = 90.0 * 60.0
    elif period == 4:
        base_offset = 105.0 * 60.0

    if not ts_str:
        return float(minute * 60 + second)

    try:
        parts = ts_str.split(":")
        h = float(parts[0])
        m = float(parts[1])
        s = float(parts[2])
        return base_offset + (h * 3600.0 + m * 60.0 + s)
    except Exception:
        return float(minute * 60 + second)


def get_time_bin(minute: int, period: int) -> str:
    """Retorna el intervalo temporal de 15 minutos según el axioma 5.2.4."""
    if period == 1 and minute >= 45:
        return "30-45"
    for low, high, label in TIME_BINS:
        if low <= minute < high:
            return label
    return "75+"


def clamp_coords(x: Optional[float], y: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if x is None or y is None:
        return None, None
    cx = max(0.0, min(PITCH_LENGTH, float(x)))
    cy = max(0.0, min(PITCH_WIDTH, float(y)))
    return cx, cy


def load_and_normalize_all_matches(
    manifest: Dict[str, Any],
    raw_dir: Path = DATA_RAW_DIR,
) -> Tuple[List[Dict[str, Any]], Dict[int, List[Dict[str, Any]]]]:
    """
    Carga y normaliza todos los eventos, lineups y 360 freeze_frames de los partidos en manifest.
    Retorna:
      - normalized_events: Lista plana de eventos enriquecidos y normalizados.
      - lineups_by_match: Diccionario {match_id: lineup_list}.
    """
    target_team = manifest["target_team"]
    events_dir = raw_dir / "events"
    lineups_dir = raw_dir / "lineups"
    threesixty_dir = raw_dir / "three-sixty"

    normalized_events: List[Dict[str, Any]] = []
    lineups_by_match: Dict[int, List[Dict[str, Any]]] = {}

    for m_info in manifest.get("matches", []):
        mid = m_info["match_id"]
        is_home = m_info["is_home"]
        opponent = m_info["opponent"]
        match_date = m_info["match_date"]

        lu_path = lineups_dir / f"{mid}.json"
        if lu_path.exists():
            lineups_by_match[mid] = json.loads(lu_path.read_text(encoding="utf-8"))

        ts_map: Dict[str, Dict[str, Any]] = {}
        ts_path = threesixty_dir / f"{mid}.json"
        if ts_path.exists():
            raw_frames = json.loads(ts_path.read_text(encoding="utf-8"))
            for fr in raw_frames:
                uuid = fr.get("event_uuid") or fr.get("id")
                if uuid:
                    ts_map[uuid] = fr

        ev_path = events_dir / f"{mid}.json"
        if not ev_path.exists():
            continue

        raw_events = json.loads(ev_path.read_text(encoding="utf-8"))

        # Seguimiento dinámico del marcador (Game State)
        goals_for = 0
        goals_against = 0

        for ev in raw_events:
            eid = ev.get("id")
            ev_type = (ev.get("type") or {}).get("name", "Unknown")
            team_name = (ev.get("team") or {}).get("name", "Unknown")
            poss_team_name = (ev.get("possession_team") or {}).get("name", "Unknown")
            is_target = (team_name == target_team)
            is_target_possession = (poss_team_name == target_team)

            period = int(ev.get("period", 1))
            minute = int(ev.get("minute", 0))
            second = int(ev.get("second", 0))
            abs_sec = parse_timestamp_seconds(ev.get("timestamp"), period, minute, second)
            duration = float(ev.get("duration") or 0.0)

            # Game state antes del evento
            goal_diff = goals_for - goals_against
            if goal_diff > 0:
                game_state = "Winning"
            elif goal_diff < 0:
                game_state = "Losing"
            else:
                game_state = "Drawing"

            # Coordenadas originales (relativas al equipo actor del evento)
            loc = ev.get("location")
            raw_x, raw_y = (loc[0], loc[1]) if (isinstance(loc, list) and len(loc) >= 2) else (None, None)
            x, y = clamp_coords(raw_x, raw_y)

            # Coordenadas de destino (pase, conducción o disparo)
            end_x, end_y = None, None
            pass_obj = ev.get("pass") or {}
            carry_obj = ev.get("carry") or {}
            shot_obj = ev.get("shot") or {}

            if "end_location" in pass_obj and len(pass_obj["end_location"]) >= 2:
                end_x, end_y = clamp_coords(pass_obj["end_location"][0], pass_obj["end_location"][1])
            elif "end_location" in carry_obj and len(carry_obj["end_location"]) >= 2:
                end_x, end_y = clamp_coords(carry_obj["end_location"][0], carry_obj["end_location"][1])
            elif "end_location" in shot_obj and len(shot_obj["end_location"]) >= 2:
                end_x, end_y = clamp_coords(shot_obj["end_location"][0], shot_obj["end_location"][1])

            # Coordenadas estandarizadas a la dirección de ataque del target_team (X -> 120)
            if x is not None and y is not None:
                target_x = x if is_target else round(PITCH_LENGTH - x, 2)
                target_y = y if is_target else round(PITCH_WIDTH - y, 2)
            else:
                target_x, target_y = None, None

            if end_x is not None and end_y is not None:
                target_end_x = end_x if is_target else round(PITCH_LENGTH - end_x, 2)
                target_end_y = end_y if is_target else round(PITCH_WIDTH - end_y, 2)
            else:
                target_end_x, target_end_y = None, None

            # Enlace con 360 freeze_frame y normalización espacial a referencia target_team
            frame_360 = ts_map.get(eid)
            norm_freeze_frame = None
            norm_visible_area = None
            line_breaking_pass_360 = False
            dist_nearest_def_360 = None
            defenders_goal_side_360 = None
            receipt_in_space_360 = False

            if frame_360:
                line_breaking_pass_360 = bool(frame_360.get("line_breaking_pass", False))
                dist_nearest_def_360 = frame_360.get("distance_to_nearest_defender")
                defenders_goal_side_360 = frame_360.get("num_defenders_on_goal_side_of_actor")
                receipt_in_space_360 = bool(frame_360.get("ball_receipt_in_space", False))

                raw_ff = frame_360.get("freeze_frame") or []
                norm_freeze_frame = []
                for pt in raw_ff:
                    ploc = pt.get("location")
                    if not isinstance(ploc, list) or len(ploc) < 2:
                        continue
                    px, py = clamp_coords(ploc[0], ploc[1])
                    if px is None or py is None:
                        continue
                    # En StatsBomb 360, 'teammate' indica compañero del actor del evento
                    teammate_of_actor = bool(pt.get("teammate", False))
                    is_target_player = teammate_of_actor if is_target else (not teammate_of_actor)
                    tx = px if is_target else round(PITCH_LENGTH - px, 2)
                    ty = py if is_target else round(PITCH_WIDTH - py, 2)
                    norm_freeze_frame.append({
                        "x": round(px, 2),
                        "y": round(py, 2),
                        "target_x": tx,
                        "target_y": ty,
                        "teammate": teammate_of_actor,
                        "is_target_team": is_target_player,
                        "actor": bool(pt.get("actor", False)),
                        "keeper": bool(pt.get("keeper", False)),
                    })

                raw_va = frame_360.get("visible_area") or []
                if len(raw_va) >= 6:
                    norm_visible_area = []
                    for i in range(0, len(raw_va) - 1, 2):
                        vx, vy = clamp_coords(raw_va[i], raw_va[i + 1])
                        if vx is not None and vy is not None:
                            tvx = vx if is_target else round(PITCH_LENGTH - vx, 2)
                            tvy = vy if is_target else round(PITCH_WIDTH - vy, 2)
                            norm_visible_area.append([tvx, tvy])

            # Extraer atributos clave de pase / disparo / tácticos
            player_obj = ev.get("player") or {}
            position_obj = ev.get("position") or {}
            play_pattern = (ev.get("play_pattern") or {}).get("name", "Regular Play")

            pass_outcome = (pass_obj.get("outcome") or {}).get("name")  # None = completado en StatsBomb
            pass_completed = (ev_type == "Pass") and (pass_outcome is None)
            pass_recipient = (pass_obj.get("recipient") or {}).get("name")
            pass_recipient_id = (pass_obj.get("recipient") or {}).get("id")
            pass_type = (pass_obj.get("type") or {}).get("name")
            pass_height = (pass_obj.get("height") or {}).get("name")
            pass_length = pass_obj.get("length")
            pass_angle = pass_obj.get("angle")
            is_through_ball = bool(pass_obj.get("through_ball") or (pass_obj.get("technique") or {}).get("name") == "Through Ball")
            is_cross = bool(pass_obj.get("cross", False))
            is_switch = bool(pass_obj.get("switch", False))

            shot_xg = float(shot_obj.get("statsbomb_xg") or ev.get("shot_statsbomb_xg") or 0.0)
            shot_outcome = (shot_obj.get("outcome") or {}).get("name")
            is_goal = (ev_type == "Shot" and shot_outcome == "Goal") or (ev_type == "Own Goal For")
            is_own_goal_against = (ev_type == "Own Goal Against")

            obv_total_net = float(ev.get("obv_total_net") or 0.0)
            obv_for_net = float(ev.get("obv_for_net") or 0.0)
            obv_against_net = float(ev.get("obv_against_net") or 0.0)

            tactics_obj = ev.get("tactics") or {}
            formation = tactics_obj.get("formation")
            tactics_lineup = tactics_obj.get("lineup")

            sub_obj = ev.get("substitution") or {}
            sub_replacement = (sub_obj.get("replacement") or {}).get("name")
            sub_replacement_id = (sub_obj.get("replacement") or {}).get("id")

            duel_obj = ev.get("duel") or {}
            duel_type = (duel_obj.get("type") or {}).get("name")
            duel_outcome = (duel_obj.get("outcome") or {}).get("name")

            under_pressure = bool(ev.get("under_pressure", False))
            counterpress = bool(ev.get("counterpress", False))

            norm_ev = {
                "id": eid,
                "match_id": mid,
                "match_date": match_date,
                "is_home": is_home,
                "opponent": opponent,
                "index": ev.get("index", 0),
                "period": period,
                "minute": minute,
                "second": second,
                "abs_seconds": round(abs_sec, 2),
                "duration": round(duration, 2),
                "time_bin": get_time_bin(minute, period),
                "type": ev_type,
                "play_pattern": play_pattern,
                "team": team_name,
                "is_target_team": is_target,
                "possession": int(ev.get("possession", 0)),
                "possession_team": poss_team_name,
                "is_target_possession": is_target_possession,
                "player_id": player_obj.get("id"),
                "player_name": player_obj.get("name"),
                "position_name": position_obj.get("name"),
                "goals_for": goals_for,
                "goals_against": goals_against,
                "goal_diff": goal_diff,
                "game_state": game_state,
                "x": x,
                "y": y,
                "end_x": end_x,
                "end_y": end_y,
                "target_x": target_x,
                "target_y": target_y,
                "target_end_x": target_end_x,
                "target_end_y": target_end_y,
                "under_pressure": under_pressure,
                "counterpress": counterpress,
                "obv_total_net": round(obv_total_net, 5),
                "obv_for_net": round(obv_for_net, 5),
                "obv_against_net": round(obv_against_net, 5),
                "pass_completed": pass_completed,
                "pass_outcome": pass_outcome,
                "pass_recipient": pass_recipient,
                "pass_recipient_id": pass_recipient_id,
                "pass_type": pass_type,
                "pass_height": pass_height,
                "pass_length": pass_length,
                "pass_angle": pass_angle,
                "is_through_ball": is_through_ball,
                "is_cross": is_cross,
                "is_switch": is_switch,
                "shot_xg": round(shot_xg, 5),
                "shot_outcome": shot_outcome,
                "is_goal": is_goal,
                "formation": formation,
                "tactics_lineup": tactics_lineup,
                "sub_replacement": sub_replacement,
                "sub_replacement_id": sub_replacement_id,
                "duel_type": duel_type,
                "duel_outcome": duel_outcome,
                "has_360": frame_360 is not None,
                "freeze_frame": norm_freeze_frame,
                "visible_area": norm_visible_area,
                "line_breaking_pass_360": line_breaking_pass_360,
                "dist_nearest_def_360": dist_nearest_def_360,
                "defenders_goal_side_360": defenders_goal_side_360,
                "receipt_in_space_360": receipt_in_space_360,
            }

            normalized_events.append(norm_ev)

            # Actualizar marcador después de registrar el evento
            if ev_type == "Shot" and shot_outcome == "Goal":
                if is_target:
                    goals_for += 1
                else:
                    goals_against += 1
            elif is_own_goal_against:
                if is_target:
                    goals_against += 1
                else:
                    goals_for += 1

    return normalized_events, lineups_by_match
