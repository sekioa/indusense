import tempfile
import unittest
from pathlib import Path

from indusense.ingestion.bronze import read_source_rows, source_record_hash, source_sha256


class BronzeIngestionTests(unittest.TestCase):
    def test_reader_preserves_empty_cells_and_physical_row_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_file = Path(temporary_directory) / "source.csv"
            source_file.write_text("id,comment\n1,\n2,ok\n", encoding="utf-8")

            rows = list(read_source_rows(source_file))

        self.assertEqual(rows, [(2, {"id": "1", "comment": ""}), (3, {"id": "2", "comment": "ok"})])

    def test_hashes_are_stable_for_the_same_source_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_file = Path(temporary_directory) / "source.csv"
            source_file.write_text("id\n1\n", encoding="utf-8")

            first_hash = source_sha256(source_file)
            second_hash = source_sha256(source_file)

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)
        self.assertEqual(source_record_hash({"id": "1"}), source_record_hash({"id": "1"}))
