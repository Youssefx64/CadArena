import React, { useRef, useCallback, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Loader2, AlertCircle, Upload, FileText } from 'lucide-react';

const DxfCanvas = forwardRef(function DxfCanvas(
  {
    previewUrl,
    zoom,
    pan,
    onWheel,
    onPan,
    onImgLoad,
    onImgError,
    imgLoading,
    previewError,
    showUpload,
    uploading,
    onFileSelect,
  },
  ref
) {
  const containerRef = useRef(null);
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });
  const [isDragOver, setIsDragOver] = React.useState(false);

  useImperativeHandle(ref, () => ({
    getContainerSize() {
      const el = containerRef.current;
      if (!el) return { w: 800, h: 600 };
      return { w: el.clientWidth, h: el.clientHeight };
    },
  }));

  const handleWheel = useCallback(
    (e) => {
      e.preventDefault();
      const el = containerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      onWheel({
        deltaY: e.deltaY,
        cursorX: e.clientX - rect.left - rect.width / 2,
        cursorY: e.clientY - rect.top - rect.height / 2,
      });
    },
    [onWheel]
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    dragging.current = true;
    lastPos.current = { x: e.clientX, y: e.clientY };
    if (containerRef.current) containerRef.current.style.cursor = 'grabbing';
  };

  const handleMouseMove = (e) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };
    onPan((prev) => ({ x: prev.x + dx, y: prev.y + dy }));
  };

  const stopDrag = () => {
    if (dragging.current) {
      dragging.current = false;
      if (containerRef.current) containerRef.current.style.cursor = showUpload ? 'default' : 'grab';
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragOver) setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file && file.name.toLowerCase().endsWith('.dxf')) {
      onFileSelect(file);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
    e.target.value = '';
  };

  const openFilePicker = () => {
    document.getElementById('viewer-file-input')?.click();
  };

  if (showUpload) {
    return (
      <div
        className="viewer-canvas-wrap"
        style={{ cursor: 'default' }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          id="viewer-file-input"
          type="file"
          accept=".dxf"
          className="hidden"
          onChange={handleFileInput}
        />

        {uploading ? (
          <div className="viewer-canvas-state">
            <Loader2 className="h-10 w-10 text-primary-500 animate-spin" />
            <p className="text-sm font-semibold text-slate-600 mt-2">Uploading file…</p>
          </div>
        ) : (
          <button
            className={`viewer-upload-zone${isDragOver ? ' drag-over' : ''}`}
            onClick={openFilePicker}
            type="button"
          >
            <span className="app-icon-badge-lg mb-2" style={{ background: 'rgba(79,70,229,0.08)' }}>
              <Upload className="h-7 w-7 text-primary-600" />
            </span>
            <p className="app-section-title text-xl">Open a DXF file</p>
            <p className="app-body text-slate-500 text-sm mt-1">
              Drag &amp; drop or click to browse — up to 20 MB
            </p>
            <div className="flex items-center gap-3 mt-4">
              <span className="app-pill-muted py-1.5 px-3 text-xs">
                <FileText className="inline h-3.5 w-3.5 mr-1 -mt-0.5" />
                .dxf only
              </span>
            </div>
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="viewer-canvas-wrap"
      style={{ cursor: 'grab' }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={stopDrag}
      onMouseLeave={stopDrag}
    >
      {imgLoading && (
        <div className="viewer-canvas-state">
          <Loader2 className="h-10 w-10 text-primary-500 animate-spin" />
          <p className="text-sm font-semibold text-slate-600 mt-2">Rendering preview…</p>
          <p className="text-xs text-slate-400 mt-0.5">This may take a moment for large files</p>
        </div>
      )}

      {!imgLoading && previewError && (
        <div className="viewer-canvas-state">
          <span
            className="app-icon-badge-lg mb-2"
            style={{ background: 'rgba(239,68,68,0.08)' }}
          >
            <AlertCircle className="h-7 w-7 text-red-500" />
          </span>
          <p className="text-sm font-semibold text-slate-700 mt-1">Preview unavailable</p>
          <p className="text-xs text-slate-400 max-w-xs text-center mt-1">{previewError}</p>
        </div>
      )}

      {previewUrl && (
        <div
          className="viewer-canvas-inner"
          style={{
            transform: `translate(calc(-50% + ${pan.x}px), calc(-50% + ${pan.y}px)) scale(${zoom})`,
            opacity: imgLoading ? 0 : 1,
            transition: imgLoading ? 'none' : 'opacity 0.25s ease',
          }}
        >
          <img
            src={previewUrl}
            alt="DXF Preview"
            draggable={false}
            className="viewer-canvas-img"
            onLoad={onImgLoad}
            onError={onImgError}
          />
        </div>
      )}
    </div>
  );
});

export default DxfCanvas;
