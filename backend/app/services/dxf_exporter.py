"""
DXF file export service.

This module provides functionality to export DXF files to various formats
(DXF, PDF, PNG) using matplotlib for rendering.
"""

import hashlib
import os
import tempfile
from enum import Enum
from pathlib import Path
from threading import Lock

import ezdxf
from app.core.file_utils import resolve_output_path


class ExportFormat(str, Enum):
    """
    Supported export formats for DXF files.

    Values:
        DXF: Native DXF format (no conversion).
        PDF: PDF export via matplotlib.
        IMAGE: PNG image export via matplotlib.
    """

    DXF = "dxf"
    PDF = "pdf"
    IMAGE = "image"


class DxfExportError(RuntimeError):
    """
    Base exception for DXF export errors.
    """

    pass


class DxfExportDependencyError(DxfExportError):
    """
    Exception raised when required dependencies for export are missing.

    Typically raised when matplotlib is not installed for PDF/IMAGE export.
    """

    pass


# File extension mapping for export formats
_EXPORT_SUFFIXES: dict[ExportFormat, str] = {
    ExportFormat.DXF: ".dxf",
    ExportFormat.PDF: ".pdf",
    ExportFormat.IMAGE: ".png",
}

# HTTP media type mapping for export formats
_EXPORT_MEDIA_TYPES: dict[ExportFormat, str] = {
    ExportFormat.DXF: "application/dxf",
    ExportFormat.PDF: "application/pdf",
    ExportFormat.IMAGE: "image/png",
}

_EXPORT_LOCKS: dict[str, Lock] = {}
_EXPORT_LOCKS_GUARD = Lock()


def get_media_type(export_format: ExportFormat) -> str:
    """
    Get HTTP media type for an export format.

    Args:
        export_format: Export format.

    Returns:
        Media type string (e.g., "application/pdf").
    """
    return _EXPORT_MEDIA_TYPES[export_format]


def export_dxf_file(
    dxf_path: str | Path,
    export_format: ExportFormat,
    visible_layers: list[str] | None = None,
) -> tuple[Path, str]:
    """
    Export a DXF file to the specified format.

    Args:
        dxf_path: Path to the source DXF file.
        export_format: Target export format.
        visible_layers: Optional list of visible layer names.

    Returns:
        Tuple of (export_path, filename) for the exported file.

    Raises:
        DxfExportError: If path resolution fails, file not found, or export fails.
        DxfExportDependencyError: If matplotlib is required but not installed.
    """
    try:
        source_path = resolve_output_path(dxf_path)
    except ValueError as exc:
        raise DxfExportError(str(exc)) from exc

    if source_path.suffix.lower() != ".dxf":
        raise DxfExportError("Input file must have .dxf extension")
    if not source_path.exists():
        raise DxfExportError(f"DXF file not found: {source_path.name}")

    # DXF format: return original file
    if export_format == ExportFormat.DXF:
        return source_path, source_path.name

    export_path = _build_export_cache_path(
        source_path=source_path,
        export_format=export_format,
        visible_layers=visible_layers,
    )
    export_path.parent.mkdir(parents=True, exist_ok=True)

    if export_path.exists():
        return export_path, export_path.name

    export_lock = _export_lock_for_path(export_path)
    with export_lock:
        if not source_path.exists():
            raise DxfExportError(f"DXF file not found: {source_path.name}")
        if export_path.exists():
            return export_path, export_path.name
        _render_dxf_with_matplotlib(source_path, export_path, visible_layers)

    return export_path, export_path.name


def _render_dxf_with_matplotlib(
    source_path: Path, export_path: Path, visible_layers: list[str] | None = None
):
    """
    Render DXF file to PDF or PNG using matplotlib.

    Args:
        source_path: Path to source DXF file.
        export_path: Path for exported file (PDF or PNG).
        visible_layers: Optional list of visible layer names.

    Raises:
        DxfExportDependencyError: If matplotlib is not installed.
        DxfExportError: If rendering or file I/O fails.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    except ModuleNotFoundError as exc:
        raise DxfExportDependencyError(
            "DXF to PDF/Image export requires matplotlib. Install backend requirements first."
        ) from exc

    fig = None
    temp_export_path: Path | None = None
    try:
        doc = ezdxf.readfile(source_path)

        # Apply layer visibility if specified
        if visible_layers is not None:
            visible_set = {lay.upper() for lay in visible_layers}
            for layer in doc.layers:
                layer_name_upper = layer.dxf.name.upper()
                if layer_name_upper not in visible_set and layer.dxf.name != "0":
                    layer.off()
                else:
                    layer.on()

        modelspace = doc.modelspace()

        # Create figure with the requested white-sheet presentation and minimum 200 DPI output.
        fig = plt.figure(figsize=(16, 10), dpi=200)
        fig.set_dpi(max(fig.get_dpi(), 200))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_aspect("equal", adjustable="box")
        # Keep preview exports on a white background so PNG and PDF match the DXF sheet style.
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")

        render_context = RenderContext(doc)
        # Force architectural layer colors in previews so walls stay black and furniture/hatches stay lighter.
        layer_overrides = {
            "WALLS": {"color": "black", "lineweight": 1.2},
            "DOORS": {"color": "black"},
            "WINDOWS": {"color": "black"},
            "BORDER": {"color": "black", "lineweight": 1.4},
            "ROOM_LABELS": {"color": "black"},
            "DIMENSIONS": {"color": "#1f5aa6"},
            "HATCH": {"color": "#d0d0d0"},
            "FURNITURE": {"color": "#9a9a9a"},
            "FURNITURE_BEDROOM": {"color": "#9a9a9a"},
            "FURNITURE_SANITARY": {"color": "#9a9a9a"},
            "FURNITURE_LIVING": {"color": "#9a9a9a"},
            "FURNITURE_KITCHEN": {"color": "#9a9a9a"},
        }

        # Apply per-layer preview overrides so sheet exports stay close to the intended CAD print hierarchy.
        def _apply_layer_override(layers):
            for layer_props in layers:
                for key, value in layer_overrides.get(
                    layer_props.layer, {}
                ).items():
                    setattr(layer_props, key, value)

        render_context.set_layer_properties_override(_apply_layer_override)
        backend = MatplotlibBackend(ax)

        frontend_kwargs = {}
        try:
            from ezdxf.addons.drawing.config import (
                BackgroundPolicy,
                ColorPolicy,
                Configuration,
            )

            config = Configuration.defaults()
            if hasattr(config, "with_changes"):
                config = config.with_changes(
                    color_policy=ColorPolicy.MONOCHROME,
                    custom_fg_color="#000000",
                    background_policy=BackgroundPolicy.CUSTOM,
                    custom_bg_color="#ffffff",
                    lineweight_scaling=1.8,
                    min_lineweight=0.28,
                )
            frontend_kwargs["config"] = config
        except Exception:
            # Support multiple ezdxf versions; default rendering still works if config API differs.
            frontend_kwargs = {}

        try:
            frontend = Frontend(render_context, backend, **frontend_kwargs)
        except TypeError:
            frontend = Frontend(render_context, backend)

        # Render DXF modelspace to matplotlib axes
        frontend.draw_layout(modelspace, finalize=True)

        # Tighten viewport around actual DXF entities so preview fills the canvas.
        try:
            from ezdxf import bbox

            ext = bbox.extents(modelspace)
            if getattr(ext, "has_data", False):
                min_x = float(ext.extmin.x)
                min_y = float(ext.extmin.y)
                max_x = float(ext.extmax.x)
                max_y = float(ext.extmax.y)
                span_x = max(max_x - min_x, 1.0)
                span_y = max(max_y - min_y, 1.0)
                pad_x = max(span_x * 0.08, 0.5)
                pad_y = max(span_y * 0.08, 0.5)
                ax.set_xlim(min_x - pad_x, max_x + pad_x)
                ax.set_ylim(min_y - pad_y, max_y + pad_y)
        except Exception:
            # Bounding-box fitting is best-effort; rendering must continue even if this fails.
            pass

        export_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=export_path.parent,
            suffix=export_path.suffix,
            prefix=f"{export_path.stem}.",
            delete=False,
        ) as temp_file:
            temp_export_path = Path(temp_file.name)

        fig.savefig(
            temp_export_path,
            format=export_path.suffix.lstrip("."),
            bbox_inches="tight",
            pad_inches=0.01,
        )
        os.replace(temp_export_path, export_path)
        temp_export_path = None
    except DxfExportError:
        raise
    except Exception as exc:
        raise DxfExportError(
            f"Failed to export DXF as {export_path.suffix.lstrip('.').upper()}: {exc}"
        ) from exc
    finally:
        if fig is not None:
            plt.close(fig)
        if temp_export_path is not None:
            try:
                temp_export_path.unlink(missing_ok=True)
            except OSError:
                pass


def _build_export_cache_path(
    *,
    source_path: Path,
    export_format: ExportFormat,
    visible_layers: list[str] | None,
) -> Path:
    suffix = _EXPORT_SUFFIXES[export_format]
    source_stat = source_path.stat()
    layers_key = ",".join(
        sorted(
            {layer.strip().upper() for layer in visible_layers or [] if layer.strip()}
        )
    )
    fingerprint = hashlib.sha1(
        "|".join(
            [
                str(source_path.resolve()),
                str(source_stat.st_mtime_ns),
                str(source_stat.st_size),
                export_format.value,
                layers_key,
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return source_path.with_name(f"{source_path.stem}_{fingerprint}{suffix}")


def _export_lock_for_path(export_path: Path) -> Lock:
    lock_key = str(export_path.resolve())
    with _EXPORT_LOCKS_GUARD:
        export_lock = _EXPORT_LOCKS.get(lock_key)
        if export_lock is None:
            export_lock = Lock()
            _EXPORT_LOCKS[lock_key] = export_lock
        return export_lock
