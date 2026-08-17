from app.matching.location import LocationMatch, classify_location, extract_district


def test_core_district_detected():
    assert classify_location("Hannover", "List", "") == LocationMatch.IN_CORE_DISTRICT


def test_core_district_from_text_only():
    assert classify_location("Hannover", None, "Wohnung in Linden-Nord") == LocationMatch.IN_CORE_DISTRICT


def test_hannover_general_without_core_district():
    assert classify_location("Hannover", None, "irgendwo in der Stadt") == LocationMatch.IN_HANNOVER


def test_nearby_area():
    assert classify_location("Garbsen", None, "") == LocationMatch.NEARBY


def test_outside():
    assert classify_location("Berlin", None, "") == LocationMatch.OUTSIDE


def test_unknown_when_no_location_info():
    assert classify_location(None, None, "") == LocationMatch.UNKNOWN


def test_extract_district_normalizes_umlauts():
    assert extract_district("Wohnung in der Südstadt") == "Südstadt"


def test_extract_district_nearby_area():
    assert extract_district("Wohnung in Langenhagen") == "Langenhagen"


def test_extract_district_none_when_absent():
    assert extract_district("keine Ortsangabe") is None
