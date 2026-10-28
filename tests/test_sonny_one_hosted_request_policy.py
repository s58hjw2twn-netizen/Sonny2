import unittest
from sonny_one.hosted_request_policy import validate_hosted_request

class HostedRequestPolicyTests(unittest.TestCase):
    def check(self, **overrides):
        args = dict(canonical_origin="https://sonny.example",
                    host="sonny.example", origin="https://sonny.example",
                    method="POST", verified_https=True)
        args.update(overrides)
        return validate_hosted_request(**args)

    def test_allowed_same_origin_post(self):
        self.assertIsNone(self.check())

    def test_allowed_get_without_origin(self):
        self.assertIsNone(self.check(method="GET", origin=None))

    def test_block_wrong_host(self):
        with self.assertRaises(PermissionError):
            self.check(host="other.example")

    def test_block_cross_origin_post(self):
        with self.assertRaises(PermissionError):
            self.check(origin="https://other.example")

    def test_block_missing_origin_post(self):
        with self.assertRaises(PermissionError):
            self.check(origin=None)

    def test_block_unverified_tls(self):
        with self.assertRaises(PermissionError):
            self.check(verified_https=False)

    def test_block_cross_origin_get(self):
        with self.assertRaises(PermissionError):
            self.check(method="GET", origin="https://other.example")

    def test_block_noncanonical_method(self):
        with self.assertRaises(PermissionError):
            self.check(method="post")

if __name__ == "__main__":
    unittest.main()
