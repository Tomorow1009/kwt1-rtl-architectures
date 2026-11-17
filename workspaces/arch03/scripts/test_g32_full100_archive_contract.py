"""Prevent partial/old/software-only results from authorizing full100 archiving."""
import copy
import unittest
from g32_full100_archive_contract import validate_scope


class CompletionGate(unittest.TestCase):
    def setUp(self):
        self.batch = dict(schema='arch03-g32-full100-batch-v6',status='passed',samples=100,
            tasks=1200,checked_outputs=30412800,checked_totals=30412800,
            checked_saturation_flags=30412800,failed=0,compile_count=1,asic_cpu_verified=True,
            cpu_executed=True,global_FPGA_defined=False,row_lanes=2,transaction_metadata_depth=2,
            shift=10,layout_id=0x00100006,numeric_format_id=0x000e0c20)
        self.precision = dict(schema='arch03-g32-full100-precision-join-v1',
            status='own_G32_ASIC1200_and_same_data_fresh_FLOAT_precision_verified',
            samples=100,tasks=1200,outputs=30412800,total_outputs=30412800,
            integer_bit_exact=True,fresh_float_reference_verified=True,
            float_reference_recomputed_in_precision_run=True,reference_error_metrics_reused_from_B0=False,
            official_precision_verified=False,internal_three_percent_layer_threshold_passed=True,
            maximum_layer_nrmse_percent=.20,maximum_task_nrmse_percent=.21,
            layer_aggregate=[dict(tasks=100,within_limit=True) for _ in range(12)])

    def test_complete_scope(self): validate_scope(self.batch,self.precision)

    def test_partial_counts_or_non_asic_rejected(self):
        for key,value in [('tasks',240),('checked_totals',6082560),('failed',1),
                          ('compile_count',2),('global_FPGA_defined',True),('cpu_executed',False)]:
            b=copy.deepcopy(self.batch);b[key]=value
            with self.assertRaises(ValueError): validate_scope(b,self.precision)

    def test_old_or_non_fresh_float_rejected(self):
        for key,value in [('samples',20),('reference_error_metrics_reused_from_B0',True),
                          ('fresh_float_reference_verified',False),('official_precision_verified',True)]:
            p=copy.deepcopy(self.precision);p[key]=value
            with self.assertRaises(ValueError): validate_scope(self.batch,p)

    def test_invalid_precision_or_layer_coverage_rejected(self):
        for value in (float('nan'),float('inf'),-1,3.00001):
            p=copy.deepcopy(self.precision);p['maximum_layer_nrmse_percent']=value
            with self.assertRaises(ValueError): validate_scope(self.batch,p)
        p=copy.deepcopy(self.precision);p['layer_aggregate'][-1]['tasks']=20
        with self.assertRaises(ValueError): validate_scope(self.batch,p)


if __name__=='__main__':unittest.main()
