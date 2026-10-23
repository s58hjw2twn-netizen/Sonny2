import unittest
from sonny_one.hosted_config import HostedConfig, require_hosted_configuration

class HostedConfigurationTests(unittest.TestCase):
    def config(self, origin="https://sonny.example", db="persistent-db",
               secret="s" * 48):
        return HostedConfig(origin, db, secret)

    def test_valid_configuration(self):
        cfg = self.config()
        self.assertIs(require_hosted_configuration(cfg), cfg)

    def test_reject_http(self):
        with self.assertRaises(ValueError):
            self.config(origin="http://sonny.example").validate()

    def test_reject_localhost(self):
        with self.assertRaises(ValueError):
            self.config(origin="https://localhost").validate()

    def test_reject_url_path(self):
        with self.assertRaises(ValueError):
            self.config(origin="https://sonny.example/login").validate()

    def test_reject_embedded_credentials(self):
        with self.assertRaises(ValueError):
            self.config(origin="https://user:pass@sonny.example").validate()

    def test_reject_missing_persistence(self):
        with self.assertRaises(ValueError):
            self.config(db="").validate()

    def test_reject_weak_secret(self):
        with self.assertRaises(ValueError):
            self.config(secret="short").validate()

if __name__ == "__main__":
    unittest.main()
