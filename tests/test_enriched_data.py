"""Integrity of the published dataset, independent of the live providers."""
import hashlib
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PublishedDataTests(unittest.TestCase):
    def test_every_original_row_has_an_attempt_and_the_workbook_is_unchanged(self):
        source = json.loads((ROOT / 'data/library-catalog.json').read_text())
        enriched = json.loads((ROOT / 'data/enriched-catalog.json').read_text())
        digest = hashlib.sha256((ROOT / 'data/sources/jeugdboeken.xlsx').read_bytes()).hexdigest()
        self.assertEqual(digest, source['sourceSha256'])
        self.assertEqual(digest, enriched['sourceSha256'])
        self.assertEqual({r['id'] for r in source['records']}, {r['id'] for r in enriched['records']})
        self.assertEqual(len(enriched['records']), source['recordCount'])
        self.assertTrue(all(r['attempts'] for r in enriched['records']))

    def test_source_facts_and_inferences_have_distinct_provenance(self):
        enriched = json.loads((ROOT / 'data/enriched-catalog.json').read_text())
        for record in enriched['records']:
            urls = {s['url'] for s in record['sources']}
            for fact in record['facts'].values():
                self.assertIn(fact['sourceUrl'], urls)
                self.assertTrue(fact['checkedAt'])
                self.assertTrue(fact['confidence'])
                self.assertEqual(urlsplit(fact['sourceUrl']).scheme, 'https')
            if record['assessments']:
                for assessment in record['assessments']['interests'] + record['assessments']['storyTags']:
                    self.assertEqual(assessment['kind'], 'inference')
                    self.assertEqual(assessment['method'], enriched['ruleVersion'])
                    self.assertIn(assessment['sourceUrl'], urls)
                    self.assertTrue(assessment['evidence'])
                    self.assertTrue(assessment['checkedAt'])
            self.assertFalse(record['editionVerified'])
            for field in ['isbn', 'pages', 'coverUrl', 'available', 'auraId', 'schoolLevels']:
                self.assertNotIn(field, record['facts'])
            if record['recommendationReady']:
                self.assertTrue(record['facts'].get('summary'))
                self.assertTrue(record['assessments']['interests'] or record['assessments']['storyTags'])


if __name__ == '__main__':
    unittest.main()
