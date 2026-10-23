import React from 'react';
import { CheckCircle2, Download, FileCode2, Loader2, X } from 'lucide-react';

export default function ExportModal({ isOpen, onClose, status, errorMsg, onConfirmExport }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-[#111827] border border-[#1F2937] rounded-2xl max-w-lg w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-[#1F2937] pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-[#00F5D4]/15 border border-[#00F5D4]/40 flex items-center justify-center">
              <FileCode2 className="w-5 h-5 text-[#00F5D4]" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Exportar Reporte HTML Único Autónomo
              </h3>
              <p className="text-xs text-slate-400">
                Bundle 100% auto-contenido con datos StatsBomb 360 embebidos
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-5 space-y-4 text-sm text-slate-300">
          <p className="leading-relaxed">
            Se empaquetará la aplicación completa (3 vistas interactivas, pizarras vectoriales SVG,
            geometría 360 Voronoi/Convex Hull, redes de pases y 10,000 simulaciones Monte Carlo)
            inyectando el estado en <code className="text-[#00F5D4] font-mono-metric">window.__PRECALCULATED_DATA__</code>.
          </p>

          <div className="bg-[#0B0F19] border border-[#1F2937] rounded-xl p-3.5 space-y-2 text-xs font-mono-metric">
            <div className="flex justify-between">
              <span className="text-slate-400">Archivo de salida:</span>
              <span className="text-[#00F5D4]">Reporte_Tactico_StatsBomb360.html</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Dependencias externas:</span>
              <span className="text-emerald-400">Ninguna (100% Offline)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Interactividad conservada:</span>
              <span className="text-[#8B5CF6]">Scrollytelling + Staff + Deep-Dive 360</span>
            </div>
          </div>

          {status === 'loading' && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-[#8B5CF6]/15 border border-[#8B5CF6]/40 text-slate-200">
              <Loader2 className="w-5 h-5 text-[#8B5CF6] animate-spin shrink-0" />
              <span className="text-xs">
                Compilando e inyectando datos tácticos en archivo único HTML...
              </span>
            </div>
          )}

          {status === 'success' && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/40 text-emerald-300">
              <CheckCircle2 className="w-5 h-5 shrink-0" />
              <span className="text-xs">
                ¡Descarga iniciada! El archivo <strong>Reporte_Tactico_StatsBomb360.html</strong> también quedó guardado en la raíz del proyecto.
              </span>
            </div>
          )}

          {status === 'error' && (
            <div className="p-3 rounded-xl bg-[#F43F5E]/15 border border-[#F43F5E]/40 text-[#F43F5E] text-xs">
              {errorMsg || 'Ocurrió un error al exportar el archivo HTML.'}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#1F2937]">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800"
          >
            Cerrar
          </button>
          <button
            onClick={onConfirmExport}
            disabled={status === 'loading'}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-[#00F5D4] text-[#0B0F19] hover:brightness-110 disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            <span>{status === 'success' ? 'Descargar Nuevamente' : 'Generar y Descargar .HTML'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
