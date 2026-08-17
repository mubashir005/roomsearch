import pytest

from app.matching import german_terms as gt


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1 Zimmer Wohnung in Hannover", 1.0),
        ("1-Zimmer-Wohnung", 1.0),
        ("1 Zi. Wohnung", 1.0),
        ("Einzimmerwohnung im Zentrum", 1.0),
        ("gemütliches Studio zu vermieten", 1.0),
        ("modernes Apartment", 1.0),
        ("2 Zimmer Wohnung", 2.0),
        ("kein Hinweis auf Zimmerzahl", None),
    ],
)
def test_extract_rooms(text, expected):
    assert gt.extract_rooms(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("32 m² große Wohnung", 32.0),
        ("28qm Studio", 28.0),
        ("45 sqm apartment", 45.0),
        ("kompakt und gemütlich", None),
    ],
)
def test_extract_size(text, expected):
    assert gt.extract_size_sqm(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("vollmöbliert und modern", "furnished"),
        ("teilmöbliert, mit Bett und Schrank", "partially_furnished"),
        ("die Wohnung ist möbliert", "furnished"),
        ("unmöbliert, ohne Küche", "unfurnished"),
        ("keine Angabe zur Einrichtung", "unknown"),
    ],
)
def test_extract_furnished(text, expected):
    assert gt.extract_furnished(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Anmeldung ist möglich", "possible"),
        ("Wohnsitzanmeldung möglich", "possible"),
        ("keine Anmeldung möglich", "impossible"),
        ("Anmeldung nicht möglich", "impossible"),
        ("ohne Anmeldung", "impossible"),
        ("keine Angabe", "unknown"),
    ],
)
def test_extract_anmeldung(text, expected):
    assert gt.extract_anmeldung(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Zwischenmiete für 3 Monate", "zwischenmiete"),
        ("Nachmieter gesucht", "zwischenmiete"),
        ("unbefristeter Mietvertrag", "long_term"),
        ("langfristig zu vermieten", "long_term"),
        ("befristet bis Ende des Jahres", "temporary"),
        ("keine Angabe", "unknown"),
    ],
)
def test_extract_rental_type(text, expected):
    assert gt.extract_rental_type(text) == expected


def test_private_vs_shared_bathroom():
    assert gt.extract_private_bathroom("eigenes Bad vorhanden") is True
    assert gt.extract_private_bathroom("gemeinsames Bad mit Mitbewohnern") is False
    assert gt.extract_private_bathroom("keine Angabe") is None


def test_private_vs_shared_kitchen():
    assert gt.extract_private_kitchen("eigene Küche") is True
    assert gt.extract_private_kitchen("geteilte Küche") is False
    assert gt.extract_private_kitchen("keine Angabe") is None


def test_balcony_detection():
    assert gt.extract_balcony("mit Balkon") is True
    assert gt.extract_balcony("keine Angabe") is None
