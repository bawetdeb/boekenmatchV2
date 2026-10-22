import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from enrich_catalog import assess, publish, same_title, lookup_aura, collect
from sync_aura import DOM


class EnrichmentTests(unittest.TestCase):
    def test_presence_is_an_inference_not_an_intensity_or_school_level(self):
        result = assess('Een jongen speelt voetbal en wordt op school gepest.', '', 'https://example.org/book')
        self.assertIn('voetbal', [r['value'] for r in result['interests']])
        self.assertIsNone(result['themeIntensities'])
        self.assertIsNone(result['readingDifficulty'])
        self.assertIsNone(result['schoolLevels'])
        self.assertTrue(all(r['kind'] == 'inference' and r['evidence'] for r in result['interests']))

    def test_negation_author_promotion_and_substrings_are_not_plot_evidence(self):
        result = assess('Dit is geen horror. Een jeugdroman van rapper 50 Cent. Honderden mensen komen bijeen.', '', 'https://example.org')
        self.assertNotIn('horror', [r['value'] for r in result['storyTags']])
        self.assertNotIn('muziek', [r['value'] for r in result['interests']])
        self.assertNotIn('honden', [r['value'] for r in result['interests']])

    def test_edition_specific_fields_and_availability_remain_unknown(self):
        evidence = {'provider': 'Test', 'url': 'https://example.org', 'checkedAt': '2026-10-22T00:00:00Z',
                    'description': 'Een meisje speelt voetbal op school. ' * 8, 'subjects': 'Sport',
                    'fields': {'ISBN': '9780000000000', 'Paginas': '200', 'Taal': 'Nederlands'},
                    'editionVerified': False, 'conflicts': []}
        result = publish({'id': 'book'}, evidence, [])
        self.assertTrue(result['recommendationReady'])
        self.assertLessEqual(len(result['facts']['summary']['value']), 220)
        for field in ['isbn', 'pages', 'coverUrl', 'available', 'auraId', 'schoolLevels']:
            self.assertNotIn(field, result['facts'])
            self.assertIn(field, result['missingFields'])
        evidence['conflicts'] = [{'field': 'language', 'values': ['Engels', 'Nederlands']}]
        self.assertNotIn('language', publish({'id': 'book'}, evidence, [])['facts'])

    def test_title_matching_keeps_subtitles_and_numbers_distinct(self):
        self.assertTrue(same_title('Het geheim!', 'geheim'))
        self.assertFalse(same_title('Boy 7', 'Boy 8'))
        self.assertFalse(same_title('Boy 7: vervolg', 'Boy 7'))

    def test_broad_school_shelf_is_not_specific_sciencefiction(self):
        result = assess('Feyre keert terug naar het hof als een High Fae.', 'Science fiction', 'https://example.org')
        self.assertNotIn('sciencefiction', [r['value'] for r in result['interests']])
        self.assertIn('fantasy', [r['value'] for r in result['interests']])
        self.assertTrue(result['notes'])
        result = assess('Katniss is gered door rebellen en keert terug naar District 13.', 'Fantasy', 'https://example.org')
        self.assertNotIn('fantasy', [r['value'] for r in result['interests']])
        result = assess('Vervolg op: Neem nooit een beste vriend. Joshua heeft relatieproblemen.', '', 'https://example.org')
        self.assertNotIn('vriendschap', [r['value'] for r in result['interests']])
        result = assess('Na zijn laatste schooldag gaat Percy op zoek naar de monsters.', 'Avonturenroman', 'https://example.org')
        self.assertNotIn('school', [r['value'] for r in result['interests']])

    def test_wrong_author_or_non_book_material_never_enriched(self):
        html = '<tr id="CPH1_grid_DXDataRow0"><a id="HLTIT" href="/detail">Boy 7</a><span class="author">Anders, Auteur</span><span class="value">Boek</span></tr>'
        with patch('enrich_catalog.aura_fetch', return_value=DOM(html).root):
            self.assertIsNone(lookup_aura({'title': 'Boy 7', 'author': 'Mirjam Mous'}))
        html = html.replace('Anders, Auteur', 'Mous, Mirjam').replace('>Boek<', '>DVD<')
        with patch('enrich_catalog.aura_fetch', return_value=DOM(html).root):
            self.assertIsNone(lookup_aura({'title': 'Boy 7', 'author': 'Mirjam Mous'}))

    def test_refresh_failure_preserves_old_source_and_its_actual_check_date(self):
        evidence = {'provider': 'Test', 'url': 'https://example.org', 'checkedAt': '2026-10-21T00:00:00Z',
                    'description': 'Een jongen speelt voetbal op school. ' * 4,
                    'subjects': 'Sport', 'fields': {}, 'conflicts': [], 'editionVerified': False}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.json'
            path.write_text(json.dumps({'evidence': evidence, 'attempts': [], 'fallbackAttempted': False}))
            with patch('enrich_catalog.CACHE', Path(directory)), patch('enrich_catalog.REFRESH', True), patch('enrich_catalog.lookup_aura', side_effect=TimeoutError('transient timeout')):
                result = collect({'id': 'book'})
            self.assertEqual(result['sources'][0]['checkedAt'], '2026-10-21T00:00:00Z')
            self.assertEqual(result['attempts'][-1]['outcome'], 'retained-previous-evidence-after-refresh-failure')


if __name__ == '__main__':
    unittest.main()
