import ast
import unittest
from pathlib import Path
import dma16_bus_metrics as m


def fixture():
    lines = ['DMA16_BUS_HEADER schema=dma16_bus_metrics_v1 outcome=cancelled started=1 cancelled=1 first_offer_cycle=10 last_ack_cycle=13 published_cycle=20 total_cycles=3 issued=1 accepted=1 successes=1 errors=0 cancelled_acks=1 committed_bytes=4 input_words=11744 output_words=12672']
    for phase in m.PHASES:
        n = int(phase == 'source_read')
        lines.append('DMA16_BUS_PHASE phase=%s issued=%d accepted=%d successes=%d errors=0 cancelled_acks=%d committed_bytes=%d' % (phase, n, n, n, n, n*4))
        for metric in m.METRICS:
            count = n if metric != 'accept_gap' else 0
            value = (1 if metric == 'offer_wait' else 2) if count else 0
            hist = [0]*9
            if count: hist[value] = 1
            lines.append('DMA16_BUS_STAT phase=%s metric=%s count=%d min=%d max=%d sum=%d hist=%s' %
                         (phase, metric, count, value, value, value, ','.join(map(str, hist))))
        lines.append('DMA16_BUS_SWITCH transition=%s count=0 min=0 max=0 sum=0 hist=0,0,0,0,0,0,0,0,0' % m.TRANSITIONS[m.PHASES.index(phase)])
    lines += ['DMA16_BUS_CONTENTION competing_cycles=1 cpu_grants=0 dma_grants=1 competing_cpu_grants=0 competing_dma_grants=1 competing_blocked=0 arb_grants=1 arb_acks=1 ready_wait_cycles=0 response_backpressure_cycles=0 cpu_owned_wait_cycles=0 initial_global_pending=0 initial_global_cpu=0',
              'DMA16_BUS_END schema=dma16_bus_metrics_v1']
    return '\n'.join(lines)


class BusMetricsTests(unittest.TestCase):
    def test_partial_cancel_is_explicit_and_cannot_be_performance_pass(self):
        result = m.parse_metrics(fixture(), require_complete=False)
        self.assertEqual(result['header']['total_cycles'], 3)
        self.assertEqual(result['header']['published_cycle'], 20)
        self.assertFalse(result['full_task_counts_verified'])
        self.assertEqual(result['header']['committed_bytes'], 4)
        with self.assertRaisesRegex(ValueError, 'not performance'):
            m.parse_metrics(fixture())

    def test_duplicate_missing_inconsistent_counts_and_false_complete_rejected(self):
        text = fixture()
        for bad in (text+'\n'+text, '\n'.join(text.splitlines()[:-1]),
                    text.replace('committed_bytes=4', 'committed_bytes=8'),
                    text.replace('outcome=cancelled', 'outcome=complete'),
                    text.replace('competing_cycles=1', 'competing_cycles=2'),
                    text.replace('min=1 max=1 sum=1', 'min=1 max=1 sum=2'),
                    text.replace('metric=offer_wait', 'metric=unknown'),
                    text+'\nDMA16_BUS_METRICS_PROTOCOL_ERROR code=9'):
            with self.assertRaises(ValueError): m.parse_metrics(bad, require_complete=False)

    def test_histogram_overflow_and_extrema_checks(self):
        row = dict(count='2', min='64', max='95', sum='159', hist='0,0,0,0,0,0,0,0,2')
        self.assertEqual(m.stats(row, ())['sum'], 159)
        for key, value in [('sum', '127'), ('min', '63'), ('count', '3'), ('hist', '0,0,0,0,0,0,0,2,0')]:
            bad = dict(row); bad[key] = value
            with self.assertRaises(ValueError): m.stats(bad, ())

    def test_observed_boundary_binding_is_passive(self):
        code = m.binding_include(dict(accel='u_e203_soc_top.real_mems.u_arch03_accel', arb='u_e203_soc_top.real_mems.u_arch03_arb'))
        self.assertIn('.dma_cmd_valid(u_e203_soc_top.real_mems.u_arch03_accel.dma_cmd_valid)', code)
        self.assertIn('.cpu_cmd_valid(u_e203_soc_top.real_mems.u_arch03_arb.cpu_cmd_valid)', code)
        self.assertIn('.task_end(a3_window_finished)', code)
        self.assertNotIn('assign ', code)
        for bad in ({}, dict(accel='top;force', arb='top.arb')):
            with self.assertRaises(ValueError): m.binding_include(bad)

    def test_server_parser_python36(self):
        ast.parse(Path(m.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__': unittest.main()
