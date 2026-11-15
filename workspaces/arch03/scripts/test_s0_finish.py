import unittest
from unittest.mock import patch
import s0_finish as finish


class FinishOrderTests(unittest.TestCase):
    def test_failure_stops_successors_and_does_not_schedule_synthesis(self):
        seen=[]
        def stage(name,*args):
            seen.append(name)
            if name=='saif':raise RuntimeError('Actual activity failed')
            return {'run':name,'sha256':'a'*64}
        with patch.object(finish,'run_stage',side_effect=stage):
            with self.assertRaisesRegex(RuntimeError,'activity failed'):
                finish.sequence({},None,{},None,{})
        self.assertEqual(seen,['structure','gate','saif'])

    def test_twelve_power_stages_follow_the_same_new_activity(self):
        seen=[]
        def stage(name,cfg,queue,state,ledger,request,refs):
            seen.append(name)
            if name=='saif':self.assertEqual(refs['gate']['run'],'gate')
            if name.startswith('power_'):self.assertEqual(refs['saif']['run'],'saif')
            return {'run':name,'sha256':'a'*64}
        with patch.object(finish,'run_stage',side_effect=stage):
            result=finish.sequence({},None,{},None,{})
        self.assertEqual(len(result),17)
        self.assertEqual(seen[-12:],['power_layer_%02d'%i for i in range(1,13)])
        self.assertNotIn('synth',seen)
        self.assertNotIn('batch100',seen)


if __name__=='__main__':unittest.main()
