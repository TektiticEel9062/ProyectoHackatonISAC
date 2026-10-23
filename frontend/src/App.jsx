import React, { useEffect, useState } from 'react';
import Header from './components/Header.jsx';
import ExportModal from './components/ExportModal.jsx';
import ScrollytellingView from './views/ScrollytellingView.jsx';
import TacticalStaffView from './views/TacticalStaffView.jsx';
import DeepDiveView from './views/DeepDiveView.jsx';
import {
  fetchAllTacticalData,
  triggerStandaloneHtmlDownload,
} from './utils/dataClient.js';
import { AlertCircle, Loader2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('scrollytelling');
  const [dataBundle, setDataBundle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportStatus, setExportStatus] = useState('idle');
  const [exportError, setExportError] = useState(null);

  useEffect(() => {
    let mounted = true;
    fetchAllTacticalData()
      .then((res) => {
        if (mounted) {
          setDataBundle(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Error al cargar los datos tácticos.');
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleConfirmExport = async () => {
    try {
      setExportStatus('loading');
      setExportError(null);
      await triggerStandaloneHtmlDownload(dataBundle);
      setExportStatus('success');
    } catch (err) {
      setExportStatus('error');
      setExportError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col items-center justify-center p-6">
        <Loader2 className="w-10 h-10 text-[#00F5D4] animate-spin mb-4" />
        <h2 className="text-lg font-bold text-white">
          Cargando Motor Táctico StatsBomb 360...
        </h2>
        <p className="text-xs text-slate-400 font-mono-metric mt-1">
          Procesando eventos, geometría Voronoi / Convex Hull y 10,000 simulaciones Monte Carlo
        </p>
      </div>
    );
  }

  if (error || !dataBundle) {
    return (
      <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col items-center justify-center p-6">
        <div className="bg-[#111827] border border-[#F43F5E]/40 rounded-2xl p-6 max-w-md text-center space-y-3">
          <AlertCircle className="w-10 h-10 text-[#F43F5E] mx-auto" />
          <h2 className="text-base font-bold text-white">Error de Conexión con Datos Tácticos</h2>
          <p className="text-xs text-slate-300">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col">
      <Header
        summary={dataBundle.summary}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onExportClick={() => {
          setExportStatus('idle');
          setExportError(null);
          setExportModalOpen(true);
        }}
        isStandalone={dataBundle.standalone}
      />

      <main className="flex-1">
        {activeTab === 'scrollytelling' && (
          <ScrollytellingView
            scrollytelling={dataBundle.scrollytelling}
            summary={dataBundle.summary}
          />
        )}
        {activeTab === 'tactical-staff' && (
          <TacticalStaffView tacticalStaff={dataBundle.tacticalStaff} />
        )}
        {activeTab === 'deep-dive' && (
          <DeepDiveView deepDive={dataBundle.deepDive} />
        )}
      </main>

      <footer className="border-t border-[#1F2937] bg-[#0B0F19] py-4 px-6 mt-12">
        <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 font-mono-metric">
          <span>
            La Historia de un Entrenador a través de los Datos · {dataBundle.summary?.target_coach} ({dataBundle.summary?.target_team})
          </span>
          <span>
            Framework Analítico Formal StatsBomb Eventos v8 + 360 v2 · Hackathon ISAC 2026
          </span>
        </div>
      </footer>

      <ExportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        status={exportStatus}
        errorMsg={exportError}
        onConfirmExport={handleConfirmExport}
      />
    </div>
  );
}
