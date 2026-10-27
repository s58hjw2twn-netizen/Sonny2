"""Summarize controlled registration benchmark outcomes without overstating scope."""
from sonny_vision.quality.translation_benchmark import run_translation_benchmark
from sonny_vision.quality.photometric_benchmark import photometric_stress_benchmark


def benchmark_summary():
    translation = run_translation_benchmark()
    lighting = photometric_stress_benchmark()
    total = translation["synthetic_cases"] + lighting["total"]
    correct = translation["correct"] + lighting["correct"]
    failures = [case["condition"] for case in lighting["cases"] if not case["correct"]]
    return {
        "synthetic_total": total,
        "synthetic_correct": correct,
        "synthetic_accuracy": correct / total,
        "photometric_failures": failures,
        "low_texture_rejected": translation["flat_rejected"],
        "real_photo_samples": 0,
        "real_photo_accuracy": None,
        "identity_preservation_verified": False,
        "commercial_readiness": False,
    }
