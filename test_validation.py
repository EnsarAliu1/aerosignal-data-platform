import unittest
from validation import validate_ingestion_params

class TestIngestionParams(unittest.TestCase):
    def test_invalid_month(self):
        with self.assertRaises(ValueError):
            validate_ingestion_params(
                year=2025,
                month=13,
                source_sha256="a" * 64
            )

    def test_valid_parameters(self):
        result = validate_ingestion_params(
            year=2025,
            month=1,
            source_sha256="a" * 64
        )

        self.assertIsNone(result)

    def test_invalid_year(self):
        with self.assertRaises(ValueError):
            validate_ingestion_params(
                year=1986,
                month=1,
                source_sha256="a" * 64
            )

    def test_invalid_sha256(self):
        invalid_hashes = [
            "a" * 63,
            "a" * 65,
            "g" * 64,
        ]

        for invalid_hash in invalid_hashes:
            with self.subTest(sha256=invalid_hash):
                with self.assertRaisesRegex(ValueError, "Invalid SHA256"):
                    validate_ingestion_params(
                        year=2025,
                        month=1,
                        source_sha256=invalid_hash
                    )
