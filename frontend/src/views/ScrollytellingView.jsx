import React, { useState, useEffect, useRef } from 'react';
import PitchSVG from '../components/PitchSVG.jsx';
import { Activity, Eye, Layers, Play, ShieldAlert, Sparkles, TrendingUp } from 'lucide-react';

/**
 * Vista 1: Página Principal — Scrollytelling ("La Historia del Entrenador")
 * Layout: Pantalla dividida.
 * - Izquierda: Tarjetas narrativas deslizantes de los 5 Capítulos.
 * - Derecha: Pizarra SVG interactiva fija (sticky pitch) + Campana de Gauss Monte Carlo en Cap. 5.
 */
export default function ScrollytellingView({ scrollytelling, summary }) {
  const chapters = scrollytelling?.chapters || [];
  const [activeChapterIdx, setActiveChapterIdx] = useState(0);
  const [showVoronoi, setShowVoronoi] = useState(true);
  const [showConvexHull, setShowConvexHull] = useState(true);
  const [showDelaunay, setShowDelaunay] = useState(false);
  const [showNetworkInCh1, setShowNetworkInCh1] = useState(true);

  const chapterRefs = useRef([]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = Number(entry.target.getAttribute('data-chapter-idx'));
            if (!Number.isNaN(idx)) {
              setActiveChapterIdx(idx);
            }
          }
        });
      },
      {
        root: null,
        rootMargin: '-28% 0px -42% 0px',
        threshold: 0.2,
      }
    );

    chapterRefs.current.forEach((el) => {
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [chapters.length]);

  if (!chapters.length) return null;

  const activeChapter = chapters[activeChapterIdx] || chapters[0];
  const ps = activeChapter.pitch_state || {};
  const mode = activeChapter.pitch_mode;

  // Configurar qué capas recibe PitchSVG según el capítulo activo
  let pitchProps = {
    title: `Capítulo ${activeChapter.number}: ${activeChapter.title}`,
    subtitle: activeChapter.subtitle,
  };

  if (mode === 'dna_formation') {
    pitchProps.heatmapGrid6x4 = ps.heatmap_grid_6x4;
    pitchProps.isDiffGrid = false;
    if (showNetworkInCh1) {
      pitchProps.passingNetwork = ps.passing_network;
    } else {
      pitchProps.startingXI = ps.starting_xi;
    }
  } else if (mode === 'progression_360') {
    pitchProps.progressiveVectors = ps.progressive_vectors;
    pitchProps.event360 = ps.featured_360_event;
    pitchProps.showVoronoi = showVoronoi;
    pitchProps.showConvexHull = showConvexHull;
    pitchProps.showDelaunay = showDelaunay;
  } else if (mode === 'defensive_convex_hull') {
    pitchProps.defensiveLineX = ps.defensive_line_x;
    pitchProps.recoveryLineX = ps.recovery_line_x;
    pitchProps.recoveries = ps.recoveries_sample;
    pitchProps.event360 = ps.featured_360_event;
    pitchProps.showVoronoi = showVoronoi;
    pitchProps.showConvexHull = showConvexHull;
    pitchProps.showDelaunay = showDelaunay;
  } else if (mode === 'context_kl_mutation') {
    pitchProps.heatmapGrid6x4 = ps.diff_grid_6x4;
    pitchProps.isDiffGrid = true;
    pitchProps.transitions = ps.transitions;
  } else if (mode === 'monte_carlo_verdict') {
    pitchProps.shotsMap = ps.shots_map;
  }

  const badgeColors = {
    offensive: 'text-[#00F5D4] bg-[#00F5D4]/10 border-[#00F5D4]/30',
    defensive: 'text-[#F59E0B] bg-[#F59E0B]/10 border-[#F59E0B]/30',
    risk: 'text-[#F43F5E] bg-[#F43F5E]/10 border-[#F43F5E]/30',
    advanced360: 'text-[#8B5CF6] bg-[#8B5CF6]/10 border-[#8B5CF6]/30',
  };

  return (
    <div className="max-w-[1600px] mx-auto px-4 lg:px-6 py-6">
      {/* Banner Introductorio de KPIs Globales */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-4 sm:p-5 mb-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3">
          <div className="text-[11px] text-slate-400">Récord Analizado</div>
          <div className="text-lg font-bold font-mono-metric text-white mt-0.5">
            {summary?.record?.wins}G - {summary?.record?.draws}E - {summary?.record?.losses}P
          </div>
          <div className="text-[11px] text-[#00F5D4] font-mono-metric">
            {summary?.total_matches} Partidos ({summary?.total_minutes} mins)
          </div>
        </div>
        <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3">
          <div className="text-[11px] text-slate-400">Puntos Reales vs xPoints</div>
          <div className="text-lg font-bold font-mono-metric text-[#00F5D4] mt-0.5">
            {summary?.headline_kpis?.real_points} <span className="text-slate-500 text-xs">vs</span>{' '}
            <span className="text-[#8B5CF6]">{summary?.headline_kpis?.expected_points}</span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono-metric">10,000 sim. Monte Carlo</div>
        </div>
        <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3">
          <div className="text-[11px] text-slate-400">Field Tilt (Dominio X≥80)</div>
          <div className="text-lg font-bold font-mono-metric text-[#00F5D4] mt-0.5">
            {summary?.headline_kpis?.field_tilt_pct}%
          </div>
          <div className="text-[11px] text-slate-400 font-mono-metric">
            {summary?.headline_kpis?.progressive_passes_per_match} pases prog. / PJ
          </div>
        </div>
        <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3">
          <div className="text-[11px] text-slate-400">Rupturas de Línea 360</div>
          <div className="text-lg font-bold font-mono-metric text-[#8B5CF6] mt-0.5">
            {summary?.headline_kpis?.line_breaking_360_per_match} / PJ
          </div>
          <div className="text-[11px] text-slate-400 font-mono-metric">
            OBV Neto: +{summary?.headline_kpis?.obv_net_total}
          </div>
        </div>
        <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3">
          <div className="text-[11px] text-slate-400">Intensidad PPDA & Bloque</div>
          <div className="text-lg font-bold font-mono-metric text-[#F59E0B] mt-0.5">
            {summary?.headline_kpis?.ppda_global} PPDA
          </div>
          <div className="text-[11px] text-slate-400 font-mono-metric">
            Hull: {summary?.headline_kpis?.convex_hull_low_mid_m2} m²
          </div>
        </div>
        <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3">
          <div className="text-[11px] text-slate-400">Consistencia Táctica (KL)</div>
          <div className="text-lg font-bold font-mono-metric text-emerald-400 mt-0.5">
            {summary?.headline_kpis?.tactical_consistency_index}%
          </div>
          <div className="text-[11px] text-slate-400 font-mono-metric">
            D_KL: {summary?.headline_kpis?.kl_losing_vs_winning}
          </div>
        </div>
      </div>

      {/* Layout Dividido: Izquierda Narrativa Scrollytelling | Derecha Pizarra Sticky */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Columna Izquierda (Capítulos Deslizantes) */}
        <div className="lg:col-span-5 space-y-8 pb-24">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-mono-metric uppercase tracking-wider text-slate-400">
              Recorrido Narrativo ({chapters.length} Capítulos)
            </span>
            <div className="flex items-center gap-1.5">
              {chapters.map((ch, idx) => (
                <button
                  key={ch.id}
                  onClick={() => {
                    setActiveChapterIdx(idx);
                    chapterRefs.current[idx]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }}
                  className={`w-6 h-6 rounded-md text-[11px] font-mono-metric font-bold transition-all ${
                    activeChapterIdx === idx
                      ? 'bg-[#00F5D4] text-[#0B0F19]'
                      : 'bg-[#111827] text-slate-400 border border-[#1F2937] hover:text-white'
                  }`}
                >
                  {ch.number}
                </button>
              ))}
            </div>
          </div>

          {chapters.map((ch, idx) => {
            const isSelected = activeChapterIdx === idx;
            return (
              <div
                key={ch.id}
                ref={(el) => (chapterRefs.current[idx] = el)}
                data-chapter-idx={idx}
                onClick={() => setActiveChapterIdx(idx)}
                className={`cursor-pointer rounded-2xl p-5 sm:p-6 transition-all duration-300 border ${
                  isSelected
                    ? 'bg-[#111827] border-[#00F5D4] shadow-xl shadow-[#00F5D4]/10 ring-1 ring-[#00F5D4]/30'
                    : 'bg-[#111827]/60 border-[#1F2937] opacity-65 hover:opacity-95'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="text-xs font-mono-metric font-bold px-2.5 py-1 rounded-md bg-[#0B0F19] text-[#00F5D4] border border-[#00F5D4]/30">
                    CAPÍTULO {ch.number}
                  </span>
                  {isSelected && (
                    <span className="text-[11px] font-mono-metric text-[#00F5D4] flex items-center gap-1">
                      <Play className="w-3 h-3 fill-current" /> Activo en Pizarra
                    </span>
                  )}
                </div>

                <h2 className="text-lg sm:text-xl font-bold text-white leading-snug">
                  {ch.title}
                </h2>
                <p className="text-xs text-slate-400 mt-1 mb-4">{ch.subtitle}</p>

                <p className="text-sm text-slate-200 leading-relaxed mb-5">
                  {ch.narrative}
                </p>

                {/* Grid de 4 KPIs del Capítulo */}
                <div className="grid grid-cols-2 gap-2.5">
                  {(ch.key_metrics || []).map((km, mIdx) => (
                    <div
                      key={mIdx}
                      className={`rounded-xl p-2.5 border ${
                        badgeColors[km.color] || badgeColors.offensive
                      }`}
                    >
                      <div className="text-[10px] uppercase tracking-wider opacity-80">
                        {km.label}
                      </div>
                      <div className="text-base font-bold font-mono-metric mt-0.5">
                        {km.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Columna Derecha Fija (Sticky Pitch + Visualizador Contextual) */}
        <div className="lg:col-span-7 lg:sticky lg:top-20 space-y-4">
          {/* Barra de Controles Interactivos de la Pizarra según Capítulo */}
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-3 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs text-slate-300 font-medium">
              <Layers className="w-4 h-4 text-[#00F5D4]" />
              <span>Capas de Pizarra Activas:</span>
            </div>

            {mode === 'dna_formation' && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowNetworkInCh1(true)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono-metric border transition-all ${
                    showNetworkInCh1
                      ? 'bg-[#00F5D4]/15 text-[#00F5D4] border-[#00F5D4]/50'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Red de Pases (Grafos)
                </button>
                <button
                  onClick={() => setShowNetworkInCh1(false)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono-metric border transition-all ${
                    !showNetworkInCh1
                      ? 'bg-[#00F5D4]/15 text-[#00F5D4] border-[#00F5D4]/50'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Once Titular + Roles
                </button>
              </div>
            )}

            {(mode === 'progression_360' || mode === 'defensive_convex_hull') && (
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setShowVoronoi(!showVoronoi)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono-metric border ${
                    showVoronoi
                      ? 'bg-[#00F5D4]/15 text-[#00F5D4] border-[#00F5D4]/40'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Voronoi 360
                </button>
                <button
                  onClick={() => setShowConvexHull(!showConvexHull)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono-metric border ${
                    showConvexHull
                      ? 'bg-[#8B5CF6]/20 text-[#8B5CF6] border-[#8B5CF6]/50'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Convex Hull (m²)
                </button>
                <button
                  onClick={() => setShowDelaunay(!showDelaunay)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono-metric border ${
                    showDelaunay
                      ? 'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/50'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Delaunay
                </button>
              </div>
            )}

            {mode === 'context_kl_mutation' && (
              <span className="text-xs font-mono-metric text-[#F43F5E]">
                Rojo = Mayor densidad Perdiendo (ΔG&lt;0) | Cian = Ganando (ΔG&gt;0)
              </span>
            )}

            {mode === 'monte_carlo_verdict' && (
              <span className="text-xs font-mono-metric text-[#8B5CF6]">
                Mapa de {ps.shots_map?.length || 0} disparos + Curva Monte Carlo (10,000 sim.)
              </span>
            )}
          </div>

          {/* Cancha Vectorial Interactiva */}
          <PitchSVG {...pitchProps} />

          {/* Panel Inferior Contextual del Capítulo */}
          {mode === 'monte_carlo_verdict' && ps.points_distribution_curve && (
            <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div>
                  <h4 className="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#8B5CF6]" />
                    <span>Campana de Gauss Monte Carlo (10,000 Temporadas Simuladas)</span>
                  </h4>
                  <p className="text-[11px] text-slate-400">
                    Contraste entre Puntos Reales ({ps.simulation_summary?.real_points_total} pts) y Media Esperada xPoints ({ps.simulation_summary?.expected_points_total} pts)
                  </p>
                </div>
                <span className="text-xs font-mono-metric px-2.5 py-1 rounded bg-[#8B5CF6]/15 text-[#8B5CF6] border border-[#8B5CF6]/30">
                  IC 95%: [{ps.simulation_summary?.ci_95_low}, {ps.simulation_summary?.ci_95_high}] pts
                </span>
              </div>

              {/* Gráfico de Barras / Campana de Distribución de Puntos */}
              <div className="h-36 flex items-end gap-1 pt-4 pb-2 px-2 bg-[#0B0F19] rounded-xl border border-[#1F2937]">
                {ps.points_distribution_curve.map((bar, i) => {
                  const maxProb = Math.max(
                    ...ps.points_distribution_curve.map((b) => b.prob_pct),
                    1
                  );
                  const heightPct = Math.max(6, (bar.prob_pct / maxProb) * 100);
                  let barColor = bar.in_ci_95 ? 'bg-[#8B5CF6]/65' : 'bg-slate-700/50';
                  if (bar.is_real_points) barColor = 'bg-[#00F5D4]';
                  else if (bar.is_expected_mean) barColor = 'bg-[#F59E0B]';

                  return (
                    <div
                      key={i}
                      className="flex-1 flex flex-col items-center justify-end h-full group relative"
                    >
                      <div
                        style={{ height: `${heightPct}%` }}
                        className={`w-full rounded-t transition-all ${barColor}`}
                      />
                      {i % 3 === 0 && (
                        <span className="text-[9px] font-mono-metric text-slate-400 mt-1">
                          {bar.points}
                        </span>
                      )}
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-7 bg-[#111827] border border-[#334155] text-[10px] font-mono-metric px-1.5 py-0.5 rounded whitespace-nowrap z-10 pointer-events-none">
                        {bar.points} pts: {bar.prob_pct}%
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 mt-2.5 text-[11px] text-slate-400">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-[#00F5D4]" />
                    <span>Puntos Reales ({ps.simulation_summary?.real_points_total})</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-[#F59E0B]" />
                    <span>Media xPoints ({Math.round(ps.simulation_summary?.expected_points_total || 0)})</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-[#8B5CF6]/70" />
                    <span>Intervalo Confianza 95%</span>
                  </span>
                </div>
                <span className="font-mono-metric text-slate-300">
                  Percentil Real: P{ps.simulation_summary?.real_points_percentile}
                </span>
              </div>
            </div>
          )}

          {/* Si hay una jugada 360 destacada en Cap 2 o Cap 3, mostrar su ficha contextual */}
          {ps.featured_360_event && (
            <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-[11px] font-mono-metric text-[#8B5CF6] uppercase">
                  Instantánea Contextual StatsBomb 360 Destacada
                </div>
                <div className="text-xs sm:text-sm font-bold text-white mt-0.5">
                  {ps.featured_360_event.player_name} vs {ps.featured_360_event.opponent} (Min{' '}
                  {ps.featured_360_event.minute}&apos;)
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono-metric">
                {ps.featured_360_event.defenders_broken > 0 && (
                  <span className="px-2.5 py-1 rounded bg-[#00F5D4]/15 text-[#00F5D4] border border-[#00F5D4]/30">
                    {ps.featured_360_event.defenders_broken} Defensores Superados
                  </span>
                )}
                {ps.featured_360_event.geometry?.hull_area_m2 > 0 && (
                  <span className="px-2.5 py-1 rounded bg-[#8B5CF6]/15 text-[#8B5CF6] border border-[#8B5CF6]/30">
                    Convex Hull: {ps.featured_360_event.geometry.hull_area_m2} m²
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
