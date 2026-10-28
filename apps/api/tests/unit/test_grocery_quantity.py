from homehub.modules.groceries.quantity import add_quantities, adjust_quantity


def test_add_quantities():
    assert add_quantities("1", "1") == "2"
    assert add_quantities("2.5", "1") == "3.5"


def test_adjust_quantity():
    assert adjust_quantity("2", -1) == "1"
    assert adjust_quantity("1", -1) is None
