import React from 'react';
import PropTypes from 'prop-types';
import { 
  Info, Layers as LayersIcon, Ruler, ShieldCheck, Download, 
  AlertTriangle, CheckCircle, FileText
} from 'lucide-react';
import LayerPanel from '../viewer/LayerPanel';
import toast from 'react-hot-toast';
import cadArenaAPI from '../../services/api';

function classNames(...items) {
  return items.filter(Boolean).join(' ');
}

export default function InspectorTabsNext({
  activeMessage,
  layers = [],
  onToggleLayer = () => {},
  activeTab = 'properties',
  onChangeTab = () => {}
}) {
  // Extract parsed design intent and quality report from activeMessage
  const designData = activeMessage?.data || null;
  const qualityReport = activeMessage?.quality_report || null;
  const fileToken = activeMessage?.file_token || null;
  const dxfName = activeMessage?.dxf_name || 'design.dxf';

  const hasData = designData !== null;

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-white dark:bg-slate-900 select-none">
      {/* Inspector tabs headers */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 overflow-x-auto shrink-0 scrollbar-none">
        {[
          { id: 'properties', label: 'Properties', icon: Info },
          { id: 'layers', label: 'Layers', icon: LayersIcon },
          { id: 'measurements', label: 'Measurements', icon: Ruler },
          { id: 'compliance', label: 'Compliance', icon: ShieldCheck },
          { id: 'exports', label: 'Exports', icon: Download }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => onChangeTab(tab.id)}
              className={classNames(
                'flex items-center gap-1.5 px-3 py-2 text-[10px] font-bold border-b-2 transition-all uppercase tracking-wider shrink-0',
                isActive
                  ? 'border-sky-500 text-sky-600 dark:text-sky-400 bg-white dark:bg-slate-900 font-bold'
                  : 'border-transparent text-slate-400 hover:text-slate-655 dark:hover:text-slate-200'
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        {!hasData ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
            <Info className="h-6 w-6 text-slate-350 dark:text-slate-650 mb-2" />
            <p className="text-xs text-slate-400">No active CAD drawing loaded</p>
            <p className="text-[10px] text-slate-500 mt-1 max-w-[200px]">
              Select a project iteration or generate a plan to load inspector details.
            </p>
          </div>
        ) : (
          <>
            {/* PROPERTIES TAB */}
            {activeTab === 'properties' && (
              <div className="space-y-4 text-xs">
                {/* Global properties card */}
                <div className="p-3 bg-slate-50 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-850 rounded-lg space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Footprint Boundary</span>
                  <div className="grid grid-cols-2 gap-4 font-mono">
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-0.5">Width & Height</span>
                      <span className="text-xs font-bold">{designData.boundary.width}m x {designData.boundary.height}m</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block mb-0.5">Total Area</span>
                      <span className="text-xs font-bold">{(designData.boundary.width * designData.boundary.height).toFixed(1)} sq. m</span>
                    </div>
                  </div>
                </div>

                {/* Geometry count summary list */}
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Geometry Count</span>
                  <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                    <div className="p-2 border border-slate-150 dark:border-slate-850 rounded-lg">
                      <span className="block text-xs font-bold">{designData.rooms.length}</span>
                      <span className="text-[9px] text-slate-450 block">Rooms</span>
                    </div>
                    <div className="p-2 border border-slate-150 dark:border-slate-850 rounded-lg">
                      <span className="block text-xs font-bold">{designData.walls.length}</span>
                      <span className="text-[9px] text-slate-450 block">Walls</span>
                    </div>
                    <div className="p-2 border border-slate-150 dark:border-slate-850 rounded-lg">
                      <span className="block text-xs font-bold">{designData.openings.length}</span>
                      <span className="text-[9px] text-slate-450 block">Openings</span>
                    </div>
                  </div>
                </div>

                {/* Rooms List Program */}
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Room List</span>
                  <div className="max-h-48 overflow-y-auto border border-slate-200 dark:border-slate-800 rounded-lg divide-y divide-slate-150 dark:divide-slate-850">
                    {designData.rooms.map((room, idx) => (
                      <div key={room.name || idx} className="p-2.5 flex items-center justify-between">
                        <div>
                          <span className="font-bold text-slate-800 dark:text-slate-250 block">{room.name}</span>
                          <span className="text-[9px] uppercase font-bold text-slate-400 font-mono tracking-wider">{room.room_type}</span>
                        </div>
                        <span className="font-mono text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded font-bold">
                          {room.width}m x {room.height}m
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* LAYERS TAB */}
            {activeTab === 'layers' && (
              <LayerPanel
                layers={layers}
                onToggle={onToggleLayer}
                loading={false}
                collapsed={false}
                onCollapse={() => {}}
              />
            )}

            {/* MEASUREMENTS TAB */}
            {activeTab === 'measurements' && (
              <div className="space-y-3.5 text-xs">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Spatial Layout Dimensions</span>
                <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden divide-y divide-slate-150 dark:divide-slate-850">
                  {designData.rooms.map((room, idx) => {
                    const area = (room.width * room.height).toFixed(2);
                    const ratio = (Math.max(room.width, room.height) / Math.min(room.width, room.height)).toFixed(2);

                    return (
                      <div key={room.name || idx} className="p-3 flex flex-col gap-1.5 font-mono">
                        <div className="flex items-center justify-between text-xs font-sans">
                          <span className="font-bold text-slate-800 dark:text-slate-200">{room.name}</span>
                          <span className="text-[10px] font-bold text-indigo-500">{area} m²</span>
                        </div>
                        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[9px] text-slate-450 leading-tight">
                          <span>W x H: {room.width}m x {room.height}m</span>
                          <span>Ratio: {ratio}:1</span>
                          <span>Origin: ({room.origin.x}, {room.origin.y})</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* COMPLIANCE TAB */}
            {activeTab === 'compliance' && (
              <div className="space-y-4 text-xs">
                {qualityReport ? (
                  <>
                    {/* Compliance scorecard */}
                    <div className="p-3 bg-slate-50 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-850 rounded-lg flex items-center justify-between gap-4">
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Scorecard Grade</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xl font-bold font-mono text-indigo-500">{qualityReport.grade}</span>
                          <span className="text-[10px] text-slate-400">({(qualityReport.score * 100).toFixed(0)}% passed)</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase block tracking-wider text-center select-none border border-slate-200 dark:border-slate-800">
                          {qualityReport.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </div>
                    </div>

                    {/* Hard failures lists */}
                    {qualityReport.hard_failures && qualityReport.hard_failures.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-[10px] font-bold text-red-500 uppercase tracking-wider flex items-center gap-1">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          Code Violations ({qualityReport.hard_failures.length})
                        </span>
                        <ul className="space-y-1.5 pl-3 border-l-2 border-red-500/30">
                          {qualityReport.hard_failures.map((fail, fIdx) => (
                            <li key={fIdx} className="text-[11px] leading-relaxed text-red-600 dark:text-red-400 font-mono">
                              {fail}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Warnings list */}
                    {qualityReport.warnings && qualityReport.warnings.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider flex items-center gap-1">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          Code Warnings ({qualityReport.warnings.length})
                        </span>
                        <ul className="space-y-1.5 pl-3 border-l-2 border-amber-500/30">
                          {qualityReport.warnings.map((warn, wIdx) => (
                            <li key={wIdx} className="text-[11px] leading-relaxed text-amber-600 dark:text-amber-400 font-mono">
                              {warn}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Repairs list */}
                    {qualityReport.repairs_applied && qualityReport.repairs_applied.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider flex items-center gap-1">
                          <CheckCircle className="h-3.5 w-3.5" />
                          Auto-repairs Applied ({qualityReport.repairs_applied.length})
                        </span>
                        <ul className="space-y-1.5 pl-3 border-l-2 border-emerald-500/30">
                          {qualityReport.repairs_applied.map((rep, rIdx) => (
                            <li key={rIdx} className="text-[11px] leading-relaxed text-emerald-600 dark:text-emerald-400 font-mono">
                              {rep}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <ShieldCheck className="h-8 w-8 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
                    <p className="text-[11px] text-slate-500 leading-normal">
                      No compliance scorecard found. Ensure the layout generator includes validation rules.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* EXPORTS TAB */}
            {activeTab === 'exports' && (
              <div className="space-y-4 text-xs select-none">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Drawing Export Controls</span>
                
                <div className="grid grid-cols-1 gap-2.5">
                  {/* DXF drawing export */}
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const url = cadArenaAPI.dxfDownloadUrl(fileToken, dxfName);
                        await cadArenaAPI.triggerFileDownload(url, dxfName);
                      } catch (err) {
                        toast.error(err.message);
                      }
                    }}
                    className="p-3 w-full text-left border border-slate-200 dark:border-slate-800 hover:border-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850 rounded-lg flex items-center justify-between group transition-all"
                  >
                    <div>
                      <span className="font-bold text-slate-800 dark:text-slate-250 block">AutoCAD DXF Drawing</span>
                      <span className="text-[10px] font-mono text-slate-400">{dxfName}</span>
                    </div>
                    <Download className="h-4.5 w-4.5 text-slate-450 group-hover:text-sky-500 transition-colors" />
                  </button>

                  {/* PNG layout download */}
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const url = cadArenaAPI.dxfPngUrl(fileToken, dxfName.replace('.dxf', '.png'));
                        await cadArenaAPI.triggerFileDownload(url, dxfName.replace('.dxf', '.png'));
                      } catch (err) {
                        toast.error(err.message);
                      }
                    }}
                    className="p-3 w-full text-left border border-slate-200 dark:border-slate-800 hover:border-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850 rounded-lg flex items-center justify-between group transition-all"
                  >
                    <div>
                      <span className="font-bold text-slate-800 dark:text-slate-250 block">PNG Image Layout</span>
                      <span className="text-[10px] font-mono text-slate-400">Flat rendered layout boundary</span>
                    </div>
                    <Download className="h-4.5 w-4.5 text-slate-450 group-hover:text-sky-500 transition-colors" />
                  </button>

                  {/* PDF layout download */}
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const url = cadArenaAPI.dxfPdfUrl(fileToken, dxfName.replace('.dxf', '.pdf'));
                        await cadArenaAPI.triggerFileDownload(url, dxfName.replace('.dxf', '.pdf'));
                      } catch (err) {
                        toast.error(err.message);
                      }
                    }}
                    className="p-3 w-full text-left border border-slate-200 dark:border-slate-800 hover:border-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850 rounded-lg flex items-center justify-between group transition-all"
                  >
                    <div>
                      <span className="font-bold text-slate-800 dark:text-slate-250 block">PDF Document Layout</span>
                      <span className="text-[10px] font-mono text-slate-400">Printable document layout</span>
                    </div>
                    <Download className="h-4.5 w-4.5 text-slate-450 group-hover:text-sky-500 transition-colors" />
                  </button>

                  {/* Compliance metadata report */}
                  {qualityReport && (
                    <button
                      type="button"
                      onClick={() => {
                        const blob = new Blob([JSON.stringify(qualityReport, null, 2)], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `compliance_report_${fileToken.slice(0, 6)}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="p-3 w-full text-left border border-slate-200 dark:border-slate-800 hover:border-slate-350 hover:bg-slate-50 dark:hover:bg-slate-850 rounded-lg flex items-center justify-between group transition-all"
                    >
                      <div>
                        <span className="font-bold text-slate-800 dark:text-slate-250 block">Compliance Audit JSON</span>
                        <span className="text-[10px] font-mono text-slate-400">Download validation scorecard logs</span>
                      </div>
                      <FileText className="h-4.5 w-4.5 text-slate-450 group-hover:text-sky-500 transition-colors" />
                    </button>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

InspectorTabsNext.propTypes = {
  activeMessage: PropTypes.object,
  layers: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string,
    visible: PropTypes.bool
  })),
  onToggleLayer: PropTypes.func,
  activeTab: PropTypes.string,
  onChangeTab: PropTypes.func
};
