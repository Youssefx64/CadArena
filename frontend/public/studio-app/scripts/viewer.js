/**
 * CadArena Canvas Viewer — AutoCAD-style DXF viewer with layers, zoom/pan, grid.
 * Consumes structured render JSON from /api/v1/dxf/render-data.
 */
(function () {
  "use strict";

  const LAYER_COLORS_LIGHT = {
    WALLS: "#1a1a1a",
    DOORS: "#333333",
    WINDOWS: "#4a4a4a",
    ROOM_LABELS: "#1a1a1a",
    DIMENSIONS: "#1f5aa6",
    FURNITURE: "#9a9a9a",
    FURNITURE_BEDROOM: "#9a9a9a",
    FURNITURE_SANITARY: "#9a9a9a",
    FURNITURE_LIVING: "#9a9a9a",
    FURNITURE_KITCHEN: "#9a9a9a",
    HATCH: "#d0d0d0",
    BORDER: "#000000",
    BOUNDARY: "#000000",
    STAIRS: "#666666",
  };

  const LAYER_COLORS_DARK = {
    WALLS: "#e0e0e0",
    DOORS: "#cccccc",
    WINDOWS: "#b0b0b0",
    ROOM_LABELS: "#e8e8e8",
    DIMENSIONS: "#6ba3e8",
    FURNITURE: "#707070",
    FURNITURE_BEDROOM: "#707070",
    FURNITURE_SANITARY: "#707070",
    FURNITURE_LIVING: "#707070",
    FURNITURE_KITCHEN: "#707070",
    HATCH: "#3a3a3a",
    BORDER: "#cccccc",
    BOUNDARY: "#cccccc",
    STAIRS: "#888888",
  };

  const BG_LIGHT = "#ffffff";
  const BG_DARK = "#1e1e2e";
  const GRID_COLOR_LIGHT = "rgba(0,0,0,0.06)";
  const GRID_COLOR_DARK = "rgba(255,255,255,0.06)";
  const GRID_TEXT_LIGHT = "rgba(0,0,0,0.25)";
  const GRID_TEXT_DARK = "rgba(255,255,255,0.2)";
  const CROSSHAIR_LIGHT = "rgba(0,0,0,0.15)";
  const CROSSHAIR_DARK = "rgba(255,255,255,0.12)";

  const MIN_ZOOM = 0.1;
  const MAX_ZOOM = 50;
  const ZOOM_FACTOR = 1.15;

  class CadViewer {
    constructor(canvas, opts = {}) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.data = null;
      this.dark = opts.dark || false;
      this.showGrid = opts.showGrid !== false;
      this.showCrosshair = opts.crosshair || false;

      this.zoom = 1;
      this.panX = 0;
      this.panY = 0;
      this.worldWidth = 1;
      this.worldHeight = 1;

      this.layerVisibility = {};
      this.hoveredRoom = null;
      this.mouseWorld = null;

      this._isPanning = false;
      this._lastMouse = null;
      this._animFrame = null;
      this._onLayerChange = opts.onLayerChange || null;
      this._onRoomHover = opts.onRoomHover || null;
      this._onZoomChange = opts.onZoomChange || null;

      this._bindEvents();
      this._resizeCanvas();
    }

    load(data) {
      this.data = data;
      this.layerVisibility = {};
      if (data.layers) {
        for (const name of Object.keys(data.layers)) {
          this.layerVisibility[name] = true;
        }
      }
      this._computeWorldBounds();
      this.zoomToFit();
      this._notifyLayerChange();
      this.render();
    }

    zoomToFit() {
      if (!this.data) return;
      const ex = this.data.extents;
      const spanX = Math.max(ex.maxX - ex.minX, 0.1);
      const spanY = Math.max(ex.maxY - ex.minY, 0.1);
      const pad = 0.12;
      const fitZoomX = this.canvas.width / (spanX * (1 + pad * 2));
      const fitZoomY = this.canvas.height / (spanY * (1 + pad * 2));
      this.zoom = Math.min(fitZoomX, fitZoomY);
      this.panX = (this.canvas.width / 2) - ((ex.minX + spanX / 2) * this.zoom);
      this.panY = (this.canvas.height / 2) + ((ex.minY + spanY / 2) * this.zoom);
      this._notifyZoom();
      this.render();
    }

    setZoom(newZoom, cx, cy) {
      cx = cx ?? this.canvas.width / 2;
      cy = cy ?? this.canvas.height / 2;
      const oldZoom = this.zoom;
      this.zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom));
      const ratio = this.zoom / oldZoom;
      this.panX = cx - (cx - this.panX) * ratio;
      this.panY = cy - (cy - this.panY) * ratio;
      this._notifyZoom();
      this.render();
    }

    zoomIn() { this.setZoom(this.zoom * ZOOM_FACTOR); }
    zoomOut() { this.setZoom(this.zoom / ZOOM_FACTOR); }

    setLayerVisible(name, visible) {
      this.layerVisibility[name] = visible;
      this.render();
    }

    toggleAllLayers(visible) {
      for (const name of Object.keys(this.layerVisibility)) {
        this.layerVisibility[name] = visible;
      }
      this._notifyLayerChange();
      this.render();
    }

    setDarkMode(dark) {
      this.dark = dark;
      this.render();
    }

    setShowGrid(show) {
      this.showGrid = show;
      this.render();
    }

    getZoomPercent() {
      return Math.round(this.zoom * 10);
    }

    destroy() {
      this.canvas.removeEventListener("wheel", this._onWheel);
      this.canvas.removeEventListener("pointerdown", this._onPointerDown);
      this.canvas.removeEventListener("pointermove", this._onPointerMove);
      this.canvas.removeEventListener("pointerup", this._onPointerUp);
      this.canvas.removeEventListener("pointerleave", this._onPointerLeave);
      if (this._resizeObserver) this._resizeObserver.disconnect();
      if (this._animFrame) cancelAnimationFrame(this._animFrame);
    }

    // ── Coordinate transforms ──
    worldToScreen(wx, wy) {
      return [wx * this.zoom + this.panX, -wy * this.zoom + this.panY];
    }

    screenToWorld(sx, sy) {
      return [(sx - this.panX) / this.zoom, -(sy - this.panY) / this.zoom];
    }

    // ── Rendering ──
    render() {
      if (this._animFrame) cancelAnimationFrame(this._animFrame);
      this._animFrame = requestAnimationFrame(() => this._draw());
    }

    _draw() {
      const ctx = this.ctx;
      const w = this.canvas.width;
      const h = this.canvas.height;

      ctx.fillStyle = this.dark ? BG_DARK : BG_LIGHT;
      ctx.fillRect(0, 0, w, h);

      if (this.showGrid) this._drawGrid();
      if (!this.data) return;

      const entities = this.data.entities;
      if (!entities) return;

      for (const ent of entities) {
        if (!this.layerVisibility[ent.layer]) continue;
        this._drawEntity(ent);
      }

      if (this.showCrosshair && this.mouseWorld) {
        this._drawCrosshair();
      }

      this._drawMinimap();
    }

    _drawGrid() {
      const ctx = this.ctx;
      const w = this.canvas.width;
      const h = this.canvas.height;

      const worldSteps = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100];
      let step = 1;
      for (const s of worldSteps) {
        if (s * this.zoom >= 40) { step = s; break; }
      }

      const [wMinX, wMinY] = this.screenToWorld(0, h);
      const [wMaxX, wMaxY] = this.screenToWorld(w, 0);

      const gridStartX = Math.floor(wMinX / step) * step;
      const gridEndX = Math.ceil(wMaxX / step) * step;
      const gridStartY = Math.floor(wMinY / step) * step;
      const gridEndY = Math.ceil(wMaxY / step) * step;

      ctx.strokeStyle = this.dark ? GRID_COLOR_DARK : GRID_COLOR_LIGHT;
      ctx.lineWidth = 1;
      ctx.beginPath();

      for (let x = gridStartX; x <= gridEndX; x += step) {
        const [sx] = this.worldToScreen(x, 0);
        ctx.moveTo(Math.round(sx) + 0.5, 0);
        ctx.lineTo(Math.round(sx) + 0.5, h);
      }
      for (let y = gridStartY; y <= gridEndY; y += step) {
        const [, sy] = this.worldToScreen(0, y);
        ctx.moveTo(0, Math.round(sy) + 0.5);
        ctx.lineTo(w, Math.round(sy) + 0.5);
      }
      ctx.stroke();

      if (this.zoom * step >= 60) {
        ctx.fillStyle = this.dark ? GRID_TEXT_DARK : GRID_TEXT_LIGHT;
        ctx.font = "10px monospace";
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        for (let x = gridStartX; x <= gridEndX; x += step) {
          const [sx, sy] = this.worldToScreen(x, gridStartY);
          ctx.fillText(x.toFixed(step < 1 ? 2 : 0), sx + 2, h - 14);
        }
        ctx.textAlign = "right";
        for (let y = gridStartY; y <= gridEndY; y += step) {
          const [sx, sy] = this.worldToScreen(gridStartX, y);
          ctx.fillText(y.toFixed(step < 1 ? 2 : 0), 40, sy + 2);
        }
      }
    }

    _drawCrosshair() {
      const ctx = this.ctx;
      const [sx, sy] = this.worldToScreen(this.mouseWorld[0], this.mouseWorld[1]);
      ctx.strokeStyle = this.dark ? CROSSHAIR_DARK : CROSSHAIR_LIGHT;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(sx, 0);
      ctx.lineTo(sx, this.canvas.height);
      ctx.moveTo(0, sy);
      ctx.lineTo(this.canvas.width, sy);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = this.dark ? "#aaa" : "#555";
      ctx.font = "11px monospace";
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillText(
        `${this.mouseWorld[0].toFixed(2)}, ${this.mouseWorld[1].toFixed(2)}`,
        sx + 8,
        sy - 6
      );
    }

    _resolveColor(ent) {
      const colors = this.dark ? LAYER_COLORS_DARK : LAYER_COLORS_LIGHT;
      if (ent.color && ent.color !== "#bylayer" && ent.color !== "#byblock") {
        if (this.dark && (ent.color === "#000000" || ent.color === "#1a1a1a")) {
          return colors[ent.layer] || "#e0e0e0";
        }
        return ent.color;
      }
      return colors[ent.layer] || (this.dark ? "#cccccc" : "#333333");
    }

    _drawEntity(ent) {
      const ctx = this.ctx;
      const color = this._resolveColor(ent);

      switch (ent.type) {
        case "line": this._drawLine(ent, color); break;
        case "lwpolyline": this._drawPolyline(ent, color); break;
        case "arc": this._drawArc(ent, color); break;
        case "circle": this._drawCircle(ent, color); break;
        case "text": this._drawText(ent, color); break;
        case "hatch": this._drawHatch(ent, color); break;
        case "dimension": this._drawDimension(ent, color); break;
        case "insert": break;
      }
    }

    _drawLine(ent, color) {
      const ctx = this.ctx;
      const [x1, y1] = this.worldToScreen(ent.start[0], ent.start[1]);
      const [x2, y2] = this.worldToScreen(ent.end[0], ent.end[1]);
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(1, (ent.lineweight > 0 ? ent.lineweight / 100 : 0.5) * this.zoom * 0.08);
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }

    _drawPolyline(ent, color) {
      const ctx = this.ctx;
      const pts = ent.points;
      if (!pts || pts.length < 2) return;

      const polyWidth = ent.width || 0;

      if (polyWidth > 0.01) {
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(1, polyWidth * this.zoom);
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        const [sx, sy] = this.worldToScreen(pts[0][0], pts[0][1]);
        ctx.moveTo(sx, sy);
        for (let i = 1; i < pts.length; i++) {
          const [px, py] = this.worldToScreen(pts[i][0], pts[i][1]);
          ctx.lineTo(px, py);
        }
        if (ent.closed) {
          const [cx, cy] = this.worldToScreen(pts[0][0], pts[0][1]);
          ctx.lineTo(cx, cy);
        }
        ctx.stroke();
      } else {
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(1, 0.5 * this.zoom * 0.08);
        ctx.lineCap = "round";
        ctx.beginPath();
        const [sx, sy] = this.worldToScreen(pts[0][0], pts[0][1]);
        ctx.moveTo(sx, sy);
        for (let i = 1; i < pts.length; i++) {
          const [px, py] = this.worldToScreen(pts[i][0], pts[i][1]);
          ctx.lineTo(px, py);
        }
        if (ent.closed) {
          const [cx, cy] = this.worldToScreen(pts[0][0], pts[0][1]);
          ctx.lineTo(cx, cy);
        }
        ctx.stroke();
      }
    }

    _drawArc(ent, color) {
      const ctx = this.ctx;
      const [cx, cy] = this.worldToScreen(ent.center[0], ent.center[1]);
      const r = ent.radius * this.zoom;
      const startRad = (ent.startAngle || 0) * Math.PI / 180;
      const endRad = (ent.endAngle || 360) * Math.PI / 180;
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(1, 0.4 * this.zoom * 0.08);
      ctx.beginPath();
      ctx.arc(cx, cy, r, -endRad, -startRad, false);
      ctx.stroke();
    }

    _drawCircle(ent, color) {
      const ctx = this.ctx;
      const [cx, cy] = this.worldToScreen(ent.center[0], ent.center[1]);
      const r = ent.radius * this.zoom;
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(1, 0.4 * this.zoom * 0.08);
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.stroke();
    }

    _drawText(ent, color) {
      const ctx = this.ctx;
      const [sx, sy] = this.worldToScreen(ent.position[0], ent.position[1]);
      const fontSize = Math.max(8, ent.height * this.zoom);
      if (fontSize < 5) return;

      ctx.fillStyle = color;
      ctx.font = `600 ${fontSize}px 'Inter', 'Segoe UI', sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      const lines = (ent.text || "").split("\\P").join("\n").split("\n");
      for (let i = 0; i < lines.length; i++) {
        let line = lines[i].replace(/\\[A-Za-z][^;]*;/g, "").replace(/[{}]/g, "");
        ctx.fillText(line, sx, sy - (lines.length - 1 - i) * fontSize * 1.2);
      }
    }

    _drawHatch(ent, color) {
      const ctx = this.ctx;
      ctx.fillStyle = this.dark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)";

      for (const path of ent.paths) {
        if (path.length < 3) continue;
        ctx.beginPath();
        const [sx, sy] = this.worldToScreen(path[0][0], path[0][1]);
        ctx.moveTo(sx, sy);
        for (let i = 1; i < path.length; i++) {
          const [px, py] = this.worldToScreen(path[i][0], path[i][1]);
          ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fill();

        ctx.strokeStyle = this.dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)";
        ctx.lineWidth = 1;
        const spacing = Math.max(4, 8 * this.zoom * 0.04);
        this._drawHatchLines(path, spacing);
      }
    }

    _drawHatchLines(path, spacing) {
      const ctx = this.ctx;
      let minSX = Infinity, maxSX = -Infinity, minSY = Infinity, maxSY = -Infinity;
      const screenPts = path.map(([wx, wy]) => {
        const [sx, sy] = this.worldToScreen(wx, wy);
        if (sx < minSX) minSX = sx;
        if (sx > maxSX) maxSX = sx;
        if (sy < minSY) minSY = sy;
        if (sy > maxSY) maxSY = sy;
        return [sx, sy];
      });

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(screenPts[0][0], screenPts[0][1]);
      for (let i = 1; i < screenPts.length; i++) {
        ctx.lineTo(screenPts[i][0], screenPts[i][1]);
      }
      ctx.closePath();
      ctx.clip();

      ctx.strokeStyle = this.dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let d = minSX + minSY; d <= maxSX + maxSY; d += spacing) {
        ctx.moveTo(d - maxSY, maxSY);
        ctx.lineTo(d - minSY, minSY);
      }
      ctx.stroke();
      ctx.restore();
    }

    _drawDimension(ent, color) {
      const ctx = this.ctx;
      if (ent.points && ent.points.length >= 2) {
        const [x1, y1] = this.worldToScreen(ent.points[0][0], ent.points[0][1]);
        const [x2, y2] = this.worldToScreen(ent.points[1][0], ent.points[1][1]);
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(1, 0.3 * this.zoom * 0.08);
        ctx.setLineDash([3, 2]);
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        ctx.setLineDash([]);

        const tickLen = 4;
        for (const [px, py] of [[x1, y1], [x2, y2]]) {
          ctx.beginPath();
          ctx.moveTo(px - tickLen, py - tickLen);
          ctx.lineTo(px + tickLen, py + tickLen);
          ctx.stroke();
        }
      }

      if (ent.text && ent.textPosition) {
        const [tx, ty] = this.worldToScreen(ent.textPosition[0], ent.textPosition[1]);
        const fontSize = Math.max(9, 0.3 * this.zoom);
        ctx.fillStyle = color;
        ctx.font = `500 ${fontSize}px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(ent.text, tx, ty);
      }
    }

    _drawMinimap() {
      if (!this.data) return;
      const ex = this.data.extents;
      const mmW = 120;
      const mmH = 80;
      const mmPad = 10;
      const mmX = this.canvas.width - mmW - mmPad;
      const mmY = this.canvas.height - mmH - mmPad;

      const ctx = this.ctx;
      ctx.fillStyle = this.dark ? "rgba(30,30,46,0.85)" : "rgba(255,255,255,0.85)";
      ctx.strokeStyle = this.dark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.12)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(mmX, mmY, mmW, mmH, 6);
      ctx.fill();
      ctx.stroke();

      const spanX = Math.max(ex.maxX - ex.minX, 0.1);
      const spanY = Math.max(ex.maxY - ex.minY, 0.1);
      const mmScale = Math.min((mmW - 16) / spanX, (mmH - 16) / spanY);
      const mmOX = mmX + (mmW - spanX * mmScale) / 2;
      const mmOY = mmY + (mmH - spanY * mmScale) / 2;

      const toMM = (wx, wy) => [
        mmOX + (wx - ex.minX) * mmScale,
        mmOY + (spanY - (wy - ex.minY)) * mmScale,
      ];

      ctx.strokeStyle = this.dark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)";
      ctx.lineWidth = 1;
      const [bx1, by1] = toMM(ex.minX, ex.minY);
      const [bx2, by2] = toMM(ex.maxX, ex.maxY);
      ctx.strokeRect(bx1, by2, bx2 - bx1, by1 - by2);

      const [vtl_x, vtl_y] = this.screenToWorld(0, 0);
      const [vbr_x, vbr_y] = this.screenToWorld(this.canvas.width, this.canvas.height);
      const [vm1x, vm1y] = toMM(Math.max(vtl_x, ex.minX), Math.max(vbr_y, ex.minY));
      const [vm2x, vm2y] = toMM(Math.min(vbr_x, ex.maxX), Math.min(vtl_y, ex.maxY));
      ctx.fillStyle = this.dark ? "rgba(99,102,241,0.2)" : "rgba(59,130,246,0.15)";
      ctx.strokeStyle = this.dark ? "rgba(99,102,241,0.6)" : "rgba(59,130,246,0.5)";
      ctx.lineWidth = 1.5;
      const vw = Math.max(0, vm2x - vm1x);
      const vh = Math.max(0, vm1y - vm2y);
      if (vw > 0 && vh > 0) {
        ctx.fillRect(vm1x, vm2y, vw, vh);
        ctx.strokeRect(vm1x, vm2y, vw, vh);
      }
    }

    // ── Internal state ──
    _computeWorldBounds() {
      if (!this.data) return;
      const ex = this.data.extents;
      this.worldWidth = Math.max(ex.maxX - ex.minX, 0.1);
      this.worldHeight = Math.max(ex.maxY - ex.minY, 0.1);
    }

    _resizeCanvas() {
      const parent = this.canvas.parentElement;
      if (!parent) return;
      const rect = parent.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      this.canvas.width = rect.width * dpr;
      this.canvas.height = rect.height * dpr;
      this.canvas.style.width = rect.width + "px";
      this.canvas.style.height = rect.height + "px";
      this.ctx.scale(dpr, dpr);
      this.canvas.width = rect.width;
      this.canvas.height = rect.height;
    }

    _bindEvents() {
      this._onWheel = (e) => {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const factor = e.deltaY < 0 ? ZOOM_FACTOR : 1 / ZOOM_FACTOR;
        this.setZoom(this.zoom * factor, mx, my);
      };

      this._onPointerDown = (e) => {
        if (e.button === 0 || e.button === 1) {
          this._isPanning = true;
          this._lastMouse = { x: e.clientX, y: e.clientY };
          this.canvas.setPointerCapture(e.pointerId);
          this.canvas.style.cursor = "grabbing";
        }
      };

      this._onPointerMove = (e) => {
        const rect = this.canvas.getBoundingClientRect();
        this.mouseWorld = this.screenToWorld(e.clientX - rect.left, e.clientY - rect.top);

        if (this._isPanning && this._lastMouse) {
          const dx = e.clientX - this._lastMouse.x;
          const dy = e.clientY - this._lastMouse.y;
          this.panX += dx;
          this.panY += dy;
          this._lastMouse = { x: e.clientX, y: e.clientY };
          this.render();
        } else if (this.showCrosshair) {
          this.render();
        }
      };

      this._onPointerUp = (e) => {
        this._isPanning = false;
        this._lastMouse = null;
        this.canvas.style.cursor = "crosshair";
      };

      this._onPointerLeave = () => {
        this._isPanning = false;
        this._lastMouse = null;
        this.mouseWorld = null;
        this.canvas.style.cursor = "crosshair";
        this.render();
      };

      this.canvas.addEventListener("wheel", this._onWheel, { passive: false });
      this.canvas.addEventListener("pointerdown", this._onPointerDown);
      this.canvas.addEventListener("pointermove", this._onPointerMove);
      this.canvas.addEventListener("pointerup", this._onPointerUp);
      this.canvas.addEventListener("pointerleave", this._onPointerLeave);

      this._resizeObserver = new ResizeObserver(() => {
        this._resizeCanvas();
        this.render();
      });
      this._resizeObserver.observe(this.canvas.parentElement || this.canvas);

      this.canvas.style.cursor = "crosshair";
    }

    _notifyLayerChange() {
      if (this._onLayerChange) this._onLayerChange(this.layerVisibility);
    }

    _notifyZoom() {
      if (this._onZoomChange) this._onZoomChange(this.getZoomPercent());
    }
  }

  // ── Layer Panel Builder ──
  function buildLayerPanel(container, viewer) {
    container.innerHTML = "";

    const header = document.createElement("div");
    header.className = "cad-layer-header";
    header.innerHTML = `
      <span class="cad-layer-title">Layers</span>
      <div class="cad-layer-actions">
        <button class="cad-layer-btn" data-action="all-on" title="Show all">👁</button>
        <button class="cad-layer-btn" data-action="all-off" title="Hide all">⊘</button>
      </div>
    `;
    container.appendChild(header);

    header.querySelector('[data-action="all-on"]').onclick = () => {
      viewer.toggleAllLayers(true);
      updateChecks(true);
    };
    header.querySelector('[data-action="all-off"]').onclick = () => {
      viewer.toggleAllLayers(false);
      updateChecks(false);
    };

    const list = document.createElement("div");
    list.className = "cad-layer-list";
    container.appendChild(list);

    const checks = [];
    const sorted = Object.keys(viewer.layerVisibility).sort();
    for (const name of sorted) {
      const row = document.createElement("label");
      row.className = "cad-layer-row";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = viewer.layerVisibility[name];
      cb.onchange = () => viewer.setLayerVisible(name, cb.checked);
      checks.push(cb);

      const colors = viewer.dark ? LAYER_COLORS_DARK : LAYER_COLORS_LIGHT;
      const swatch = document.createElement("span");
      swatch.className = "cad-layer-swatch";
      swatch.style.background = colors[name] || "#888";

      const label = document.createElement("span");
      label.className = "cad-layer-name";
      label.textContent = name;

      row.appendChild(cb);
      row.appendChild(swatch);
      row.appendChild(label);
      list.appendChild(row);
    }

    function updateChecks(val) {
      checks.forEach((c) => (c.checked = val));
    }
  }

  // Expose globally
  window.CadViewer = CadViewer;
  window.buildLayerPanel = buildLayerPanel;
})();
