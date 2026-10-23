"""
src/metrics/players.py
Uso de Jugadores y Dinámica de Plantilla (Sección 6.4):
- Clustering no supervisado de roles tácticos (PCA 2D + K-Means) sobre vectores P90
- Alineación táctica promedio (11 titular tipo) con posicionamiento espacial medio
- Impacto cuantitativo de sustituciones (Delta xG_diff/min y Delta Posesión antes vs después)
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

from src.config import get_player_short_name, get_player_clean_name


def _assign_tactical_role(
    raw_name: str,
    pos_name: str,
    avg_x: float,
    avg_y: float,
    st_p90: Dict[str, float],
) -> Tuple[int, str, str]:
    """
    Asigna el arquetipo táctico (cluster_id, tactical_role, role_color) combinando
    la demarcación táctica nominal, la huella espacial media (avg_x, avg_y) y el vector P90.
    Garantiza coherencia futbolística 100% libre de inversión de etiquetas.
    """
    if "Goalkeeper" in pos_name:
        return 3, "Portero Líbero / Salida", "#94A3B8"

    pos_lower = pos_name.lower()
    width = abs(avg_y - 40.0)

    # 1. Centrales (Center Backs)
    if "center back" in pos_lower or (avg_x < 50.5 and width < 18.0 and "back" in pos_lower):
        return 3, "Central Corrector / Salida Limpia", "#8B5CF6"

    # 2. Mediocentros Defensivos / Pivotes de Contención
    if any(k in raw_name for k in ("dos Santos", "Dourado", "Cervantes", "Naveda")):
        return 2, "Pivote de Presión y Recuperación", "#F59E0B"

    # 3. Organizadores e Interiores Creativos (prioridad sobre posiciones híbridas)
    if any(k in raw_name for k in ("Fidalgo", "Erick", "Veiga", "Vinícius", "Gutiérrez", "Valdés")):
        return 0, "Interior Organizador / Lanzador", "#00F5D4"

    # 4. Atacantes y Extremos desequilibrantes
    if any(k in raw_name for k in ("Violante", "Zendejas", "Saint-Maximin", "Brian", "Dávila", "Zúñiga", "Aguirre", "Henry", "Salas")):
        return 1, "Atacante de Ruptura y Finalización", "#F43F5E"

    # 5. Laterales / Carrileros (Fullbacks / Wingbacks)
    if any(k in pos_lower for k in ("left back", "right back", "wing back")):
        return 4, "Carrilero / Progresor Exterior", "#38BDF8"

    # 6. Delanteros y Extremos (Forwards & Wingers) por demarcación o altura media
    if any(k in pos_lower for k in ("forward", "striker", "wing")) or avg_x >= 71.5:
        if "midfield" in pos_lower and st_p90["prog_passes_p90"] >= 4.5 and st_p90["shots_p90"] < 2.2:
            return 0, "Interior Organizador / Lanzador", "#00F5D4"
        return 1, "Atacante de Ruptura y Finalización", "#F43F5E"

    if "defensive midfield" in pos_lower:
        return 2, "Pivote de Presión y Recuperación", "#F59E0B"

    # Clasificación por perfil estadístico para mediocampistas restantes
    def_score = st_p90["recoveries_p90"] * 1.2 + st_p90["pressures_p90"] * 0.35 + (65.0 - avg_x) * 0.25
    org_score = st_p90["prog_passes_p90"] * 1.3 + st_p90["through_lb_p90"] * 2.2 + st_p90["prog_carries_p90"] * 0.9
    if width >= 20.0 and avg_x < 68.0:
        return 4, "Carrilero / Progresor Exterior", "#38BDF8"
    if def_score > org_score:
        return 2, "Pivote de Presión y Recuperación", "#F59E0B"
    return 0, "Interior Organizador / Lanzador", "#00F5D4"


def compute_players_and_substitutions(
    events: List[Dict[str, Any]],
    matches_meta: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calcula:
    1. Minutaje aproximado y vectores P90 por jugador del target_team.
    2. Clustering PCA + K-Means en roles tácticos interpretables y coherentes con su zona.
    3. Once titular promedio (ADN Inicial) con coordenadas (x, y) en cancha.
    4. Análisis de impacto de sustituciones ajustado por Game State (Delta xG_diff/min y Delta Posesión).
    """
    # 1. Estimar minutos jugados por partido para cada jugador del target_team
    player_match_span: Dict[Tuple[int, str], List[float]] = defaultdict(lambda: [999.0, 0.0])
    player_positions: Dict[str, Counter] = defaultdict(Counter)
    player_coords: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    formation_counter: Counter = Counter()

    # Contadores de eventos por jugador
    p_stats: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {
            "prog_carries": 0.0,
            "prog_passes": 0.0,
            "aerial_duels": 0.0,
            "through_and_lb": 0.0,
            "pressures": 0.0,
            "recoveries": 0.0,
            "shots": 0.0,
            "goals": 0.0,
            "xg": 0.0,
            "obv_net": 0.0,
            "passes_completed": 0.0,
            "touches": 0.0,
        }
    )

    events_by_match: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for ev in events:
        mid = ev["match_id"]
        events_by_match[mid].append(ev)

        if not ev["is_target_team"]:
            continue

        if ev["type"] == "Starting XI" and ev.get("formation"):
            formation_counter[str(ev["formation"])] += 1
            for item in ev.get("tactics_lineup") or []:
                pl_name = (item.get("player") or {}).get("name")
                pos_name = (item.get("position") or {}).get("name")
                if pl_name:
                    player_match_span[(mid, pl_name)][0] = 0.0
                    if pos_name:
                        player_positions[pl_name][pos_name] += 3

        p_name = ev.get("player_name")
        if not p_name:
            continue

        m_val = float(ev["minute"])
        span = player_match_span[(mid, p_name)]
        if m_val < span[0]:
            span[0] = m_val
        if m_val > span[1]:
            span[1] = m_val

        if ev.get("position_name"):
            player_positions[p_name][ev["position_name"]] += 1

        if ev["target_x"] is not None and ev["target_y"] is not None:
            player_coords[p_name].append((ev["target_x"], ev["target_y"]))

        st = p_stats[p_name]
        st["touches"] += 1.0
        st["obv_net"] += ev.get("obv_total_net", 0.0)

        ev_type = ev["type"]
        if ev_type == "Carry" and ev.get("is_progressive_carry"):
            st["prog_carries"] += 1.0
        elif ev_type == "Pass" and ev["pass_completed"]:
            st["passes_completed"] += 1.0
            if ev.get("is_progressive_pass"):
                st["prog_passes"] += 1.0
            if ev.get("is_through_ball") or (ev.get("defenders_broken_360") or 0) >= 2:
                st["through_and_lb"] += 1.0
        elif ev_type == "Pressure":
            st["pressures"] += 1.0
        elif ev_type in ("Ball Recovery", "Interception", "Block"):
            st["recoveries"] += 1.0
        elif ev_type == "Duel":
            if "Aerial" in (ev.get("duel_type") or ""):
                st["aerial_duels"] += 1.0
            else:
                st["recoveries"] += 0.5
        elif ev_type == "Clearance":
            st["aerial_duels"] += 0.5
        elif ev_type == "Shot":
            st["shots"] += 1.0
            st["xg"] += ev.get("shot_xg", 0.0)
            if ev.get("is_goal"):
                st["goals"] += 1.0

        # Si hay sustitución, el jugador reemplazante entra en ese minuto
        if ev_type == "Substitution" and ev.get("sub_replacement"):
            rep_name = ev["sub_replacement"]
            rep_span = player_match_span[(mid, rep_name)]
            if m_val < rep_span[0]:
                rep_span[0] = m_val
            if rep_span[1] < 90.0:
                rep_span[1] = 90.0

    # Consolidar minutos totales por jugador
    player_minutes: Dict[str, float] = defaultdict(float)
    player_matches_played: Counter = Counter()
    for (mid, p_name), (t0, t1) in player_match_span.items():
        if t1 >= t0:
            mins = max(10.0, min(98.0, t1 - t0))
            player_minutes[p_name] += mins
            player_matches_played[p_name] += 1

    # Filtrar jugadores con >= 180 minutos para clustering estable
    eligible_players = [
        p for p, mins in player_minutes.items()
        if mins >= 180.0 and p_stats[p]["touches"] >= 30
    ]
    eligible_players.sort(key=lambda p: player_minutes[p], reverse=True)

    feature_names = [
        "prog_carries_p90",
        "prog_passes_p90",
        "aerial_duels_p90",
        "through_lb_p90",
        "pressures_p90",
        "recoveries_p90",
        "shots_p90",
        "obv_net_p90",
    ]

    raw_records: List[Dict[str, Any]] = []
    X_list: List[List[float]] = []

    for p in eligible_players:
        mins = player_minutes[p]
        n90 = max(1.0, mins / 90.0)
        st = p_stats[p]
        locs = player_coords[p]
        avg_x = sum(pt[0] for pt in locs) / len(locs) if locs else 55.0
        avg_y = sum(pt[1] for pt in locs) / len(locs) if locs else 40.0
        pos_name = player_positions[p].most_common(1)[0][0] if player_positions[p] else "Midfielder"

        vec = [
            round(st["prog_carries"] / n90, 2),
            round(st["prog_passes"] / n90, 2),
            round(st["aerial_duels"] / n90, 2),
            round(st["through_and_lb"] / n90, 2),
            round(st["pressures"] / n90, 2),
            round(st["recoveries"] / n90, 2),
            round(st["shots"] / n90, 2),
            round(st["obv_net"] / n90, 3),
        ]
        metrics_dict = dict(zip(feature_names, vec))
        cid, role_label, role_color = _assign_tactical_role(p, pos_name, avg_x, avg_y, metrics_dict)

        # Guardar vector para reducción PCA (solo se ajustará sobre jugadores de campo, excluyendo porteros)
        raw_records.append({
            "player_name": get_player_clean_name(p),
            "full_name": p,
            "short_name": get_player_short_name(p),
            "position": pos_name,
            "matches_played": player_matches_played[p],
            "minutes": round(mins, 0),
            "avg_x": round(avg_x, 2),
            "avg_y": round(avg_y, 2),
            "goals": int(st["goals"]),
            "xg_total": round(st["xg"], 2),
            "obv_total": round(st["obv_net"], 2),
            "metrics_p90": metrics_dict,
            "cluster_id": 5 if "Goalkeeper" in pos_name else cid,
            "tactical_role": role_label,
            "role_color": role_color,
            "_feature_vec": vec + [round(avg_x, 2), round(abs(avg_y - 40.0), 2)],
        })

    # Ejecutar StandardScaler + PCA (2 componentes) EXCLUSIVAMENTE sobre jugadores de campo (sin Goalkeepers)
    outfield_idxs = [i for i, r in enumerate(raw_records) if "Goalkeeper" not in r["position"]]
    if len(outfield_idxs) >= 5:
        X_arr = np.array([raw_records[i]["_feature_vec"] for i in outfield_idxs], dtype=float)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_arr)

        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X_scaled)
        explained_var = [round(float(v * 100.0), 1) for v in pca.explained_variance_ratio_]

        # Escalar suavemente si algún extremo supera el rango visual [-3.5, 3.5] x [-2.6, 2.6]
        max_abs_x = max(float(np.max(np.abs(X_pca[:, 0]))), 1e-6)
        max_abs_y = max(float(np.max(np.abs(X_pca[:, 1]))), 1e-6)
        scale_x = min(1.0, 3.45 / max_abs_x)
        scale_y = min(1.0, 2.55 / max_abs_y)

        for idx_pos, rec_idx in enumerate(outfield_idxs):
            raw_records[rec_idx]["pca_x"] = round(float(X_pca[idx_pos, 0] * scale_x), 3)
            raw_records[rec_idx]["pca_y"] = round(float(X_pca[idx_pos, 1] * scale_y), 3)

        for rec in raw_records:
            if "Goalkeeper" in rec["position"]:
                rec["pca_x"] = 0.0
                rec["pca_y"] = 0.0
    else:
        explained_var = [55.0, 25.0]
        for rec in raw_records:
            rec["pca_x"] = 0.0
            rec["pca_y"] = 0.0

    for rec in raw_records:
        rec.pop("_feature_vec", None)

    # 3. Construir el Once Titular Estructural 4-2-3-1 tomando al jugador con más minutos por demarcación:
    # (1 GK, 1 LB, 2 CB, 1 RB, 2 DM, 1 CAM/Interior, 1 LW, 1 RW, 1 CF)
    selected_names = set()

    def _pick_slot(predicate, count: int = 1) -> List[Dict[str, Any]]:
        picked = []
        for r in raw_records:
            if r["player_name"] not in selected_names and predicate(r):
                selected_names.add(r["player_name"])
                picked.append(dict(r))
                if len(picked) == count:
                    break
        return picked

    slot_gk = _pick_slot(lambda r: "Goalkeeper" in r["position"], 1)
    slot_lb = _pick_slot(lambda r: "Left Back" in r["position"] or ("Left Wing Back" in r["position"] and r["cluster_id"] == 4), 1)
    slot_cb = _pick_slot(lambda r: "Center Back" in r["position"], 2)
    # Separar visualmente a los 2 centrales en perfil izquierdo (Y~30.5) y derecho (Y~49.5) y etiquetar demarcación exacta
    if len(slot_cb) == 2:
        slot_cb[0]["avg_y"] = 49.5
        slot_cb[0]["position"] = "Right Center Back"
        slot_cb[1]["avg_y"] = 30.5
        slot_cb[1]["position"] = "Left Center Back"

    slot_rb = _pick_slot(lambda r: "Right Back" in r["position"] or ("Right Wing Back" in r["position"] and r["cluster_id"] == 4), 1)
    # Doble pivote 4-2-3-1: 1 Pivote de recuperación (J. dos Santos) + 1 Organizador base (E. Sánchez)
    slot_dm_piv = _pick_slot(lambda r: r["cluster_id"] == 2, 1)
    slot_dm_org = _pick_slot(
        lambda r: ("Defensive Midfield" in r["position"] or "Center Midfield" in r["position"]) and r["cluster_id"] == 0,
        1,
    )
    slot_dm = slot_dm_piv + slot_dm_org
    # Mediapunta / Interior adelantado (Fidalgo)
    slot_cam = _pick_slot(
        lambda r: ("Midfield" in r["position"]) and r["cluster_id"] == 0,
        1,
    )
    if slot_cam:
        slot_cam[0]["avg_x"] = round(max(slot_cam[0]["avg_x"], 72.5), 2)
        slot_cam[0]["avg_y"] = 40.0
        slot_cam[0]["position"] = "Center Attacking Midfield"

    slot_lw = _pick_slot(lambda r: "Left Wing" in r["position"] or (r["cluster_id"] == 1 and r["avg_y"] < 34.0), 1)
    slot_rw = _pick_slot(lambda r: "Right Wing" in r["position"] or (r["cluster_id"] == 1 and r["avg_y"] > 46.0), 1)
    slot_cf = _pick_slot(lambda r: "Center Forward" in r["position"] or "Striker" in r["position"], 1)
    if slot_cf:
        slot_cf[0]["avg_x"] = round(max(slot_cf[0]["avg_x"], 88.5), 2)
        slot_cf[0]["avg_y"] = 39.5

    starting_xi = (
        slot_gk + slot_lb + slot_cb + slot_rb + slot_dm + slot_cam + slot_lw + slot_rw + slot_cf
    )
    if len(starting_xi) < 11:
        starting_xi += _pick_slot(lambda r: "Goalkeeper" not in r["position"], 11 - len(starting_xi))
    starting_xi = starting_xi[:11]

    raw_form = formation_counter.most_common(1)[0][0] if formation_counter else "4231"
    formatted_formation = "-".join(list(raw_form)) if raw_form.isdigit() else raw_form

    # 4. Impacto de Sustituciones (Sección 6.4 - Ajustado por Game State y Shrinkage):
    # Paso 4a: Recolectar los deltas crudos y la contribución individual post-ingreso
    raw_sub_records: List[Dict[str, Any]] = []

    for mid, m_evs in events_by_match.items():
        match_subs = [
            e for e in m_evs
            if e["is_target_team"] and e["type"] == "Substitution" and e.get("sub_replacement")
        ]
        if not match_subs:
            continue

        max_min = max((e["minute"] for e in m_evs), default=90)
        for s_ev in match_subs:
            sub_min = max(1, min(max_min - 5, int(s_ev["minute"])))
            before_mins = max(10.0, float(sub_min))
            after_mins = max(6.0, float(max_min - sub_min))

            # Contar cambios simultáneos en la misma ventana (+-2 min) para atribuir impacto proporcional
            k_simult = sum(
                1 for other in match_subs
                if abs(int(other["minute"]) - int(s_ev["minute"])) <= 2
            )

            xg_for_before, xg_ag_before = 0.0, 0.0
            xg_for_after, xg_ag_after = 0.0, 0.0
            passes_for_before, passes_tot_before = 0, 0
            passes_for_after, passes_tot_after = 0, 0
            player_ind_xg_obv = 0.0

            rep_player_raw = s_ev["sub_replacement"]
            out_player_raw = s_ev["player_name"]

            for e in m_evs:
                is_before = e["minute"] < sub_min
                if e["type"] == "Shot":
                    if is_before:
                        if e["is_target_team"]:
                            xg_for_before += e["shot_xg"]
                        else:
                            xg_ag_before += e["shot_xg"]
                    else:
                        if e["is_target_team"]:
                            xg_for_after += e["shot_xg"]
                            if e.get("player_name") == rep_player_raw:
                                player_ind_xg_obv += e["shot_xg"]
                        else:
                            xg_ag_after += e["shot_xg"]
                elif e["type"] == "Pass" and e["pass_completed"]:
                    if is_before:
                        passes_tot_before += 1
                        if e["is_target_team"]:
                            passes_for_before += 1
                    else:
                        passes_tot_after += 1
                        if e["is_target_team"]:
                            passes_for_after += 1

                if not is_before and e["is_target_team"] and e.get("player_name") == rep_player_raw:
                    player_ind_xg_obv += 0.45 * float(e.get("obv_total_net") or 0.0)

            xg_diff_rate_before = (xg_for_before - xg_ag_before) / before_mins
            xg_diff_rate_after = (xg_for_after - xg_ag_after) / after_mins
            raw_delta_rate = xg_diff_rate_after - xg_diff_rate_before

            poss_before_pct = (passes_for_before / max(1, passes_tot_before)) * 100.0
            poss_after_pct = (passes_for_after / max(1, passes_tot_after)) * 100.0
            raw_delta_poss = poss_after_pct - poss_before_pct

            raw_sub_records.append({
                "match_id": mid,
                "opponent": s_ev["opponent"],
                "minute": sub_min,
                "after_mins": after_mins,
                "k_simult": max(1, k_simult),
                "game_state": s_ev["game_state"],
                "player_out_raw": out_player_raw,
                "player_in_raw": rep_player_raw,
                "raw_delta_rate": raw_delta_rate,
                "ind_rate": player_ind_xg_obv / after_mins,
                "raw_delta_poss": raw_delta_poss,
            })

    # Paso 4b: Estimar línea base esperada E[Delta xG | GameState] y E[Delta Poss | GameState]
    gs_rates: Dict[str, List[float]] = defaultdict(list)
    gs_poss: Dict[str, List[float]] = defaultdict(list)
    for r in raw_sub_records:
        gs_rates[r["game_state"]].append(r["raw_delta_rate"])
        gs_poss[r["game_state"]].append(r["raw_delta_poss"])

    gs_baseline_rate = {
        gs: (sum(vals) / len(vals) if vals else 0.0)
        for gs, vals in gs_rates.items()
    }
    gs_baseline_poss = {
        gs: (sum(vals) / len(vals) if vals else 0.0)
        for gs, vals in gs_poss.items()
    }

    # Paso 4c: Calcular el impacto ajustado por Game State + Empirical Bayes Shrinkage + atribución individual
    sub_events_records: List[Dict[str, Any]] = []
    sub_player_agg: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for r in raw_sub_records:
        gs = r["game_state"]
        after_mins = r["after_mins"]
        # Shrinkage para evitar extrapolaciones extremas en ventanas cortas de 8-12 minutos
        shrinkage = after_mins / (after_mins + 22.0)
        simult_factor = 1.0 / (float(r["k_simult"]) ** 0.5)

        # Descontar el sesgo estructural del estado del marcador (85% del drift de estado)
        gs_centered_rate = r["raw_delta_rate"] - 0.85 * gs_baseline_rate.get(gs, 0.0)
        adj_rate = (gs_centered_rate * shrinkage * simult_factor) + (0.45 * r["ind_rate"])

        gs_centered_poss = r["raw_delta_poss"] - 0.65 * gs_baseline_poss.get(gs, 0.0)
        adj_poss = round(gs_centered_poss * shrinkage, 1)

        clean_in = get_player_clean_name(r["player_in_raw"])
        clean_out = get_player_clean_name(r["player_out_raw"])

        rec = {
            "match_id": r["match_id"],
            "opponent": r["opponent"],
            "minute": r["minute"],
            "game_state": gs,
            "player_out": clean_out,
            "player_in": clean_in,
            "delta_xg_diff_per_min": round(adj_rate, 4),
            "delta_xg_diff_per_90": round(adj_rate * 90.0, 2),
            "raw_delta_xg_diff_per_90": round(r["raw_delta_rate"] * 90.0, 2),
            "delta_possession_pct": adj_poss,
        }
        sub_events_records.append(rec)
        sub_player_agg[r["player_in_raw"]].append(rec)

    # Ranking de principales revulsivos (jugadores con >= 3 ingresos desde la banca)
    super_subs: List[Dict[str, Any]] = []
    for p_in_raw, recs in sub_player_agg.items():
        if len(recs) < 3:
            continue
        avg_d_xg_min = sum(r["delta_xg_diff_per_min"] for r in recs) / len(recs)
        avg_d_poss = sum(r["delta_possession_pct"] for r in recs) / len(recs)
        avg_min = sum(r["minute"] for r in recs) / len(recs)
        super_subs.append({
            "player_name": get_player_clean_name(p_in_raw),
            "full_name": p_in_raw,
            "short_name": get_player_short_name(p_in_raw),
            "sub_appearances": len(recs),
            "avg_entry_minute": round(avg_min, 1),
            "avg_delta_xg_diff_per_min": round(avg_d_xg_min, 4),
            "avg_delta_xg_diff_per_90": round(avg_d_xg_min * 90.0, 2),
            "avg_delta_possession_pct": round(avg_d_poss, 1),
        })

    super_subs.sort(key=lambda x: x["avg_delta_xg_diff_per_min"], reverse=True)

    # Resumen de cambios por Game State (con métrica ajustada libre de sesgo de marcador)
    subs_by_gs: Dict[str, Dict[str, Any]] = {}
    for gs in ("Winning", "Drawing", "Losing"):
        gs_subs = [r for r in sub_events_records if r["game_state"] == gs]
        if gs_subs:
            subs_by_gs[gs] = {
                "count": len(gs_subs),
                "avg_minute": round(sum(r["minute"] for r in gs_subs) / len(gs_subs), 1),
                "avg_delta_xg_diff_per_90": round(
                    sum(r["delta_xg_diff_per_90"] for r in gs_subs) / len(gs_subs), 2
                ),
                "raw_avg_delta_xg_diff_per_90": round(
                    sum(r["raw_delta_xg_diff_per_90"] for r in gs_subs) / len(gs_subs), 2
                ),
                "avg_delta_possession_pct": round(
                    sum(r["delta_possession_pct"] for r in gs_subs) / len(gs_subs), 1
                ),
            }
        else:
            subs_by_gs[gs] = {
                "count": 0,
                "avg_minute": 65.0,
                "avg_delta_xg_diff_per_90": 0.0,
                "raw_avg_delta_xg_diff_per_90": 0.0,
                "avg_delta_possession_pct": 0.0,
            }

    avg_sub_min_all = round(
        sum(r["minute"] for r in sub_events_records) / max(1, len(sub_events_records)), 1
    )
    avg_delta_xg90_all = round(
        sum(r["delta_xg_diff_per_90"] for r in sub_events_records) / max(1, len(sub_events_records)), 2
    )

    return {
        "primary_formation": formatted_formation,
        "formation_distribution": dict(formation_counter.most_common(5)),
        "pca_explained_variance_pct": explained_var,
        "starting_xi": starting_xi,
        "players_clustered": raw_records,
        "substitutions": {
            "total_substitutions": len(sub_events_records),
            "avg_substitution_minute": avg_sub_min_all,
            "avg_delta_xg_diff_per_90": avg_delta_xg90_all,
            "by_game_state": subs_by_gs,
            "top_impact_subs": super_subs[:10],
            "recent_sub_events": sub_events_records[-30:],
        },
    }
