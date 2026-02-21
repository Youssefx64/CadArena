"""Prompt compiler for design parser providers."""

from __future__ import annotations

from app.utils.design_prompt import build_design_parser_prompt


class PromptCompiler:
    """Builds provider-ready prompts from user text."""

    def compile(self, user_prompt: str) -> str:
        return build_design_parser_prompt(user_prompt)

