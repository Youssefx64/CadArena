import React, {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from 'react';
import { useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import DxfCanvas from '../components/viewer/DxfCanvas';
import LayerPanel from '../components/viewer/LayerPanel';
import ViewerToolbar from '../components/viewer/ViewerToolbar';

const MIN_ZOOM = 0.04;
const MAX_ZOOM = 12;

const CADARENA_DEFAULT_LAYERS = [
  'BORDER',
  'WALLS',
  'DOORS',
  'WINDOWS',
  'ROOM_LABELS',
  'DIMENSIONS',
  'HATCH',
  'FURNITURE',
  'FURNITURE_BEDROOM',
  'FURNITURE_SANITARY',
  'FURNITURE_LIVING',
  'FURNITURE_KITCHEN',
];

function parseDxfLayers(text) {
  const layers = new Set();
  const lines = text.split('\n').map((l) => l.trim());
  for (let i = 0; i < lines.length - 3; i++) {
    if (lines[i] === '0' && lines[i + 1] === 'LAYER') {
      const nameCode = lines[i + 2];
      const name = lines[i + 3]?.trim();
      if ((nameCode === '2' || nameCode === '  2') && name && name !== '0') {
        layers.add(name);
      }
    }
  }
  return [...layers];
}

function clamp(val, min, max) {
  return Math.min(max, Math.max(min, val));
}

function ViewerPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const name = searchParams.get('name') || 'design.dxf';

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [layers, setLayers] = useState([]);
  const [layersLoading, setLayersLoading] = useState(false);
  const [imgLoading, setImgLoading] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [imgSize, setImgSize] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [panelCollapsed, setPanelCollapsed] = useState(false);

  const canvasRef = useRef(null);

  const previewUrl = useMemo(
    () =>
      token
        ? `/api/v1/dxf/preview?file_token=${encodeURIComponent(token)}`
        : null,
    [token]
  );

  useEffect(() => {
    if (!token) {
      setLayers([]);
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

    setLayersLoading(true);
    const downloadUrl = `/api/v1/dxf/download?file_token=${encodeURIComponent(token)}`;
    fetch(downloadUrl, { credentials: 'include' })
      .then((r) => {
        if (!r.ok) throw new Error('Failed to fetch DXF');
        return r.text();
      })
      .then((text) => {
        const parsed = parseDxfLayers(text);
        const names =
          parsed.length > 0 ? parsed : CADARENA_DEFAULT_LAYERS;
        setLayers(names.map((n) => ({ name: n, visible: true })));
      })
      .catch(() => {
        setLayers(CADARENA_DEFAULT_LAYERS.map((n) => ({ name: n, visible: true })));
      })
      .finally(() => setLayersLoading(false));
  }, [token]);

  const handleImgLoad = (e) => {
    const { naturalWidth: w, naturalHeight: h } = e.target;
    setImgSize({ w, h });
    setImgLoading(false);
    setPreviewError(null);
    if (canvasRef.current && w && h) {
      const { w: cw, h: ch } = canvasRef.current.getContainerSize();
      const fz = clamp(Math.min(cw / w, ch / h) * 0.88, MIN_ZOOM, MAX_ZOOM);
      setZoom(fz);
    }
  };

  const handleImgError = useCallback(() => {
    setImgLoading(false);
    setPreviewError(
      'The backend could not render this DXF file. Make sure the backend is running and the file token is valid.'
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

  const handleLayerToggle = (layerName) => {
    setLayers((prev) =>
      prev.map((l) =>
        l.name === layerName ? { ...l, visible: !l.visible } : l
      )
    );
  };

  const handleFileSelect = useCallback(
    async (file) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith('.dxf')) {
        toast.error('Only .dxf files are supported');
        return;
      }
      if (file.size > 20 * 1024 * 1024) {
        toast.error('File is too large. Maximum size is 20 MB.');
        return;
      }

      setUploading(true);
      try {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('/api/v1/dxf/upload', {
          method: 'POST',
          body: formData,
          credentials: 'include',
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Upload failed (${res.status})`);
        }

        const data = await res.json();
        const newToken = data.file_token;
        const newName = data.original_filename || file.name;

        setSearchParams({ token: newToken, name: newName });
        toast.success('File loaded successfully');
      } catch (err) {
        toast.error(err.message || 'Upload failed');
      } finally {
        setUploading(false);
      }
    },
    [setSearchParams]
  );

  const handleOpenFile = () => {
    document.getElementById('viewer-file-input')?.click();
  };

  useEffect(() => {
    const onKey = (e) => {
      if (
        e.target.tagName === 'INPUT' ||
        e.target.tagName === 'TEXTAREA'
      )
        return;
      if (e.key === 'f' || e.key === 'F') handleFit();
      if (e.key === 'r' || e.key === 'R') handleReset();
      if (e.key === '+' || e.key === '=') handleZoomIn();
      if (e.key === '-') handleZoomOut();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [handleFit]);

  const showUpload = !token;

  return (
    <div className="viewer-shell">
      <ViewerToolbar
        fileName={name}
        zoom={zoom}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFit={handleFit}
        onReset={handleReset}
        token={token || null}
        onOpenFile={handleOpenFile}
      />

      <div className="viewer-body">
        {token && (
          <LayerPanel
            layers={layers}
            onToggle={handleLayerToggle}
            loading={layersLoading}
            collapsed={panelCollapsed}
            onCollapse={() => setPanelCollapsed((v) => !v)}
          />
        )}

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
          showUpload={showUpload}
          uploading={uploading}
          onFileSelect={handleFileSelect}
        />
      </div>
    </div>
  );
}

export default ViewerPage;
