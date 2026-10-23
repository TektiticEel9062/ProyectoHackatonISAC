import React, { useState } from 'react';
import PitchSVG from '../components/PitchSVG.jsx';
import {
  ArrowRightLeft,
  CheckCircle2,
  CornerDownRight,
  Crosshair,
  Flame,
  Flag,
  ShieldAlert,
  Sparkles,
  Users,
  Zap,
} from 'lucide-react';

/**
 * Vista 2: Resumen para Cuerpo Técnico (Enfoque Cancha)
 * Lenguaje estrictamente futbolístico y accionable para entrenadores y directores deportivos:
 * 1. Pizarra Táctica de Fases (Salida, Progresión, Remate, Comportamiento tras pérdida)
 * 2. Gestión de Plantilla (Mapa de roles en cancha + Efectividad de sustituciones / Revulsivos)
 * 3. Laboratorio de Balón Parado - ABP (Rutinas ofensivas, vulnerabilidad defensiva y sobrecarga 360 en área chica)
 * 4. Plan de Partido (3 Claves para Potenciar + 3 Claves para Neutralizar)
 */
export default function TacticalStaffView({ tacticalStaff }) {
  const [boardPhase, setBoardPhase] = useState('progression'); // 'progression' | 'finishing' | 'after_loss' | 'roles' | 'set_pieces'
  const [abpSide, setAbpSide] = useState('offensive'); // 'offensive' | 'defensive' | '360'
  const [selectedCornerIdx, setSelectedCornerIdx] = useState(0);

  if (!tacticalStaff) return null;

  const {
    team,
    coach,
    primary_formation,
    phases_board = {},
    squad_management = {},
    set_pieces_lab = {},
    actionable_plan = {},
  } = tacticalStaff;

  const buildup = phases_board.buildup || {};
  const lanes = phases_board.progression_lanes || {};
  const reaction = phases_board.reaction_after_loss || {};
  const subs = squad_management.substitutions || {};
  const playersRoles = squad_management.players_roles || [];
  const startingXI = squad_management.starting_xi || [];
  const corner360List = set_pieces_lab.corner_360_samples || [];
  const activeCorner360 = corner360List[selectedCornerIdx] || corner360List[0] || null;

  // Configurar qué muestra la Pizarra Táctica Principal según la pestaña activa
  let pitchConfig = {
    title: 'Pizarra Táctica de Fases: Construcción y Carriles de Progresión',
    subtitle: 'Vectores de pases progresivos (avance ≥25% hacia meta rival) y envíos que rompen líneas',
  };

  if (boardPhase === 'progression') {
    pitchConfig.progressiveVectors = phases_board.progressive_vectors;
    pitchConfig.startingXI = startingXI;
  } else if (boardPhase === 'finishing') {
    pitchConfig.title = 'Zonas de Finalización y Transiciones Ofensivas Rápidas (<10s)';
    pitchConfig.subtitle =
      'Círculos = Disparos escalados por calidad de ocasión (xG) | Trazos = Contraataques en ≤4 pases';
    pitchConfig.shotsMap = phases_board.shots_map;
    pitchConfig.transitions = (phases_board.transitions || []).slice(0, 30);
  } else if (boardPhase === 'after_loss') {
    pitchConfig.title = 'Comportamiento Tras Pérdida y Altura de Recuperación';
    pitchConfig.subtitle = `Línea media de presión en X=${reaction.defensive_line_height_x} y recuperaciones tras pérdida`;
    pitchConfig.defensiveLineX = reaction.defensive_line_height_x;
    pitchConfig.recoveryLineX = reaction.avg_recovery_height_x;
    pitchConfig.recoveries = reaction.recoveries_sample;
  } else if (boardPhase === 'roles') {
    pitchConfig.title = `Mapa de Roles Tácticos en Cancha (Sistema Base ${primary_formation})`;
    pitchConfig.subtitle = 'Ubicación media de intervención y rol funcional asignado a cada futbolista';
    pitchConfig.startingXI = startingXI;
  } else if (boardPhase === 'set_pieces') {
    pitchConfig.title =
      abpSide === 'offensive'
        ? 'Laboratorio ABP: Rutinas Ofensivas de Tiro de Esquina'
        : abpSide === 'defensive'
        ? 'Laboratorio ABP: Zonas de Caída en Córners Concedidos'
        : 'Laboratorio ABP 360: Sobrecarga en Área Chica al Momento del Cobro';
    pitchConfig.subtitle =
      abpSide === '360' && activeCorner360
        ? `Córner cobrado por ${activeCorner360.taker} vs ${activeCorner360.opponent} (Zona: ${activeCorner360.zone} | Atacantes en área chica: ${activeCorner360.att_in_6yd})`
        : 'Cian = Culminó en remate | Violeta = Sin remate directo';
    if (abpSide === 'offensive') {
      pitchConfig.cornerDeliveries = set_pieces_lab.offensive_deliveries;
    } else if (abpSide === 'defensive') {
      pitchConfig.cornerDeliveries = set_pieces_lab.defensive_deliveries;
    } else {
      pitchConfig.event360 = activeCorner360;
      pitchConfig.showVoronoi = false;
      pitchConfig.showConvexHull = true;
    }
  }

  return (
    <div className="max-w-[1600px] mx-auto px-4 lg:px-6 py-6 space-y-8">
      {/* SECCIÓN 1: PLAN DE PARTIDO (TARJETAS ACCIONABLES) */}
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="text-xs font-mono-metric uppercase tracking-wider text-[#F59E0B]">
              Informe Ejecutivo de Banquillo · Scouting & Plan de Partido
            </span>
            <h2 className="text-xl font-bold text-white mt-0.5">
              Hoja de Ruta Táctica: Potenciar a {team} vs Neutralizar su Modelo
            </h2>
          </div>
          <span className="text-xs font-mono-metric px-3 py-1.5 rounded-xl bg-[#111827] border border-[#1F2937] text-slate-300">
            Sistema Base: <strong className="text-[#00F5D4]">{primary_formation}</strong> · DT: {coach}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 3 Claves para Potenciar a este Equipo */}
          <div className="bg-[#111827] border border-[#00F5D4]/30 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1F2937] pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#00F5D4]/15 border border-[#00F5D4]/40 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-[#00F5D4]" />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-white">
                    3 Claves para Potenciar a {team}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Recomendaciones para el propio cuerpo técnico basadas en ventajas competitivas
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-mono-metric px-2 py-0.5 rounded bg-[#00F5D4]/15 text-[#00F5D4]">
                PROPIO
              </span>
            </div>

            <div className="space-y-3">
              {(actionable_plan.boost_team || []).map((card, i) => (
                <div
                  key={card.id || i}
                  className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-4 hover:border-[#00F5D4]/50 transition-all"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                    <span className="text-[10px] font-mono-metric uppercase tracking-wider text-[#00F5D4]">
                      0{i + 1} · {card.tag}
                    </span>
                    <span className="text-[11px] font-mono-metric px-2 py-0.5 rounded bg-[#00F5D4]/10 text-[#00F5D4] border border-[#00F5D4]/30">
                      {card.metric_badge}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white mb-1">{card.title}</h4>
                  <p className="text-xs text-slate-300 leading-relaxed">{card.Action}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 3 Claves Tácticas para un Rival que Busque Neutralizarlo */}
          <div className="bg-[#111827] border border-[#F43F5E]/30 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1F2937] pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#F43F5E]/15 border border-[#F43F5E]/40 flex items-center justify-center">
                  <Crosshair className="w-4 h-4 text-[#F43F5E]" />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-white">
                    3 Claves para un Rival que Busque Neutralizarlo
                  </h3>
                  <p className="text-xs text-slate-400">
                    Plan de partido opositor para desconectar sus circuitos y explotar grietas
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-mono-metric px-2 py-0.5 rounded bg-[#F43F5E]/15 text-[#F43F5E]">
                RIVAL / SCOUTING
              </span>
            </div>

            <div className="space-y-3">
              {(actionable_plan.neutralize_rival || []).map((card, i) => (
                <div
                  key={card.id || i}
                  className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-4 hover:border-[#F43F5E]/50 transition-all"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                    <span className="text-[10px] font-mono-metric uppercase tracking-wider text-[#F43F5E]">
                      0{i + 1} · {card.tag}
                    </span>
                    <span className="text-[11px] font-mono-metric px-2 py-0.5 rounded bg-[#F43F5E]/10 text-[#F43F5E] border border-[#F43F5E]/30">
                      {card.metric_badge}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white mb-1">{card.title}</h4>
                  <p className="text-xs text-slate-300 leading-relaxed">{card.Action}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SECCIÓN 2: PIZARRA TÁCTICA INTERACTIVA DE FASES */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7 space-y-3">
          {/* Selector de Fase de Juego */}
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-2 flex flex-wrap gap-1.5">
            {[
              { id: 'progression', label: '1. Salida y Progresión', icon: CornerDownRight },
              { id: 'finishing', label: '2. Remate y Transiciones', icon: Zap },
              { id: 'after_loss', label: '3. Tras Pérdida (≤6s)', icon: Flame },
              { id: 'roles', label: '4. Mapa de Roles XI', icon: Users },
              { id: 'set_pieces', label: '5. Laboratorio ABP (Córners)', icon: Flag },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = boardPhase === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setBoardPhase(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                    active
                      ? 'bg-[#00F5D4] text-[#0B0F19]'
                      : 'bg-[#0B0F19] text-slate-300 hover:text-white border border-[#1F2937]'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {boardPhase === 'set_pieces' && (
            <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-2.5 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAbpSide('offensive')}
                  className={`px-3 py-1 rounded-lg text-xs font-mono-metric border ${
                    abpSide === 'offensive'
                      ? 'bg-[#00F5D4]/15 text-[#00F5D4] border-[#00F5D4]/40'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Córners a Favor ({set_pieces_lab.kpis?.offensive_corners_total})
                </button>
                <button
                  onClick={() => setAbpSide('defensive')}
                  className={`px-3 py-1 rounded-lg text-xs font-mono-metric border ${
                    abpSide === 'defensive'
                      ? 'bg-[#F43F5E]/15 text-[#F43F5E] border-[#F43F5E]/40'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Córners en Contra ({set_pieces_lab.kpis?.defensive_corners_total})
                </button>
                <button
                  onClick={() => setAbpSide('360')}
                  className={`px-3 py-1 rounded-lg text-xs font-mono-metric border ${
                    abpSide === '360'
                      ? 'bg-[#8B5CF6]/20 text-[#8B5CF6] border-[#8B5CF6]/40'
                      : 'bg-[#0B0F19] text-slate-400 border-[#1F2937]'
                  }`}
                >
                  Ocupación Área Chica 360
                </button>
              </div>

              {abpSide === '360' && corner360List.length > 1 && (
                <select
                  value={selectedCornerIdx}
                  onChange={(e) => setSelectedCornerIdx(Number(e.target.value))}
                  className="bg-[#0B0F19] border border-[#334155] rounded-lg px-2.5 py-1 text-xs text-white font-mono-metric"
                >
                  {corner360List.map((c, idx) => (
                    <option key={c.event_id || idx} value={idx}>
                      {c.zone} vs {c.opponent} (Min {c.minute}&apos;)
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          <PitchSVG {...pitchConfig} />
        </div>

        {/* Panel Derecho de Desglose Futbolístico por Fase */}
        <div className="lg:col-span-5 space-y-5">
          {/* Card 1: Salida de Fondo y Carriles de Progresión */}
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center justify-between">
              <span>Diagnóstico de Fase con Balón y Tras Pérdida</span>
              <span className="text-[11px] font-mono-metric text-[#00F5D4]">Lenguaje Cancha</span>
            </h3>

            {/* Salida Corta vs Larga */}
            <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3.5 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-semibold">
                  Salida Asociativa Corta ({buildup.short_ratio_pct}%)
                </span>
                <span className="font-mono-metric text-[#00F5D4]">
                  {buildup.short_accuracy_pct}% efectividad ({buildup.short_obv_net > 0 ? '+' : ''}
                  {buildup.short_obv_net} OBV)
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${buildup.short_ratio_pct || 75}%` }}
                  className="bg-[#00F5D4] h-full"
                />
                <div
                  style={{ width: `${100 - (buildup.short_ratio_pct || 75)}%` }}
                  className="bg-[#F59E0B] h-full"
                />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Envío en corto (&lt;28m): {buildup.short_passes_completed} completados</span>
                <span>
                  Envío directo largo: {buildup.long_accuracy_pct}% éxito ({buildup.long_obv_net} OBV)
                </span>
              </div>
            </div>

            {/* Carriles de Progresión */}
            <div className="grid grid-cols-3 gap-2.5">
              {['left', 'center', 'right'].map((key) => {
                const l = lanes[key] || {};
                const titleShort =
                  key === 'left'
                    ? 'Carril Izquierdo'
                    : key === 'center'
                    ? 'Carril Central'
                    : 'Carril Derecho';
                return (
                  <div
                    key={key}
                    className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3 text-center"
                  >
                    <div className="text-[11px] text-slate-400">{titleShort}</div>
                    <div className="text-base font-bold font-mono-metric text-white mt-1">
                      {l.progressive} prog.
                    </div>
                    <div className="text-[11px] font-mono-metric text-[#00F5D4] mt-0.5">
                      {l.obv > 0 ? '+' : ''}
                      {l.obv} OBV
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Comportamiento Tras Pérdida */}
            <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3.5 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-semibold">
                  Reacción Inmediata Tras Pérdida (≤6 seg)
                </span>
                <span className="font-mono-metric text-[#F59E0B]">
                  {reaction.counterpress_share_pct}% de la presión activa
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                El equipo ejecuta <strong>{reaction.counterpress_events_6s}</strong> acciones de
                contra-presión inmediata tras perder la posesión y{' '}
                <strong>{reaction.high_press_events_x80}</strong> presiones en tercio ofensivo (X≥80),
                recuperando el balón a una altura media de{' '}
                <strong className="text-white">X = {reaction.avg_recovery_height_x}m</strong>.
              </p>
            </div>
          </div>

          {/* Card 2: Laboratorio de Balón Parado (ABP) */}
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-3.5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white">
                Laboratorio de Balón Parado (ABP Ofensivo vs Defensivo)
              </h3>
              <span className="text-[11px] font-mono-metric text-[#8B5CF6]">
                Sobrecarga Área Chica 360
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#1F2937] text-[10px] font-mono-metric uppercase text-slate-400">
                    <th className="py-2">Zona de Entrega</th>
                    <th className="py-2 text-right">A Favor (Rem%)</th>
                    <th className="py-2 text-right">xG Propio</th>
                    <th className="py-2 text-right">xG Concedido</th>
                    <th className="py-2 text-right">Atac. Área Chica</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1F2937]/60 font-mono-metric">
                  {(set_pieces_lab.offensive_by_zone || []).map((oz, idx) => {
                    const dz =
                      (set_pieces_lab.defensive_by_zone || []).find((d) => d.zone === oz.zone) || {};
                    return (
                      <tr key={oz.zone || idx} className="hover:bg-[#0B0F19]/60">
                        <td className="py-2 font-sans font-medium text-slate-200">{oz.zone}</td>
                        <td className="py-2 text-right text-[#00F5D4]">
                          {oz.count} ({oz.shot_conversion_pct}%)
                        </td>
                        <td className="py-2 text-right text-white">{oz.xg_total}</td>
                        <td className="py-2 text-right text-[#F43F5E]">
                          {dz.xg_conceded ?? 0} ({dz.shot_conceded_pct ?? 0}%)
                        </td>
                        <td className="py-2 text-right text-[#8B5CF6]">
                          {oz.avg_attackers_6yd} vs {oz.avg_defenders_6yd}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* SECCIÓN 3: GESTIÓN DE PLANTILLA, ROLES Y EFECTIVIDAD DE SUSTITUCIONES */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Mapa de Roles de Jugadores */}
        <div className="lg:col-span-7 bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-base font-bold text-white">
                Estructura de Plantilla y Roles Funcionales (P90)
              </h3>
              <p className="text-xs text-slate-400">
                Perfiles tácticos identificados automáticamente por comportamiento en cancha
              </p>
            </div>
            <span className="text-xs font-mono-metric text-[#00F5D4]">
              {playersRoles.length} Jugadores Auditados (≥180 mins)
            </span>
          </div>

          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="sticky top-0 bg-[#111827] border-b border-[#1F2937] text-[10px] font-mono-metric uppercase text-slate-400">
                <tr>
                  <th className="py-2.5 pr-2">Futbolista</th>
                  <th className="py-2.5 px-2">Rol Táctico Asignado</th>
                  <th className="py-2.5 px-2 text-right">Mins</th>
                  <th className="py-2.5 px-2 text-right">Pases Prog/90</th>
                  <th className="py-2.5 px-2 text-right">Cond. Prog/90</th>
                  <th className="py-2.5 px-2 text-right">Presiones/90</th>
                  <th className="py-2.5 pl-2 text-right">OBV Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2937]/60">
                {playersRoles.slice(0, 16).map((pl, idx) => (
                  <tr key={pl.player_name || idx} className="hover:bg-[#0B0F19]/60">
                    <td className="py-2 pr-2 font-medium text-white">
                      {pl.player_name}
                      <span className="block text-[10px] text-slate-400">{pl.position}</span>
                    </td>
                    <td className="py-2 px-2">
                      <span
                        className="inline-block text-[11px] px-2 py-0.5 rounded-md font-medium border"
                        style={{
                          color: pl.role_color || '#00F5D4',
                          borderColor: `${pl.role_color || '#00F5D4'}55`,
                          backgroundColor: `${pl.role_color || '#00F5D4'}15`,
                        }}
                      >
                        {pl.tactical_role}
                      </span>
                    </td>
                    <td className="py-2 px-2 text-right font-mono-metric text-slate-300">
                      {pl.minutes}&apos;
                    </td>
                    <td className="py-2 px-2 text-right font-mono-metric text-[#00F5D4]">
                      {pl.metrics_p90?.prog_passes_p90}
                    </td>
                    <td className="py-2 px-2 text-right font-mono-metric text-slate-200">
                      {pl.metrics_p90?.prog_carries_p90}
                    </td>
                    <td className="py-2 px-2 text-right font-mono-metric text-[#F59E0B]">
                      {pl.metrics_p90?.pressures_p90}
                    </td>
                    <td className="py-2 pl-2 text-right font-mono-metric font-bold text-white">
                      {pl.obv_total > 0 ? `+${pl.obv_total}` : pl.obv_total}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Impacto de Sustituciones y Revulsivos */}
        <div className="lg:col-span-5 bg-[#111827] border border-[#1F2937] rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ArrowRightLeft className="w-4 h-4 text-[#F59E0B]" />
                <span>Efectividad de Sustituciones y Revulsivos</span>
              </h3>
              <p className="text-xs text-slate-400">
                Impacto real en diferencial de ocasiones (ΔxG/90&apos;) y posesión tras cada cambio
              </p>
            </div>
            <span className="text-xs font-mono-metric px-2.5 py-1 rounded bg-[#F59E0B]/15 text-[#F59E0B]">
              Min. Medio: {subs.avg_substitution_minute}&apos;
            </span>
          </div>

          {/* Resumen de Cambios según Marcador */}
          <div className="grid grid-cols-3 gap-2.5">
            {['Winning', 'Drawing', 'Losing'].map((gs) => {
              const info = (subs.by_game_state || {})[gs] || {};
              const labelEs =
                gs === 'Winning' ? 'Ganando' : gs === 'Drawing' ? 'Empatando' : 'Perdiendo';
              return (
                <div
                  key={gs}
                  className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3 text-center"
                >
                  <div className="text-[11px] text-slate-400">{labelEs}</div>
                  <div className="text-sm font-bold font-mono-metric text-white mt-0.5">
                    Min {info.avg_minute}&apos; ({info.count})
                  </div>
                  <div
                    className={`text-[11px] font-mono-metric mt-0.5 ${
                      (info.avg_delta_xg_diff_per_90 || 0) >= 0
                        ? 'text-[#00F5D4]'
                        : 'text-[#F43F5E]'
                    }`}
                  >
                    {(info.avg_delta_xg_diff_per_90 || 0) >= 0 ? '+' : ''}
                    {info.avg_delta_xg_diff_per_90} ΔxG/90&apos;
                  </div>
                </div>
              );
            })}
          </div>

          {/* Tabla de Principales Revulsivos */}
          <div>
            <div className="text-xs font-semibold text-slate-300 mb-2">
              Ranking de Revulsivos (Impacto neto tras ingresar desde el banquillo)
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#1F2937] text-[10px] font-mono-metric uppercase text-slate-400">
                    <th className="py-2">Jugador (Revulsivo)</th>
                    <th className="py-2 text-right">Ingresos</th>
                    <th className="py-2 text-right">Min. Entrada</th>
                    <th className="py-2 text-right">ΔxG diff / 90&apos;</th>
                    <th className="py-2 text-right">Δ Posesión</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1F2937]/60 font-mono-metric">
                  {(subs.top_impact_subs || []).map((sub, i) => (
                    <tr key={sub.player_name || i} className="hover:bg-[#0B0F19]/60">
                      <td className="py-2 font-sans font-medium text-white">{sub.player_name}</td>
                      <td className="py-2 text-right text-slate-300">{sub.sub_appearances}</td>
                      <td className="py-2 text-right text-slate-400">{sub.avg_entry_minute}&apos;</td>
                      <td
                        className={`py-2 text-right font-bold ${
                          sub.avg_delta_xg_diff_per_90 >= 0 ? 'text-[#00F5D4]' : 'text-[#F43F5E]'
                        }`}
                      >
                        {sub.avg_delta_xg_diff_per_90 >= 0 ? '+' : ''}
                        {sub.avg_delta_xg_diff_per_90}
                      </td>
                      <td
                        className={`py-2 text-right ${
                          sub.avg_delta_possession_pct >= 0 ? 'text-emerald-400' : 'text-amber-400'
                        }`}
                      >
                        {sub.avg_delta_possession_pct >= 0 ? '+' : ''}
                        {sub.avg_delta_possession_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
