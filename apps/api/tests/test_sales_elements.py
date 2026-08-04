from app.services.sales_elements import SALES_ELEMENTS


def test_exactly_17_sales_elements() -> None:
    assert len(SALES_ELEMENTS) == 17
    assert [x[0] for x in SALES_ELEMENTS] == [f"SE{i:02d}" for i in range(1, 18)]


def test_trigger_pain_is_unresolved_key() -> None:
    assert SALES_ELEMENTS[0][2] == "trigger_pain"
