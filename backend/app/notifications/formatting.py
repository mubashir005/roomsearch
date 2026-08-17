"""Shared message formatting for email + Telegram notifications."""
from __future__ import annotations

from app.models import Listing


def rent_label(listing: Listing) -> str:
    if listing.rent_warm is None:
        return "Warmmiete unknown"
    if listing.rent_warm_is_estimated:
        return f"Estimated Warmmiete: €{listing.rent_warm:.0f}"
    return f"€{listing.rent_warm:.0f} Warmmiete"


def anmeldung_label(listing: Listing) -> str:
    return {"possible": "Yes", "impossible": "No", "unknown": "Unknown"}.get(listing.anmeldung.value, "Unknown")


def furnished_label(listing: Listing) -> str:
    return {
        "furnished": "Yes",
        "partially_furnished": "Partially",
        "unfurnished": "No",
        "unknown": "Unknown",
    }.get(listing.furnished.value, "Unknown")


def sources_label(listing: Listing) -> str:
    return ", ".join(listing.sources_found_on) or "unknown"


def email_subject(listings: list[Listing]) -> str:
    if len(listings) == 1:
        l = listings[0]
        size = f"{l.size_sqm:g} m²" if l.size_sqm else ""
        district = l.district or l.city
        return f"🏠 New Hannover Apartment – {rent_label(l)} – {district} – {size}".strip()
    return f"🏠 New Hannover apartment matches – {len(listings)} new listings"


def _yes_no_unknown(value: bool | None) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "Unknown"


def _listing_text_block(listing: Listing) -> str:
    availability = listing.availability_date.strftime("%d.%m.%Y") if listing.availability_date else "unknown"
    first_seen = listing.first_seen_at.strftime("%d %b %Y, %H:%M") if listing.first_seen_at else "unknown"
    why = "\n".join(f"✓ {r.lstrip('✓ ').strip()}" for r in (listing.match_explanation or []) if r.startswith("✓"))

    lines = [f"{listing.title}", ""]
    lines.append(f"💰 {rent_label(listing)}")
    if listing.size_sqm:
        lines.append(f"📐 {listing.size_sqm:g} m²")
    if listing.rooms:
        lines.append(f"🏠 {listing.rooms:g} Zimmer")
    lines.append(f"📍 {listing.district or listing.city}")
    lines.append(f"📅 Available: {availability}")
    lines.append("")
    lines.append(f"📝 Anmeldung: {anmeldung_label(listing)}")
    lines.append(f"🛋 Furnished: {furnished_label(listing)}")
    lines.append(f"🚿 Private bathroom: {_yes_no_unknown(listing.private_bathroom)}")
    lines.append(f"🍳 Private kitchen: {_yes_no_unknown(listing.private_kitchen)}")
    lines.append("")
    lines.append(f"⭐ Match score: {listing.match_score}/100")
    lines.append("")
    lines.append(f"Why it matches:\n{why or 'See dashboard for details.'}")
    lines.append("")
    lines.append(f"Sources: {sources_label(listing)}")
    lines.append(f"[OPEN LISTING] {listing.canonical_url}")
    lines.append("")
    lines.append(f"First seen: {first_seen}")
    lines.append("-" * 40)
    return "\n".join(lines)


def email_body_text(listings: list[Listing]) -> str:
    header = "NEW MATCH\n\n" if len(listings) == 1 else f"NEW MATCHES ({len(listings)})\n\n"
    return header + "\n\n".join(_listing_text_block(l) for l in listings)


def email_body_html(listings: list[Listing]) -> str:
    cards = []
    for l in listings:
        availability = l.availability_date.strftime("%d.%m.%Y") if l.availability_date else "unknown"
        why_items = "".join(
            f"<li>{r}</li>" for r in (l.match_explanation or []) if r.startswith("✓")
        )
        cards.append(
            f"""
            <div style="border:1px solid #e2e2e2;border-radius:8px;padding:16px;margin-bottom:16px;font-family:Arial,sans-serif;">
              <h2 style="margin:0 0 8px;">{l.title}</h2>
              <p style="margin:4px 0;">💰 <b>{rent_label(l)}</b> &nbsp; 📐 {l.size_sqm or '?'} m² &nbsp; 🏠 {l.rooms or '?'} Zimmer</p>
              <p style="margin:4px 0;">📍 {l.district or l.city} &nbsp; 📅 Available: {availability}</p>
              <p style="margin:4px 0;">📝 Anmeldung: {anmeldung_label(l)} &nbsp; 🛋 Furnished: {furnished_label(l)}</p>
              <p style="margin:4px 0;">⭐ Match score: <b>{l.match_score}/100</b></p>
              <ul style="margin:8px 0;">{why_items}</ul>
              <p style="margin:4px 0;">Sources: {sources_label(l)}</p>
              <p style="margin:8px 0;"><a href="{l.canonical_url}" style="background:#2563eb;color:#fff;padding:8px 14px;border-radius:6px;text-decoration:none;">Open listing</a></p>
              <p style="margin:4px 0;color:#666;font-size:12px;">First seen: {l.first_seen_at.strftime('%d %b %Y, %H:%M') if l.first_seen_at else 'unknown'}</p>
            </div>
            """
        )
    return f"<html><body>{''.join(cards)}</body></html>"


def telegram_message(listing: Listing) -> str:
    availability = listing.availability_date.strftime("%d.%m.%Y") if listing.availability_date else "unknown"
    size = f"{listing.size_sqm:g} m²" if listing.size_sqm else "? m²"
    rooms = f"{listing.rooms:g} Zimmer" if listing.rooms else "? Zimmer"
    return (
        "🏠 NEW HANNOVER MATCH\n\n"
        f"{rent_label(listing)}\n"
        f"{size} | {rooms}\n"
        f"📍 {listing.district or listing.city}\n\n"
        f"📅 {availability}\n"
        f"📝 Anmeldung: {anmeldung_label(listing)}\n\n"
        f"⭐ {listing.match_score}/100\n\n"
        f"{listing.canonical_url}"
    )
