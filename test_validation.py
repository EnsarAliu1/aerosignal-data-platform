import hashlib
import unittest
from validation import validate_ingestion_params, validate_required_columns, validate_file_checksum

import tempfile
from pathlib import Path

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

class TestRequiredColumns(unittest.TestCase):
    def test_required_columns_present(self):
        result = validate_required_columns(
            actual_columns=["YEAR", "MONTH", "FL_DATE", "EXTRA"],
            required_columns=["YEAR", "MONTH", "FL_DATE"],
        )
        self.assertIsNone(result)

    
    def test_required_columns_missing(self):
        with self.assertRaisesRegex(ValueError, "FL_DATE"):
            validate_required_columns(
                actual_columns=["YEAR", "MONTH"],
                required_columns=["YEAR", "MONTH", "FL_DATE"]
            )


class TestFileChecksum(unittest.TestCase):
    def test_valid_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "sample.csv"
            test_file.write_text("YEAR,MONTH\n2025,1\n")

            actual = hashlib.sha256(test_file.read_bytes()).hexdigest()

            result = validate_file_checksum(
                source_path=str(test_file),
                expected_sha256=actual
            )
            self.assertIsNone(result)


    def test_invalid_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "sample.csv"
            test_file.write_text("YEAR,MONTH\n2025,1\n")

            with self.assertRaisesRegex(ValueError, "Source SHA256 mismatch"):
                result = validate_file_checksum(
                    source_path=str(test_file),
                    expected_sha256="0" * 64
                )