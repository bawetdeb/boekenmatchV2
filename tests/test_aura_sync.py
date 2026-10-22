import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sync_aura import DOM, lookup, normal, author, same_title
SEARCH='''<tr id="CPH1_grid_DXDataRow0"><td><a id="CPH1_grid_row0_HLTIT_0" href="ajdetailsx.aspx?DOCSTART=06326">Boy 7</a><td class="author">Mous, Mirjam</td><td class="value">Boek</td></td></tr>'''
DETAIL='''<h2 class="titel">Boy 7</h2><span class="dtaut">Mous, Mirjam</span><img id="CPH1_imgCover" src="koppelingen/afbeeldingen/9789047505945.jpg.ashx"><table><tr><td class="ajdgeg2">Taal</td><td class="ajdgeg3">Nederlands</td></tr><tr><td class="ta1">Hemdijk 2</td><td class="ta1">Mediatheek H2</td><td class="ta3">Aanwezig</td></tr></table>'''
BOOK={'id':'b001','title':'Boy 7','author':'Mirjam Mous'}
class ImportTests(unittest.TestCase):
 def run_lookup(self,search=SEARCH,detail=DETAIL,landing=DETAIL):
  with patch('sync_aura.fetch',side_effect=[DOM(search).root,DOM(detail).root]),patch('sync_aura.urllib.request.urlopen',return_value=io.BytesIO(landing.encode())):
   return lookup(BOOK)
 def test_exact_identity_and_copy(self):
  b=self.run_lookup();self.assertEqual(b['isbn'],'9789047505945');self.assertEqual(b['auraId'],'06326');self.assertTrue(b['available']);self.assertEqual(b['location'],'Hemdijk 2 · Mediatheek H2')
 def test_wrong_author_or_material_not_accepted(self):
  self.assertIsNone(self.run_lookup(search=SEARCH.replace('Mous, Mirjam','Anders, Auteur')))
  self.assertIsNone(self.run_lookup(search=SEARCH.replace('>Boek<','>DVD<')))
 def test_unknown_status_not_available(self):
  self.assertFalse(self.run_lookup(detail=DETAIL.replace('Aanwezig','Onbekend'))['available'])
 def test_wrong_deep_link_falls_back(self):
  self.assertEqual(self.run_lookup(landing=DETAIL.replace('Boy 7','Ander boek'))['auraUrl'],'')
 def test_missing_language_retained_as_unknown(self):
  self.assertEqual(self.run_lookup(detail=DETAIL.replace('>Nederlands<','><'))['language'],'')
  self.assertIsNone(self.run_lookup(detail=DETAIL.replace('Nederlands','Engels')))
 def test_translator_credit_and_film_edition(self):
  self.assertIsNotNone(self.run_lookup(search=SEARCH.replace('Mous, Mirjam','Mous, Mirjam ; Iemand [ vert. ]'),detail=DETAIL.replace('Boy 7','Boy 7 ; filmeditie')))
  self.assertFalse(same_title('Boy 7: een ander avontuur','Boy 7'))
 def test_normalization(self):
  self.assertEqual(author('Mous, Mirjam'),author('Mirjam Mous'));self.assertEqual(normal('Spijt!'),normal('Spijt'))
if __name__=='__main__':unittest.main()
