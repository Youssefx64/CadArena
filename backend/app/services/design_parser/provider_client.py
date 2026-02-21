"""LLM provider client interfaces and implementations."""

from __future__ import annotations

import asyncio
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.services.design_parser.config import (
    HF_EAGER_LOAD,
    HF_MAX_CONCURRENCY,
    HF_MODEL_ID,
    MAX_NEW_TOKENS,
    OLLAMA_GENERATE_URL,
    OLLAMA_MODEL_ID,
    REQUEST_TIMEOUT_SECONDS,
)
from app.services.design_parser.errors import ParseDesignServiceError
from app.services.ports.llm_provider import LLMProviderPort

logger = get_logger(__name__)


class ProviderClient(LLMProviderPort):
    """Abstraction for model generation providers."""


class OllamaProviderClient(ProviderClient):
    key = "ollama"
    model_id = OLLAMA_MODEL_ID

    async def startup(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def generate(self, compiled_prompt: str, *, request_id: str) -> str:
        payload = {
            "model": self.model_id,
            "prompt": compiled_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0,
                "top_p": 0.9,
                "num_predict": MAX_NEW_TOKENS,
            },
        }

        try:
            body = await asyncio.wait_for(
                asyncio.to_thread(self._request_sync, payload),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise ParseDesignServiceError(
                code="OLLAMA_TIMEOUT",
                message="Timed out while waiting for Ollama response",
                status_code=504,
                model_used=self.model_id,
                provider_used=self.model_id,
            ) from exc

        generated = body.get("response") if isinstance(body, dict) else None
        if not isinstance(generated, str) or not generated.strip():
            raise ParseDesignServiceError(
                code="OLLAMA_EMPTY_OUTPUT",
                message="Ollama returned an empty generation",
                status_code=502,
                model_used=self.model_id,
                provider_used=self.model_id,
            )

        logger.info("request_id=%s provider=%s event=generated", request_id, self.model_id)
        return generated.strip()

    def _request_sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        request_data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            OLLAMA_GENERATE_URL,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                status_code = getattr(response, "status", 200)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise ParseDesignServiceError(
                code="OLLAMA_HTTP_ERROR",
                message=f"Ollama returned HTTP {exc.code}",
                status_code=502,
                model_used=self.model_id,
                provider_used=self.model_id,
                details=[error_body[:500]],
            ) from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise ParseDesignServiceError(
                code="OLLAMA_CONNECTION_ERROR",
                message="Failed to call Ollama endpoint",
                status_code=503,
                model_used=self.model_id,
                provider_used=self.model_id,
                details=[str(exc)],
            ) from exc

        if status_code >= 400:
            raise ParseDesignServiceError(
                code="OLLAMA_HTTP_ERROR",
                message=f"Ollama returned HTTP {status_code}",
                status_code=502,
                model_used=self.model_id,
                provider_used=self.model_id,
                details=[response_body[:500]],
            )
        try:
            body = json.loads(response_body)
        except ValueError as exc:
            raise ParseDesignServiceError(
                code="OLLAMA_INVALID_RESPONSE",
                message="Ollama response is not valid JSON",
                status_code=502,
                model_used=self.model_id,
                provider_used=self.model_id,
                details=[response_body[:500]],
            ) from exc
        if not isinstance(body, dict):
            raise ParseDesignServiceError(
                code="OLLAMA_INVALID_RESPONSE",
                message="Ollama response must be a JSON object",
                status_code=502,
                model_used=self.model_id,
                provider_used=self.model_id,
            )
        return body


@dataclass
class _HuggingFaceBundle:
    tokenizer: Any
    model: Any
    torch: Any


class HuggingFaceProviderClient(ProviderClient):
    key = "huggingface"
    model_id = HF_MODEL_ID

    def __init__(self) -> None:
        self._bundle: _HuggingFaceBundle | None = None
        self._load_lock = asyncio.Lock()
        self._preload_task: asyncio.Task[None] | None = None
        self._inference_semaphore = asyncio.Semaphore(HF_MAX_CONCURRENCY)

    async def startup(self) -> None:
        if not HF_EAGER_LOAD:
            logger.info("HuggingFace eager-load disabled; model will load lazily")
            return
        if self._preload_task is None or self._preload_task.done():
            self._preload_task = asyncio.create_task(self._preload_bundle())

    async def shutdown(self) -> None:
        if self._preload_task is not None and not self._preload_task.done():
            self._preload_task.cancel()
            try:
                await self._preload_task
            except asyncio.CancelledError:
                pass
        self._preload_task = None

    async def generate(self, compiled_prompt: str, *, request_id: str) -> str:
        acquired = False
        try:
            await asyncio.wait_for(self._inference_semaphore.acquire(), timeout=0.001)
            acquired = True
        except asyncio.TimeoutError as exc:
            raise ParseDesignServiceError(
                code="HUGGINGFACE_CONCURRENCY_LIMIT",
                message="HuggingFace concurrency limit exceeded",
                status_code=429,
                model_used=self.model_id,
                provider_used=self.model_id,
            ) from exc

        try:
            bundle = await self._get_bundle()
            generated = await asyncio.wait_for(
                asyncio.to_thread(self._generate_sync, bundle, compiled_prompt),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise ParseDesignServiceError(
                code="HUGGINGFACE_TIMEOUT",
                message="Timed out while running HuggingFace inference",
                status_code=504,
                model_used=self.model_id,
                provider_used=self.model_id,
            ) from exc
        finally:
            if acquired:
                self._inference_semaphore.release()

        if not generated:
            raise ParseDesignServiceError(
                code="HUGGINGFACE_EMPTY_OUTPUT",
                message="HuggingFace model returned an empty generation",
                status_code=502,
                model_used=self.model_id,
                provider_used=self.model_id,
            )
        logger.info("request_id=%s provider=%s event=generated", request_id, self.model_id)
        return generated

    async def _get_bundle(self) -> _HuggingFaceBundle:
        if self._bundle is not None:
            return self._bundle

        async with self._load_lock:
            if self._bundle is not None:
                return self._bundle
            logger.info("Loading HuggingFace model: %s", self.model_id)
            self._bundle = await asyncio.to_thread(self._load_bundle_sync)
            logger.info("HuggingFace model loaded: %s", self.model_id)
        return self._bundle

    async def _preload_bundle(self) -> None:
        try:
            await self._get_bundle()
        except ParseDesignServiceError as exc:
            logger.warning("HuggingFace preload skipped: %s (%s)", exc.message, exc.code)
        except Exception:
            logger.exception("Unexpected error during HuggingFace preload")

    def _load_bundle_sync(self) -> _HuggingFaceBundle:
        try:
            import torch
        except ImportError as exc:
            raise ParseDesignServiceError(
                code="HUGGINGFACE_DEPENDENCY_ERROR",
                message="torch is required for huggingface backend",
                status_code=500,
                model_used=self.model_id,
                provider_used=self.model_id,
                details=[str(exc)],
            ) from exc
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ParseDesignServiceError(
                code="HUGGINGFACE_DEPENDENCY_ERROR",
                message="transformers is required for huggingface backend",
                status_code=500,
                model_used=self.model_id,
                provider_used=self.model_id,
                details=[str(exc)],
            ) from exc

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
                device_map="auto",
                low_cpu_mem_usage=True,
            )
        except Exception as exc:
            raise ParseDesignServiceError(
                code="HUGGINGFACE_LOAD_ERROR",
                message="Failed to load HuggingFace model",
                status_code=500,
                model_used=self.model_id,
                provider_used=self.model_id,
                details=[str(exc)],
            ) from exc

        if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
            tokenizer.pad_token = tokenizer.eos_token

        model.eval()
        return _HuggingFaceBundle(tokenizer=tokenizer, model=model, torch=torch)

    def _generate_sync(self, bundle: _HuggingFaceBundle, compiled_prompt: str) -> str:
        tokenizer = bundle.tokenizer
        model = bundle.model
        torch = bundle.torch

        messages = [{"role": "user", "content": compiled_prompt}]
        if hasattr(tokenizer, "apply_chat_template"):
            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt_text = compiled_prompt

        encoded = tokenizer(prompt_text, return_tensors="pt")
        if not hasattr(model, "hf_device_map") and getattr(model, "device", None) is not None:
            encoded = {name: tensor.to(model.device) for name, tensor in encoded.items()}

        kwargs = {
            "max_new_tokens": MAX_NEW_TOKENS,
            "do_sample": False,
            "temperature": 0.0,
            "num_beams": 1,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
        with torch.inference_mode():
            output = model.generate(**encoded, **kwargs)

        prompt_tokens = encoded["input_ids"].shape[-1]
        generated_tokens = output[0][prompt_tokens:]
        return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
