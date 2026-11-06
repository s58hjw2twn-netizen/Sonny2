"""Regression checks for conservative Sonny Vision fidelity research primitives."""
import numpy as np
import pytest

from sonny_vision.fidelity_v2 import (
    detect_damage_candidates, evaluate_preservation,
    selective_conventional_repair, texture_diagnostics,
)


def fixtures():
    image = np.full((32, 32, 3), 120, dtype=np.uint8)
    face = np.zeros((32, 32), dtype=bool)
    face[8:24, 8:24] = True
    return image, face


def test_unchanged_image_never_grants_release():
    image, face = fixtures()
    report = evaluate_preservation(image, image.copy(), face)
    assert report["face_max_channel_change"] == 0
    assert report["identity_verified"] is False
    assert report["release_allowed"] is False


def test_deliberate_face_change_detected():
    image, face = fixtures()
    candidate = image.copy()
    candidate[12:16, 12:16] = 250
    report = evaluate_preservation(image, candidate, face)
    assert report["face_max_channel_change"] == 130
    assert not report["face_heuristic_passed"]


def test_missing_face_mask_fails_closed():
    image, _ = fixtures()
    with pytest.raises(ValueError):
        evaluate_preservation(image, image, None)


def test_historical_mask_reports_changes():
    image, face = fixtures()
    historic = np.zeros((32, 32), dtype=bool)
    historic[0:4, 0:4] = True
    candidate = image.copy()
    candidate[0, 0] = 200
    report = evaluate_preservation(image, candidate, face, historic)
    assert report["historical_max_channel_change"] == 80
    assert not report["historical_details_verified"]


def test_selective_repair_preserves_protected_and_unmasked_pixels():
    image, face = fixtures()
    image[3, 3] = 0
    image[12, 12] = 0
    damage = np.zeros((32, 32), dtype=bool)
    damage[3, 3] = True
    damage[12, 12] = True
    before = image.copy()
    output = selective_conventional_repair(image, damage, face)
    assert np.array_equal(image, before)
    assert np.array_equal(output[face], image[face])
    assert np.array_equal(output[~damage], image[~damage])


def test_no_damage_candidate_on_flat_image():
    image, face = fixtures()
    assert not detect_damage_candidates(image).any()
    assert texture_diagnostics(image, image, face)["authentic_texture_verified"] is False
