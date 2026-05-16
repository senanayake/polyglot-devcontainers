import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from python_node_secure_template import add

pytestmark = pytest.mark.acceptance

scenarios("addition.feature")


@given(parsers.parse("the backend numbers {left:d} and {right:d}"), target_fixture="numbers")
def given_numbers(left: int, right: int) -> dict[str, int]:
    return {"left": left, "right": right}


@when("the backend numbers are added", target_fixture="result")
def when_numbers_are_added(numbers: dict[str, int]) -> int:
    return add(numbers["left"], numbers["right"])


@then(parsers.parse("the backend result is {expected:d}"))
def then_result_is(result: int, expected: int) -> None:
    assert result == expected
