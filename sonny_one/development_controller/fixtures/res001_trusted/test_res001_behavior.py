import os
import pytest

if os.environ.get("SONNY_APL_EVALUATION") != "1":
    pytest.skip("APL candidate-only fixture; baseline expected to fail", allow_module_level=True)

"""Trusted behavioral fixtures for the RES-001 mean() experiment.

This file is intended for execution only inside the separately configured
APL Docker sandbox, never by importing an untrusted candidate on the host.
The target's function semantics are intentionally tested independently of
the model's patch-generation prompt.
"""
import pytest

from sonny_one.apl_targets.offline_strategy import mean, smallest, largest


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([1, 2, 3], 2),
        ([5], 5),
        ([-5, 5], 0),
        ([0, 0, 0], 0),
        ([0.5, 1.5], 1),
        ([-3, -1, -2], -2),
    ],
)
def test_mean_preserves_numeric_behavior(values, expected):
    assert mean(values) == pytest.approx(expected)


@pytest.mark.skipif(os.environ.get("SONNY_APL_CANDIDATE_TEST") != "1", reason="candidate-only behavior")
def test_mean_empty_input_is_value_error():
    with pytest.raises(ValueError, match=r".+"):
        mean([])


def test_smallest_unchanged():
    assert smallest([9, 2, 7]) == 2


def test_largest_unchanged():
    assert largest([9, 2, 7]) == 9
