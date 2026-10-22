import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("import_excel", ROOT / "scripts/import_excel.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExcelImportTests(unittest.TestCase):
    def test_reproduces_saved_database_and_preserves_all_source_rows(self):
        catalog = module.build_catalog()
        self.assertEqual(catalog, json.loads((ROOT / "data/library-catalog.json").read_text()))
        self.assertEqual(catalog["recordCount"], 1529)
        self.assertEqual(len({r["id"] for r in catalog["records"]}), 1529)
        self.assertEqual(catalog["records"][0]["source"]["values"]["Auteur(s)"], "50 cent")

    def test_no_invented_metadata_or_school_level_mapping(self):
        records = module.build_catalog()["records"]
        self.assertEqual(sum(r["catalogLevel"] is None for r in records), 4)
        for record in records:
            self.assertFalse(record["recommendationReady"])
            for field in module.UNKNOWN:
                self.assertIsNone(record[field])
                self.assertIn(field, record["missingFields"])


if __name__ == "__main__":
    unittest.main()
