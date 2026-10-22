import base64
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from collect_covers import inspect_image, lookup, work_key
from enrich_catalog import same_title
from sync_aura import DOM, author


class CoverImageTests(unittest.TestCase):
    def test_placeholder_and_html_are_not_book_covers(self):
        tiny = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
        for data in [tiny, b'<html>not an image</html>']:
            with self.assertRaises((ValueError, OSError, SyntaxError)):
                inspect_image(data)

    def test_aliases_preserve_author_and_series_identity(self):
        self.assertEqual(work_key({'title': 'Het geheim!', 'author': 'Mous, Mirjam; Vertaler'}),
                         work_key({'title': 'Geheim', 'author': 'Mirjam Mous'}))
        self.assertNotEqual(work_key({'title': 'Boy 7', 'author': 'Mirjam Mous'}),
                            work_key({'title': 'Boy 8', 'author': 'Mirjam Mous'}))

    def test_wrong_author_or_material_never_downloads_a_cover(self):
        html = '<tr id="CPH1_grid_DXDataRow0"><a id="HLTIT" href="/detail">Boy 7</a><span class="author">Andere Auteur</span><span class="value">Boek</span></tr>'
        for candidate in [html, html.replace('Andere Auteur', 'Mous, Mirjam').replace('>Boek<', '>DVD<')]:
            with patch('collect_covers.fetch', return_value=DOM(candidate).root), patch('collect_covers.download') as download:
                self.assertEqual(lookup({'title': 'Boy 7', 'author': 'Mirjam Mous'})['covers'], [])
                download.assert_not_called()


class PublishedCoverTests(unittest.TestCase):
    def test_visual_reviews_reject_wrong_language_and_cross_title_reuse(self):
        review = json.loads((ROOT / 'data/cover-review.json').read_text())
        records = json.loads((ROOT / 'data/cover-catalog.json').read_text())['records']
        for approved in review['approved']:
            selected = records[approved['bookId']]['covers']
            self.assertIn(approved['cover']['sha256'], [cover['sha256'] for cover in selected])
        for record in records.values():
            key = work_key(record)
            for rejected in review['rejected']:
                if key == rejected['workKey']:
                    self.assertNotIn(rejected['sha256'], [c['sha256'] for c in record['covers']])
            for cover in record['covers']:
                if cover['sha256'] in review['quarantinedImageHashes']:
                    allowed = [r for r in review['approved'] if r['cover']['sha256'] == cover['sha256']]
                    self.assertTrue(any(item['workKey'] == key for item in allowed))

    def test_complete_manifest_identity_and_every_selected_image(self):
        source = json.loads((ROOT / 'data/library-catalog.json').read_text())
        snapshot = json.loads((ROOT / 'data/cover-catalog.json').read_text())
        self.assertTrue(snapshot['complete'])
        self.assertEqual(snapshot['sourceSha256'], source['sourceSha256'])
        self.assertTrue({r['id'] for r in source['records']} <= snapshot['records'].keys())
        seen = set()
        for record in snapshot['records'].values():
            self.assertTrue(record['checkedAt'])
            for cover in record['covers']:
                self.assertTrue(same_title(record['title'], cover['matchedTitle']))
                self.assertEqual(author(record['author']), author(cover['matchedAuthor']))
                self.assertFalse(cover['editionVerified'])
                self.assertEqual(urlsplit(cover['sourceUrl']).scheme, 'https')
                self.assertEqual(cover['identityConfidence'], 'high')
                if cover['sha256'] in seen:
                    continue
                seen.add(cover['sha256'])
                path = ROOT / cover['url']
                self.assertTrue(path.resolve().is_relative_to((ROOT / 'assets/covers').resolve()))
                data = path.read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), cover['sha256'])
                width, height, _ = inspect_image(data)
                self.assertEqual((width, height), (cover['width'], cover['height']))


if __name__ == '__main__':
    unittest.main()
