import pytest
from hypothesis import given
from hypothesis import strategies as st

from python_secure_template import add

pytestmark = pytest.mark.property


@given(st.integers(), st.integers())
def test_add_is_commutative(left: int, right: int) -> None:
    assert add(left, right) == add(right, left)
