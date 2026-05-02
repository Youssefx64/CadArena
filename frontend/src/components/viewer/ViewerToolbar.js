import React from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Download,
  FileText,
  Upload,
  Image,
  FileDown,
} from 'lucide-react';

function ViewerToolbar({
  fileName,
  zoom,
  onZoomIn,
  onZoomOut,
  onFit,
  onReset,
  token,
  onOpenFile,
}) {
  const navigate = useNavigate();
  const pct = Math.round(zoom * 100);

  const safeName = fileName || 'design.dxf';
  const downloadUrl = token
    ? `/api/v1/dxf/download?file_token=${encodeURIComponent(token)}&filename=${encodeURIComponent(safeName)}`
    : null;
  const exportPngUrl = token
    ? `/api/v1/dxf/export?file_token=${encodeURIComponent(token)}&format=image&filename=${encodeURIComponent(safeName.replace(/\.dxf$/i, '.png'))}`
    : null;
  const exportPdfUrl = token
    ? `/api/v1/dxf/export?file_token=${encodeURIComponent(token)}&format=pdf&filename=${encodeURIComponent(safeName.replace(/\.dxf$/i, '.pdf'))}`
    : null;

  return (
    <div className="viewer-toolbar">
      <button
        onClick={() => navigate(-1)}
        className="app-button-ghost app-button-compact"
        title="Go back"
      >
        <ArrowLeft className="h-4 w-4" />
      </button>

      <div className="viewer-toolbar-sep" />

      <span className="app-icon-badge" style={{ background: 'rgba(79,70,229,0.09)' }}>
        <FileText className="h-4 w-4 text-primary-600" />
      </span>
      <span className="text-sm font-semibold text-slate-900 truncate max-w-[14rem] hidden sm:block">
        {safeName}
      </span>
      <span className="app-pill-muted py-0.5 px-2 text-xs font-bold hidden sm:inline-flex">DXF</span>

      <div className="flex-1" />

      <div className="viewer-zoom-group">
        <button
          onClick={onZoomOut}
          className="app-button-ghost app-button-compact"
          title="Zoom out (scroll down)"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <span className="viewer-zoom-display">{pct}%</span>
        <button
          onClick={onZoomIn}
          className="app-button-ghost app-button-compact"
          title="Zoom in (scroll up)"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
      </div>

      <button
        onClick={onFit}
        className="app-button-ghost app-button-compact"
        title="Fit to screen (F)"
      >
        <Maximize2 className="h-4 w-4" />
      </button>

      <button
        onClick={onReset}
        className="app-button-ghost app-button-compact"
        title="Reset view (R)"
      >
        <RotateCcw className="h-4 w-4" />
      </button>

      <div className="viewer-toolbar-sep" />

      {token ? (
        <>
          <a
            href={downloadUrl}
            className="app-button-secondary app-button-compact gap-1.5"
            download={safeName}
            title="Download DXF"
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Download</span>
          </a>
          <a
            href={exportPngUrl}
            className="app-button-ghost app-button-compact gap-1"
            download
            title="Export as PNG"
          >
            <Image className="h-3.5 w-3.5" />
            <span className="text-xs font-semibold">PNG</span>
          </a>
          <a
            href={exportPdfUrl}
            className="app-button-ghost app-button-compact gap-1"
            download
            title="Export as PDF"
          >
            <FileDown className="h-3.5 w-3.5" />
            <span className="text-xs font-semibold">PDF</span>
          </a>

          <div className="viewer-toolbar-sep" />
        </>
      ) : null}

      <button
        onClick={onOpenFile}
        className="app-button-ghost app-button-compact gap-1.5"
        title="Open a DXF file"
      >
        <Upload className="h-4 w-4" />
        <span className="hidden sm:inline text-sm">Open file</span>
      </button>
    </div>
  );
}

ViewerToolbar.propTypes = {
  fileName:   PropTypes.string,
  zoom:       PropTypes.number.isRequired,
  onZoomIn:   PropTypes.func.isRequired,
  onZoomOut:  PropTypes.func.isRequired,
  onFit:      PropTypes.func.isRequired,
  onReset:    PropTypes.func.isRequired,
  token:      PropTypes.string,
  onOpenFile: PropTypes.func.isRequired,
};
ViewerToolbar.defaultProps = { fileName: null, token: null };

export default ViewerToolbar;
