"""Offline gate contracts. Fixtures are never presented as mapped simulation."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tkinter
import dma16_gate as g
from dma16_synth import SYSMEM
from test_dma16_synth import inventory, total


def probe_fixture():
    parent = 'observed_chip/observed_mems'
    cells = dict(accel=parent+'/u_arch03_accel', core=parent+'/u_arch03_accel/core',
                 shared=parent+'/u_arch03_shared', arb=parent+'/u_arch03_arb', router=parent+'/u_arch03_router')
    lines = []; pins = {}
    for role, spec in g.interfaces().items():
        lines.append('cell\t%s\t%s\t%s' % (role, cells[role], g.REFERENCES[role]))
        pins[role] = [cells[role]+'/'+name for name in g.port_bits(spec)]
        lines += ['pin\t%s\t%s/%s\t%s' % (role, cells[role], name, direction)
                  for name, direction in g.port_bits(spec).items()]
    for name in ('test_mode', 'pllbypass', 'plloutdivby1'):
        lines.append('guard\t%s\tobserved_chip/u_e203_subsys_hclkgen/%s\tin' % (name, name))
    lines.append('guard\tbootrom_selected\tobserved_aon/u_sirv_aon_wrapper/bootrom_deglitch/io_q\tout')
    dma = [name for name in pins['accel'] if name.startswith(cells['accel']+'/dma_')]
    frozen = 'dma_interface\t%d\t%s\ncore_interface\t%d\t%s\n' % (len(dma), ' '.join(dma), len(pins['core']), ' '.join(pins['core']))
    return '\n'.join(lines)+'\n', frozen


def top():
    declarations = ['input '+name+';' for name in g.baseline_inputs()]
    for name, (direction, width) in SYSMEM.items():
        declarations.append('%s %ssysmem_icb_%s;' % ('input' if direction == 'in' else 'output',
                            '' if width == 1 else '[%d:0] ' % (width-1), name))
    return 'module e203_soc_top();\n'+'\n'.join(declarations)+'\nendmodule\n'


class Dma16GateTests(unittest.TestCase):
    def test_actual_observed_paths_bind_all_five_modules_without_default_root(self):
        text, frozen = probe_fixture(); receipt = g.parse_probe(text, frozen)
        self.assertTrue(receipt['frozen_synthesis_interfaces_crosschecked'])
        self.assertFalse(receipt['alias_binding_used'])
        self.assertTrue(all('observed_chip' in path for path in receipt['bindings'].values()))
        monitor = g.generate((g.A3/'tb/arch03_dma16_monitor.svh').read_text(), receipt['bindings'])
        self.assertIn('u_e203_soc_top.observed_chip.observed_mems.u_arch03_accel.core.out_valid', monitor)
        for bad in ('fifo_count_q', 'core_done_q', 'a3_arb_pending', 'a3_router_pending', '`A3MEM', '`A3DMA'):
            self.assertNotIn(bad, monitor)
        self.assertIn('a3_gate_proof_complete', monitor)

    def test_absent_duplicate_wrong_width_direction_and_frozen_disagreement_fail(self):
        text, frozen = probe_fixture()
        first_pin = next(line for line in text.splitlines() if line.startswith('pin\taccel\t') and '/dma_cmd_addr[17]\t' in line)
        mutations = [text.replace(first_pin+'\n', ''), text+first_pin+'\n',
                     text.replace(first_pin, first_pin.rsplit('\t', 1)[0]+'\tin'),
                     text.replace('/u_arch03_accel/core\t', '/wrong_core\t'),
                     '\n'.join(line for line in text.splitlines() if not line.startswith('cell\trouter\t'))]
        for bad in mutations:
            with self.assertRaises(ValueError):
                g.parse_probe(bad, frozen)
        for bad in ('', frozen.replace('dma_cmd_addr[17]', 'dma_cmd_addr[99]'), frozen+frozen):
            with self.assertRaises(ValueError):
                g.parse_probe(text, bad)

    def test_netlist_has_full_sysmem_and_only_reviewed_top_inputs(self):
        receipt = g.parse_probe(*probe_fixture()); tb = g.testbench(top(), receipt)
        for name in SYSMEM:
            self.assertIn('.sysmem_icb_%s(a3_source_%s)' % (name, name), tb)
        self.assertIn('always #3.333333 clk', tb)
        self.assertIn('.bootrom_selected(u_e203_soc_top.observed_aon.', tb)
        self.assertNotIn('readmemh', tb)
        self.assertNotIn('EXPECTED', tb)
        self.assertLess(tb.index('arch03_dma16_gate_monitor.svh'),tb.index('arch03_dma16_metrics.svh'))
        with self.assertRaises(ValueError):
            g.testbench(top().replace('endmodule', 'input unknown_control;\nendmodule'), receipt)
        with self.assertRaises(ValueError):
            g.testbench(top().replace('[31:0] sysmem_icb_rsp_rdata', '[30:0] sysmem_icb_rsp_rdata'), receipt)

    def test_probe_tcl_never_recompiles_or_overwrites_mapped_design(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); (run/'libs').mkdir(); databases = []
            for name in ('std', 'small', 'large'):
                path = run/'libs'/(name+'.db'); path.write_text(name); databases.append(path)
            (run/'source_inputs.json').write_text(json.dumps({str(p): g.sha(p) for p in databases}))
            script = g.probe_script(run)
        self.assertEqual(tkinter.Tcl().call('info', 'complete', script), 1)
        for forbidden in ('compile ', 'write -format', 'write_sdc', 'set_dont_touch', 'set_false_path'):
            self.assertNotIn(forbidden, script)
        for expected in ('read_ddc', 'get_pins -of_objects', 'get_attribute $pin direction', 'sh_continue_on_error false', 'exit 1'):
            self.assertIn(expected, script)

    def test_probe_missing_hierarchy_stops_before_port_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory); (run/'libs').mkdir(); paths = []
            for name in ('std', 'small', 'large'):
                path = run/'libs'/(name+'.db'); path.write_text(name); paths.append(path)
            (run/'source_inputs.json').write_text(json.dumps({str(p): g.sha(p) for p in paths}))
            script = g.probe_script(run)
        t = tkinter.Tcl(); t.eval(r'''
set probed 0
proc set_app_var {args} {}
proc read_ddc {args} {}
proc current_design {args} {}
proc link {} {return 1}
proc open {args} {return sink}
proc get_cells {args} {return {}}
proc sizeof_collection {args} {return 0}
proc get_pins {args} {set ::probed 1}
proc puts {args} {}
proc exit {code} {error "TASK_EXIT $code"}
proc quit {} {error UNEXPECTED_QUIT}
''')
        with self.assertRaisesRegex(tkinter.TclError, 'TASK_EXIT 1'):
            t.eval(script)
        self.assertEqual(int(t.getvar('probed')), 0)

    def test_source_provenance_rejects_old_stage_and_changed_platform(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); bundle = root/'bundle'; run = bundle/'runs/synth/dma16_synth'; run.mkdir(parents=True)
            preparation = ['workspaces/arch03/scripts/'+n for n in ('install_platform.py', 'install_dma16.py',
                'technology_binding.py', 'memory_technology.py', 'timing_contract.py', 'dma16_synth.py')]+[
                'workspaces/arch03/'+n for n in ('technology_bindings.json', 'memory_technology.json')]+['workspaces/arch03/rtl/core.sv']
            for name in preparation:
                path = bundle/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('frozen fixture')
            (bundle/'manifest.json').write_text(json.dumps({'files': {n: g.sha(bundle/n) for n in preparation}}))
            rows = inventory(); (run/'leaf_area.tsv').write_text('\n'.join(rows)); (run/'mapped.v').write_text(top())
            (run/'mapped_probe_inventory.tsv').write_text(probe_fixture()[1])
            for name in ('mapped.ddc', 'mapped.sdc', 'area_inventory.json', 'mapped_sysmem_ports.tsv', 'area_basis.json'):
                (run/name).write_text('immutable test artifact')
            (run/'libs').mkdir(); dbs = []
            for name in ('std', 'small', 'large'):
                path = run/'libs'/(name+'.db'); path.write_text(name); dbs.append(path)
            source_inputs = {str(p): g.sha(p) for p in dbs}
            source_inputs[str(bundle/preparation[-1])] = g.sha(bundle/preparation[-1])
            (run/'source_inputs.json').write_text(json.dumps(source_inputs))
            (run/'synthesis_inputs.json').write_text(json.dumps({str(run/'mapped.ddc'): g.sha(run/'mapped.ddc')}))
            summary = dict(scope='dma16_whole_soc_task_mode_preliminary_synthesis', synthesis_completed=True,
                           setup_hold_nonnegative=False, metrics=dict(period_ns='6.666666', RAMSP128X16=32, RAMSP4096X16=130,
                           area=total(rows)), artifacts={p.name: g.sha(p) for p in run.iterdir() if p.is_file()})
            (run/'summary.json').write_text(json.dumps(summary)); digest = g.sha(run/'summary.json')
            state = {'stages': {'dma16_synth': dict(status='passed', summary_sha256=digest)}}
            (run.parent/'state.json').write_text(json.dumps(state))
            with patch.object(g, 'ROOT', bundle):
                report, area = g.verify_synthesis(run, digest, {'server_root': str(root)})
                self.assertFalse(report['setup_hold_nonnegative'])
                self.assertEqual(area['macro_count'], 162)
                # Independent later gate bundle adds software that never went
                # into synthesis; only the selected firmware is checked later.
                current = root/'later_gate_bundle'; current.mkdir()
                for relative in preparation:
                    path = current/relative; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((bundle/relative).read_bytes())
                additions = ('workspaces/arch03/sw/mmio8_test.c', 'workspaces/arch03/sw/sequence_test.c',
                             'workspaces/arch03/rtl/uncompiled_debug_fixture.sv')
                for relative in additions:
                    path = current/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('unrelated new fixture')
                manifest = {'files': {n: g.sha(current/n) for n in preparation+list(additions)}}
                (current/'manifest.json').write_text(json.dumps(manifest))
                with patch.object(g, 'ROOT', current):
                    g.verify_synthesis(run, digest, {'server_root': str(root)})
                    (current/preparation[-1]).write_text('changed compiled core')
                    manifest['files'][preparation[-1]] = g.sha(current/preparation[-1])
                    (current/'manifest.json').write_text(json.dumps(manifest))
                    with self.assertRaisesRegex(ValueError, 'hardware preparation'):
                        g.verify_synthesis(run, digest, {'server_root': str(root)})
                state['stages']['asic_synth'] = state['stages'].pop('dma16_synth')
                (run.parent/'state.json').write_text(json.dumps(state))
                with self.assertRaisesRegex(ValueError, 'not complete'):
                    g.verify_synthesis(run, digest, {'server_root': str(root)})
                state['stages']['dma16_synth'] = state['stages'].pop('asic_synth')
                (run.parent/'state.json').write_text(json.dumps(state))
                (bundle/preparation[1]).write_text('changed platform loader')
                with self.assertRaisesRegex(ValueError, 'hardware preparation'):
                    g.verify_synthesis(run, digest, {'server_root': str(root)})

    def test_power_database_trace_uses_actual_dma16_run_library_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)/'runs/synth/dma16_synth'; (run/'libs').mkdir(parents=True)
            records = {}
            for name in ('scc40nll_vhsc40_rvt_ss_v0p99_125c_basic.db',
                         'RAMSP128X16_ss_0p99v_0p99v_125c.db', 'RAMSP4096X16_ss_0p99v_0p99v_125c.db'):
                path = run/'libs'/name; path.write_bytes(name.encode('ascii'))
                records[str(path.resolve())] = g.sha(path)
            # dma16_synth stores the standard DB plus both locally LC-compiled
            # SRAM DB paths in source_inputs; .lib/.sv inputs are ignored here.
            records[str(run/'libs/standard.lib')] = 'a'*64
            records[str(run/'platform/rtl/e203_soc_top.v')] = 'b'*64
            receipt = run/'source_inputs.json'; receipt.write_text(json.dumps(records))
            self.assertEqual({p.name for p in g.power_databases(run)}, {Path(k).name for k in records if k.endswith('.db')})
            database = run/'libs/RAMSP128X16_ss_0p99v_0p99v_125c.db'
            original = database.read_bytes(); database.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'database changed'):
                g.power_databases(run)
            database.write_bytes(original)
            records[str(Path(directory)/'conflict'/database.name)] = 'c'*64; receipt.write_text(json.dumps(records))
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                g.power_databases(run)

    def test_generated_production_sram_header_must_match_synthesis_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); synth = root/'synth'; gate = root/'gate'; synth.mkdir(); gate.mkdir()
            source = synth/'arch02_sram_config.vh'; source.write_text('fixed ASIC SRAM configuration')
            current = gate/source.name; current.write_bytes(source.read_bytes())
            (synth/'source_inputs.json').write_text(json.dumps({str(source): g.sha(source)}))
            g.verify_gate_memory_config(synth, gate)
            current.write_text('changed latency or macro mode')
            with self.assertRaisesRegex(ValueError, 'configuration differs'):
                g.verify_gate_memory_config(synth, gate)

    def test_gate_sram_loader_only_initializes_itcm_actual_macros(self):
        rows = []
        for bank in range(8):
            for half in range(4):
                rows.append(dict(kind='sram', owner='itcm', reference='RAMSP4096X16',
                     instance='observed/u_e203_itcm_gnrl_ram/banks[%d].halves[%d].memory/memory' % (bank, half)))
        loader = g.mapped_loader({'rows': rows})
        self.assertIn('u_e203_soc_top.observed.u_e203_itcm_gnrl_ram.', loader)
        self.assertNotIn('u_arch03_shared', loader)
        self.assertNotIn('u_arch03_accel', loader)
        with self.assertRaises(ValueError):
            g.mapped_loader({'rows': rows[:-1]})

    def test_python36_syntax(self):
        ast.parse(Path(g.__file__).read_text(), feature_version=(3, 6))


if __name__ == '__main__':
    unittest.main()
