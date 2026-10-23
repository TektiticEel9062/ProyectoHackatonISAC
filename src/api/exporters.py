"""
src/api/exporters.py
Generador del Reporte Exportable Autónomo en un único archivo .html auto-contenido
(Reporte_Tactico_StatsBomb360.html) con datos embebidos en window.__PRECALCULATED_DATA__.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from src.config import BASE_DIR, DATA_PROCESSED_DIR, FRONTEND_DIST_DIR


def build_standalone_html(full_bundle: Dict[str, Any]) -> Path:
    """
    Toma el build single-file de Vite (frontend/dist/index.html),
    inyecta window.__PRECALCULATED_DATA__ antes de cerrar </head> (o al inicio de <body>)
    y escribe el archivo autónomo Reporte_Tactico_StatsBomb360.html en la raíz del proyecto
    y en data/processed/.
    """
    dist_index = FRONTEND_DIST_DIR / "index.html"
    frontend_dir = BASE_DIR / "frontend"

    if not dist_index.exists() and (frontend_dir / "package.json").exists():
        # Compilar automáticamente con Vite si aún no existe dist/index.html
        subprocess.run(
            "npm run build",
            cwd=str(frontend_dir),
            shell=True,
            check=False,
        )

    if dist_index.exists():
        template_html = dist_index.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(
            f"No se encontró el bundle compilado en {dist_index}. Ejecuta 'npm run build' en frontend/."
        )

    json_str = json.dumps(full_bundle, ensure_ascii=False)
    # Evitar que secuencias </script> dentro del JSON rompan el parser HTML
    safe_json_str = json_str.replace("</script>", "<\\/script>")
    injected_script = f"<script>window.__PRECALCULATED_DATA__ = {safe_json_str};</script>"

    if "<!--__INJECT_PRECALCULATED_DATA__-->" in template_html:
        final_html = template_html.replace("<!--__INJECT_PRECALCULATED_DATA__-->", injected_script, 1)
    elif "</head>" in template_html:
        final_html = template_html.replace("</head>", f"{injected_script}\n</head>", 1)
    else:
        final_html = f"{injected_script}\n{template_html}"

    output_root_path = BASE_DIR / "Reporte_Tactico_StatsBomb360.html"
    output_proc_path = DATA_PROCESSED_DIR / "Reporte_Tactico_StatsBomb360.html"

    output_root_path.write_text(final_html, encoding="utf-8")
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_proc_path.write_text(final_html, encoding="utf-8")

    return output_root_path
