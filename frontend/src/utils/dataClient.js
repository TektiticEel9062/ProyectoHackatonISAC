/**
 * frontend/src/utils/dataClient.js
 * Cliente Dual:
 * 1. En modo Standalone HTML (cuando existe window.__PRECALCULATED_DATA__),
 *    retorna instantáneamente los datos embebidos sin requerir servidor activo.
 * 2. En modo Full-Stack (Desarrollo / Demo en vivo), consulta los endpoints de FastAPI (/api/...).
 */

const API_BASE = '';

export function isStandaloneMode() {
  return typeof window !== 'undefined' && Boolean(window.__PRECALCULATED_DATA__);
}

export async function fetchAllTacticalData() {
  if (isStandaloneMode()) {
    const pre = window.__PRECALCULATED_DATA__;
    return {
      summary: pre.summary,
      scrollytelling: pre.scrollytelling,
      tacticalStaff: pre.tacticalStaff,
      deepDive: pre.deepDive,
      standalone: true,
    };
  }

  const [summaryRes, scrollRes, staffRes, deepRes] = await Promise.all([
    fetch(`${API_BASE}/api/summary`),
    fetch(`${API_BASE}/api/scrollytelling`),
    fetch(`${API_BASE}/api/tactical-staff`),
    fetch(`${API_BASE}/api/deep-dive`),
  ]);

  if (!summaryRes.ok || !scrollRes.ok || !staffRes.ok || !deepRes.ok) {
    throw new Error('Error al obtener los datos tácticos desde el servidor FastAPI.');
  }

  const [summary, scrollytelling, tacticalStaff, deepDive] = await Promise.all([
    summaryRes.json(),
    scrollRes.json(),
    staffRes.json(),
    deepRes.json(),
  ]);

  return {
    summary,
    scrollytelling,
    tacticalStaff,
    deepDive,
    standalone: false,
  };
}

export async function triggerStandaloneHtmlDownload(currentDataBundle) {
  // Si ya estamos en el HTML único autónomo, serializar el documento actual
  if (isStandaloneMode()) {
    const htmlContent = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Reporte_Tactico_StatsBomb360.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    return { mode: 'client-self-bundle', filename: 'Reporte_Tactico_StatsBomb360.html' };
  }

  // En modo Full-Stack, solicitar al backend FastAPI (/api/export-html) el bundle compilado con datos inyectados
  const res = await fetch(`${API_BASE}/api/export-html`);
  if (!res.ok) {
    throw new Error('No se pudo generar el archivo HTML autónomo desde /api/export-html');
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Reporte_Tactico_StatsBomb360.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  return { mode: 'fastapi-singlefile', filename: 'Reporte_Tactico_StatsBomb360.html' };
}
