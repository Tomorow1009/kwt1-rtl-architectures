"""Scope and isolation guards for the approved G32 full100 addendum."""
import copy
import unittest
from unittest.mock import patch

import g32_batch
import g32_full100_batch as batch
import g32_full100_precision_join as precision
import g32_full100_float as floating
import g32_full100_queue as queue


class Full100Scope(unittest.TestCase):
    def setUp(self):
        self.tasks = [dict(sample=s, layer=l, shift=10)
                      for s in range(1, 101) for l in range(1, 13)]

    def test_full_selection_and_unchanged_first20(self):
        self.assertEqual(len(batch.select_full100(self.tasks)), 1200)
        self.assertEqual(len(g32_batch.select_first20(self.tasks)), 240)
        self.assertEqual(batch.select_full100(self.tasks)[-1], dict(sample=100, layer=12, shift=10))

    def test_late_or_missing_cases_rejected(self):
        wrong = copy.deepcopy(self.tasks); wrong[-1]['layer'] = 11
        reordered = self.tasks[:-2]+self.tasks[-2:][::-1]
        for tasks in (self.tasks[:240], self.tasks[:-1], wrong, reordered, self.tasks+self.tasks[-1:]):
            with self.assertRaises(ValueError): batch.select_full100(tasks)

    def test_late_shift_rejected(self):
        self.tasks[-1]['shift'] = 16
        with self.assertRaises(ValueError): batch.select_full100(self.tasks)

    def test_old_scope_cannot_enter_new_precision(self):
        with self.assertRaises(ValueError):
            precision.audit_batch('does-not-exist', dict(schema=g32_batch.SCHEMA,
                asic_cpu_verified=True, tasks=240, checked_outputs=6082560,
                checked_totals=6082560, failed=0, shift=10, numeric_format_id=0x000e0c20))

    def test_float_count_rejected_before_io(self):
        with self.assertRaises(ValueError):
            floating._audit('does-not-exist.zip', '0'*64, 'no-data', 'no-output', sample_count=20)

    def test_old_queue_requires_new_explicit_authorization(self):
        for authorization in (False, None):
            with self.assertRaises(ValueError):
                queue.execute(dict(schema=queue.SCHEMA, full100_authorized=authorization,
                                   samples=100, tasks=1200), None)


if __name__ == '__main__': unittest.main()
