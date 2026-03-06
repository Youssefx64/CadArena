"""
DXF file export service.

This module provides functionality to export DXF files to various formats
(DXF, PDF, PNG) using matplotlib for rendering.
"""

from enum import Enum
from pathlib import Path

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
) -> tuple[Path, str]:
    """
    Export a DXF file to the specified format.
    
    Args:
        dxf_path: Path to the source DXF file.
        export_format: Target export format.
    
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

    # PDF/IMAGE: convert using matplotlib
    export_path = source_path.with_suffix(_EXPORT_SUFFIXES[export_format])
    _render_dxf_with_matplotlib(source_path, export_path)
    return export_path, export_path.name


def _render_dxf_with_matplotlib(source_path: Path, export_path: Path):
    """
    Render DXF file to PDF or PNG using matplotlib.
    
    Args:
        source_path: Path to source DXF file.
        export_path: Path for exported file (PDF or PNG).
    
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
    try:
        doc = ezdxf.readfile(source_path)
        modelspace = doc.modelspace()

        # Create figure with high DPI for quality
        fig = plt.figure(figsize=(16, 10), dpi=360)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_aspect("equal", adjustable="box")
        # Dark background with brighter foreground gives better DXF readability in browser previews.
        ax.set_facecolor("#0f1d24")
        fig.patch.set_facecolor("#0f1d24")

        render_context = RenderContext(doc)
        backend = MatplotlibBackend(ax)

        frontend_kwargs = {}
        try:
            from ezdxf.addons.drawing.config import ColorPolicy, Configuration

            config = Configuration.defaults()
            if hasattr(config, "with_changes"):
                config = config.with_changes(
                    color_policy=ColorPolicy.MONOCHROME,
                    custom_fg_color="#ecf6f3",
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
        fig.savefig(
            export_path,
            format=export_path.suffix.lstrip("."),
            bbox_inches="tight",
            pad_inches=0.01,
        )
    except DxfExportError:
        raise
    except Exception as exc:
        raise DxfExportError(
            f"Failed to export DXF as {export_path.suffix.lstrip('.').upper()}: {exc}"
        ) from exc
    finally:
        if fig is not None:
            plt.close(fig)
