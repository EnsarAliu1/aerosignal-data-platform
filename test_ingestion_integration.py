import unittest
import hashlib

from ingestion import ingest_bts_month, TABLE_NAME

class TestBronzeIngestion(unittest.TestCase):
    def test_empty_file_rejected(self):
        test_path = (
            "/Volumes/workspace/aerosignal_bronze/source_files/test_empty.csv"
        )

        with open(test_path, "rb") as file:
            test_sha256 = hashlib.file_digest(
                file, "sha256"
            ).hexdigest()

        rows_before = self.spark.table(TABLE_NAME).count()

        version_before = self.spark.sql(
            f"DESCRIBE HISTORY {TABLE_NAME}"
        ).first()["version"]

        with self.assertRaisesRegex(
            ValueError,
            "Source file is empty"
        ):
            ingest_bts_month(
                spark=self.spark,
                source_path=test_path,
                year=2025,
                month=1,
                source_sha256=test_sha256,
            )

        rows_after = self.spark.table(TABLE_NAME).count()

        version_after = self.spark.sql(
            f"DESCRIBE HISTORY {TABLE_NAME}"
        ).first()["version"]

        self.assertEqual(rows_before, rows_after)
        self.assertEqual(version_before, version_after)

