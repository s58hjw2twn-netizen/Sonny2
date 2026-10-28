"""Conservative review-only orchestration of Sonny Vision geometry and texture checks."""
from sonny_vision.identity.drift_gate import drift_report
from sonny_vision.quality.texture import texture_report
from sonny_vision.identity.release_gate import restoration_release_gate


def evaluate_restoration(faces, *, identity_scores=None, reference_review_passed=False, owner_approved=False):
    """All face measurements must be aligned and supplied by independent tools."""
    reports, textures, failures = [], [], []
    for index, face in enumerate(faces):
        try:
            drift = drift_report(face['landmark_stages'])
            texture = texture_report(face['original_crop'], face['restored_crop'])
            reports.append({'geometry_pass': drift['geometry_pass']})
            textures.append(texture)
            if not drift['geometry_pass']:
                failures.append(f'face_{index}_drift')
            if not texture['texture_pass']:
                failures.append(f'face_{index}_texture')
        except (ValueError, KeyError, TypeError, OverflowError):
            reports.append({'geometry_pass': False})
            textures.append({'texture_pass': False, 'reason': 'invalid_or_missing_evidence'})
            failures.append(f'face_{index}_invalid_evidence')
    release = restoration_release_gate(
        reports, identity_scores=identity_scores,
        texture_review_passed=bool(textures) and all(t['texture_pass'] for t in textures),
        reference_review_passed=reference_review_passed,
        owner_approved=owner_approved)
    return {'release_allowed': release['release_allowed'] and not failures,
            'release_gate': release, 'texture_reports': textures,
            'diagnostic_failures': failures, 'identity_verified': False,
            'human_review_required': True}
