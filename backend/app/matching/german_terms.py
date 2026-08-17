"""German real-estate terminology normalization.

Recognizes room counts, furnishing level, Anmeldung status, rental type, and
apartment size from German (and mixed German/English) listing text.
"""
from __future__ import annotations

import re

_ROOM_PATTERNS = [
    (re.compile(r"\b(\d+([.,]\d)?)\s*[- ]?zi(?:mmer)?\b\.?", re.IGNORECASE), None),
    (re.compile(r"\beinzimmerwohnung\b", re.IGNORECASE), 1.0),
    (re.compile(r"\bzweizimmerwohnung\b", re.IGNORECASE), 2.0),
    (re.compile(r"\bstudio\b", re.IGNORECASE), 1.0),
    (re.compile(r"\bapartment\b", re.IGNORECASE), 1.0),
]


def extract_rooms(text: str) -> float | None:
    if not text:
        return None
    for pattern, fixed_value in _ROOM_PATTERNS:
        m = pattern.search(text)
        if m:
            if fixed_value is not None:
                return fixed_value
            try:
                return float(m.group(1).replace(",", "."))
            except (ValueError, IndexError):
                continue
    return None


_SIZE_RE = re.compile(r"(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:m²|m2|qm|sqm)\b", re.IGNORECASE)


def extract_size_sqm(text: str) -> float | None:
    if not text:
        return None
    m = _SIZE_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


_FURNISHED_FULL = re.compile(r"\bvoll\s*m[oö]bliert\w*", re.IGNORECASE)
_FURNISHED_PARTIAL = re.compile(r"\bteil\s*m[oö]bliert\w*", re.IGNORECASE)
_FURNISHED_PLAIN = re.compile(r"(?<!un)(?<!teil)(?<!teil-)m[oö]bliert\w*", re.IGNORECASE)
_UNFURNISHED = re.compile(r"\bunm[oö]bliert\w*", re.IGNORECASE)


def extract_furnished(text: str) -> str:
    """Returns one of: furnished, partially_furnished, unfurnished, unknown."""
    if not text:
        return "unknown"
    if _UNFURNISHED.search(text):
        return "unfurnished"
    if _FURNISHED_FULL.search(text):
        return "furnished"
    if _FURNISHED_PARTIAL.search(text):
        return "partially_furnished"
    if _FURNISHED_PLAIN.search(text):
        return "furnished"
    return "unknown"


_ANMELDUNG_POSSIBLE = re.compile(
    r"anmeldung\s*(?:ist\s*)?(?:m[oö]glich|erlaubt|kein\s*problem|möglich)|"
    r"wohnsitzanmeldung\s*(?:m[oö]glich|möglich)|meldeadresse\s*(?:m[oö]glich|vorhanden)",
    re.IGNORECASE,
)
_ANMELDUNG_IMPOSSIBLE = re.compile(
    r"(keine|kein)\s*anmeldung|anmeldung\s*(?:ist\s*)?nicht\s*m[oö]glich|"
    r"anmeldung\s*nicht\s*erlaubt|ohne\s*anmeldung",
    re.IGNORECASE,
)


def extract_anmeldung(text: str) -> str:
    """Returns one of: possible, impossible, unknown."""
    if not text:
        return "unknown"
    # Check impossible first: "keine Anmeldung möglich" would also match the
    # possible regex's "möglich", so negatives must win when both fire.
    if _ANMELDUNG_IMPOSSIBLE.search(text):
        return "impossible"
    if _ANMELDUNG_POSSIBLE.search(text):
        return "possible"
    return "unknown"


_ZWISCHENMIETE = re.compile(r"\bzwischenmiete\w*", re.IGNORECASE)
_BEFRISTET = re.compile(r"\bbefristet\w*", re.IGNORECASE)
_UNBEFRISTET = re.compile(r"\bunbefristet\w*", re.IGNORECASE)
_LANGFRISTIG = re.compile(r"\blangfristig\w*", re.IGNORECASE)
_NACHMIETER = re.compile(r"\bnachmieter\w*", re.IGNORECASE)


def extract_rental_type(text: str) -> str:
    """Returns one of: long_term, temporary, zwischenmiete, unknown."""
    if not text:
        return "unknown"
    if _ZWISCHENMIETE.search(text) or _NACHMIETER.search(text):
        return "zwischenmiete"
    if _UNBEFRISTET.search(text) or _LANGFRISTIG.search(text):
        return "long_term"
    if _BEFRISTET.search(text):
        return "temporary"
    return "unknown"


_PRIVATE_BATHROOM = re.compile(r"eigenes?\s*bad|privates?\s*bad|eigenes?\s*badezimmer", re.IGNORECASE)
_SHARED_BATHROOM = re.compile(r"gemeinsames?\s*bad|geteiltes?\s*bad|shared\s*bathroom", re.IGNORECASE)
_PRIVATE_KITCHEN = re.compile(r"eigene\s*k[uü]che|private\s*kitchen", re.IGNORECASE)
_SHARED_KITCHEN = re.compile(r"gemeinsame\s*k[uü]che|geteilte\s*k[uü]che|shared\s*kitchen", re.IGNORECASE)
_BALCONY = re.compile(r"balkon|balcony|terrasse", re.IGNORECASE)


def extract_bool_feature(text: str, positive: re.Pattern, negative: re.Pattern | None = None) -> bool | None:
    if not text:
        return None
    if negative is not None and negative.search(text):
        return False
    if positive.search(text):
        return True
    return None


def extract_private_bathroom(text: str) -> bool | None:
    return extract_bool_feature(text, _PRIVATE_BATHROOM, _SHARED_BATHROOM)


def extract_private_kitchen(text: str) -> bool | None:
    return extract_bool_feature(text, _PRIVATE_KITCHEN, _SHARED_KITCHEN)


def extract_balcony(text: str) -> bool | None:
    return extract_bool_feature(text, _BALCONY)
