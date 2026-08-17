"""German rent price parsing: Warmmiete / Kaltmiete / Nebenkosten / Heizkosten.

German listings are inconsistent about whether the quoted price is cold rent,
warm rent, or something in between. This module extracts whichever pieces are
present and derives a warm-rent estimate ONLY when it must be calculated from
parts -- and always flags derived values as estimated. It never silently
treats Kaltmiete as Warmmiete.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_AMOUNT = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s?(?:€|eur|euro)?"

# Keyword groups, ordered by specificity (checked warm before cold so
# "Gesamtmiete" / "Miete inkl. Nebenkosten" isn't mistaken for cold rent).
_WARM_KEYWORDS = [
    r"warmmiete",
    r"gesamtmiete",
    r"miete\s*inkl\.?\s*(?:aller\s*)?nebenkosten",
    r"gesamtkosten\s*(?:monatlich)?",
    r"gesamtpreis",
]
_COLD_KEYWORDS = [r"kaltmiete", r"grundmiete", r"nettokaltmiete"]
_UTILITIES_KEYWORDS = [r"nebenkosten", r"nk\b", r"betriebskosten"]
_HEATING_KEYWORDS = [r"heizkosten", r"heizkostenvorauszahlung"]


def _to_float(raw: str) -> float | None:
    """Parse a German- or English-formatted number string into a float."""
    raw = raw.strip()
    if not raw:
        return None
    # German format: '.' thousands, ',' decimal -> normalize to plain float string.
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        # Ambiguous: '400,00' (decimal) vs '1,200' (thousands, rare for rent).
        integer_part, _, frac = raw.partition(",")
        if len(frac) == 3:
            raw = raw.replace(",", "")
        else:
            raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _find_amount_near(text: str, keywords: list[str]) -> float | None:
    for kw in keywords:
        # amount after keyword, e.g. "Warmmiete: 480 €" / "Warmmiete 480€"
        m = re.search(kw + r"[:\s]{0,20}" + _AMOUNT, text, re.IGNORECASE)
        if m:
            val = _to_float(m.group(1))
            if val is not None:
                return val
        # amount before keyword, e.g. "480 € Warmmiete"
        m = re.search(_AMOUNT + r"\s{0,10}" + kw, text, re.IGNORECASE)
        if m:
            val = _to_float(m.group(1))
            if val is not None:
                return val
    return None


@dataclass
class RentInfo:
    cold: float | None = None
    warm: float | None = None
    utilities: float | None = None
    heating: float | None = None
    warm_is_estimated: bool = False
    warm_unknown: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def display_warm_label(self) -> str:
        if self.warm_unknown:
            return "Warmmiete unknown"
        if self.warm_is_estimated:
            return f"Estimated Warmmiete: €{self.warm:.0f}"
        return f"Warmmiete: €{self.warm:.0f}"


def parse_rent(
    text: str = "",
    *,
    cold: float | None = None,
    warm: float | None = None,
    utilities: float | None = None,
    heating: float | None = None,
) -> RentInfo:
    """Extract rent components from free text, optionally seeded with already
    structured values (e.g. from a source's own price/cold-rent/nebenkosten
    fields) which take precedence over text-derived values."""
    text = text or ""

    warm = warm if warm is not None else _find_amount_near(text, _WARM_KEYWORDS)
    cold = cold if cold is not None else _find_amount_near(text, _COLD_KEYWORDS)
    utilities = utilities if utilities is not None else _find_amount_near(text, _UTILITIES_KEYWORDS)
    heating = heating if heating is not None else _find_amount_near(text, _HEATING_KEYWORDS)

    info = RentInfo(cold=cold, utilities=utilities, heating=heating)

    if warm is not None:
        info.warm = warm
        info.warm_is_estimated = False
        return info

    if cold is not None and (utilities is not None or heating is not None):
        parts = [cold]
        if utilities is not None:
            parts.append(utilities)
        if heating is not None:
            parts.append(heating)
        info.warm = sum(parts)
        info.warm_is_estimated = True
        info.notes.append(
            "Warmmiete derived from Kaltmiete + " + " + ".join(
                n for n, v in (("Nebenkosten", utilities), ("Heizkosten", heating)) if v is not None
            )
        )
        return info

    # Cold rent alone, or nothing at all -- warm rent cannot be determined.
    info.warm = None
    info.warm_unknown = True
    if cold is not None:
        info.notes.append("Only Kaltmiete found; Nebenkosten unknown, Warmmiete cannot be calculated.")
    else:
        info.notes.append("No rent information could be parsed.")
    return info
