"""Tests for the heuristic engine."""
from beanie import PydanticObjectId

from smartcvapply.models.profile import Profile
from smartcvapply.services.heuristic_engine import ExtractedField, HeuristicEngine


def make_field(fid: str, label: str, type_: str = "text", **kwargs) -> ExtractedField:
    return ExtractedField(field_id=fid, label=label, type=type_, **kwargs)


def _profile() -> Profile:
    return Profile(user_id=PydanticObjectId())


def test_email_by_type() -> None:
    p = _profile()
    p.email = "jane@example.com"
    out = HeuristicEngine().resolve([make_field("f1", "anything", type_="email")], p)
    assert out["f1"] == "jane@example.com"


def test_phone_by_type() -> None:
    p = _profile()
    p.phone = "+34612345678"
    out = HeuristicEngine().resolve([make_field("f1", "anything", type_="tel")], p)
    assert out["f1"] == "+34612345678"


def test_first_name_by_keyword() -> None:
    p = _profile()
    p.first_name = "Jane"
    out = HeuristicEngine().resolve([make_field("f1", "First name")], p)
    assert out["f1"] == "Jane"


def test_linkedin_by_keyword() -> None:
    p = _profile()
    p.linkedin_url = "https://linkedin.com/in/jane"
    out = HeuristicEngine().resolve([make_field("f1", "LinkedIn Profile URL")], p)
    assert out["f1"] == "https://linkedin.com/in/jane"


def test_unknown_field_is_skipped() -> None:
    p = _profile()
    p.first_name = "Jane"
    out = HeuristicEngine().resolve([make_field("f1", "Mother's maiden name")], p)
    assert "f1" not in out


def test_field_already_filled_is_skipped() -> None:
    p = _profile()
    p.first_name = "Jane"
    out = HeuristicEngine().resolve(
        [make_field("f1", "First name", current_value="John")], p,
    )
    assert "f1" not in out
