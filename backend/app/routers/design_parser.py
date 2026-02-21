"""Router for design prompt parsing endpoint."""

from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models.design_parser import (
    ParseDesignErrorResponse,
    ParseDesignRequest,
    ParseDesignSuccessResponse,
    ParseErrorBody,
)
from app.services.design_parser_service import (
    ParseDesignServiceError,
    parse_design_prompt_with_metadata,
)
from app.utils.parse_output_storage import save_parse_design_output

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/parse-design",
    response_model=ParseDesignSuccessResponse,
    responses={
        400: {"model": ParseDesignErrorResponse},
        422: {"model": ParseDesignErrorResponse},
        500: {"model": ParseDesignErrorResponse},
        502: {"model": ParseDesignErrorResponse},
        503: {"model": ParseDesignErrorResponse},
        504: {"model": ParseDesignErrorResponse},
    },
)
async def parse_design(request: ParseDesignRequest):
    """Convert a natural-language architectural prompt into strict JSON intent."""

    started_at = perf_counter()
    requested_model = request.model.value
    request_id = uuid4().hex

    try:
        result = await parse_design_prompt_with_metadata(
            prompt=request.prompt,
            model_choice=request.model,
            recovery_mode=request.recovery_mode,
            request_id=request_id,
        )
        model_used = result.model_used
        parsed_data = result.data

        try:
            saved_output_path = save_parse_design_output(
                prompt=request.prompt,
                model_used=model_used,
                parsed_data=parsed_data,
            )
            logger.info("request_id=%s parse-design output saved path=%s", request_id, saved_output_path)
        except Exception as save_exc:  # pragma: no cover - non-critical persistence failure
            logger.warning("request_id=%s parse-design output save skipped: %s", request_id, save_exc)

        latency_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "request_id=%s event=parse-design-success model=%s provider=%s failover=%s latency_ms=%.2f",
            request_id,
            model_used,
            result.provider_used,
            result.failover_triggered,
            latency_ms,
        )
        return ParseDesignSuccessResponse(
            success=True,
            model_used=model_used,
            provider_used=result.provider_used,
            failover_triggered=result.failover_triggered,
            latency_ms=round(latency_ms, 3),
            data=parsed_data,
        )

    except ParseDesignServiceError as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        logger.warning(
            "request_id=%s event=parse-design-failure model=%s provider=%s failover=%s code=%s latency_ms=%.2f message=%s",
            request_id,
            exc.model_used,
            exc.provider_used,
            exc.failover_triggered,
            exc.code,
            latency_ms,
            exc.message,
        )

        payload = ParseDesignErrorResponse(
            success=False,
            model_used=exc.model_used or requested_model,
            provider_used=exc.provider_used or exc.model_used or requested_model,
            failover_triggered=exc.failover_triggered,
            latency_ms=round(latency_ms, 3),
            error=ParseErrorBody(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    except Exception as exc:  # pragma: no cover - safety net
        latency_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "request_id=%s event=parse-design-unhandled-error model=%s latency_ms=%.2f",
            request_id,
            requested_model,
            latency_ms,
        )

        payload = ParseDesignErrorResponse(
            success=False,
            model_used=requested_model,
            provider_used=requested_model,
            failover_triggered=False,
            latency_ms=round(latency_ms, 3),
            error=ParseErrorBody(
                code="INTERNAL_ERROR",
                message="Unexpected server error",
                details=[str(exc)],
            ),
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))
