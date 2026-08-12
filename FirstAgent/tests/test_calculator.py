import pytest

from skills.calculator import CalculatorSkill


@pytest.fixture
def calculator() -> CalculatorSkill:
    return CalculatorSkill()


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (1, 2, 3),
        (-1, 1, 0),
        (1.5, 2.5, 4.0),
        (0, 0, 0),
    ],
)
def test_add(
    calculator: CalculatorSkill,
    a: int | float,
    b: int | float,
    expected: int | float,
) -> None:
    assert calculator.add(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (111, 444, 49284),
        (123, 456, 56088),
        (-2, 3, -6),
        (1.5, 2, 3.0),
        (0, 999, 0),
    ],
)
def test_multiply(
    calculator: CalculatorSkill,
    a: int | float,
    b: int | float,
    expected: int | float,
) -> None:
    assert calculator.multiply(a, b) == expected


@pytest.mark.parametrize("value", [True, False, "10", None, [], {}])
def test_rejects_non_numeric_values(
    calculator: CalculatorSkill,
    value: object,
) -> None:
    with pytest.raises(TypeError):
        calculator.add(value, 1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_rejects_non_finite_values(
    calculator: CalculatorSkill,
    value: float,
) -> None:
    with pytest.raises(ValueError):
        calculator.multiply(value, 1)
