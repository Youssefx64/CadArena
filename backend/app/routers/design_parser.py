"""Router for design prompt parsing endpoint."""

from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models.design_parser import (
    ParseDesignAndDxfSuccessResponse,
    ParseDesignErrorResponse,
    ParseDesignModel,
    ParseDesignRequest,
    ParseDesignSuccessResponse,
    ParseErrorBody,
)
from app.schemas.design_intent import DesignIntent
from app.services.design_parser.config import (
    DEFAULT_PARSE_MODEL,
    HF_MODEL_ID,
    OLLAMA_CLOUD_MODELS,
    OLLAMA_LOCAL_MODELS,
    OLLAMA_MODEL_ID,
)
from app.services.design_parser_service import (
    ParseDesignServiceError,
    parse_design_prompt_with_metadata,
)
from app.utils.parse_output_storage import save_parse_design_output

logger = get_logger(__name__)
router = APIRouter()


@router.get("/parse-design-models")
def parse_design_models():
    """Return selectable parse-design backends with their concrete model ids."""
    default_model = (
        DEFAULT_PARSE_MODEL
        if DEFAULT_PARSE_MODEL in {model.value for model in ParseDesignModel}
        else ParseDesignModel.HUGGINGFACE.value
    )
    # Expand the public cloud provider into one selectable request value per concrete hosted model.
    if default_model in {ParseDesignModel.OLLAMA_CLOUD.value, ParseDesignModel.QWEN_CLOUD.value} and OLLAMA_CLOUD_MODELS:
        default_model = f"{ParseDesignModel.OLLAMA_CLOUD.value}::{OLLAMA_CLOUD_MODELS[0]}"

    models = []

    for model_id in OLLAMA_CLOUD_MODELS:
        models.append(
            {
                "request_value": f"{ParseDesignModel.OLLAMA_CLOUD.value}::{model_id}",
                "provider": ParseDesignModel.OLLAMA_CLOUD.value,
                "model_id": model_id,
                "display_name": f"Ollama Cloud ({model_id})",
            }
        )

    ordered_local_models = [
        model_id for model_id in OLLAMA_LOCAL_MODELS if model_id != OLLAMA_MODEL_ID
    ] + [OLLAMA_MODEL_ID]

    for model_id in ordered_local_models:
        request_value = (
            ParseDesignModel.OLLAMA.value
            if model_id == OLLAMA_MODEL_ID
            else f"{ParseDesignModel.OLLAMA.value}::{model_id}"
        )
        models.append(
            {
                "request_value": request_value,
                "provider": ParseDesignModel.OLLAMA.value,
                "model_id": model_id,
                "display_name": f"Ollama Local ({model_id})",
            }
        )

    models.append(
        {
            "request_value": ParseDesignModel.HUGGINGFACE.value,
            "provider": "huggingface",
            "model_id": HF_MODEL_ID,
            "display_name": f"HuggingFace Local ({HF_MODEL_ID})",
        }
    )

    return {
        "default_model": default_model,
        "models": models,
    }


@router.post(
    "/parse-design",
    response_model=ParseDesignSuccessResponse,
    responses={
        400: {"model": ParseDesignErrorResponse},
        429: {"model": ParseDesignErrorResponse},
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
                request_id=request_id,
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
            self_review_triggered=result.self_review_triggered,
            latency_ms=round(latency_ms, 3),
            data=parsed_data,
            metrics=result.metrics,
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
                reason=exc.reason,
                violated_rule=exc.violated_rule,
                room=exc.room,
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


@router.post(
    "/parse-design-generate-dxf",
    response_model=ParseDesignAndDxfSuccessResponse,
    responses={
        400: {"model": ParseDesignErrorResponse},
        422: {"model": ParseDesignErrorResponse},
        429: {"model": ParseDesignErrorResponse},
        500: {"model": ParseDesignErrorResponse},
        502: {"model": ParseDesignErrorResponse},
        503: {"model": ParseDesignErrorResponse},
        504: {"model": ParseDesignErrorResponse},
    },
)
async def parse_design_generate_dxf(request: ParseDesignRequest):
    """Parse prompt to structured intent and generate DXF in one request."""

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
                request_id=request_id,
            )
            logger.info("request_id=%s parse-design output saved path=%s", request_id, saved_output_path)
        except Exception as save_exc:  # pragma: no cover - non-critical persistence failure
            logger.warning("request_id=%s parse-design output save skipped: %s", request_id, save_exc)

        try:
            dxf_intent = DesignIntent.model_validate(
                {
                    "boundary": parsed_data.get("boundary", {}),
                    "rooms": parsed_data.get("rooms", []),
                    "openings": parsed_data.get("openings", []),
                }
            )
        except Exception as exc:
            raise ParseDesignServiceError(
                code="DXF_INTENT_INVALID",
                message="Parsed layout could not be converted to DXF intent",
                status_code=422,
                model_used=model_used,
                provider_used=result.provider_used,
                failover_triggered=result.failover_triggered,
                details=[str(exc)],
            ) from exc

        try:
            from app.pipeline.intent_to_agent import generate_dxf_from_intent

            dxf_path = await run_in_threadpool(generate_dxf_from_intent, dxf_intent)
        except (RuntimeError, ValueError) as exc:
            raise ParseDesignServiceError(
                code="GENERATE_DXF_FAILED",
                message="DXF generation failed",
                status_code=422,
                model_used=model_used,
                provider_used=result.provider_used,
                failover_triggered=result.failover_triggered,
                details=[str(exc)],
            ) from exc

        latency_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "request_id=%s event=parse-design-generate-dxf-success model=%s provider=%s failover=%s latency_ms=%.2f dxf_path=%s",
            request_id,
            model_used,
            result.provider_used,
            result.failover_triggered,
            latency_ms,
            dxf_path,
        )
        return ParseDesignAndDxfSuccessResponse(
            success=True,
            model_used=model_used,
            provider_used=result.provider_used,
            failover_triggered=result.failover_triggered,
            self_review_triggered=result.self_review_triggered,
            latency_ms=round(latency_ms, 3),
            dxf_path=str(dxf_path),
            data=parsed_data,
            metrics=result.metrics,
        )

    except ParseDesignServiceError as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        logger.warning(
            "request_id=%s event=parse-design-generate-dxf-failure model=%s provider=%s failover=%s code=%s latency_ms=%.2f message=%s",
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
                reason=exc.reason,
                violated_rule=exc.violated_rule,
                room=exc.room,
                details=exc.details,
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    except Exception as exc:  # pragma: no cover - safety net
        latency_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "request_id=%s event=parse-design-generate-dxf-unhandled-error model=%s latency_ms=%.2f",
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
