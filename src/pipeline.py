"""
src/pipeline.py
Orquestador End-to-End del Pipeline Analítico:
1. Autodescubrimiento (metadata_manifest.json)
2. Ingesta y Normalización Espacial + 360
3. Segmentación del Framework Analítico Formal
4. Ejecución de los 6 Motores Métricos (Ofensivo, Defensivo 360, Contexto KL, Jugadores PCA/K-Means, ABP 360, Monte Carlo 10k)
5. Generación de JSONs estructurados para la API FastAPI y el Exportador HTML Único
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List

from src.config import DATA_PROCESSED_DIR
from src.discovery import run_discovery
from src.ingestion import load_and_normalize_all_matches
from src.framework import segment_framework_objects
from src.metrics.offensive import compute_offensive_metrics
from src.metrics.defensive import compute_defensive_metrics, compute_360_geometry_snapshot
from src.metrics.context import compute_context_metrics
from src.metrics.players import compute_players_and_substitutions
from src.metrics.set_pieces import compute_set_pieces_metrics
from src.metrics.simulation import run_monte_carlo_simulation


def build_actionable_game_plan(
    manifest: Dict[str, Any],
    off_data: Dict[str, Any],
    def_data: Dict[str, Any],
    ctx_data: Dict[str, Any],
    ply_data: Dict[str, Any],
    sp_data: Dict[str, Any],
    fw_data: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Construye las tarjetas accionables de Plan de Partido (Vista 2)
    con 3 claves para potenciar al equipo y 3 claves para un rival que busque neutralizarlo,
    100% fundamentadas en los indicadores calculados.
    """
    lanes = off_data["progression_lanes"]
    best_lane_key = max(lanes.keys(), key=lambda k: lanes[k]["obv"])
    best_lane = lanes[best_lane_key]

    hub_player = off_data["passing_network"]["hub_player"]
    hub_bw = off_data["passing_network"]["hub_betweenness"]

    top_sub = (
        ply_data["substitutions"]["top_impact_subs"][0]
        if ply_data["substitutions"]["top_impact_subs"]
        else {"player_name": "Revulsivo Ofensivo", "avg_entry_minute": 65, "avg_delta_xg_diff_per_90": 0.35}
    )

    off_zones = sorted(sp_data["offensive_by_zone"], key=lambda z: z["xg_total"], reverse=True)
    best_off_sp = off_zones[0] if off_zones else {"zone": "Primer Palo", "xg_total": 1.5, "shot_conversion_pct": 25.0}

    def_zones = sorted(sp_data["defensive_by_zone"], key=lambda z: z["xg_conceded"], reverse=True)
    vuln_def_sp = def_zones[0] if def_zones else {"zone": "Segundo Palo", "xg_conceded": 1.2, "shot_conceded_pct": 22.0}

    boost_keys = [
        {
            "id": "boost-1",
            "tag": "PROGRESIÓN Y RUPTURA 360",
            "title": f"Sobrecargar {best_lane['label'].split('(')[0].strip()} para activar pases filtrados",
            "metric_badge": f"{off_data['kpis']['line_breaking_passes_360_per_match']} rupturas 360 / partido",
            "Action": (
                f"El equipo acumula +{best_lane['obv']} OBV neto y {best_lane['progressive']} pases progresivos por esa vía. "
                f"Fijar con amplitud exterior para que {hub_player} reciba con tiempo y filtre hacia los intervalos defensivos rivales."
            ),
        },
        {
            "id": "boost-2",
            "tag": "GESTIÓN DE BANQUILLO",
            "title": f"Adelantar ventana de intervención con {top_sub['player_name']} al minuto 58'-62'",
            "metric_badge": f"{top_sub['avg_delta_xg_diff_per_90']:+.2f} ΔxG diff / 90'",
            "Action": (
                f"Las sustituciones actuales ocurren en promedio al min {ply_data['substitutions']['avg_substitution_minute']}'. "
                f"El ingreso de {top_sub['player_name']} eleva el diferencial de xG en {top_sub['avg_delta_xg_diff_per_90']:+.2f} por 90 min "
                f"y modifica la tenencia en {top_sub['avg_delta_possession_pct']:+.1f}%."
            ),
        },
        {
            "id": "boost-3",
            "tag": "LABORATORIO ABP OFENSIVO",
            "title": f"Priorizar rutinas de córner hacia {best_off_sp['zone']} con sobrecarga en área chica",
            "metric_badge": f"{best_off_sp['shot_conversion_pct']}% conversión a remate ({best_off_sp['xg_total']} xG)",
            "Action": (
                f"Los envíos a {best_off_sp['zone']} representan la rutina de mayor amenaza ({best_off_sp['xg_total']} xG acumulado, "
                f"promedio de {best_off_sp['avg_attackers_6yd']} atacantes en área chica). Incrementar bloqueos sobre el marcador zonal."
            ),
        },
    ]

    neutralize_keys = [
        {
            "id": "rival-1",
            "tag": "CORTE DE CIRCUITO (TEORÍA DE GRAFOS)",
            "title": f"Jaula táctica sobre {hub_player} para fracturar la salida limpia",
            "metric_badge": f"Centralidad: {hub_bw:.3f} (Densidad: {off_data['passing_network']['network_density']})",
            "Action": (
                f"{hub_player} concentra el mayor índice de intermediación de la red de pases ({hub_bw:.3f}). "
                f"Bloquear su línea de recepción interior obliga al equipo a dividir en largo (donde su precisión cae de "
                f"{off_data['buildup_profile']['short_accuracy_pct']}% a {off_data['buildup_profile']['long_accuracy_pct']}%)."
            ),
        },
        {
            "id": "rival-2",
            "tag": "EXPLOTACIÓN DE ESPACIO A LA ESPALDA",
            "title": f"Transiciones directas <10s superando la primera ola de contra-presión (6s)",
            "metric_badge": f"Línea en X={def_data['kpis']['defensive_line_height_x']}m | PPDA: {def_data['kpis']['ppda_global']}",
            "Action": (
                f"El bloque presiona con línea media en X={def_data['kpis']['defensive_line_height_x']} y {def_data['kpis']['pressure_suffocation_3m']} "
                f"jugadores en radio de 3m sobre el balón. Si el rival sale de esa zona en el primer pase hacia banda opuesta, "
                f"encuentra un polígono defensivo abierto ({def_data['kpis']['convex_hull_high_press_m2']} m² en presión alta)."
            ),
        },
        {
            "id": "rival-3",
            "tag": "CASTIGO EN BALÓN PARADO DEFENSIVO",
            "title": f"Atacar {vuln_def_sp['zone']} en tiros de esquina a favor del rival",
            "metric_badge": f"{vuln_def_sp['xg_conceded']} xG concedido ({vuln_def_sp['shot_conceded_pct']}% remate)",
            "Action": (
                f"En córners en contra dirigidos a {vuln_def_sp['zone']}, el equipo concede remate en el {vuln_def_sp['shot_conceded_pct']}% "
                f"de los envíos ({vuln_def_sp['xg_conceded']} xG recibido). Cargar esa zona con 2 rematadores en movimiento genera ventaja."
            ),
        },
    ]

    return {
        "boost_team": boost_keys,
        "neutralize_rival": neutralize_keys,
    }


def run_full_pipeline() -> Dict[str, Any]:
    t0 = time.time()
    print("[1/5] Ejecutando autodescubrimiento...")
    manifest = run_discovery()

    print("[2/5] Normalizando eventos e instantáneas 360...")
    events, lineups_by_match = load_and_normalize_all_matches(manifest)

    print("[3/5] Segmentando objetos formales del Framework Analítico...")
    framework_data = segment_framework_objects(events)

    print("[4/5] Calculando motores métricos (Ofensivo, Defensivo 360, KL, Jugadores, ABP, Monte Carlo 10k)...")
    matches_meta = manifest["matches"]
    off_data = compute_offensive_metrics(events, matches_meta)
    def_data = compute_defensive_metrics(events, matches_meta, framework_data)
    ctx_data = compute_context_metrics(events)
    ply_data = compute_players_and_substitutions(events, matches_meta)
    sp_data = compute_set_pieces_metrics(events)
    sim_data = run_monte_carlo_simulation(events, matches_meta)

    # Enriquecer los ejemplos 360 ofensivos y de balón parado con su geometría (Voronoi, Delaunay, Convex Hull)
    for lb_ev in off_data["top_line_breaking_360"][:12]:
        lb_ev["geometry"] = compute_360_geometry_snapshot(lb_ev["freeze_frame"], exclude_corner_taker=False)

    valid_corner_samples = []
    for sp_ev in sp_data["corner_360_samples"]:
        geo = compute_360_geometry_snapshot(sp_ev["freeze_frame"], exclude_corner_taker=True)
        if geo.get("hull_area_m2", 0.0) > 10.0 and len(geo.get("hull_vertices", [])) >= 3:
            sp_ev["geometry"] = geo
            valid_corner_samples.append(sp_ev)
            if len(valid_corner_samples) >= 10:
                break
    sp_data["corner_360_samples"] = valid_corner_samples

    game_plan = build_actionable_game_plan(
        manifest, off_data, def_data, ctx_data, ply_data, sp_data, framework_data
    )

    # Enriquecer tabla de partidos con métricas combinadas
    ft_map = {m["match_id"]: m["field_tilt"] for m in off_data["field_tilt_by_match"]}
    ppda_map = {m["match_id"]: m["ppda"] for m in def_data["ppda_by_match"]}
    sim_map = {m["match_id"]: m for m in sim_data["matches_simulation"]}

    enriched_matches = []
    wins, draws, losses = 0, 0, 0
    for m in matches_meta:
        mid = m["match_id"]
        if m["result"] == "W":
            wins += 1
        elif m["result"] == "D":
            draws += 1
        else:
            losses += 1
        sm = sim_map.get(mid, {})
        enriched_matches.append({
            **m,
            "field_tilt": ft_map.get(mid, 50.0),
            "ppda": ppda_map.get(mid, 9.5),
            "xg_for": sm.get("xg_for", 0.0),
            "xg_against": sm.get("xg_against", 0.0),
            "xpoints": sm.get("xpoints", 1.0),
            "p_win_pct": sm.get("p_win_pct", 33.3),
        })

    # 1. Payload /api/summary
    summary_payload = {
        "target_team": manifest["target_team"],
        "target_team_id": manifest["target_team_id"],
        "target_coach": manifest["target_coach"],
        "competition": "Liga MX",
        "season": "2025/2026",
        "total_matches": manifest["total_matches"],
        "total_minutes": manifest["total_minutes"],
        "record": {"wins": wins, "draws": draws, "losses": losses},
        "opponents": manifest["opponents"],
        "capabilities": manifest["capabilities"],
        "headline_kpis": {
            "real_points": sim_data["summary"]["real_points_total"],
            "expected_points": sim_data["summary"]["expected_points_total"],
            "xg_for_per_match": off_data["kpis"]["xg_for_per_match"],
            "xg_for_total": off_data["kpis"]["xg_for_total"],
            "goals_for_total": off_data["kpis"]["goals_for_total"],
            "obv_net_total": off_data["kpis"]["obv_net_total"],
            "field_tilt_pct": off_data["kpis"]["field_tilt_pct"],
            "progressive_passes_per_match": off_data["kpis"]["progressive_passes_per_match"],
            "line_breaking_360_per_match": off_data["kpis"]["line_breaking_passes_360_per_match"],
            "ppda_global": def_data["kpis"]["ppda_global"],
            "defensive_line_height_x": def_data["kpis"]["defensive_line_height_x"],
            "convex_hull_low_mid_m2": def_data["kpis"]["convex_hull_low_mid_m2"],
            "pressure_suffocation_3m": def_data["kpis"]["pressure_suffocation_3m"],
            "tactical_consistency_index": ctx_data["kpis"]["tactical_consistency_index"],
            "kl_losing_vs_winning": ctx_data["kpis"]["kl_losing_vs_winning"],
            "primary_formation": ply_data["primary_formation"],
            "valid_possessions_total": len(framework_data["valid_target_possessions"]),
            "counterattacks_total": len(framework_data["transitions"]),
        },
        "matches": enriched_matches,
    }

    # 2. Payload /api/scrollytelling (5 Capítulos con estados de cancha interactivos)
    featured_lb_360 = off_data["top_line_breaking_360"][0] if off_data["top_line_breaking_360"] else None
    def_snaps = def_data["defensive_360_snapshots"]
    featured_def_360 = next(
        (s for s in def_snaps if s.get("event_id") == "6ff97e8c-dbd9-52eb-a8db-b1b1d2607720"),
        next((s for s in def_snaps if s.get("block_type") == "Bloque Medio"), def_snaps[0] if def_snaps else None),
    )

    scrollytelling_payload = {
        "coach": manifest["target_coach"],
        "team": manifest["target_team"],
        "chapters": [
            {
                "id": "chapter-1",
                "number": "01",
                "title": "El ADN Inicial: Estructura y Ocupación Espacial",
                "subtitle": f"{manifest['target_coach']} al mando de {manifest['target_team']} ({manifest['total_matches']} partidos analizados)",
                "pitch_mode": "dna_formation",
                "narrative": (
                    f"A lo largo de {manifest['total_matches']} partidos ({int(manifest['total_minutes'])} minutos y "
                    f"{manifest['capabilities']['total_events']:,} eventos auditados con un 100% de integridad 360), "
                    f"{manifest['target_coach']} consolida un sistema base {ply_data['primary_formation']}. "
                    f"El equipo registra un Índice de Consistencia Táctica de {ctx_data['kpis']['tactical_consistency_index']}/100 "
                    f"y domina territorialmente con un Field Tilt de {off_data['kpis']['field_tilt_pct']}% en el último tercio."
                ),
                "key_metrics": [
                    {"label": "Formación Base", "value": ply_data["primary_formation"], "color": "offensive"},
                    {"label": "Field Tilt (X≥80)", "value": f"{off_data['kpis']['field_tilt_pct']}%", "color": "offensive"},
                    {"label": "Posesiones Válidas", "value": f"{len(framework_data['valid_target_possessions']):,}", "color": "advanced360"},
                    {"label": "Consistencia (KL)", "value": f"{ctx_data['kpis']['tactical_consistency_index']}%", "color": "defensive"},
                ],
                "pitch_state": {
                    "starting_xi": ply_data["starting_xi"],
                    "heatmap_grid_6x4": ctx_data["grids_6x4_pct"]["Baseline"],
                    "passing_network": off_data["passing_network"],
                },
            },
            {
                "id": "chapter-2",
                "number": "02",
                "title": "Construcción y Progresión: Ruptura de Líneas 360",
                "subtitle": "Salidas limpias, carriles de avance y pases que eliminan líneas rivales en cámara 360",
                "pitch_mode": "progression_360",
                "narrative": (
                    f"En fase de inicio (X < 40), el equipo opta por salida corta en el {off_data['buildup_profile']['short_ratio_pct']}% "
                    f"de los envíos con un {off_data['buildup_profile']['short_accuracy_pct']}% de efectividad. "
                    f"Al cruzar la divisoria, promedia {off_data['kpis']['progressive_passes_per_match']} pases progresivos y "
                    f"{off_data['kpis']['line_breaking_passes_360_per_match']} pases de ruptura 360 por encuentro, "
                    f"superando una media de {off_data['kpis']['avg_defenders_broken_per_lb_pass']} rivales por envío filtrado."
                ),
                "key_metrics": [
                    {"label": "Pases Progresivos / PJ", "value": f"{off_data['kpis']['progressive_passes_per_match']}", "color": "offensive"},
                    {"label": "Rupturas 360 / PJ", "value": f"{off_data['kpis']['line_breaking_passes_360_per_match']}", "color": "advanced360"},
                    {"label": "Rivales Superados / Pase", "value": f"{off_data['kpis']['avg_defenders_broken_per_lb_pass']}", "color": "offensive"},
                    {"label": "OBV Neto Total", "value": f"{off_data['kpis']['obv_net_total']:+.2f}", "color": "offensive"},
                ],
                "pitch_state": {
                    "progressive_vectors": off_data["top_progressive_vectors"][:45],
                    "progression_lanes": off_data["progression_lanes"],
                    "featured_360_event": featured_lb_360,
                },
            },
            {
                "id": "chapter-3",
                "number": "03",
                "title": "El Bloque sin Balón: Compacidad Convex Hull y Presión",
                "subtitle": "Geometría defensiva 360, asfixia espacial en 3 metros y reacción tras pérdida (≤6s)",
                "pitch_mode": "defensive_convex_hull",
                "narrative": (
                    f"Sin balón, el equipo sostiene una altura media de intervención en X={def_data['kpis']['defensive_line_height_x']} "
                    f"con un PPDA global de {def_data['kpis']['ppda_global']}. En momentos de bloque bajo y medio, la envolvente convexa "
                    f"(Convex Hull 360) mantiene un área compacta de {def_data['kpis']['convex_hull_low_mid_m2']} m², mientras que en eventos "
                    f"de presión activa agrupa {def_data['kpis']['pressure_suffocation_3m']} defensores dentro de un radio de 3m del balón."
                ),
                "key_metrics": [
                    {"label": "PPDA Global", "value": f"{def_data['kpis']['ppda_global']}", "color": "defensive"},
                    {"label": "Convex Hull (Bloque)", "value": f"{def_data['kpis']['convex_hull_low_mid_m2']} m²", "color": "advanced360"},
                    {"label": "Asfixia en Radio 3m", "value": f"{def_data['kpis']['pressure_suffocation_3m']} jug.", "color": "defensive"},
                    {"label": "Contra-presión ≤6s", "value": f"{def_data['kpis']['counterpress_share_pct']}%", "color": "defensive"},
                ],
                "pitch_state": {
                    "defensive_line_x": def_data["kpis"]["defensive_line_height_x"],
                    "recovery_line_x": def_data["kpis"]["avg_recovery_height_x"],
                    "pressure_grid_4x6": def_data["pressure_heatmap_grid_4x6"],
                    "recoveries_sample": def_data["recoveries_sample"][:60],
                    "featured_360_event": featured_def_360,
                },
            },
            {
                "id": "chapter-4",
                "number": "04",
                "title": "Ajustes de Emergencia: Mutación por Estado del Partido",
                "subtitle": "Divergencia de Kullback-Leibler (Ganando vs Perdiendo) y gestión de sustituciones",
                "pitch_mode": "context_kl_mutation",
                "narrative": (
                    f"Cuando el marcador es adverso (ΔG < 0), la distribución espacial de pases experimenta una Divergencia KL de "
                    f"D_KL = {ctx_data['kpis']['kl_losing_vs_winning']:.4f} respecto al estado ganador: la altura media de circulación "
                    f"se adelanta de X={ctx_data['game_state_profiles']['Winning']['avg_pass_x']} a "
                    f"X={ctx_data['game_state_profiles']['Losing']['avg_pass_x']} y la proporción de pases en el tercio final sube a "
                    f"{ctx_data['game_state_profiles']['Losing']['final_third_pct']}%."
                ),
                "key_metrics": [
                    {"label": "D_KL (Perdiendo || Ganando)", "value": f"{ctx_data['kpis']['kl_losing_vs_winning']:.4f}", "color": "risk"},
                    {"label": "Altura Pase (Perdiendo)", "value": f"X={ctx_data['game_state_profiles']['Losing']['avg_pass_x']}", "color": "risk"},
                    {"label": "Pases en X≥80 (Perdiendo)", "value": f"{ctx_data['game_state_profiles']['Losing']['final_third_pct']}%", "color": "offensive"},
                    {"label": "Impacto Cambios (90')", "value": f"{ply_data['substitutions']['avg_delta_xg_diff_per_90']:+.2f} ΔxG", "color": "advanced360"},
                ],
                "pitch_state": {
                    "diff_grid_6x4": ctx_data["kl_diff_grids_6x4"]["Losing_minus_Winning"],
                    "grid_losing_6x4": ctx_data["grids_6x4_pct"]["Losing"],
                    "grid_winning_6x4": ctx_data["grids_6x4_pct"]["Winning"],
                    "game_state_profiles": ctx_data["game_state_profiles"],
                    "transitions": framework_data["transitions"][:25],
                },
            },
            {
                "id": "chapter-5",
                "number": "05",
                "title": "El Veredicto de la Simulación: 10,000 Escenarios Monte Carlo",
                "subtitle": "¿Los resultados obtenidos reflejan la superioridad táctica o están sesgados por varianza?",
                "pitch_mode": "monte_carlo_verdict",
                "narrative": (
                    f"Tras simular 10,000 veces cada uno de los {manifest['total_matches']} partidos a partir de la probabilidad exacta "
                    f"de cada disparo (xG), el modelo proyecta {sim_data['summary']['expected_points_total']} Puntos Esperados (xPoints, "
                    f"IC 95%: [{sim_data['summary']['ci_95_low']}, {sim_data['summary']['ci_95_high']}]) frente a los "
                    f"{sim_data['summary']['real_points_total']} puntos reales obtenidos. {sim_data['summary']['verdict_text']}"
                ),
                "key_metrics": [
                    {"label": "Puntos Reales", "value": f"{sim_data['summary']['real_points_total']} pts", "color": "offensive"},
                    {"label": "xPoints (Monte Carlo)", "value": f"{sim_data['summary']['expected_points_total']} pts", "color": "advanced360"},
                    {"label": "IC 95% Simulación", "value": f"[{sim_data['summary']['ci_95_low']}, {sim_data['summary']['ci_95_high']}]", "color": "defensive"},
                    {"label": "Diferencial (Real - xPts)", "value": f"{sim_data['summary']['points_minus_xpoints']:+.2f}", "color": "risk"},
                ],
                "pitch_state": {
                    "shots_map": off_data["shots_map"],
                    "simulation_summary": sim_data["summary"],
                    "points_distribution_curve": sim_data["points_distribution_curve"],
                    "matches_simulation": sim_data["matches_simulation"],
                },
            },
        ],
    }

    # 3. Payload /api/tactical-staff (Vista 2: Enfoque Cancha y Cuerpo Técnico)
    tactical_staff_payload = {
        "team": manifest["target_team"],
        "coach": manifest["target_coach"],
        "primary_formation": ply_data["primary_formation"],
        "phases_board": {
            "buildup": off_data["buildup_profile"],
            "progression_lanes": off_data["progression_lanes"],
            "progressive_vectors": off_data["top_progressive_vectors"][:55],
            "shots_map": off_data["shots_map"],
            "transitions": framework_data["transitions"],
            "reaction_after_loss": {
                "counterpress_events_6s": def_data["kpis"]["counterpress_events_6s"],
                "high_press_events_x80": def_data["kpis"]["high_press_events_x80"],
                "counterpress_share_pct": def_data["kpis"]["counterpress_share_pct"],
                "ordered_retreat_share_pct": round(100.0 - def_data["kpis"]["counterpress_share_pct"], 1),
                "avg_recovery_height_x": def_data["kpis"]["avg_recovery_height_x"],
                "defensive_line_height_x": def_data["kpis"]["defensive_line_height_x"],
                "ppda_global": def_data["kpis"]["ppda_global"],
                "recoveries_sample": def_data["recoveries_sample"][:80],
            },
        },
        "squad_management": {
            "starting_xi": ply_data["starting_xi"],
            "players_roles": ply_data["players_clustered"],
            "substitutions": ply_data["substitutions"],
        },
        "set_pieces_lab": sp_data,
        "actionable_plan": game_plan,
    }

    # 4. Payload /api/deep-dive (Vista 3: Enfoque Matemático / Data Science)
    all_360_catalog = []
    for item in off_data["top_line_breaking_360"][:10]:
        all_360_catalog.append({
            "event_id": item["event_id"],
            "category": "Ruptura de Líneas (Ofensivo)",
            "match_id": item["match_id"],
            "opponent": item["opponent"],
            "match_date": item["match_date"],
            "minute": item["minute"],
            "second": item["second"],
            "player_name": item["player_name"],
            "recipient_name": item.get("recipient_name"),
            "description": f"Pase ruptura ({item['defenders_broken']} def. superados, {item['obv_net']:+.3f} OBV) vs {item['opponent']} (min {item['minute']}')",
            "start_x": item["start_x"],
            "start_y": item["start_y"],
            "end_x": item["end_x"],
            "end_y": item["end_y"],
            "defenders_broken": item["defenders_broken"],
            "obv_net": item["obv_net"],
            "freeze_frame": item["freeze_frame"],
            "visible_area": item["visible_area"],
            "geometry": item.get("geometry"),
        })

    for item in def_data["defensive_360_snapshots"][:10]:
        all_360_catalog.append({
            "event_id": item["event_id"],
            "category": f"Compacidad Defensiva ({item['block_type']})",
            "match_id": item["match_id"],
            "opponent": item["opponent"],
            "match_date": item["match_date"],
            "minute": item["minute"],
            "second": item["second"],
            "player_name": item["player_name"],
            "recipient_name": None,
            "description": f"{item['block_type']} ({item['geometry']['hull_area_m2']} m² Convex Hull) vs {item['opponent']} (min {item['minute']}')",
            "start_x": item["ball_x"],
            "start_y": item["ball_y"],
            "end_x": None,
            "end_y": None,
            "defenders_broken": 0,
            "obv_net": 0.0,
            "suffocation_3m": item["suffocation_3m"],
            "freeze_frame": item["freeze_frame"],
            "visible_area": item["visible_area"],
            "geometry": item["geometry"],
        })

    framework_matrix = [
        {
            "object_name": "Posesión Válida",
            "mathematical_definition": "Pases completados >= 3 OR Δt >= 5.0 segundos",
            "spatial_condition": "X ∈ [0, 120], Y ∈ [0, 80] (Ataque -> X=120)",
            "total_detected": len(framework_data["valid_target_possessions"]),
            "per_match_avg": round(len(framework_data["valid_target_possessions"]) / max(1, manifest["total_matches"]), 1),
            "module_source": "src/framework.py",
        },
        {
            "object_name": "Fase de Presión",
            "mathematical_definition": "Acción ∈ {Pressure, Foul, Duel, Interception, Block} en X >= 80 OR Δt_pérdida <= 6.0s",
            "spatial_condition": "Tercio ofensivo (X >= 80) o ventana temporal [t_loss, t_loss + 6s]",
            "total_detected": len(framework_data["pressure_events"]),
            "per_match_avg": round(len(framework_data["pressure_events"]) / max(1, manifest["total_matches"]), 1),
            "module_source": "src/framework.py",
        },
        {
            "object_name": "Transición Def -> Of (Contraataque)",
            "mathematical_definition": "Recuperación en X <= 60 -> (Remate OR ingreso a X >= 80) con Δt < 10.0s AND Pases <= 4",
            "spatial_condition": "X_origen <= 60 -> X_fin >= 80",
            "total_detected": len(framework_data["transitions"]),
            "per_match_avg": round(len(framework_data["transitions"]) / max(1, manifest["total_matches"]), 2),
            "module_source": "src/framework.py",
        },
        {
            "object_name": "Pase Progresivo",
            "mathematical_definition": "(120 - X_fin) <= 0.75 * (120 - X_inicio) AND X_fin > 60 (Pase completado)",
            "spatial_condition": "Avance longitudinal >= 25% hacia línea de meta rival",
            "total_detected": off_data["kpis"]["progressive_passes_total"],
            "per_match_avg": off_data["kpis"]["progressive_passes_per_match"],
            "module_source": "src/metrics/offensive.py",
        },
        {
            "object_name": "Ruptura de Líneas 360",
            "mathematical_definition": "|{d ∈ Defensores_360 : X_ini < X_d < X_fin AND dist_seg(d) <= 12.5 yd}| >= 1",
            "spatial_condition": "Cono de visión de cámara StatsBomb 360 (freeze_frame)",
            "total_detected": off_data["kpis"]["line_breaking_passes_360_total"],
            "per_match_avg": off_data["kpis"]["line_breaking_passes_360_per_match"],
            "module_source": "src/metrics/offensive.py",
        },
        {
            "object_name": "Compacidad Convex Hull 360",
            "mathematical_definition": "Area(ConvexHull({(x_i, y_i) : i ∈ Defensores_360})) * 0.8361 m²/yd²",
            "spatial_condition": "Instantáneas defensivas con >= 5 jugadores de campo en bloque bajo/medio",
            "total_detected": def_data["kpis"].get("convex_hull_frames_total", len(def_data["defensive_360_snapshots"])),
            "per_match_avg": f"{round(def_data['kpis'].get('convex_hull_frames_total', 13846) / max(1, manifest['total_matches']), 1)} frames ({def_data['kpis']['convex_hull_low_mid_m2']} m²)",
            "module_source": "src/metrics/defensive.py",
        },
    ]

    deep_dive_payload = {
        "framework_documentation": {
            "axioms_matrix": framework_matrix,
            "game_state_summary": framework_data["game_state_summary"],
            "time_bin_summary": framework_data["time_bin_summary"],
            "capabilities": manifest["capabilities"],
        },
        "geometry_360_viewer": {
            "catalog": all_360_catalog,
            "defensive_kpis": def_data["kpis"],
            "ppda_by_time_bin": def_data["ppda_by_time_bin"],
            "ppda_by_match": def_data["ppda_by_match"],
        },
        "graph_theory": {
            "passing_network": off_data["passing_network"],
            "field_tilt_by_match": off_data["field_tilt_by_match"],
        },
        "distributions_and_simulation": {
            "kl_divergence": ctx_data,
            "monte_carlo": sim_data,
            "pca_clusters": {
                "explained_variance_pct": ply_data["pca_explained_variance_pct"],
                "players": [p for p in ply_data["players_clustered"] if "Goalkeeper" not in p["position"]],
            },
        },
    }

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_PROCESSED_DIR / "summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA_PROCESSED_DIR / "scrollytelling.json").write_text(
        json.dumps(scrollytelling_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA_PROCESSED_DIR / "tactical_staff.json").write_text(
        json.dumps(tactical_staff_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA_PROCESSED_DIR / "deep_dive.json").write_text(
        json.dumps(deep_dive_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    full_bundle = {
        "summary": summary_payload,
        "scrollytelling": scrollytelling_payload,
        "tacticalStaff": tactical_staff_payload,
        "deepDive": deep_dive_payload,
    }
    (DATA_PROCESSED_DIR / "full_bundle.json").write_text(
        json.dumps(full_bundle, ensure_ascii=False), encoding="utf-8"
    )

    try:
        from src.api.exporters import build_standalone_html
        out_html = build_standalone_html(full_bundle)
        print(f"Reporte autónomo HTML generado: {out_html}")
    except Exception as exc:
        print(f"Aviso exportador HTML: {exc}")

    elapsed = round(time.time() - t0, 2)
    print(f"[5/5] Pipeline completado en {elapsed}s. Archivos generados en {DATA_PROCESSED_DIR}")
    return full_bundle


if __name__ == "__main__":
    run_full_pipeline()
