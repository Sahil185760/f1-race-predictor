import copy,json,unittest
from pathlib import Path
import engine
class Tests(unittest.TestCase):
 def setUp(self):
  self.data=json.loads(Path(__file__).with_name('example.json').read_text());self.data['simulations']=500
 def test_probabilities_and_seed(self):
  out=engine.run(self.data)
  self.assertAlmostEqual(sum(r['win_probability'] for r in out['rows']),1)
  self.assertAlmostEqual(sum(r['podium_probability'] for r in out['rows']),3)
  self.assertEqual(out,engine.run(self.data))
 def test_future_race_rejected(self):
  self.data['races'][-1]['date']='2026-05-25'
  with self.assertRaises(ValueError):engine.run(self.data)
 def test_target_race_rejected(self):
  self.data['races'][-1]['round']=5
  with self.assertRaises(ValueError):engine.run(self.data)
 def test_target_outcome_rejected(self):
  self.data['entrants'][0]['finish']=1
  with self.assertRaises(ValueError):engine.run(self.data)
 def test_no_current_or_future_result_in_features(self):
  before=engine.training_rows(self.data['races']); changed=copy.deepcopy(self.data['races'])
  for race in changed[10:]:
   for r in race['results']:r['finish']=31-r['finish']
  after=engine.training_rows(changed)
  for a,b in zip(before,after):
   if a['date']<=changed[10]['date']:self.assertEqual(a['x'],b['x'])
 def test_chronological_holdout(self):
  out=engine.run(self.data)
  self.assertEqual(out['details']['held_out_races'],['Las Vegas Grand Prix','Qatar Grand Prix','Abu Dhabi Grand Prix','Australian Grand Prix','Chinese Grand Prix','Japanese Grand Prix','Miami Grand Prix'])
  self.assertEqual(out['details']['latest_included_date'],'2026-05-03')
 def test_duplicate_driver_rejected(self):
  self.data['entrants'][1]['driver']=self.data['entrants'][0]['driver']
  with self.assertRaises(ValueError):engine.run(self.data)
 def test_snapshot_cutoff(self):
  self.assertTrue(all(r['date']<'2026-05-18' and (r['season'],r['round'])<(2026,5) for r in self.data['races']))
 def test_prior_season_late_round_accepted(self):
  self.assertTrue(any(r['round']>5 and r['season']==2025 for r in self.data['races']))
  engine.validate(self.data)
 def test_season_date_mismatch_rejected(self):
  self.data['races'][-1]['season']=2025
  with self.assertRaises(ValueError):engine.run(self.data)
if __name__=='__main__':unittest.main()
