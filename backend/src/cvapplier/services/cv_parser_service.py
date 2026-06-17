"""CV parser: text extraction + LLM structured data extraction."""
import textwrap
from io import BytesIO
from typing import Any

import pdfplumber
from docx import Document

from cvapplier.core.logging import get_logger
from cvapplier.services.llm_gateway import LLMGateway

log = get_logger(__name__)

SYSTEM_PROMPT = textwrap.dedent("""\
    You are a CV parser. Given the raw text of a CV/resume, extract structured information.

    Return a JSON object with these fields (omit null/empty fields):
    - first_name, last_name, email, phone
    - linkedin_url, github_url, portfolio_url
    - summary (1-2 sentences from the profile/objective section)
    - skills: list of strings
    - languages: list of { "name": string, "level": string }  (e.g. "native", "fluent", "B2")
    - work_experience: list of { "company": string, "title": string, "location": string?, "start_date": string? (YYYY-MM-DD), "end_date": string? (YYYY-MM-DD or null if current), "current": bool, "description": string? }
    - education: list of { "institution": string, "degree": string?, "field": string?, "start_date": string?, "end_date": string? }
    - certifications: list of { "name": string, "issuer": string?, "issue_date": string? }

    Rules:
    - Only extract information explicitly present in the CV text. Never invent facts.
    - For dates, use YYYY-MM-DD. If only year is available use YYYY-01-01.
    - Start date must be before end date.
    - Group entries logically (e.g., multiple positions at the same company).
    - Order work_experience and education chronologically (most recent first).
    - Respond with STRICT JSON only, no prose or markdown.
""")


def build_extract_prompt(cv_text: str) -> str:
    return textwrap.dedent(f"""\
        CV TEXT:
        ---
        {cv_text[:8000]}
        ---

        Return JSON with the extracted profile fields.
    """)


class CVParserService:
    """Extract text from CV files and run LLM extraction."""

    @staticmethod
    def extract_text(mime_type: str, data: bytes) -> str:
        if mime_type == "application/pdf" or mime_type.endswith("/pdf"):
            return _extract_pdf(data)
        if mime_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ):
            return _extract_docx(data)
        raise ValueError(f"Unsupported CV format: {mime_type}")

    @staticmethod
    async def parse_with_llm(
        *,
        provider: str,
        model: str,
        api_key: str | None,
        api_base: str | None,
        text: str,
    ) -> dict[str, Any]:
        gw = LLMGateway(
            provider=provider,
            model=model,
            api_key=api_key,
            api_base=api_base,
        )
        user_msg = build_extract_prompt(text)
        result = await gw.complete_json(
            system=SYSTEM_PROMPT,
            user_msg=user_msg,
            timeout=45,
            max_tokens=2000,
        )
        return result if isinstance(result, dict) else {}


def _extract_pdf(data: bytes) -> str:
    with pdfplumber.open(BytesIO(data)) as pdf:
        parts = []
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n".join(parts).strip()


def _extract_docx(data: bytes) -> str:
    doc = Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text).strip()
