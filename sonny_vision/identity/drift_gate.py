"""Track landmark drift across registered restoration stages."""
from sonny_vision.identity.geometry_gate import geometry_report

def drift_report(stages, *, max_mean_displacement=0.015, max_single_displacement=0.035):
    """Compare each stage against original and preceding stage; not identity proof."""
    frames = list(stages)
    if len(frames) < 2:
        raise ValueError("at least two stages required")
    comparisons = []
    for index in range(1, len(frames)):
        kw = dict(max_mean_displacement=max_mean_displacement,
                  max_single_displacement=max_single_displacement)
        original = geometry_report(frames[0], frames[index], **kw)
        previous = geometry_report(frames[index - 1], frames[index], **kw)
        comparisons.append(dict(stage=index, against_original=original,
                                against_previous=previous))
    return dict(
        geometry_pass=all(c["against_original"]["geometry_pass"] and
                          c["against_previous"]["geometry_pass"] for c in comparisons),
        identity_verified=False, requires_reference_review=True,
        comparisons=comparisons)
