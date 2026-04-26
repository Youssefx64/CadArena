"""CadArena chat assistant — handles non-design conversational messages.

Uses Ollama locally with an architectural consultant persona.
Falls back to rule-based responses when Ollama is unavailable.
"""

from __future__ import annotations

import logging

import httpx

from app.services.design_parser.config import OLLAMA_GENERATE_URL, OLLAMA_MODEL_ID

logger = logging.getLogger(__name__)

_SYSTEM_PERSONA = """\
You are CadArena Assistant — an expert AI architectural consultant.
Your personality:
- Knowledgeable, professional, but friendly and approachable
- Bilingual (English and Arabic) — respond in the same language the user used
- You help users design floor plans, understand architectural concepts, and use CadArena
- You are enthusiastic about good design and spatial planning

Your capabilities (tell users when relevant):
- Generate 2D architectural floor plans from natural language descriptions
- Support Arabic and English prompts
- Export floor plans as DXF (CAD), PNG, and PDF
- Iteratively edit existing floor plans ("make the bedroom bigger")
- Suggest design improvements and alternatives

Keep responses concise (2-4 sentences max) unless the user asks for detail.
Do NOT generate JSON. Do NOT pretend to generate a floor plan.
Just respond naturally as an assistant."""

_RULE_BASED_RESPONSES: dict[str, str] = {
    "greet": (
        "Welcome to CadArena! I'm your AI architectural assistant.\n\n"
        "I can help you:\n"
        "- **Generate floor plans** — just describe what you need "
        '(e.g. "2 bedroom apartment with kitchen and bathroom")\n'
        '- **Edit your design** — say "make the living room bigger" after generating\n'
        "- **Export** your plan as DXF, PNG, or PDF\n\n"
        "What would you like to design today?"
    ),
    "greet_ar": (
        "أهلاً بك في CadArena! أنا مساعدك المعماري الذكي.\n\n"
        "أقدر أساعدك في:\n"
        '- **توليد مساقط** — وصّف ما تريد (مثال: "شقة بغرفتين نوم ومطبخ وحمام")\n'
        '- **تعديل التصميم** — قل "كبّر الصالة" بعد التوليد\n'
        "- **تحميل** المسقط كـ DXF أو PNG أو PDF\n\n"
        "ماذا تريد أن تصمم اليوم؟"
    ),
    "help": (
        "Here's how to use CadArena:\n\n"
        "**To generate a floor plan:**\n"
        '- "Design a 2 bedroom apartment with living room, kitchen and bathroom"\n'
        '- "شقة 3 غرف نوم وحمامين ومطبخ مساحة 120 متر"\n\n'
        "**To edit your design:**\n"
        '- "Make the bedroom bigger"\n'
        '- "Add a bathroom"\n'
        '- "Remove the corridor"\n\n'
        "**To download:**\n"
        "Use the Download button for DXF / PNG / PDF"
    ),
    "capabilities": (
        "I'm CadArena — an AI-powered architectural floor plan generator.\n\n"
        "I convert natural language descriptions into precise 2D floor plans:\n"
        "- Walls, doors, windows with correct architectural logic\n"
        "- Room sizing based on real architectural standards\n"
        "- Export-ready DXF files for AutoCAD/SketchUp\n"
        "- Arabic and English support\n\n"
        'Try: "Design a 3 bedroom villa with 2 bathrooms and open kitchen"'
    ),
    "default": (
        "I'm here to help you design floor plans!\n\n"
        "Try describing what you want to build, for example:\n"
        '- "2 bedroom apartment with living room and bathroom"\n\n'
        "Or ask me anything about architecture and floor plan design."
    ),
}


def _detect_arabic(text: str) -> bool:
    return any("؀" <= c <= "ۿ" for c in text)


def _rule_based_reply(prompt: str) -> str:
    text = prompt.lower().strip()
    is_arabic = _detect_arabic(prompt)

    if any(w in text for w in ("hello", "hi", "hey", "مرحبا", "اهلا", "هلو", "salam", "marhaba")):
        return _RULE_BASED_RESPONSES["greet_ar" if is_arabic else "greet"]
    if any(w in text for w in ("help", "مساعدة", "ساعد")):
        return _RULE_BASED_RESPONSES["help"]
    if any(w in text for w in ("what", "who", "can you", "ما", "من", "ماذا", "بتعمل")):
        return _RULE_BASED_RESPONSES["capabilities"]
    return _RULE_BASED_RESPONSES["default"]


async def get_assistant_reply(prompt: str) -> str:
    """Get a conversational reply. Tries Ollama first, falls back to rule-based."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            payload = {
                "model": OLLAMA_MODEL_ID,
                "prompt": f"{_SYSTEM_PERSONA}\n\nUser: {prompt}\nAssistant:",
                "stream": False,
                "options": {"num_predict": 200, "temperature": 0.7},
            }
            resp = await client.post(OLLAMA_GENERATE_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("response", "").strip()
            if reply:
                return reply
    except Exception as exc:
        logger.debug("Ollama assistant unavailable: %s — using rule-based fallback", exc)

    return _rule_based_reply(prompt)
