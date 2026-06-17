"""Server-side heuristic engine for field resolution."""
from dataclasses import dataclass
from typing import Any


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


_KEYWORD_RULES: list[tuple[tuple[str, ...], str]] = [
    (("first name", "given name", "nombre", "firstname"), "first_name"),
    (("last name", "surname", "family name", "apellido", "apellidos", "lastname"), "last_name"),
    (("full name", "your name", "nombre completo"), "first_name"),
    (("email", "correo", "correo electronico"), "email"),
    (("phone", "telephone", "mobile", "telefono", "movil"), "phone"),
    (("linkedin",), "linkedin_url"),
    (("github",), "github_url"),
    (("portfolio", "website", "sitio web"), "portfolio_url"),
    (("summary", "bio", "about you", "sobre ti"), "summary"),
    (("city", "ciudad"), "location.city"),
    (("country", "pais"), "location.country"),
]

_TYPE_RULES: dict[str, str] = {
    "email": "email",
    "tel": "phone",
}


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
        if f.type and f.type in _TYPE_RULES:
            attr = _TYPE_RULES[f.type]
            v = self._resolve_attr(profile, attr)
            if v:
                return v
        haystacks = [(f.label or "").lower(), (f.name or "").lower(), (f.placeholder or "").lower()]
        for keywords, attr in _KEYWORD_RULES:
            for h in haystacks:
                if any(k in h for k in keywords):
                    v = self._resolve_attr(profile, attr)
                    if v:
                        return v
        return None

    @staticmethod
    def _resolve_attr(obj: Any, dotted: str) -> Any:
        cur: Any = obj
        for part in dotted.split("."):
            cur = getattr(cur, part, None)
            if cur is None:
                return None
        return cur
