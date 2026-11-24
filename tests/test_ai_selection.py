import unittest
from unittest.mock import patch
from ranking import local_rank
class AiSelection(unittest.TestCase):
 def test_rank_controls_selected_moments_and_limit(self):
  words=[[i,i+.8,'segmen '+str(i)] for i in range(18)];clips=[dict(start=i,end=i+.9,title=str(i),score=99-i) for i in range(18)]
  with patch('ranking.relevance',return_value=[i/20 for i in range(18)]):
   result,method=local_rank(clips,words)
  self.assertEqual([x['start'] for x in result],list(range(17,7,-1)));self.assertIn('E5',method)
