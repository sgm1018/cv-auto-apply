"""Server-side heuristic engine for field resolution."""
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

_FILE_VALUE_SENTINEL = "<<<CV_FILE_FIELD>>>"


@dataclass
class ExtractedField:
    field_id: str
    label: str | None = None
    type: str | None = None
    name: str | None = None
    placeholder: str | None = None
    required: bool = False
    options: list[dict[str, str]] | None = None
    current_value: str | None = None
    context: str | None = None


def _unaccent(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ── CV / Resume file keywords ───────────────────────────────────────
_CV_FILE_KEYWORDS: tuple[str, ...] = (
    "curriculum", "curriculum vitae", "cv", "resume", "curriculum",
    "hoja de vida", "archivo adjunto", "subir cv", "adjuntar cv",
    "upload resume", "attach cv", "upload cv", "attach resume",
    "upload your resume", "upload your cv", "attach your cv",
    "upload file", "attached file", "attachment", "cv file", "resume file",
    "choose file", "select file", "browse file", "adjuntar archivo",
    "subir archivo", "seleccionar archivo", "examina", "examinar",
    "drop files", "arrastrar archivo",
)

# ── Salary / compensation keywords ──────────────────────────────────
_SALARY_KEYWORDS: tuple[str, ...] = (
    "salario", "salarial", "expectativa salarial", "salary",
    "remuneracion", "remuneracion", "pretension", "pretension",
    "wage", "compensation", "compensacion", "compensacion",
    "salary expectation", "desired salary", "expected salary",
    "salary requirements", "rango salarial", "salary range",
    "sueldo", "sueldo deseado", "pretension salarial",
    "pretension economica", "pretension economica",
    "salario deseado", "retribucion", "retribucion",
)

# ── Cover letter keywords ──────────────────────────────────────────
_COVER_LETTER_KEYWORDS: tuple[str, ...] = (
    "carta de presentacion", "carta de presentacion", "cover letter",
    "carta de motivacion", "carta de motivacion", "motivation letter",
    "personal statement", "letter of motivation",
)

# ── Privacy / consent / terms keywords ─────────────────────────────
_PRIVACY_KEYWORDS: tuple[str, ...] = (
    "privacidad", "privacy", "politica", "politica", "terms",
    "terminos", "terminos", "condiciones", "data protection",
    "proteccion de datos", "proteccion de datos", "consent",
    "consentimiento", "acepto", "i agree", "aceptar",
    "politica de privacidad", "aviso legal", "legal notice",
)

# ── Word-boundary rules (single words that need \b guard) ───────────
_WORD_BOUNDARY_RULES: list[tuple[str, str]] = [
    ("name",    "first_name"),
    ("phone",   "phone"),
    ("tel",     "phone"),
    ("cp",      "location.zip_code"),
    ("zip",     "location.zip_code"),
    ("city",    "location.city"),
    ("state",   "location.region"),
]

# ── Labels that contain "name" but are NOT a person's name ──────────
_NAME_SKIP_KEYWORDS: tuple[str, ...] = (
    "company", "business", "organization", "organisation",
    "employer", "team", "project", "product", "school",
    "university", "brand", "account", "department", "group",
    "division", "agency", "firm", "corporation", "corp",
    "enterprise", "institution", "facility", "site",
    "maiden",  # "mother's maiden name" should NOT map to first_name
)

# ── Type rules (used as LAST RESORT fallback) ───────────────────────
_TYPE_RULES: dict[str, str] = {
    "email": "email",
    "tel": "phone",
}


# ══════════════════════════════════════════════════════════════════════
#  KEYWORD RULES – ordered: most specific first, generic last
#  Each entry: ((keyword, ...), "profile.attribute")
# ══════════════════════════════════════════════════════════════════════
_KEYWORD_RULES: list[tuple[tuple[str, ...], str]] = [

    # ── First name ──────────────────────────────────────────────────
    (("first name", "given name", "nombre", "firstname", "first_name",
      "primer nombre", "nombre de pila", "your first name",
      "forename", "nombre propio", "nombre/s"),
     "first_name"),

    # ── Last name ───────────────────────────────────────────────────
    (("last name", "surname", "family name", "apellido", "apellidos",
      "lastname", "last_name", "apellido paterno", "apellido materno",
      "segundo apellido", "your last name", "patronymic",
      "maternal surname", "paternal surname", "apellido/s",
      "primer apellido", "second surname"),
     "last_name"),

    # ── Full name → first_name (best-effort) ────────────────────────
    (("full name", "your name", "nombre completo", "nombre y apellidos",
      "complete name", "entire name", "fullname", "full_name",
      "candidate name", "applicant name", "solicitante nombre",
      "postulant name"),
     "first_name"),

    # ── Email ───────────────────────────────────────────────────────
    (("email", "correo", "e-mail", "e mail", "email address",
      "correo electronico", "correo electronico",
      "direccion de correo", "direccion de email",
      "mail", "mail address", "your email", "work email",
      "personal email", "primary email", "email id", "email id",
      "electronic mail", "direccion mail",
      "direccion electronica", "direccion electronica",
      "e-mail address", "correo personal", "correo de contacto",
      "correo laboral", "email account", "cuenta de correo"),
     "email"),

    # ── Phone ───────────────────────────────────────────────────────
    (("phone number", "telephone number", "mobile number",
      "numero de telefono", "numero de telefono",
      "numero de contacto", "numero de contacto",
      "phone", "telephone", "mobile", "telefono", "telefono",
      "telf", "tlfn", "tfno", "movil", "movil", "celular",
      "cel", "cell", "cell phone", "cel phone",
      "contact number", "work phone", "home phone",
      "primary phone", "contact phone", "phone (mobile)",
      "phone (home)", "phone (work)", "telephone no",
      "phone no", "phone #", "phone num",
      "numer de telephone", "numer de telephone",
      "contact telephone", "phone contact"),
     "phone"),

    # ── LinkedIn ────────────────────────────────────────────────────
    (("linkedin", "linked in", "linkedin profile",
      "perfil de linkedin", "linkedin url", "linkedin id",
      "linkedin handle", "linkedin username",
      "linkedin account", "mi linkedin", "my linkedin",
      "linkedin link", "url de linkedin",
      "linkedin profile url", "linkedin id"),
     "linkedin_url"),

    # ── GitHub ─────────────────────────────────────────────────────
    (("github", "git hub", "github profile",
      "perfil de github", "github url", "github handle",
      "github username", "github id", "github account",
      "mi github", "my github", "github user",
      "git", "url de github"),
     "github_url"),

    # ── Portfolio / Website ─────────────────────────────────────────
    (("portfolio", "website", "sitio web", "pagina web", "pagina web",
      "personal website", "personal site", "personal url",
      "url personal", "web", "sitio personal",
      "pagina personal", "pagina personal", "portafolio",
      "personal webpage", "my website", "my site",
      "online portfolio", "professional website",
      "professional site", "web portfolio",
      "digital portfolio", "work portfolio",
      "muestrario", "portafolio digital", "proyectos web",
      "personal page", "homepage", "home page"),
     "portfolio_url"),

    # ── Summary / Bio ────────────────────────────────────────────────
    (("professional summary", "career summary",
      "summary", "bio", "about you", "sobre ti", "sobre mi", "sobre mi",
      "descripcion", "descripcion", "perfil", "resumen",
      "professional profile", "personal statement",
      "about me", "who you are",
      "tell us about yourself", "cuentanos sobre ti", "cuentanos sobre ti",
      "introduccion", "introduccion", "candidate summary",
      "your background", "professional background",
      "career objective", "professional objective",
      "resumen profesional", "perfil profesional",
      "objetivo profesional", "carta de presentacion breve"),
     "summary"),

    # ── Skills ───────────────────────────────────────────────────────
    (("skills", "skill set", "skill",
      "technical skills", "professional skills",
      "habilidades", "competencias", "aptitudes",
      "destrezas", "conocimientos tecnicos", "conocimientos tecnicos",
      "technical competencies", "core competencies",
      "areas of expertise", "expertise",
      "technologies", "tech stack", "technical stack",
      "tools and technologies", "tools & technologies",
      "what technologies do you use",
      "programming languages", "lenguajes de programacion",
      "lenguajes de programacion", "lenguajes",
      "competencias tecnicas", "competencias tecnicas",
      "habilidades tecnicas", "habilidades tecnicas",
      "qualifications", "qualifications summary",
      "specialties", "specialities", "specializacion"),
     "skills"),

    # ── Languages (spoken) ──────────────────────────────────────────
    (("languages", "idiomas", "lenguas",
      "spoken languages", "languages spoken",
      "language proficiency", "idiomas que habla",
      "idiomas que hablas", "idiomas que hablo",
      "languages you speak", "language skills",
      "conocimiento de idiomas", "nivel de idiomas",
      "nivel de idioma", "idioma", "language level",
      "foreign languages", "lengua extranjera",
      "lengua materna", "habilidades lingueisticas",
      "habilidades linguisticas", "competencias linguisticas",
      "competencias linguisticas"),
     "languages"),

    # ── Location city ───────────────────────────────────────────────
    (("city", "ciudad", "localidad", "poblacion", "poblacion",
      "town", "municipality", "municipio", "poblacion",
      "city / town", "current city", "home city",
      "residence city", "ciudad de residencia",
      "ciudad actual", "ciudad natal", "municipio de residencia",
      "location", "ubicacion", "ubicacion",
      "donde vives", "where do you live", "lugar de residencia",
      "residencia", "residence"),
     "location.city"),

    # ── Location region / state ─────────────────────────────────────
    (("region", "state", "province", "provincia", "estado",
      "region", "region", "departamento",
      "comunidad autonoma", "comunidad autonoma",
      "autonomous community", "prefecture",
      "territory", "county", "parish", "canton",
      "state / province", "province / state",
      "region / state", "administrative region",
      "autonomous region", "district",
      "provincia/estado", "departamento/estado",
      "circunscripcion", "circunscripcion"),
     "location.region"),

    # ── Location country ────────────────────────────────────────────
    (("country", "pais", "pais", "nacion", "nacion",
      "nationality", "nacionalidad", "citizenship",
      "ciudadania", "ciudadania",
      "residence country", "current country",
      "country of residence", "pais de residencia",
      "pais de origen", "country of origin",
      "nation", "pais/nacion", "country/nation"),
     "location.country"),

    # ── Zip / Postal code ──────────────────────────────────────────
    (("postal code", "postal", "zip code", "zip/postal",
      "postal/zip", "post code", "postcode",
      "codigo postal", "codigo postal",
      "codigo postal / zip", "zip / postal code",
      "c.p.", "codigo de area", "codigo de area",
      "postal/zip code", "zip/postal code"),
     "location.zip_code"),

    # ── Address ──────────────────────────────────────────────────────
    (("address", "direccion", "direccion", "domicilio",
      "street", "street address", "calle",
      "direccion completa", "full address",
      "current address", "home address",
      "direccion postal", "postal address",
      "residential address", "calle y numero",
      "calle y n", "domicilio particular",
      "direccion particular", "direccion de residencia",
      "living address", "primary address"),
     "location.city"),
]

# ── Additional rules that don't map to existing profile fields
#    but let the LLM/custom-answers stage handle them via context.
#    (These are kept as a reference / documentation, not executed)
_EXTRA_RECOGNIZED_TOPICS: tuple[str, ...] = (
    "date of birth", "fecha de nacimiento", "nacimiento", "birth",
    "genero", "gender", "sexo", "sex",
    "estado civil", "marital status",
    "years of experience", "anos de experiencia", "experiencia laboral",
    "current position", "current job", "puesto actual", "cargo actual",
    "notice period", "periodo de preaviso", "preaviso", "disponibilidad",
    "start date", "fecha de inicio", "starting date", "available from",
    "work authorization", "authorization to work", "visa",
    "permiso de trabajo", "need visa", "require sponsorship",
    "willing to relocate", "relocation", "disponibilidad para viajar",
    "how did you hear", "referral", "como nos conocio",
    "references", "referencias", "contact references",
    "education", "formacion", "formacion academica",
    "highest degree", "titulo", "degree",
    "school", "university", "college",
    "graduation year", "ano de graduacion",
    "field of study", "major", "area de estudio",
)

# ── Context clues that hint a set of fields is a "person block" ────
_PERSON_BLOCK_HINTS: tuple[str, ...] = (
    "personal information", "personal details", "informacion personal",
    "datos personales", "contact information", "datos de contacto",
    "candidate details", "applicant details",
    "informacion del candidato", "informacion del solicitante",
)


class HeuristicEngine:
    def resolve(self, fields: list[ExtractedField], profile: Any) -> dict[str, object]:
        out: dict[str, object] = {}
        for f in fields:
            if f.current_value:
                continue
            value = self._match(f, profile)
            if value is not None:
                out[f.field_id] = value
        return out

    def _match(self, f: ExtractedField, profile: Any) -> object | None:
        hay = self._hay(f)

        # 1) CV file upload detection (before type rules, since type=file is generic)
        if _contains_any(hay, _CV_FILE_KEYWORDS) and f.type in (None, "file"):
            return _FILE_VALUE_SENTINEL

        # 2) Keyword rules (specific label/name/placeholder matching)
        for keywords, attr in _KEYWORD_RULES:
            if _contains_any(hay, keywords):
                v = self._resolve_attr(profile, attr)
                if v:
                    return v

        # 3) Type-based fallback (only if keyword rules didn't match)
        if f.type and f.type in _TYPE_RULES:
            attr = _TYPE_RULES[f.type]
            v = self._resolve_attr(profile, attr)
            if v:
                return v

        # 4) Word-boundary rules (single words like "name", "phone", "city")
        if not _contains_any(hay, _NAME_SKIP_KEYWORDS):
            for needle, attr in _WORD_BOUNDARY_RULES:
                if _contains_word(hay, needle):
                    v = self._resolve_attr(profile, attr)
                    if v:
                        return v

        return None

    @staticmethod
    def _hay(f: ExtractedField) -> str:
        parts = [
            _unaccent((f.label or "").lower()),
            _unaccent((f.name or "").lower()),
            _unaccent((f.placeholder or "").lower()),
        ]
        return " | ".join(parts)

    @staticmethod
    def _resolve_attr(obj: Any, dotted: str) -> Any:
        cur: Any = obj
        for part in dotted.split("."):
            cur = getattr(cur, part, None)
            if cur is None:
                return None
        return cur


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(n in haystack for n in needles)


def _contains_word(haystack: str, needle: str) -> bool:
    return bool(re.search(r"\b" + re.escape(needle) + r"\b", haystack, re.IGNORECASE))
