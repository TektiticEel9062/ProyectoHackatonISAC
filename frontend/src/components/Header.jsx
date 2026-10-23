import React from 'react';
import { BookOpen, Compass, Cpu, Download, ShieldCheck, Sparkles } from 'lucide-react';

export default function Header({
  summary,
  activeTab,
  setActiveTab,
  onExportClick,
  isStandalone,
}) {
  const navItems = [
    {
      id: 'scrollytelling',
      label: '1. La Historia del Entrenador',
      badge: 'Scrollytelling',
      icon: BookOpen,
      accent: 'text-[#00F5D4] border-[#00F5D4]',
    },
    {
      id: 'tactical-staff',
      label: '2. Resumen Cuerpo Técnico',
      badge: 'Enfoque Cancha',
      icon: Compass,
      accent: 'text-[#F59E0B] border-[#F59E0B]',
    },
    {
      id: 'deep-dive',
      label: '3. Deep-Dive Analítico',
      badge: 'Data Science & 360',
      icon: Cpu,
      accent: 'text-[#8B5CF6] border-[#8B5CF6]',
    },
  ];

  const teamName = summary?.target_team || 'Club América';
  const coachName = summary?.target_coach || 'André Soares Jardine';
  const matchesCount = summary?.total_matches || 37;
  const totalEvents = summary?.capabilities?.total_events || 121369;
  const total360 = summary?.capabilities?.total_360_frames || 108144;

  return (
    <header className="sticky top-0 z-40 bg-[#0B0F19]/95 backdrop-blur-md border-b border-[#1F2937]">
      <div className="max-w-[1600px] mx-auto px-4 lg:px-6 py-3 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Identidad del Proyecto y Sujeto de Estudio */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00F5D4]/20 via-[#8B5CF6]/20 to-[#F59E0B]/20 border border-[#00F5D4]/40 flex items-center justify-center shadow-lg shadow-[#00F5D4]/5">
            <Sparkles className="w-5 h-5 text-[#00F5D4]" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-mono-metric uppercase tracking-wider px-2 py-0.5 rounded bg-[#00F5D4]/10 text-[#00F5D4] border border-[#00F5D4]/30">
                StatsBomb 360 + OBV
              </span>
              <span className="text-[11px] font-mono-metric text-slate-400">
                {matchesCount} Partidos · {(totalEvents / 1000).toFixed(1)}k Eventos · {(total360 / 1000).toFixed(1)}k Frames 360
              </span>
              {isStandalone && (
                <span className="text-[10px] font-mono-metric uppercase px-2 py-0.5 rounded bg-[#8B5CF6]/15 text-[#8B5CF6] border border-[#8B5CF6]/30 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Modo Offline Autónomo
                </span>
              )}
            </div>
            <h1 className="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2 mt-0.5">
              <span>{coachName}</span>
              <span className="text-slate-500 font-normal">/</span>
              <span className="text-[#00F5D4]">{teamName}</span>
              <span className="hidden xl:inline text-xs font-normal text-slate-400 ml-1">
                ({summary?.competition || 'Liga MX'} {summary?.season || '2025/2026'})
              </span>
            </h1>
          </div>
        </div>

        {/* Selector de las 3 Vistas por Perfil de Usuario */}
        <nav className="flex items-center gap-1.5 bg-[#111827] p-1 rounded-xl border border-[#1F2937] overflow-x-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-[#0B0F19] text-white shadow-sm border border-[#334155]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#0B0F19]/40 border border-transparent'
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${
                    isActive
                      ? item.id === 'scrollytelling'
                        ? 'text-[#00F5D4]'
                        : item.id === 'tactical-staff'
                        ? 'text-[#F59E0B]'
                        : 'text-[#8B5CF6]'
                      : 'text-slate-400'
                  }`}
                />
                <span>{item.label}</span>
                <span
                  className={`hidden md:inline-block text-[10px] font-mono-metric px-1.5 py-0.5 rounded ${
                    isActive ? 'bg-slate-800 text-slate-200' : 'bg-slate-800/50 text-slate-400'
                  }`}
                >
                  {item.badge}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Botón Principal de Exportación a Archivo HTML Único */}
        <div className="flex items-center justify-end">
          <button
            onClick={onExportClick}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-gradient-to-r from-[#00F5D4] to-[#00C4AA] text-[#0B0F19] hover:brightness-110 active:scale-[0.99] transition-all shadow-lg shadow-[#00F5D4]/15"
          >
            <Download className="w-4 h-4 stroke-[2.4]" />
            <span>Exportar Reporte HTML Único</span>
          </button>
        </div>
      </div>
    </header>
  );
}
