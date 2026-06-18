"""CV parser: text extraction + LLM structured data extraction."""
import textwrap
from io import BytesIO
from typing import Any

import pdfplumber
from docx import Document

from smartcvapply.core.logging import get_logger
from smartcvapply.services.llm_gateway import LLMGateway

log = get_logger(__name__)

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert CV/resume parser. Your job is to extract EVERY piece of information
    from the CV text and return it as structured JSON. Do NOT skip fields that are present.
    If information exists anywhere in the text, you MUST extract it.

    Return a JSON object with these fields exactly (use null for missing values, [] for empty arrays):

    BASIC INFO:
    - first_name: string
    - last_name: string
    - email: string (look for any email pattern)
    - phone: string (look for any phone pattern, include country code if present)
    - linkedin_url: string (look for linkedin.com links)
    - github_url: string (look for github.com links or GitHub usernames)
    - portfolio_url: string (look for any personal website, portfolio, or blog URL)
    - location: { city: string?, region: string?, country: string?, country_code: string? }
      (extract from address, header, or personal info section)

    - summary: string
      (2-4 sentences from the profile/objective/about section. Combine the most relevant
      information: current role, years of experience, key specializations, and main achievements.
      If there is no explicit summary section, synthesize one from job titles and descriptions.)

    SKILLS & LANGUAGES:
    - skills: string[]
      (Extract EVERY skill mentioned: programming languages, frameworks, databases, cloud platforms,
      DevOps tools, security, soft skills, methodologies, etc. Deduplicate and normalize names.
      E.g. "C#" not "C Sharp", "TypeScript" not "Typescript". Order alphabetically.)
    - languages: [{ name: string, level: string }]
      (Look for a "Languages" or "Idiomas" section. If no explicit section, scan the entire
      text for mentions of language proficiency. Native language with no level stated = "native".
      Common levels: native, fluent, advanced, intermediate, B2, C1, C2, etc.)

    WORK EXPERIENCE:
    - work_experience: [{ company, title, location?, start_date?, end_date?, current, description? }]
      (Extract EVERY position listed. For each entry:
      - company: the employer name
      - title: the job title (use the most specific title if multiple are listed)
      - location: city/region/country if mentioned
      - start_date / end_date: YYYY-MM-DD format. If only month+year, use YYYY-MM-01.
        If only year, use YYYY-01-01. If currently working there, end_date = null and current = true.
      - current: true if this is the current position (end_date is null or "present"/"actualidad")
      - description: combine ALL bullet points, achievements, and responsibilities into one
        paragraph. Include technical details, technologies used, metrics, and results.
        Do NOT truncate — capture the full description.)
      Order chronologically: most recent first. Group consecutive roles at the same company
      as separate entries.)

    EDUCATION:
    - education: [{ institution, degree?, field?, start_date?, end_date? }]
      (Extract EVERY educational entry: university degrees, vocational training, bootcamps,
      courses that award a certificate/diploma. Look for university names, degree titles
      (BSc, MSc, PhD, Engineer, etc.), fields of study, and graduation years.
      Even if dates are partial, include them. Order most recent first.)

    CERTIFICATIONS:
    - certifications: [{ name, issuer?, issue_date? }]
      (Extract EVERY certification mentioned: AWS, Azure, GCP, Scrum, PMP, Cisco, CompTIA,
      language certificates (TOEFL, IELTS, DELE), security certs (CISSP, CEH), etc.
      Look for explicit "Certifications" sections AND mentions embedded in other sections.)

    EXTRACTION RULES:
    1. Be EXHAUSTIVE — if data exists in the CV, it MUST appear in the output.
    2. ANTI-HALLUCINATION — NEVER invent, guess, or fabricate data:
       - If there is NO email in the text, email MUST be null — do NOT construct one from the name.
       - If there is NO phone, phone MUST be null — do NOT insert a placeholder.
       - If there is NO LinkedIn/GitHub/portfolio URL in the text, those fields MUST be null.
         Do NOT guess URLs from the person's name or company.
       - If there is NO explicit summary, summary MUST be null — do NOT synthesize one.
       - If there is NO education section, education MUST be [] — do NOT invent degrees.
       - If there is NO certifications section, certifications MUST be [].
       - If there is NO languages section, languages MUST be [].
       - Only include skills that are EXPLICITLY listed in the CV text.
       - If a work experience entry has no description, use null — do NOT write one.
    3. NULL vs EMPTY: use null when data is absent, [] when the list is genuinely empty.
    4. If you see a section header like "Experience", "Formacion", "Skills", "Idiomas",
       "Certifications", "Education", "Work History" — extract ALL entries under it.
    5. For URLs: ONLY extract URLs that appear literally in the text (http/https or
       explicit domain mentions like "linkedin.com/in/username" or "github.com/username").
    6. For dates: normalize all formats (MM/YYYY, Month YYYY, "2020 - 2023", "2019- actualidad")
       to YYYY-MM-DD. Use 01 for unknown day or month.
    7. Remove markdown, HTML tags, and excessive whitespace from descriptions.
    8. Deduplicate skills: "JavaScript" and "JS" → "JavaScript". "AWS" and "Amazon Web Services" → "AWS".
    9. If the CV is in Spanish or another language, still extract field names in English
       but preserve the original content of descriptions, titles, and company names.

    Respond with STRICT JSON only. No markdown, no code fences, no comments.
    Every field must be present in the output even if null/empty.
""")


def build_extract_prompt(cv_text: str) -> str:
    return textwrap.dedent(f"""\
        CV TEXT:
        ---
        {cv_text[:12000]}
        ---

        Extract ALL fields from this CV. Return EXACTLY this JSON structure
        (replace null with actual data when found, use [] for empty arrays):

        {{
          "first_name": "string or null",
          "last_name": "string or null",
          "email": "string or null",
          "phone": "string or null",
          "linkedin_url": "string or null",
          "github_url": "string or null",
          "portfolio_url": "string or null",
          "location": {{ "city": "string or null", "region": "string or null", "country": "string or null", "country_code": "string or null" }},
          "summary": "string or null",
          "skills": ["skill1", "skill2"],
          "languages": [{{ "name": "English", "level": "native" }}],
          "work_experience": [
            {{
              "company": "Company Name",
              "title": "Job Title",
              "location": "City, Country or null",
              "start_date": "YYYY-MM-DD or null",
              "end_date": "YYYY-MM-DD or null",
              "current": false,
              "description": "Full description combining all bullet points or null"
            }}
          ],
          "education": [
            {{
              "institution": "University Name",
              "degree": "Bachelor's or null",
              "field": "Computer Science or null",
              "start_date": "YYYY-MM-DD or null",
              "end_date": "YYYY-MM-DD or null"
            }}
          ],
          "certifications": [
            {{
              "name": "AWS Solutions Architect",
              "issuer": "Amazon or null",
              "issue_date": "YYYY-MM-DD or null"
            }}
          ]
        }}

        RETURN ONLY VALID JSON. No markdown, no explanation.
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
            timeout=60,
            max_tokens=3000,
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
