"""
src/discovery.py
Módulo de Autodescubrimiento Agnóstico y Conector de API StatsBomb.
Detecta archivos en data/raw/ (o los sincroniza desde la API de StatsBomb),
identifica automáticamente target_team y target_coach, audita capacidades (OBV, xG, 360)
y genera data/processed/metadata_manifest.json.
"""

import os
import json
import base64
import urllib.request
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple

from src.config import DATA_RAW_DIR, DATA_PROCESSED_DIR


def load_env_file(env_path: Path = Path(".env")) -> Dict[str, str]:
    """Carga variables de entorno desde .env sin requerir librerías externas."""
    env_vars: Dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


class StatsBombAPIClient:
    """Cliente ligero con autenticación HTTP Basic para la API de StatsBomb."""

    def __init__(self, user: Optional[str] = None, password: Optional[str] = None, base_url: str = "https://data.statsbomb.com"):
        env = load_env_file()
        self.user = user or os.environ.get("STATSBOMB_USER") or env.get("STATSBOMB_USER", "")
        self.password = password or os.environ.get("STATSBOMB_PASSWORD") or env.get("STATSBOMB_PASSWORD", "")
        self.base_url = (os.environ.get("STATSBOMB_BASE_URL") or env.get("STATSBOMB_BASE_URL") or base_url).rstrip("/")
        auth_bytes = f"{self.user}:{self.password}".encode("utf-8")
        self.auth_header = f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

    def get_json(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", self.auth_header)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def download_team_coach_matches(
        self,
        competition_id: int = 73,
        season_id: int = 318,
        target_team_name: Optional[str] = None,
        target_coach_substr: Optional[str] = None,
        max_matches: Optional[int] = None,
    ) -> Path:
        """
        Descarga desde la API de StatsBomb todos los partidos disponibles (con 360)
        de un equipo y director técnico específicos hacia data/raw/.
        """
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        events_dir = DATA_RAW_DIR / "events"
        lineups_dir = DATA_RAW_DIR / "lineups"
        threesixty_dir = DATA_RAW_DIR / "three-sixty"
        events_dir.mkdir(exist_ok=True)
        lineups_dir.mkdir(exist_ok=True)
        threesixty_dir.mkdir(exist_ok=True)

        all_matches = self.get_json(f"/api/v6/competitions/{competition_id}/seasons/{season_id}/matches")
        avail_matches = [
            m for m in all_matches
            if m.get("match_status") == "available" and m.get("match_status_360") == "available"
        ]

        # Si no se especifica equipo/DT, elegir el binomio equipo+DT con más partidos 360 disponibles
        if not target_team_name:
            counts: Counter = Counter()
            for m in avail_matches:
                for side_key, name_key in [("home_team", "home_team_name"), ("away_team", "away_team_name")]:
                    t_name = m[side_key][name_key]
                    mgrs = m[side_key].get("managers") or []
                    c_name = mgrs[0]["name"] if mgrs else "Unknown"
                    counts[(t_name, c_name)] += 1
            (target_team_name, target_coach_substr), _ = counts.most_common(1)[0]

        filtered_matches = []
        for m in avail_matches:
            ht = m["home_team"]["home_team_name"]
            at = m["away_team"]["away_team_name"]
            hm = [c["name"] for c in (m["home_team"].get("managers") or [])]
            am = [c["name"] for c in (m["away_team"].get("managers") or [])]

            is_home_target = (ht == target_team_name) and (
                not target_coach_substr or any(target_coach_substr.lower() in c.lower() for c in hm)
            )
            is_away_target = (at == target_team_name) and (
                not target_coach_substr or any(target_coach_substr.lower() in c.lower() for c in am)
            )
            if is_home_target or is_away_target:
                filtered_matches.append(m)

        # Ordenar cronológicamente
        filtered_matches.sort(key=lambda x: x.get("match_date", ""))
        if max_matches and len(filtered_matches) > max_matches:
            filtered_matches = filtered_matches[-max_matches:]

        matches_path = DATA_RAW_DIR / "matches.json"
        matches_path.write_text(json.dumps(filtered_matches, ensure_ascii=False, indent=2), encoding="utf-8")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _fetch_match_bundle(idx_m):
            idx, m = idx_m
            mid = m["match_id"]
            ev_file = events_dir / f"{mid}.json"
            lu_file = lineups_dir / f"{mid}.json"
            ts_file = threesixty_dir / f"{mid}.json"

            if not ev_file.exists():
                ev_data = self.get_json(f"/api/v8/events/{mid}")
                ev_file.write_text(json.dumps(ev_data, ensure_ascii=False), encoding="utf-8")
            if not lu_file.exists():
                lu_data = self.get_json(f"/api/v4/lineups/{mid}")
                lu_file.write_text(json.dumps(lu_data, ensure_ascii=False), encoding="utf-8")
            if not ts_file.exists():
                ts_data = self.get_json(f"/api/v2/360-frames/{mid}")
                ts_file.write_text(json.dumps(ts_data, ensure_ascii=False), encoding="utf-8")
            return f"[{idx}/{len(filtered_matches)}] Sincronizado partido {mid} ({m.get('match_date')})"

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(_fetch_match_bundle, (i, m)) for i, m in enumerate(filtered_matches, 1)]
            for fut in as_completed(futures):
                print(fut.result())

        return matches_path


def scan_raw_files(raw_dir: Path = DATA_RAW_DIR) -> Dict[str, List[Path]]:
    """
    1. Detección de Archivos:
    Busca recursivamente archivos .json, .parquet o .csv asociados a matches, events, lineups y three-sixty / 360.
    """
    catalog: Dict[str, List[Path]] = {
        "matches": [],
        "events": [],
        "lineups": [],
        "three_sixty": [],
    }
    if not raw_dir.exists():
        return catalog

    for file_path in raw_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".json", ".parquet", ".csv"}:
            continue

        parts_lower = [p.lower() for p in file_path.parts]
        stem_lower = file_path.stem.lower()

        if "match" in stem_lower or any("match" in p for p in parts_lower):
            catalog["matches"].append(file_path)
        elif any(k in parts_lower or k in stem_lower for k in ("three-sixty", "three_sixty", "360", "360-frames")):
            catalog["three_sixty"].append(file_path)
        elif any(k in parts_lower or k in stem_lower for k in ("lineup", "lineups")):
            catalog["lineups"].append(file_path)
        elif any(k in parts_lower or k in stem_lower for k in ("event", "events")):
            catalog["events"].append(file_path)

    return catalog


def run_discovery(raw_dir: Path = DATA_RAW_DIR) -> Dict[str, Any]:
    """
    Ejecuta la rutina de inspección agnóstica sobre data/raw/:
    - Detecta archivos
    - Identifica target_team (presente en 100% de los partidos) y target_coach
    - Audita columnas y capacidades (obv_total_net, shot_statsbomb_xg, enlace events.id <-> three_sixty.event_uuid)
    - Genera data/processed/metadata_manifest.json
    """
    catalog = scan_raw_files(raw_dir)
    if not catalog["matches"]:
        raise FileNotFoundError(f"No se encontraron archivos de partidos en {raw_dir}")

    # Cargar todos los partidos
    matches: List[Dict[str, Any]] = []
    seen_match_ids = set()
    for m_file in catalog["matches"]:
        if m_file.suffix.lower() == ".json":
            data = json.loads(m_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data = [data]
            for m in data:
                mid = m.get("match_id")
                if mid not in seen_match_ids:
                    seen_match_ids.add(mid)
                    matches.append(m)

    matches.sort(key=lambda x: x.get("match_date", ""))
    total_matches = len(matches)

    # 2. Identificación de Sujetos de Estudio
    team_counts: Counter = Counter()
    team_ids: Dict[str, int] = {}
    coach_counts_by_team: Dict[str, Counter] = {}

    for m in matches:
        ht = m.get("home_team", {})
        at = m.get("away_team", {})
        h_name = ht.get("home_team_name") or ht.get("team_name") or "Unknown Home"
        a_name = at.get("away_team_name") or at.get("team_name") or "Unknown Away"
        h_id = ht.get("home_team_id") or ht.get("team_id")
        a_id = at.get("away_team_id") or at.get("team_id")

        team_counts[h_name] += 1
        team_counts[a_name] += 1
        if h_id:
            team_ids[h_name] = h_id
        if a_id:
            team_ids[a_name] = a_id

        coach_counts_by_team.setdefault(h_name, Counter())
        for mgr in ht.get("managers") or []:
            coach_counts_by_team[h_name][mgr.get("name", "Unknown")] += 1

        coach_counts_by_team.setdefault(a_name, Counter())
        for mgr in at.get("managers") or []:
            coach_counts_by_team[a_name][mgr.get("name", "Unknown")] += 1

    # Equipo presente en el 100% de los partidos del lote (o el de mayor frecuencia)
    target_team, target_freq = team_counts.most_common(1)[0]
    target_team_id = team_ids.get(target_team)
    coach_counter = coach_counts_by_team.get(target_team, Counter())
    target_coach = coach_counter.most_common(1)[0][0] if coach_counter else "Director Técnico"

    # Mapear archivos de eventos y 360 por match_id
    events_by_match: Dict[int, Path] = {}
    for p in catalog["events"]:
        if p.stem.isdigit():
            events_by_match[int(p.stem)] = p

    threesixty_by_match: Dict[int, Path] = {}
    for p in catalog["three_sixty"]:
        if p.stem.isdigit():
            threesixty_by_match[int(p.stem)] = p

    lineups_by_match: Dict[int, Path] = {}
    for p in catalog["lineups"]:
        if p.stem.isdigit():
            lineups_by_match[int(p.stem)] = p

    # 3. Auditoría de Columnas y Capacidades
    has_obv_total_net = False
    has_shot_statsbomb_xg = False
    total_events_count = 0
    total_360_frames_count = 0
    linked_360_events_count = 0
    total_minutes = 0.0
    opponents: List[str] = []
    match_summaries: List[Dict[str, Any]] = []

    for m in matches:
        mid = m["match_id"]
        ht = m.get("home_team", {})
        at = m.get("away_team", {})
        h_name = ht.get("home_team_name") or ht.get("team_name")
        a_name = at.get("away_team_name") or at.get("team_name")
        is_home = (h_name == target_team)
        opponent_name = a_name if is_home else h_name
        if opponent_name and opponent_name not in opponents:
            opponents.append(opponent_name)

        goals_for = m.get("home_score", 0) if is_home else m.get("away_score", 0)
        goals_against = m.get("away_score", 0) if is_home else m.get("home_score", 0)

        ev_path = events_by_match.get(mid)
        ts_path = threesixty_by_match.get(mid)

        match_max_min = 90.0
        match_events_n = 0
        match_360_n = 0
        match_linked_360_n = 0

        event_ids = set()
        if ev_path and ev_path.exists():
            evs = json.loads(ev_path.read_text(encoding="utf-8"))
            match_events_n = len(evs)
            total_events_count += match_events_n
            for e in evs:
                eid = e.get("id")
                if eid:
                    event_ids.add(eid)
                if "obv_total_net" in e and e["obv_total_net"] is not None:
                    has_obv_total_net = True
                shot_obj = e.get("shot")
                if (isinstance(shot_obj, dict) and "statsbomb_xg" in shot_obj) or ("shot_statsbomb_xg" in e):
                    has_shot_statsbomb_xg = True
                minute_val = e.get("minute", 0)
                if minute_val > match_max_min:
                    match_max_min = float(minute_val)

        if ts_path and ts_path.exists():
            frames = json.loads(ts_path.read_text(encoding="utf-8"))
            match_360_n = len(frames)
            total_360_frames_count += match_360_n
            for fr in frames:
                uuid = fr.get("event_uuid") or fr.get("id")
                if uuid in event_ids:
                    match_linked_360_n += 1
            linked_360_events_count += match_linked_360_n

        total_minutes += match_max_min
        result_char = "W" if goals_for > goals_against else ("D" if goals_for == goals_against else "L")

        match_summaries.append({
            "match_id": mid,
            "match_date": m.get("match_date"),
            "competition": m.get("competition", {}).get("competition_name", "Liga MX"),
            "season": m.get("season", {}).get("season_name", ""),
            "is_home": is_home,
            "venue": "Local" if is_home else "Visitante",
            "opponent": opponent_name,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "result": result_char,
            "minutes_played": round(match_max_min, 1),
            "events_count": match_events_n,
            "frames_360_count": match_360_n,
            "linked_360_count": match_linked_360_n,
            "has_lineups": mid in lineups_by_match,
        })

    link_integrity_ratio = (
        round(linked_360_events_count / total_360_frames_count, 4)
        if total_360_frames_count > 0 else 0.0
    )

    manifest = {
        "target_team": target_team,
        "target_team_id": target_team_id,
        "target_coach": target_coach,
        "target_presence_ratio": round(target_freq / total_matches, 4) if total_matches else 0.0,
        "total_matches": total_matches,
        "total_minutes": round(total_minutes, 1),
        "opponents": opponents,
        "capabilities": {
            "has_obv_total_net": has_obv_total_net,
            "has_shot_statsbomb_xg": has_shot_statsbomb_xg,
            "spatial_control_fallback_active": not (has_obv_total_net and has_shot_statsbomb_xg),
            "has_360_freeze_frames": total_360_frames_count > 0,
            "total_events": total_events_count,
            "total_360_frames": total_360_frames_count,
            "linked_360_events": linked_360_events_count,
            "event_to_360_link_integrity": link_integrity_ratio,
        },
        "matches": match_summaries,
    }

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = DATA_PROCESSED_DIR / "metadata_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    if not (DATA_RAW_DIR / "matches.json").exists():
        print("Descargando partidos de Club América (DT: André Jardine, Temporada 2025/2026) desde StatsBomb API...")
        client = StatsBombAPIClient()
        client.download_team_coach_matches(
            competition_id=73,
            season_id=318,
            target_team_name="América",
            target_coach_substr="Jardine",
        )
    manifest_data = run_discovery()
    print(f"Autodescubrimiento completado: {manifest_data['target_team']} ({manifest_data['target_coach']}) - {manifest_data['total_matches']} partidos.")

