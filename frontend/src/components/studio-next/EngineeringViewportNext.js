import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import { 
  ZoomIn, ZoomOut, Maximize2, RotateCcw, Grid, Crosshair, FileCode2, ChevronRight, Loader2
} from 'lucide-react';
import DxfCanvas from '../viewer/DxfCanvas';
import cadArenaAPI from '../../services/api';

const MIN_ZOOM = 0.04;
const MAX_ZOOM = 12;

function clamp(val, min, max) {
  return Math.min(max, Math.max(min, val));
}

export default function EngineeringViewportNext({
  fileToken,
  fileName,
  onImgLoadComplete, // triggers when image is parsed and size is resolved
  onCollapse = () => {},
  layers = []
}) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [imgLoading, setImgLoading] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [imgSize, setImgSize] = useState(null);
  const [showGrid, setShowGrid] = useState(true);
  const [showCrosshair, setShowCrosshair] = useState(false);
  const [mouseCoords, setMouseCoords] = useState({ x: 0, y: 0 });

  const canvasRef = useRef(null);
  const viewportRef = useRef(null);

  const previewUrl = useMemo(() => {
    if (!fileToken) return null;
    const visibleNames = layers.filter(l => l.visible).map(l => l.name).join(',');
    return cadArenaAPI.dxfPreviewUrl(fileToken, visibleNames);
  }, [fileToken, layers]);

  // Reset viewport states when active drawing token changes
  useEffect(() => {
    if (!fileToken) {
      setImgLoading(false);
      setPreviewError(null);
      setZoom(1);
      setPan({ x: 0, y: 0 });
      setImgSize(null);
      return;
    }

    setImgLoading(true);
    setPreviewError(null);
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setImgSize(null);
  }, [fileToken]);

  const handleImgLoad = (e) => {
    const { naturalWidth: w, naturalHeight: h } = e.target;
    setImgSize({ w, h });
    setImgLoading(false);
    setPreviewError(null);

    // Call callback to notify parent
    if (onImgLoadComplete) {
      onImgLoadComplete({ w, h });
    }

    if (canvasRef.current && w && h) {
      const { w: cw, h: ch } = canvasRef.current.getContainerSize();
      const fz = clamp(Math.min(cw / w, ch / h) * 0.88, MIN_ZOOM, MAX_ZOOM);
      setZoom(fz);
    }
  };

  const handleImgError = useCallback(() => {
    setImgLoading(false);
    setPreviewError(
      'Could not render preview. Make sure the backend is active and drawing contains valid structures.'
    );
  }, []);

  const handleWheel = useCallback(({ deltaY, cursorX, cursorY }) => {
    const factor = deltaY < 0 ? 1.12 : 1 / 1.12;
    setZoom((z) => {
      const next = clamp(z * factor, MIN_ZOOM, MAX_ZOOM);
      const ratio = next / z;
      setPan((p) => ({
        x: cursorX - (cursorX - p.x) * ratio,
        y: cursorY - (cursorY - p.y) * ratio,
      }));
      return next;
    });
  }, []);

  const handleZoomIn = () =>
    setZoom((z) => clamp(z * 1.25, MIN_ZOOM, MAX_ZOOM));
    
  const handleZoomOut = () =>
    setZoom((z) => clamp(z / 1.25, MIN_ZOOM, MAX_ZOOM));

  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleFit = useCallback(() => {
    if (!imgSize || !canvasRef.current) return;
    const { w: cw, h: ch } = canvasRef.current.getContainerSize();
    const fz = clamp(Math.min(cw / imgSize.w, ch / imgSize.h) * 0.88, MIN_ZOOM, MAX_ZOOM);
    setZoom(fz);
    setPan({ x: 0, y: 0 });
  }, [imgSize]);

  const handleMouseMove = (e) => {
    if (!viewportRef.current) return;
    const rect = viewportRef.current.getBoundingClientRect();
    // Calculate local relative coordinates on viewport (relative to origin center if preferred, or top-left)
    const rx = e.clientX - rect.left;
    const ry = e.clientY - rect.top;
    
    // Scale back using viewport zoom/pan settings to approximate CAD coordinate calculations
    const cadX = ((rx - rect.width / 2 - pan.x) / zoom).toFixed(2);
    const cadY = (-(ry - rect.height / 2 - pan.y) / zoom).toFixed(2); // Invert y-axis to match CAD system Cartesian systems
    setMouseCoords({ x: cadX, y: cadY });
  };

  // Handle automatic refit on panel or window resize
  useEffect(() => {
    if (!viewportRef.current) return;
    const observer = new ResizeObserver(() => {
      if (imgSize) {
        handleFit();
      }
    });
    observer.observe(viewportRef.current);
    return () => observer.disconnect();
  }, [imgSize, handleFit]);

  // Keyboard shortcut listener
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'f' || e.key === 'F') handleFit();
      if (e.key === 'r' || e.key === 'R') handleReset();
      if (e.key === '+' || e.key === '=') handleZoomIn();
      if (e.key === '-') handleZoomOut();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [handleFit]);

  return (
    <div 
      ref={viewportRef}
      onMouseMove={handleMouseMove}
      className="flex-1 min-h-0 flex flex-col relative select-none"
    >
      {/* Viewport Toolbar Header */}
      <div className="h-12 px-3 bg-white/95 dark:bg-slate-900/95 border-b border-slate-100 dark:border-slate-850 flex items-center justify-between z-10">
        <div className="flex items-center gap-2 min-w-0">
          <FileCode2 className="h-4 w-4 text-sky-500 shrink-0" />
          <span className="text-xs font-bold truncate text-slate-800 dark:text-slate-250">
            {fileToken ? (fileName || 'design.dxf') : 'DXF Render'}
          </span>
        </div>

        {/* Viewport Control Actions */}
        <div className="flex items-center gap-1.5">
          {/* Zoom controls */}
          <button
            onClick={handleZoomIn}
            className="p-1 hover:bg-slate-100 dark:hover:bg-slate-850 rounded text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
            title="Zoom In (+)"
            disabled={!fileToken}
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 hover:bg-slate-100 dark:hover:bg-slate-850 rounded text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
            title="Zoom Out (-)"
            disabled={!fileToken}
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 hover:bg-slate-100 dark:hover:bg-slate-850 rounded text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
            title="Fit View (F)"
            disabled={!fileToken}
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={handleReset}
            className="p-1 hover:bg-slate-100 dark:hover:bg-slate-850 rounded text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
            title="Reset View (R)"
            disabled={!fileToken}
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>

          <div className="w-px h-3.5 bg-slate-250 dark:bg-slate-800 mx-1" />

          {/* Grid & Crosshair switches */}
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`p-1 rounded transition-colors ${showGrid ? 'bg-sky-50 text-sky-600 dark:bg-sky-950/40 dark:text-sky-400' : 'text-slate-400 hover:text-slate-600'}`}
            title="Toggle Grid Lines"
          >
            <Grid className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setShowCrosshair(!showCrosshair)}
            className={`p-1 rounded transition-colors ${showCrosshair ? 'bg-sky-50 text-sky-600 dark:bg-sky-950/40 dark:text-sky-400' : 'text-slate-400 hover:text-slate-600'}`}
            title="Toggle Crosshair Guides"
          >
            <Crosshair className="h-3.5 w-3.5" />
          </button>

          <div className="w-px h-3.5 bg-slate-250 dark:bg-slate-800 mx-1" />

          {/* Panel Close button */}
          <button
            onClick={onCollapse}
            className="p-1 hover:bg-slate-100 dark:hover:bg-slate-850 rounded text-slate-400 hover:text-slate-600"
            title="Collapse Inspector Workspace"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Viewport Workspace */}
      <div className="flex-1 min-h-0 bg-slate-950 border-b border-slate-200 dark:border-slate-800 relative overflow-hidden flex flex-col">
        {/* Empty state */}
        {!fileToken && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 bg-slate-950 select-none z-20">
            {/* Grid blueprint grid background */}
            <div 
              className="absolute inset-0 pointer-events-none opacity-[0.03]"
              style={{
                backgroundImage: 'radial-gradient(circle, rgba(148,163,184,0.15) 1.5px, transparent 1.5px)',
                backgroundSize: '24px 24px',
              }}
            />
            
            <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-850 flex items-center justify-center mb-4 text-sky-500 shadow-md">
              <FileCode2 className="h-5 w-5" />
            </div>
            
            <h3 className="text-xs font-bold text-slate-200 mb-1">CAD Workspace Empty</h3>
            <p className="text-[11px] text-slate-500 max-w-[240px] leading-relaxed">
              Describe your target floor plan layout in the prompt composer to generate CAD vectors.
            </p>
          </div>
        )}

        {/* Dynamic CAD grid lines background overlay */}
        {showGrid && fileToken && (
          <div 
            className="absolute inset-0 pointer-events-none opacity-20 z-0"
            style={{
              backgroundImage: 'radial-gradient(circle, rgba(148,163,184,0.15) 1.5px, transparent 1.5px)',
              backgroundSize: `${24 * zoom}px ${24 * zoom}px`,
              backgroundPosition: `${pan.x}px ${pan.y}px`,
            }}
          />
        )}

        {/* Crosshair guide guides */}
        {showCrosshair && fileToken && (
          <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
            {/* Horizontal coordinate indicator line */}
            <div 
              className="absolute left-0 right-0 h-px bg-sky-500/25 border-dashed"
              style={{ top: `${(mouseCoords.y * -zoom) + (viewportRef.current?.getBoundingClientRect().height / 2 || 0) + pan.y}px` }}
            />
            {/* Vertical coordinate indicator line */}
            <div 
              className="absolute top-0 bottom-0 w-px bg-sky-500/25 border-dashed"
              style={{ left: `${(mouseCoords.x * zoom) + (viewportRef.current?.getBoundingClientRect().width / 2 || 0) + pan.x}px` }}
            />
          </div>
        )}

        {/* DXF Canvas Rendering */}
        <DxfCanvas
          ref={canvasRef}
          previewUrl={previewUrl}
          zoom={zoom}
          pan={pan}
          onWheel={handleWheel}
          onPan={setPan}
          onImgLoad={handleImgLoad}
          onImgError={handleImgError}
          imgLoading={imgLoading}
          previewError={previewError}
          showUpload={false} // Disable direct upload box
          uploading={false}
          onFileSelect={() => {}}
        />

        {/* Loading Overlay */}
        {imgLoading && fileToken && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/75 backdrop-blur-xs select-none z-20">
            <div className="flex flex-col items-center gap-3 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl max-w-xs">
              <Loader2 className="h-6 w-6 text-sky-500 animate-spin" />
              <div className="text-center">
                <span className="text-xs font-bold text-slate-200 block">Compiling CAD Geometry</span>
                <span className="text-[9px] text-slate-500 font-mono block mt-0.5">Rasterizing vector elements...</span>
              </div>
            </div>
          </div>
        )}

        {/* Mouse coordinates tracking overlay */}
        {fileToken && !imgLoading && !previewError && (
          <div className="absolute bottom-2.5 right-2.5 bg-slate-950/80 backdrop-blur-xs text-[10px] font-mono text-slate-400 py-1 px-2 border border-slate-800 rounded z-10 shadow-sm pointer-events-none">
            X: {mouseCoords.x}m | Y: {mouseCoords.y}m
          </div>
        )}
      </div>
    </div>
  );
}

EngineeringViewportNext.propTypes = {
  fileToken: PropTypes.string,
  fileName: PropTypes.string,
  onImgLoadComplete: PropTypes.func,
  onCollapse: PropTypes.func,
  layers: PropTypes.arrayOf(PropTypes.object)
};
