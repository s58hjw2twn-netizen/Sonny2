"""Experimental-only toy functions for offline patch generation.

Not used by the production Sonny ONE application.
"""


def mean(values):
    return sum(values) / len(values)


def smallest(values):
    return sorted(values)[0]


def largest(values):
    return max(values)
