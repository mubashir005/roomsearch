from app.matching.price_parser import parse_rent


def test_warm_rent_given_directly():
    info = parse_rent("Warmmiete: 480 € - schöne Wohnung")
    assert info.warm == 480
    assert info.warm_is_estimated is False
    assert info.warm_unknown is False


def test_cold_plus_nebenkosten_is_estimated():
    info = parse_rent("Kaltmiete 400 €, Nebenkosten 80 €")
    assert info.cold == 400
    assert info.utilities == 80
    assert info.warm == 480
    assert info.warm_is_estimated is True


def test_cold_plus_nebenkosten_plus_heizkosten():
    info = parse_rent("Kaltmiete 400 €, Nebenkosten 80 €, Heizkosten 70 €")
    assert info.warm == 550
    assert info.warm_is_estimated is True
    assert "derived" in info.notes[0].lower()


def test_cold_only_is_unknown_not_treated_as_warm():
    info = parse_rent("Kaltmiete 400 €")
    assert info.cold == 400
    assert info.warm is None
    assert info.warm_unknown is True


def test_nothing_found_is_unknown():
    info = parse_rent("A lovely place to live.")
    assert info.warm is None
    assert info.cold is None
    assert info.warm_unknown is True


def test_structured_values_take_precedence_over_text():
    info = parse_rent("random text with no numbers", warm=450)
    assert info.warm == 450
    assert info.warm_is_estimated is False


def test_gesamtmiete_recognized_as_warm():
    info = parse_rent("Gesamtmiete 495€ inkl. aller Kosten")
    assert info.warm == 495


def test_german_decimal_comma_format():
    info = parse_rent("Warmmiete 480,50 €")
    assert info.warm == 480.5


def test_display_label_estimated():
    info = parse_rent("Kaltmiete 400 €, Nebenkosten 80 €")
    assert info.display_warm_label == "Estimated Warmmiete: €480"


def test_display_label_unknown():
    info = parse_rent("no price here")
    assert info.display_warm_label == "Warmmiete unknown"
