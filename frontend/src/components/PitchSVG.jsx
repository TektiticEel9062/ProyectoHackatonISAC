import React, { useState } from 'react';
import FreezeFrame360 from './FreezeFrame360.jsx';

/**
 * frontend/src/components/PitchSVG.jsx
 * Cancha vectorial interactiva normalizada al estándar StatsBomb (X in [0, 120], Y in [0, 80]).
 * Soporta superposición modular de:
 * - Grillas de calor 6x4 (probabilidad o diferencial KL)
 * - Redes de pases dirigidas ponderadas (Teoría de Grafos)
 * - Once titular promedio con roles tácticos
 * - Vectores de pases progresivos y transiciones rápidas
 * - Mapa de tiros xG y córners ABP
 * - Instantáneas 360 (Voronoi, Convex Hull, Delaunay)
 */
export default function PitchSVG({
  title,
  subtitle,
  heatmapGrid6x4 = null,
  isDiffGrid = false,
  startingXI = null,
  passingNetwork = null,
  progressiveVectors = null,
  transitions = null,
  shotsMap = null,
  recoveries = null,
  defensiveLineX = null,
  recoveryLineX = null,
  cornerDeliveries = null,
  event360 = null,
  showVoronoi = true,
  showConvexHull = true,
  showDelaunay = false,
  showVisibleArea = true,
  footerLegend = null,
}) {
  const [hoveredItem, setHoveredItem] = useState(null);

  // Función de color para celdas de la grilla 6x4 (4 filas Y x 6 columnas X)
  const getCellFill = (val) => {
    if (isDiffGrid) {
      // Diferencial KL (ej. Perdiendo - Ganando): positivo en Ámbar/Carmesí, negativo en Cian/Azul
      if (val > 0.15) {
        const op = Math.min(0.62, 0.12 + Math.abs(val) * 0.11);
        return { fill: '#F43F5E', opacity: op };
      }
      if (val < -0.15) {
        const op = Math.min(0.55, 0.1 + Math.abs(val) * 0.1);
        return { fill: '#00F5D4', opacity: op };
      }
      return { fill: '#1E293B', opacity: 0.12 };
    }
    // Grilla de densidad base (% de pases)
    const op = Math.min(0.58, Math.max(0.04, (val / 8.5) * 0.52));
    return { fill: '#00F5D4', opacity: op };
  };

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-3 sm:p-4 shadow-2xl flex flex-col">
      {/* Cabecera de la Pizarra */}
      {(title || subtitle) && (
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5 px-1">
          <div>
            {title && (
              <h3 className="text-xs sm:text-sm font-bold text-white tracking-wide flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#00F5D4]" />
                <span>{title}</span>
              </h3>
            )}
            {subtitle && <p className="text-[11px] text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          <div className="flex items-center gap-2 text-[10px] font-mono-metric text-slate-400 bg-[#0B0F19] px-2.5 py-1 rounded-lg border border-[#1F2937]">
            <span>StatsBomb 120×80</span>
            <span className="text-[#00F5D4]">Ataque → X=120</span>
          </div>
        </div>
      )}

      {/* Lienzo Vectorial SVG (120 x 80 con margen de 4 unidades) */}
      <div className="relative w-full aspect-[128/88] bg-[#0B0F19] rounded-xl border border-[#1F2937] overflow-hidden">
        <svg
          viewBox="-4 -4 128 88"
          className="w-full h-full select-none"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <marker
              id="arrow-cyan"
              viewBox="0 0 10 10"
              refX="7"
              refY="5"
              markerWidth="3.2"
              markerHeight="3.2"
              orient="auto-start-reverse"
            >
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#00F5D4" />
            </marker>
            <marker
              id="arrow-amber"
              viewBox="0 0 10 10"
              refX="7"
              refY="5"
              markerWidth="3.2"
              markerHeight="3.2"
              orient="auto-start-reverse"
            >
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#F59E0B" />
            </marker>
            <marker
              id="arrow-crimson"
              viewBox="0 0 10 10"
              refX="7"
              refY="5"
              markerWidth="3.2"
              markerHeight="3.2"
              orient="auto-start-reverse"
            >
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#F43F5E" />
            </marker>
            <marker
              id="arrow-violet"
              viewBox="0 0 10 10"
              refX="7"
              refY="5"
              markerWidth="3.2"
              markerHeight="3.2"
              orient="auto-start-reverse"
            >
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#8B5CF6" />
            </marker>
          </defs>

          {/* Fondo de Cancha */}
          <rect x="0" y="0" width="120" height="80" fill="#0B0F19" />

          {/* 1. Capa de Grilla Espacial 6x4 (si está activa) */}
          {heatmapGrid6x4 &&
            heatmapGrid6x4.map((row, rIdx) =>
              row.map((val, cIdx) => {
                const { fill, opacity } = getCellFill(val);
                const cellX = cIdx * 20;
                const cellY = rIdx * 20;
                return (
                  <g key={`grid-${rIdx}-${cIdx}`}>
                    <rect
                      x={cellX}
                      y={cellY}
                      width="20"
                      height="20"
                      fill={fill}
                      fillOpacity={opacity}
                      stroke="#1F2937"
                      strokeWidth="0.2"
                    />
                    <text
                      x={cellX + 10}
                      y={cellY + 11}
                      textAnchor="middle"
                      fill="#E2E8F0"
                      fillOpacity="0.72"
                      fontSize="2.2"
                      fontFamily="JetBrains Mono, monospace"
                    >
                      {isDiffGrid ? `${val > 0 ? '+' : ''}${val}%` : `${val}%`}
                    </text>
                  </g>
                );
              })
            )}

          {/* Líneas Reglamentarias de Cancha StatsBomb 120x80 en #334155 */}
          <g stroke="#334155" strokeWidth="0.42" fill="none">
            {/* Contorno exterior */}
            <rect x="0" y="0" width="120" height="80" />
            {/* Línea de medio campo */}
            <line x1="60" y1="0" x2="60" y2="80" />
            {/* Círculo central */}
            <circle cx="60" cy="40" r="9.15" />
            <circle cx="60" cy="40" r="0.6" fill="#334155" />

            {/* Área grande izquierda */}
            <rect x="0" y="18" width="18" height="44" />
            {/* Área chica izquierda */}
            <rect x="0" y="30" width="6" height="20" />
            {/* Punto penal izquierdo y arco */}
            <circle cx="12" cy="40" r="0.5" fill="#334155" />
            <path d="M 18 32.5 A 9.15 9.15 0 0 1 18 47.5" />
            {/* Portería izquierda */}
            <rect x="-2" y="36" width="2" height="8" stroke="#475569" />

            {/* Área grande derecha (Rival) */}
            <rect x="102" y="18" width="18" height="44" />
            {/* Área chica derecha */}
            <rect x="114" y="30" width="6" height="20" />
            {/* Punto penal derecho y arco */}
            <circle cx="108" cy="40" r="0.5" fill="#334155" />
            <path d="M 102 32.5 A 9.15 9.15 0 0 0 102 47.5" />
            {/* Portería derecha */}
            <rect x="120" y="36" width="2" height="8" stroke="#475569" />

            {/* Líneas punteadas sutiles de tercios (X=40 y X=80) */}
            <line x1="40" y1="0" x2="40" y2="80" strokeDasharray="1.5 1.5" strokeOpacity="0.45" />
            <line x1="80" y1="0" x2="80" y2="80" strokeDasharray="1.5 1.5" strokeOpacity="0.45" />
          </g>

          {/* Etiquetas de Tercios en el margen inferior */}
          <g fill="#64748B" fontSize="2.0" fontFamily="JetBrains Mono, monospace">
            <text x="20" y="82.8" textAnchor="middle">
              Tercio Inicio (0-40)
            </text>
            <text x="60" y="82.8" textAnchor="middle">
              Tercio Medio (40-80)
            </text>
            <text x="100" y="82.8" textAnchor="middle">
              Tercio Final (80-120)
            </text>
          </g>

          {/* 2. Líneas de Altura Defensiva y de Recuperación */}
          {defensiveLineX != null && (
            <g>
              <line
                x1={defensiveLineX}
                y1="2"
                x2={defensiveLineX}
                y2="78"
                stroke="#F59E0B"
                strokeWidth="0.7"
                strokeDasharray="2 1.2"
              />
              <rect
                x={defensiveLineX - 13}
                y="2.5"
                width="26"
                height="4.2"
                rx="1"
                fill="#0B0F19"
                stroke="#F59E0B"
                strokeWidth="0.3"
              />
              <text
                x={defensiveLineX}
                y="5.3"
                textAnchor="middle"
                fill="#F59E0B"
                fontSize="2.0"
                fontFamily="JetBrains Mono, monospace"
                fontWeight="bold"
              >
                {`Alt. Presión X=${defensiveLineX}`}
              </text>
            </g>
          )}

          {recoveryLineX != null && (
            <g>
              <line
                x1={recoveryLineX}
                y1="2"
                x2={recoveryLineX}
                y2="78"
                stroke="#00F5D4"
                strokeWidth="0.55"
                strokeDasharray="1.2 1.2"
              />
              <rect
                x={recoveryLineX - 13}
                y="73.2"
                width="26"
                height="4.2"
                rx="1"
                fill="#0B0F19"
                stroke="#00F5D4"
                strokeWidth="0.3"
              />
              <text
                x={recoveryLineX}
                y="76"
                textAnchor="middle"
                fill="#00F5D4"
                fontSize="2.0"
                fontFamily="JetBrains Mono, monospace"
              >
                {`Recuperación X=${recoveryLineX}`}
              </text>
            </g>
          )}

          {/* 3. Vectores de Pases Progresivos */}
          {progressiveVectors &&
            progressiveVectors.map((vec, i) => (
              <line
                key={`prog-${i}`}
                x1={vec.start_x}
                y1={vec.start_y}
                x2={vec.end_x}
                y2={vec.end_y}
                stroke={vec.broken_defenders >= 2 ? '#8B5CF6' : '#00F5D4'}
                strokeOpacity="0.65"
                strokeWidth={vec.broken_defenders >= 2 ? '0.6' : '0.42'}
                markerEnd={vec.broken_defenders >= 2 ? 'url(#arrow-violet)' : 'url(#arrow-cyan)'}
                onMouseEnter={() =>
                  setHoveredItem({
                    title: `${vec.player} → ${vec.recipient || 'Compañero'}`,
                    detail: `OBV: +${vec.obv} | Def. superados: ${vec.broken_defenders || 0}`,
                  })
                }
                onMouseLeave={() => setHoveredItem(null)}
              />
            ))}

          {/* 4. Trayectorias de Contraataques / Transiciones (<10s, <=4 pases) */}
          {transitions &&
            transitions.map((tr, idx) => {
              const pts = (tr.path || [])
                .map((p) => `${p[0]},${p[1]}`)
                .join(' ');
              if (!pts) return null;
              return (
                <g
                  key={`tr-${idx}`}
                  className="cursor-pointer"
                  onMouseEnter={() =>
                    setHoveredItem({
                      title: `Contraataque: ${tr.initiator} → ${tr.finisher} (Min ${tr.minute}')`,
                      detail: `Duración: ${tr.duration_sec}s | xG: ${tr.xg} | ${
                        tr.ended_in_goal ? '⚽ GOL' : tr.ended_in_shot ? 'Finalizó en Tiro' : 'Ingreso a X≥80'
                      }`,
                    })
                  }
                  onMouseLeave={() => setHoveredItem(null)}
                >
                  <polyline
                    points={pts}
                    fill="none"
                    stroke={tr.ended_in_goal ? '#00F5D4' : '#F59E0B'}
                    strokeWidth={tr.ended_in_shot ? '0.65' : '0.4'}
                    strokeOpacity="0.82"
                    markerEnd={tr.ended_in_goal ? 'url(#arrow-cyan)' : 'url(#arrow-amber)'}
                  />
                  <circle
                    cx={tr.origin_x}
                    cy={tr.origin_y}
                    r="1.05"
                    fill="#F59E0B"
                  />
                </g>
              );
            })}

          {/* 5. Envíos de Córner (Laboratorio ABP) */}
          {cornerDeliveries &&
            cornerDeliveries.map((c, idx) => {
              if (c.start_x == null || c.end_x == null) return null;
              const isShot = c.led_to_shot;
              return (
                <line
                  key={`cor-${idx}`}
                  x1={c.start_x}
                  y1={c.start_y}
                  x2={c.end_x}
                  y2={c.end_y}
                  stroke={isShot ? '#00F5D4' : '#8B5CF6'}
                  strokeOpacity={isShot ? '0.82' : '0.45'}
                  strokeWidth={isShot ? '0.6' : '0.35'}
                  markerEnd={isShot ? 'url(#arrow-cyan)' : 'url(#arrow-violet)'}
                />
              );
            })}

          {/* 6. Puntos de Recuperación Defensiva */}
          {recoveries &&
            recoveries.map((rec, idx) => (
              <circle
                key={`rec-${idx}`}
                cx={rec.x}
                cy={rec.y}
                r="1.05"
                fill={rec.x >= 80 ? '#F43F5E' : '#F59E0B'}
                fillOpacity="0.78"
                stroke="#0B0F19"
                strokeWidth="0.25"
              />
            ))}

          {/* 7. Mapa de Disparos (xG escalado al radio) */}
          {shotsMap &&
            shotsMap.map((sh, idx) => {
              const radius = Math.max(0.95, Math.min(2.8, 0.85 + Math.sqrt(sh.xg || 0.05) * 3.1));
              return (
                <circle
                  key={`shot-${idx}`}
                  cx={sh.x}
                  cy={sh.y}
                  r={radius}
                  fill={sh.is_goal ? '#00F5D4' : '#F43F5E'}
                  fillOpacity={sh.is_goal ? '0.9' : '0.52'}
                  stroke={sh.is_goal ? '#FFFFFF' : '#F43F5E'}
                  strokeWidth="0.32"
                  className="cursor-pointer"
                  onMouseEnter={() =>
                    setHoveredItem({
                      title: `${sh.player_name} (${sh.minute}') vs ${sh.opponent}`,
                      detail: `xG: ${sh.xg} | Resultado: ${sh.is_goal ? '⚽ GOL' : sh.outcome}`,
                    })
                  }
                  onMouseLeave={() => setHoveredItem(null)}
                />
              );
            })}

          {/* 8. Red de Pases (Teoría de Grafos: Aristas + Nodos escalados por Centralidad) */}
          {passingNetwork && (
            <g>
              {(passingNetwork.edges || []).map((edge, idx) => {
                const sw = Math.min(1.6, Math.max(0.28, edge.weight / 28));
                return (
                  <line
                    key={`edge-${idx}`}
                    x1={edge.source_x}
                    y1={edge.source_y}
                    x2={edge.target_x}
                    y2={edge.target_y}
                    stroke="#00F5D4"
                    strokeOpacity={Math.min(0.82, 0.25 + edge.weight / 90)}
                    strokeWidth={sw}
                  />
                );
              })}
              {(passingNetwork.nodes || []).map((node, idx) => {
                const r = 1.65 + (node.betweenness_centrality || 0) * 4.5;
                const isHub = node.name === passingNetwork.hub_player;
                return (
                  <g
                    key={`node-${idx}`}
                    transform={`translate(${node.x}, ${node.y})`}
                    className="cursor-pointer"
                    onMouseEnter={() =>
                      setHoveredItem({
                        title: `${node.name} (${node.position})`,
                        detail: `Betweenness: ${node.betweenness_centrality} | Pases env/rec: ${node.passes_sent}/${node.passes_received}`,
                      })
                    }
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    {isHub && (
                      <circle
                        r={r + 1.1}
                        fill="none"
                        stroke="#8B5CF6"
                        strokeWidth="0.45"
                      />
                    )}
                    <circle
                      r={r}
                      fill={isHub ? '#8B5CF6' : '#00F5D4'}
                      stroke="#0B0F19"
                      strokeWidth="0.45"
                    />
                    <text
                      y={r + 2.3}
                      textAnchor="middle"
                      fill="#F8FAFC"
                      fontSize="1.95"
                      fontWeight="600"
                      fontFamily="Inter, sans-serif"
                    >
                      {node.short_name}
                    </text>
                  </g>
                );
              })}
            </g>
          )}

          {/* 9. Once Titular Promedio (si no se está mostrando ya la red completa o en modo ADN) */}
          {startingXI && !passingNetwork && (
            <g>
              {startingXI.map((pl, idx) => (
                <g
                  key={`xi-${idx}`}
                  transform={`translate(${pl.avg_x}, ${pl.avg_y})`}
                  className="cursor-pointer"
                  onMouseEnter={() =>
                    setHoveredItem({
                      title: `${pl.player_name} (${pl.position}) — ${pl.tactical_role}`,
                      detail: `${pl.minutes} mins | OBV: ${pl.obv_total} | xG: ${pl.xg_total}`,
                    })
                  }
                  onMouseLeave={() => setHoveredItem(null)}
                >
                  <circle
                    r="2.1"
                    fill={pl.role_color || '#00F5D4'}
                    stroke="#0B0F19"
                    strokeWidth="0.45"
                  />
                  <text
                    y="3.8"
                    textAnchor="middle"
                    fill="#F8FAFC"
                    fontSize="2.0"
                    fontWeight="bold"
                  >
                    {pl.short_name}
                  </text>
                </g>
              ))}
            </g>
          )}

          {/* 10. Instantánea StatsBomb 360 (Voronoi, Convex Hull, Delaunay) */}
          {event360 && (
            <FreezeFrame360
              event360={event360}
              showVoronoi={showVoronoi}
              showConvexHull={showConvexHull}
              showDelaunay={showDelaunay}
              showVisibleArea={showVisibleArea}
            />
          )}
        </svg>

        {/* Tooltip Flotante en Cancha */}
        {hoveredItem && (
          <div className="absolute bottom-3 left-3 bg-[#0B0F19]/95 border border-[#00F5D4]/50 rounded-lg px-3 py-1.5 text-xs shadow-xl pointer-events-none">
            <div className="font-bold text-white">{hoveredItem.title}</div>
            <div className="text-[#00F5D4] font-mono-metric text-[11px]">{hoveredItem.detail}</div>
          </div>
        )}
      </div>

      {/* Leyenda Semántica Inferior Dinámica (100% adaptada a las capas activas en cancha) */}
      {footerLegend ? (
        <div className="mt-2.5 pt-2 border-t border-[#1F2937]">{footerLegend}</div>
      ) : (
        <div className="mt-2.5 pt-2 border-t border-[#1F2937] flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
          <div className="flex flex-wrap items-center gap-x-3.5 gap-y-1.5">
            {/* Caso 1: Once Titular 4-2-3-1 por Roles Tácticos */}
            {startingXI && !passingNetwork && (
              <>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#94A3B8]" />
                  <span>Portero Líbero</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#8B5CF6]" />
                  <span>Central Corrector</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#38BDF8]" />
                  <span>Carrilero Exterior</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                  <span>Pivote Presión</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#00F5D4]" />
                  <span>Interior Organizador</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]" />
                  <span>Atacante / Extremo</span>
                </span>
                {heatmapGrid6x4 && !isDiffGrid && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-[#00F5D4]/40 border border-[#00F5D4]" />
                    <span>Grilla: % Volumen de Pases</span>
                  </span>
                )}
              </>
            )}

            {/* Caso 2: Red de Pases (Teoría de Grafos) */}
            {passingNetwork && (
              <>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#8B5CF6] ring-2 ring-[#8B5CF6]/40" />
                  <span>Hub Organizador (Mayor Intermediación)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#00F5D4]" />
                  <span>Nodo Jugador (Radio = Centralidad)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-0.5 bg-[#00F5D4]" />
                  <span>Flujo de Pases (Grosor = Frecuencia)</span>
                </span>
                {heatmapGrid6x4 && !isDiffGrid && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-[#00F5D4]/40 border border-[#00F5D4]" />
                    <span>Grilla: % Pases por Zona</span>
                  </span>
                )}
              </>
            )}

            {/* Caso 3: Mapa de Disparos xG */}
            {shotsMap && (
              <>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#00F5D4] border border-white" />
                  <span>Gol Anotado (América)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]/80 border border-[#F43F5E]" />
                  <span>Tiro sin Gol (Atajado / Desviado / Bloqueado)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full border border-slate-400" />
                  <span>Tamaño del Círculo = Probabilidad de Gol (xG)</span>
                </span>
              </>
            )}

            {/* Caso 4: Grilla de Densidad Simple (cuando no hay XI ni Red de Pases) */}
            {heatmapGrid6x4 && !isDiffGrid && !startingXI && !passingNetwork && (
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#00F5D4]/45 border border-[#00F5D4]" />
                <span>Grilla Cian: % Volumen / Densidad Espacial por Zona (6×4)</span>
              </span>
            )}

            {/* Caso 4B: Grilla de Diferencial KL y/o Transiciones */}
            {(isDiffGrid || transitions) && (
              <>
                {isDiffGrid && (
                  <>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-sm bg-[#F43F5E]/60 border border-[#F43F5E]" />
                      <span>Celda Roja (+%): Mayor Volumen en Estado P (ej. Perdiendo)</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-sm bg-[#00F5D4]/50 border border-[#00F5D4]" />
                      <span>Celda Cian (-%): Mayor Volumen en Estado Q (ej. Ganando)</span>
                    </span>
                  </>
                )}
                {transitions && (
                  <>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                      <span>Recuperación Origen (X ≤ 60)</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-3.5 h-0.5 bg-[#00F5D4]" />
                      <span>Contraataque en Gol</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-3.5 h-0.5 bg-[#F59E0B]" />
                      <span>Transición Rápida a X≥80 / Tiro (≤15s)</span>
                    </span>
                  </>
                )}
              </>
            )}

            {/* Caso 5: Vectores Progresivos */}
            {progressiveVectors && (
              <>
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-0.5 bg-[#8B5CF6]" />
                  <span>Pase Progresivo de Ruptura (≥ 2 Def. Superados)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-0.5 bg-[#00F5D4]" />
                  <span>Pase Progresivo (1 Def. Superado)</span>
                </span>
              </>
            )}

            {/* Caso 6: Bloque Defensivo / Recuperaciones */}
            {(defensiveLineX != null || recoveries) && (
              <>
                {defensiveLineX != null && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-3.5 h-0.5 bg-[#F59E0B]" />
                    <span>Línea Media de Presión (X={defensiveLineX})</span>
                  </span>
                )}
                {recoveryLineX != null && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-3.5 h-0.5 bg-[#00F5D4]" />
                    <span>Línea Media de Recuperación (X={recoveryLineX})</span>
                  </span>
                )}
                {recoveries && (
                  <>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]" />
                      <span>Recuperación en Tercio Alto (X ≥ 80)</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                      <span>Recuperación en Bloque Medio/Bajo</span>
                    </span>
                  </>
                )}
              </>
            )}

            {/* Caso 7: Envíos de Córner */}
            {cornerDeliveries && (
              <>
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-0.5 bg-[#00F5D4]" />
                  <span>Córner que Generó Remate</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-0.5 bg-[#8B5CF6]" />
                  <span>Envío de Córner sin Remate</span>
                </span>
              </>
            )}

            {/* Caso 8: Instantánea StatsBomb 360 */}
            {event360 && (
              <>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B] ring-2 ring-[#F59E0B]/40" />
                  <span>Actor con Balón (Radio 3m)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#00F5D4]" />
                  <span>Jugador América (360)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]" />
                  <span>Jugador Rival (360)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-[#8B5CF6]/40 border border-[#8B5CF6]" />
                  <span>Convex Hull (m²) / Cámara 360</span>
                </span>
              </>
            )}
          </div>
          <span className="font-mono-metric text-[10px] text-slate-500">
            Pasa el cursor sobre los elementos para inspeccionar
          </span>
        </div>
      )}
    </div>
  );
}
