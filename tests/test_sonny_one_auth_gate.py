import unittest

from sonny_one.integration.auth_gate import authorize_bearer


class AuthGateTests(unittest.TestCase):
    TOKEN = "a" * 48

    def test_exact_token(self):
        self.assertTrue(authorize_bearer([(b"Authorization", b"Bearer " + self.TOKEN.encode())], self.TOKEN))

    def test_rejects_missing_duplicate_and_wrong_credentials(self):
        cases = [
            [],
            [(b"authorization", b"Bearer wrong")],
            [(b"authorization", b"Basic " + self.TOKEN.encode())],
            [(b"authorization", b"Bearer " + self.TOKEN.encode())] * 2,
            [(b"authorization", b"Bearer " + self.TOKEN.encode() + b" ")],
            [(b"authorization", b"Bearer \xff")],
            [(b"authorization", "Bearer " + self.TOKEN)],
        ]
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertFalse(authorize_bearer(headers, self.TOKEN))

    def test_rejects_weak_configuration(self):
        headers = [(b"authorization", b"Bearer short")]
        self.assertFalse(authorize_bearer(headers, "short"))
        self.assertFalse(authorize_bearer(headers, None))


if __name__ == "__main__":
    unittest.main()
