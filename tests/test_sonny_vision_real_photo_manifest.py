import unittest
from sonny_vision.quality.real_photo_manifest import validate_manifest

def sample():
    return {"pairs":[{"id":"case-001","consent_confirmed":True,"owner_review_required":True,
       "original_sha256":"a"*64,"restored_sha256":"b"*64}]}

class RealPhotoManifestTests(unittest.TestCase):
    def test_valid_metadata_not_identity_proof(self):
        r=validate_manifest(sample())
        self.assertEqual(r["pairs_validated"],1)
        self.assertFalse(r["identity_verified"])
        self.assertFalse(r["image_bytes_verified"])
    def test_missing_consent_rejected(self):
        m=sample();m["pairs"][0]["consent_confirmed"]="yes"
        with self.assertRaises(ValueError):validate_manifest(m)
    def test_duplicate_ids_rejected(self):
        m=sample();m["pairs"].append(dict(m["pairs"][0]))
        with self.assertRaises(ValueError):validate_manifest(m)
    def test_private_embedding_rejected(self):
        m=sample();m["pairs"][0]["face_embedding"]=[.1,.2]
        with self.assertRaises(ValueError):validate_manifest(m)
    def test_invalid_digest_rejected(self):
        m=sample();m["pairs"][0]["restored_sha256"]="x"*64
        with self.assertRaises(ValueError):validate_manifest(m)
