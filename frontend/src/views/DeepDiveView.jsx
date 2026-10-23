import React, { useState } from 'react';
import PitchSVG from '../components/PitchSVG.jsx';
import {
  Activity,
  BarChart3,
  Binary,
  Cpu,
  GitGraph,
  Layers,
  Network,
  Sigma,
  Sliders,
} from 'lucide-react';

/**
 * Vista 3: Deep-Dive Analítico (Enfoque Matemático / Data Science)
 * 1. Documentación del Framework Analítico Formal (Matriz de axiomas, umbrales y trazabilidad)
 * 2. Visualizador Geométrico 360 (Selector de eventos con Voronoi, Delaunay y Convex Hull en m^2)
 * 3. Teoría de Grafos en Redes de Pases (Betweenness Centrality, PageRank, Densidad) y Clustering PCA/K-Means
 * 4. Análisis de Distribuciones (Matrices de calor de Divergencia de Kullback-Leibler y Monte Carlo 10,000 iteraciones con IC 95%)
 */
export default function DeepDiveView({ deepDive }) {
  const [selected360Idx, setSelected360Idx] = useState(0);
  const [showVoronoi, setShowVoronoi] = useState(true);
  const [showConvexHull, setShowConvexHull] = useState(true);
  const [showDelaunay, setShowDelaunay] = useState(true);
  const [showVisibleArea, setShowVisibleArea] = useState(true);
  const [klContextKey, setKlContextKey] = useState('Losing_minus_Winning');
  const [selectedMatchSimIdx, setSelectedMatchSimIdx] = useState(0);

  if (!deepDive) return null;

  const fwDoc = deepDive.framework_documentation || {};
  const geoViewer = deepDive.geometry_360_viewer || {};
  const graphData = deepDive.graph_theory || {};
  const distSim = deepDive.distributions_and_simulation || {};

  const catalog360 = geoViewer.catalog || [];
  const active360 = catalog360[selected360Idx] || catalog360[0] || null;

  const klData = distSim.kl_divergence || {};
  const mcData = distSim.monte_carlo || {};
  const pcaData = distSim.pca_clusters || {};

  const matchesSim = mcData.matches_simulation || [];
  const selectedMatchSim = matchesSim[selectedMatchSimIdx] || matchesSim[0] || null;

  const klContextOptions = [
    {
      key: 'Losing_minus_Winning',
      label: 'Perdiendo (P) vs Ganando (Q)',
      dkl: klData.kpis?.kl_losing_vs_winning,
    },
    {
      key: 'Losing_minus_Drawing',
      label: 'Perdiendo (P) vs Empatando (Q)',
      dkl: klData.kpis?.kl_losing_vs_drawing,
    },
    {
      key: 'Home_minus_Away',
      label: 'Local (P) vs Visitante (Q)',
      dkl: klData.kpis?.kl_home_vs_away,
    },
    {
      key: '2H_minus_1H',
      label: '2º Tiempo (P) vs 1er Tiempo (Q)',
      dkl: klData.kpis?.kl_2h_vs_1h,
    },
  ];

  const activeKlOption =
    klContextOptions.find((o) => o.key === klContextKey) || klContextOptions[0];
  const activeKlDiffGrid = (klData.kl_diff_grids_6x4 || {})[klContextKey] || null;

  return (
    <div className="max-w-[1600px] mx-auto px-4 lg:px-6 py-6 space-y-8">
      {/* SECCIÓN 1: MATRIZ DEL FRAMEWORK ANALÍTICO FORMAL */}
      <section className="bg-[#111827] border border-[#1F2937] rounded-2xl p-5 sm:p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1F2937] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#8B5CF6]/15 border border-[#8B5CF6]/40 flex items-center justify-center">
              <Sigma className="w-5 h-5 text-[#8B5CF6]" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white">
                1. Framework Analítico Formal y Trazabilidad Matemática
              </h2>
              <p className="text-xs text-slate-400">
                Definiciones lógicas, axiomas espaciales (X ∈ [0,120], Y ∈ [0,80]) e integridad del enlace 360 ({(fwDoc.capabilities?.event_to_360_link_integrity || 1) * 100}%)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono-metric">
            <span className="px-2.5 py-1 rounded bg-[#0B0F19] border border-[#1F2937] text-[#00F5D4]">
              OBV Nativo: {fwDoc.capabilities?.has_obv_total_net ? 'ACTIVO' : 'FALLBACK'}
            </span>
            <span className="px-2.5 py-1 rounded bg-[#0B0F19] border border-[#1F2937] text-[#8B5CF6]">
              Frames 360: {(fwDoc.capabilities?.total_360_frames || 0).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#1F2937] text-[10px] font-mono-metric uppercase text-slate-400">
                <th className="py-2.5 pr-3">Objeto Formal</th>
                <th className="py-2.5 px-3">Formulación Lógica / Umbral</th>
                <th className="py-2.5 px-3">Dominio Espacial / Temporal</th>
                <th className="py-2.5 px-3 text-right">N Total</th>
                <th className="py-2.5 px-3 text-right">Media / Partido</th>
                <th className="py-2.5 pl-3 text-right">Módulo Fuente</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2937]/60">
              {(fwDoc.axioms_matrix || []).map((ax, i) => (
                <tr key={i} className="hover:bg-[#0B0F19]/60">
                  <td className="py-2.5 pr-3 font-bold text-white">{ax.object_name}</td>
                  <td className="py-2.5 px-3 font-mono-metric text-[#00F5D4]">
                    {ax.mathematical_definition}
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">{ax.spatial_condition}</td>
                  <td className="py-2.5 px-3 text-right font-mono-metric text-white">
                    {ax.total_detected.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono-metric text-[#8B5CF6]">
                    {ax.per_match_avg}
                  </td>
                  <td className="py-2.5 pl-3 text-right font-mono-metric text-slate-400">
                    {ax.module_source}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Segmentación por Intervalos de 15 minutos y Game State */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
          <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-4">
            <div className="text-xs font-bold text-white mb-2 font-mono-metric">
              Distribución por Estado de Partido (Game State ΔG)
            </div>
            <div className="grid grid-cols-3 gap-2.5 text-xs font-mono-metric">
              {['Winning', 'Drawing', 'Losing'].map((gs) => {
                const st = (fwDoc.game_state_summary || {})[gs] || {};
                return (
                  <div key={gs} className="bg-[#111827] border border-[#1F2937] rounded-lg p-2.5">
                    <div className="text-slate-400 text-[10px]">
                      {gs === 'Winning'
                        ? 'Ganando (ΔG > 0)'
                        : gs === 'Drawing'
                        ? 'Empatando (ΔG = 0)'
                        : 'Perdiendo (ΔG < 0)'}
                    </div>
                    <div className="text-white font-bold mt-1">
                      {st.valid_possessions} posesiones válidas
                    </div>
                    <div className="text-[#F59E0B] text-[11px] mt-0.5">
                      {st.pressure_actions} presiones · {st.transitions} trans.
                    </div>
                    <div className="text-[#00F5D4] text-[11px] mt-0.5">
                      xG: {st.xg_for} vs {st.xg_against}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-4">
            <div className="text-xs font-bold text-white mb-2 font-mono-metric">
              Segmentación Temporal cada 15 Minutos + PPDA
            </div>
            <div className="grid grid-cols-6 gap-1.5 text-center font-mono-metric text-[11px]">
              {(geoViewer.ppda_by_time_bin || []).map((tbObj) => {
                const st = (fwDoc.time_bin_summary || {})[tbObj.time_bin] || {};
                return (
                  <div
                    key={tbObj.time_bin}
                    className="bg-[#111827] border border-[#1F2937] rounded-lg p-2"
                  >
                    <div className="text-slate-400 text-[10px]">{tbObj.time_bin}&apos;</div>
                    <div className="text-[#F59E0B] font-bold mt-0.5">PPDA {tbObj.ppda}</div>
                    <div className="text-[#00F5D4] text-[10px] mt-0.5">
                      {st.valid_possessions} pos.
                    </div>
                    <div className="text-slate-300 text-[10px]">{st.xg_for} xG</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* SECCIÓN 2: VISUALIZADOR GEOMÉTRICO 360 (VORONOI + DELAUNAY + CONVEX HULL) */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-8 space-y-3">
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#8B5CF6]" />
              <span className="text-xs font-bold text-white">
                2. Visualizador Geométrico 360 (Voronoi, Delaunay & Convex Hull)
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
              <button
                onClick={() => setShowVoronoi(!showVoronoi)}
                className={`px-2.5 py-1 rounded text-xs font-mono-metric border ${
                  showVoronoi
                    ? 'bg-[#00F5D4]/15 text-[#00F5D4] border-[#00F5D4]/40'
                    : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                }`}
              >
                Voronoi
              </button>
              <button
                onClick={() => setShowConvexHull(!showConvexHull)}
                className={`px-2.5 py-1 rounded text-xs font-mono-metric border ${
                  showConvexHull
                    ? 'bg-[#8B5CF6]/20 text-[#8B5CF6] border-[#8B5CF6]/50'
                    : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                }`}
              >
                Convex Hull
              </button>
              <button
                onClick={() => setShowDelaunay(!showDelaunay)}
                className={`px-2.5 py-1 rounded text-xs font-mono-metric border ${
                  showDelaunay
                    ? 'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/50'
                    : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                }`}
              >
                Delaunay
              </button>
              <button
                onClick={() => setShowVisibleArea(!showVisibleArea)}
                className={`px-2.5 py-1 rounded text-xs font-mono-metric border ${
                  showVisibleArea
                    ? 'bg-slate-800 text-slate-200 border-slate-600'
                    : 'bg-[#0B0F19] text-slate-500 border-[#1F2937]'
                }`}
              >
                Cono Cámara 360
              </button>
            </div>
          </div>

          <PitchSVG
            title={active360?.description || 'Instantánea Geométrica StatsBomb 360'}
            subtitle={`Actor: ${active360?.player_name} | Partido vs ${active360?.opponent} (${active360?.match_date})`}
            event360={active360}
            showVoronoi={showVoronoi}
            showConvexHull={showConvexHull}
            showDelaunay={showDelaunay}
            showVisibleArea={showVisibleArea}
          />
        </div>

        {/* Selector de Eventos 360 y Métricas Geométricas del Frame */}
        <div className="lg:col-span-4 bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-white">
              Catálogo de Instantáneas 360 Auditadas
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Selecciona un evento para recalcular y renderizar su geometría espacial
            </p>
          </div>

          {/* Ficha matemática del evento 360 activo */}
          {active360 && (
            <div className="bg-[#0B0F19] border border-[#8B5CF6]/40 rounded-xl p-3.5 grid grid-cols-2 gap-2.5 font-mono-metric text-xs">
              <div>
                <div className="text-[10px] text-slate-400">Área Convex Hull</div>
                <div className="text-sm font-bold text-[#8B5CF6]">
                  {active360.geometry?.hull_area_m2 || 0} m²
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">Dimensiones Bloque</div>
                <div className="text-sm font-bold text-white">
                  {active360.geometry?.block_length_m}m × {active360.geometry?.block_width_m}m
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">Celdas Voronoi</div>
                <div className="text-sm font-bold text-[#00F5D4]">
                  {active360.geometry?.voronoi_cells?.length || 0} regiones
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">Aristas Delaunay</div>
                <div className="text-sm font-bold text-[#F59E0B]">
                  {active360.geometry?.delaunay_edges?.length || 0} conexiones
                </div>
              </div>
            </div>
          )}

          {/* Lista deslizable de eventos 360 */}
          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            {catalog360.map((item, idx) => {
              const isSel = idx === selected360Idx;
              return (
                <button
                  key={item.event_id || idx}
                  onClick={() => setSelected360Idx(idx)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    isSel
                      ? 'bg-[#0B0F19] border-[#8B5CF6] shadow-md'
                      : 'bg-[#0B0F19]/50 border-[#1F2937] hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono-metric">
                    <span
                      className={
                        item.category.includes('Ruptura') ? 'text-[#00F5D4]' : 'text-[#F59E0B]'
                      }
                    >
                      {item.category}
                    </span>
                    <span className="text-slate-400">
                      Min {item.minute}:{String(item.second || 0).padStart(2, '0')}
                    </span>
                  </div>
                  <div className="text-xs font-bold text-white mt-1">
                    {item.player_name} vs {item.opponent}
                  </div>
                  <div className="text-[11px] font-mono-metric text-slate-400 mt-0.5">
                    Hull: {item.geometry?.hull_area_m2} m² ·{' '}
                    {item.defenders_broken > 0
                      ? `${item.defenders_broken} def. superados`
                      : `Asfixia 3m: ${item.suffocation_3m ?? 0}`}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* SECCIÓN 3: TEORÍA DE GRAFOS (CENTRALIDAD) Y CLUSTERING PCA + K-MEANS */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Teoría de Grafos en Redes de Pases */}
        <div className="lg:col-span-6 bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Network className="w-4 h-4 text-[#00F5D4]" />
                <span>3. Teoría de Grafos en Redes de Pases</span>
              </h3>
              <p className="text-xs text-slate-400">
                Centralidad de Intermediación (Betweenness), Grado y PageRank sobre el grafo dirigido G=(V,E)
              </p>
            </div>
            <div className="text-right font-mono-metric text-xs">
              <div className="text-[#00F5D4]">
                Densidad: {graphData.passing_network?.network_density}
              </div>
              <div className="text-slate-400 text-[11px]">
                Hub: {graphData.passing_network?.hub_player}
              </div>
            </div>
          </div>

          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="sticky top-0 bg-[#111827] border-b border-[#1F2937] text-[10px] font-mono-metric uppercase text-slate-400">
                <tr>
                  <th className="py-2">Nodo (Jugador)</th>
                  <th className="py-2 text-right">Betweenness</th>
                  <th className="py-2 text-right">Degree Cent.</th>
                  <th className="py-2 text-right">PageRank</th>
                  <th className="py-2 text-right">Flujo (Env/Rec)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2937]/60 font-mono-metric">
                {(graphData.passing_network?.nodes || []).map((n, idx) => (
                  <tr key={n.id || idx} className="hover:bg-[#0B0F19]/60">
                    <td className="py-2 font-sans font-medium text-white">
                      {n.name}
                      <span className="block text-[10px] text-slate-400">{n.position}</span>
                    </td>
                    <td className="py-2 text-right font-bold text-[#8B5CF6]">
                      {n.betweenness_centrality}
                    </td>
                    <td className="py-2 text-right text-[#00F5D4]">{n.degree_centrality}</td>
                    <td className="py-2 text-right text-slate-300">{n.pagerank}</td>
                    <td className="py-2 text-right text-slate-400">
                      {n.passes_sent} / {n.passes_received}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Proyección PCA 2D + K-Means de Roles Tácticos */}
        <div className="lg:col-span-6 bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-base font-bold text-white">
                Clustering No Supervisado de Roles (PCA + K-Means)
              </h3>
              <p className="text-xs text-slate-400">
                Proyección ortogonal sobre vectores P90 estandarizados (Varianza explicada:{' '}
                {(pcaData.explained_variance_pct || [])[0]}% + {(pcaData.explained_variance_pct || [])[1]}%)
              </p>
            </div>
            <span className="text-xs font-mono-metric px-2.5 py-1 rounded bg-[#0B0F19] border border-[#1F2937] text-[#8B5CF6]">
              k = 5 Clusters
            </span>
          </div>

          {/* Plano Cartesiano SVG de PCA 1 vs PCA 2 */}
          <div className="w-full h-72 bg-[#0B0F19] border border-[#1F2937] rounded-xl p-2 relative">
            <svg viewBox="-4.4 -3.5 8.8 7.0" className="w-full h-full">
              <line x1="-4.2" y1="0" x2="4.2" y2="0" stroke="#334155" strokeWidth="0.03" />
              <line x1="0" y1="-3.3" x2="0" y2="3.3" stroke="#334155" strokeWidth="0.03" />
              <text x="4.1" y="-0.15" textAnchor="end" fill="#64748B" fontSize="0.23" fontFamily="JetBrains Mono">
                PC1 (Progresión / Volumen) →
              </text>
              <text x="0.15" y="-3.05" fill="#64748B" fontSize="0.23" fontFamily="JetBrains Mono">
                ↑ PC2 (Verticalidad / Área)
              </text>

              {(pcaData.players || []).map((pl, idx) => {
                const px = Math.max(-4.1, Math.min(4.1, pl.pca_x || 0));
                const py = Math.max(-3.05, Math.min(3.05, -(pl.pca_y || 0)));
                return (
                  <g key={pl.player_name || idx} transform={`translate(${px}, ${py})`}>
                    <circle
                      r="0.18"
                      fill={pl.role_color || '#00F5D4'}
                      stroke="#0B0F19"
                      strokeWidth="0.04"
                    />
                    <text
                      y="-0.24"
                      textAnchor="middle"
                      fill="#E2E8F0"
                      fontSize="0.21"
                      fontFamily="Inter, sans-serif"
                    >
                      {pl.short_name}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </section>

      {/* SECCIÓN 4: ANÁLISIS DE DISTRIBUCIONES (DIVERGENCIA KL 6x4 + SIMULACIÓN MONTE CARLO 10,000 ITERACIONES) */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Divergencia de Kullback-Leibler sobre Grilla 6x4 */}
        <div className="lg:col-span-6 space-y-3">
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-bold text-white">
                4A. Divergencia de Kullback-Leibler D_KL(P || Q) en Grilla 6×4
              </h3>
              <p className="text-[11px] text-slate-400 font-mono-metric">
                D_KL = Σ P(z) log(P(z) / (Q(z) + ε)) · Índice Consistencia:{' '}
                {klData.kpis?.tactical_consistency_index}%
              </p>
            </div>
            <select
              value={klContextKey}
              onChange={(e) => setKlContextKey(e.target.value)}
              className="bg-[#0B0F19] border border-[#334155] rounded-lg px-2.5 py-1.5 text-xs text-white font-mono-metric"
            >
              {klContextOptions.map((opt) => (
                <option key={opt.key} value={opt.key}>
                  {opt.label} (D_KL = {opt.dkl})
                </option>
              ))}
            </select>
          </div>

          <PitchSVG
            title={`Matriz de Diferencial Espacial P(z) - Q(z): ${activeKlOption.label}`}
            subtitle={`Divergencia de Kullback-Leibler calculada: D_KL = ${activeKlOption.dkl} nats`}
            heatmapGrid6x4={activeKlDiffGrid}
            isDiffGrid={true}
          />
        </div>

        {/* Simulación Estocástica Monte Carlo (10,000 iteraciones por partido y global) */}
        <div className="lg:col-span-6 bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1F2937] pb-3">
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white">
                4B. Motor Estocástico Monte Carlo (10,000 Iteraciones / Partido)
              </h3>
              <p className="text-xs text-slate-400 font-mono-metric">
                E[Points] = 3·P(Win) + 1·P(Draw) + 0·P(Loss)
              </p>
            </div>
            <span className="text-xs font-mono-metric px-2.5 py-1 rounded bg-[#00F5D4]/15 text-[#00F5D4]">
              IC 95%: [{mcData.summary?.ci_95_low}, {mcData.summary?.ci_95_high}] pts
            </span>
          </div>

          {/* Selector de Partido Individual para Inspeccionar sus 10,000 Simulaciones */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs text-slate-300 font-medium">
                Inspeccionar Simulación de Partido (10,000 iteraciones):
              </span>
              <select
                value={selectedMatchSimIdx}
                onChange={(e) => setSelectedMatchSimIdx(Number(e.target.value))}
                className="bg-[#0B0F19] border border-[#334155] rounded-lg px-3 py-1.5 text-xs text-white font-mono-metric"
              >
                {matchesSim.map((m, idx) => (
                  <option key={m.match_id || idx} value={idx}>
                    J{m.match_index} · {m.match_date} vs {m.opponent} ({m.real_score}) — xPts:{' '}
                    {m.xpoints}
                  </option>
                ))}
              </select>
            </div>

            {selectedMatchSim && (
              <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-4 space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono-metric text-xs">
                  <div className="bg-[#111827] p-2.5 rounded-lg border border-[#1F2937]">
                    <div className="text-[10px] text-slate-400">Marcador Real</div>
                    <div className="text-sm font-bold text-white mt-0.5">
                      {selectedMatchSim.real_score} ({selectedMatchSim.real_points} pts)
                    </div>
                  </div>
                  <div className="bg-[#111827] p-2.5 rounded-lg border border-[#1F2937]">
                    <div className="text-[10px] text-slate-400">xG (Propio vs Rival)</div>
                    <div className="text-sm font-bold text-[#00F5D4] mt-0.5">
                      {selectedMatchSim.xg_for} vs {selectedMatchSim.xg_against}
                    </div>
                  </div>
                  <div className="bg-[#111827] p-2.5 rounded-lg border border-[#1F2937]">
                    <div className="text-[10px] text-slate-400">xPoints Esperados</div>
                    <div className="text-sm font-bold text-[#8B5CF6] mt-0.5">
                      {selectedMatchSim.xpoints} xPts
                    </div>
                  </div>
                  <div className="bg-[#111827] p-2.5 rounded-lg border border-[#1F2937]">
                    <div className="text-[10px] text-slate-400">P(V) / P(E) / P(D)</div>
                    <div className="text-xs font-bold text-[#F59E0B] mt-1">
                      {selectedMatchSim.p_win_pct}% / {selectedMatchSim.p_draw_pct}% /{' '}
                      {selectedMatchSim.p_loss_pct}%
                    </div>
                  </div>
                </div>

                {/* Histograma de Diferencia de Goles Simulada (-4 a +4) */}
                <div>
                  <div className="text-[11px] font-mono-metric text-slate-400 mb-2">
                    Distribución de Diferencia de Goles en 10,000 Iteraciones (Goles Propios - Goles Rival)
                  </div>
                  <div className="h-28 flex items-end gap-2 bg-[#111827] rounded-lg p-3 border border-[#1F2937]">
                    {(selectedMatchSim.goal_diff_distribution || []).map((gd, idx) => {
                      const hPct = Math.max(6, Math.min(100, gd.prob_pct * 2.4));
                      const col =
                        gd.goal_diff > 0
                          ? 'bg-[#00F5D4]'
                          : gd.goal_diff === 0
                          ? 'bg-[#F59E0B]'
                          : 'bg-[#F43F5E]';
                      return (
                        <div
                          key={idx}
                          className="flex-1 flex flex-col items-center justify-end h-full"
                        >
                          <span className="text-[9px] font-mono-metric text-slate-300 mb-1">
                            {gd.prob_pct}%
                          </span>
                          <div style={{ height: `${hPct}%` }} className={`w-full rounded-t ${col}`} />
                          <span className="text-[10px] font-mono-metric text-slate-400 mt-1">
                            {gd.goal_diff > 0 ? `+${gd.goal_diff}` : gd.goal_diff}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Marcadores Exactos Más Probables */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                  <span className="text-[11px] text-slate-400">Marcadores más probables:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {(selectedMatchSim.top_scorelines || []).map((sc, i) => (
                      <span
                        key={i}
                        className="text-[11px] font-mono-metric px-2 py-0.5 rounded bg-[#111827] border border-[#1F2937] text-slate-200"
                      >
                        <strong>{sc.score}</strong> ({sc.prob_pct}%)
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Tabla de Convergencia Acumulada (Últimos 10 partidos) */}
          <div className="overflow-x-auto max-h-56">
            <table className="w-full text-left border-collapse text-xs font-mono-metric">
              <thead className="sticky top-0 bg-[#111827] border-b border-[#1F2937] text-[10px] uppercase text-slate-400">
                <tr>
                  <th className="py-1.5">J#</th>
                  <th className="py-1.5">Rival</th>
                  <th className="py-1.5 text-right">Score</th>
                  <th className="py-1.5 text-right">xG F/C</th>
                  <th className="py-1.5 text-right">xPts</th>
                  <th className="py-1.5 text-right">Acum. Real vs xPts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2937]/60">
                {matchesSim.map((m, i) => (
                  <tr
                    key={m.match_id || i}
                    onClick={() => setSelectedMatchSimIdx(i)}
                    className="cursor-pointer hover:bg-[#0B0F19]/60"
                  >
                    <td className="py-1.5 text-slate-400">J{m.match_index}</td>
                    <td className="py-1.5 font-sans text-white">{m.opponent}</td>
                    <td className="py-1.5 text-right text-slate-200">{m.real_score}</td>
                    <td className="py-1.5 text-right text-[#00F5D4]">
                      {m.xg_for} - {m.xg_against}
                    </td>
                    <td className="py-1.5 text-right text-[#8B5CF6]">{m.xpoints}</td>
                    <td className="py-1.5 text-right text-white">
                      {m.cumulative_real_points} vs {m.cumulative_xpoints}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
