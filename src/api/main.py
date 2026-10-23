"""
src/api/main.py
Servidor FastAPI para el sistema "La Historia de un Entrenador a través de los Datos".
Expone los endpoints requeridos en GEMINI.md:
- GET /api/summary
- GET /api/scrollytelling
- GET /api/tactical-staff
- GET /api/deep-dive
- GET /api/export-html
"""

import json
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from src.config import DATA_PROCESSED_DIR
from src.pipeline import run_full_pipeline
from src.api.exporters import build_standalone_html

app = FastAPI(
    title="StatsBomb 360 Tactical Intelligence API",
    description="La Historia de un Entrenador a través de los Datos — FastAPI Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_or_compute_json(filename: str) -> Dict[str, Any]:
    target = DATA_PROCESSED_DIR / filename
    if not target.exists():
        run_full_pipeline()
    if not target.exists():
        raise HTTPException(status_code=500, detail=f"Archivo procesado {filename} no disponible.")
    return json.loads(target.read_text(encoding="utf-8"))


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/summary")
def get_summary() -> JSONResponse:
    """Metadatos del entrenador, partidos y KPIs globales."""
    data = _load_or_compute_json("summary.json")
    return JSONResponse(content=data)


@app.get("/api/scrollytelling")
def get_scrollytelling() -> JSONResponse:
    """Capítulos secuenciales con estados de cancha interactivos."""
    data = _load_or_compute_json("scrollytelling.json")
    return JSONResponse(content=data)


@app.get("/api/tactical-staff")
def get_tactical_staff() -> JSONResponse:
    """Datos tácticos, fases, roles de plantilla, sustituciones, ABP y Plan de Partido."""
    data = _load_or_compute_json("tactical_staff.json")
    return JSONResponse(content=data)


@app.get("/api/deep-dive")
def get_deep_dive() -> JSONResponse:
    """Métricas matemáticas, Voronoi/Convex Hull 360, teoría de grafos, KL y Monte Carlo."""
    data = _load_or_compute_json("deep_dive.json")
    return JSONResponse(content=data)


@app.get("/api/export-html")
def export_standalone_html() -> FileResponse:
    """Genera y descarga el archivo único interactivo Reporte_Tactico_StatsBomb360.html."""
    full_bundle = _load_or_compute_json("full_bundle.json")
    try:
        out_path = build_standalone_html(full_bundle)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return FileResponse(
        path=str(out_path),
        media_type="text/html; charset=utf-8",
        filename="Reporte_Tactico_StatsBomb360.html",
    )
