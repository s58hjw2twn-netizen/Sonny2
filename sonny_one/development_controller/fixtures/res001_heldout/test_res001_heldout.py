"""Held-out RES-001 regression tests for isolated Docker evaluation.

Keep these tests outside the model prompt. Running them against a generated
candidate requires the APL evaluator's separate fixture custody and Docker
sandbox. They are not proof of successful model performance by themselves.
"""
import pytest

from sonny_one.apl_targets.offline_strategy import mean, smallest, largest


@pytest.mark.parametrize("values", [
    [10, 20, 30, 40],
    [1.25, 2.75, 3.5, 4.5],
    [-100, 0, 100],
    [7] * 17,
    list(range(-20, 21)),
])
def test_mean_additional_numeric_cases(values):
    assert mean(values) == pytest.approx(sum(values) / len(values))


def test_empty_tuple_rejected():
    with pytest.raises(ValueError):
        mean(())


def test_unrelated_functions_preserved():
    values = [8, -2, 3, 8]
    assert smallest(values) == -2
    assert largest(values) == 8


def test_mean_does_not_mutate_input():
    values = [4, 1, 7]
    original = list(values)
    mean(values)
    assert values == original
