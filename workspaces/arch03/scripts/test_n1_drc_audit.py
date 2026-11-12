"""Offline report/query tests, not actual DC or N1 timing acceptance."""
import json
from pathlib import Path
import tempfile
import tkinter
import unittest

import n1_drc_audit as drc
from test_dma16_power import fake_databases


REPORT = '''****************************************
Report : constraint -all_violators
Design : e203_soc_top
****************************************
max_transition
Pin Required Actual Slack
---------------------------------
core/control[2]/Z 0.10 0.12 -0.02 (VIOLATED)
core/control[3]/Z
 0.10 0.11 -0.01 (VIOLATED)

max_capacitance
core/control[2]/Z 0.04 0.06 -0.02 (VIOLATED)

multiple_port_nets
core/n982 1 2 -1 (VIOLATED)

max_delay/setup ('HFCLK' group)
core/result_reg[4]/D 6.666666 6.70 -0.033334 (VIOLATED)
'''


class N1DrcTests(unittest.TestCase):
    def test_inventory_keeps_pin_duplicates_separate_from_unique_targets(self):
        parsed = drc.constraints_inventory(REPORT)
        self.assertEqual(parsed['violation_record_count'], 5)
        self.assertEqual(parsed['unique_query_target_count'], 3)
        self.assertEqual(parsed['by_section']['max_transition'], 2)
        self.assertEqual(parsed['query_targets'], ['core/control[2]/Z','core/control[3]/Z','core/n982'])
        self.assertTrue(parsed['violations'][1]['wrapped'])
        self.assertTrue(parsed['extraction_complete'])
        self.assertFalse(parsed['explicit_no_violations'])

    def test_only_explicit_clean_report_is_clear(self):
        self.assertTrue(drc.constraints_inventory(drc.NO_VIOLATIONS+'.')['explicit_no_violations'])
        for text in ('', 'Report aborted', drc.NO_VIOLATIONS+'\n'+drc.NO_VIOLATIONS,
                     'core/Z 1 2 -1 (VIOLATED)', 'max_transition\nunknown format VIOLATED'):
            inventory = drc.constraints_inventory(text)
            self.assertFalse(inventory['explicit_no_violations'])
            self.assertFalse(inventory['extraction_complete'])
        with self.assertRaises(ValueError):
            drc.constraints_inventory(REPORT+'\n'+drc.NO_VIOLATIONS)

    def test_unknown_or_truncated_rows_never_silently_clear(self):
        for bad in ('max_transition\ncore/Z ---- (VIOLATED)',
                    'max_transition\ncore/Z 1 2 -1 (VIOLATED) extra',
                    'unrecognized_constraint\ncore/Z 1 2 -1 (VIOLATED)',
                    'max_transition\nmax_unknown_constraint\ncore/Z 1 2 -1 (VIOLATED)',
                    'max_transition\ncore/Z\n\n 1 2 -1 (VIOLATED)'):
            inventory = drc.constraints_inventory(bad)
            self.assertEqual(inventory['violation_record_count'],1)
            self.assertFalse(inventory['extraction_complete'])
            self.assertFalse(inventory['explicit_no_violations'])

    def test_driver_query_parser_requires_actual_endpoint_completeness(self):
        text = ('schema\tn1-drc-driver-query-v1\n'
                'target\tcore/control[2]/Z\t1\t0\t0\n'
                'net\tcore/control[2]/Z\tcore/n4\t2\n'
                'endpoint\tcore/control[2]/Z\tcore/n4\tcore/control[2]/Z\tpin\tout\t1\n'
                'endpoint\tcore/control[2]/Z\tcore/n4\tcore/sink/A\tpin\tin\t0\n'
                'driver\tcore/control[2]/Z\tcore/n4\tcore/control[2]/Z\tcore/control[2]\tBUFV2RD_12TR40\n'
                'driver_attribute\tcore/control[2]/Z\tcore/control[2]\tarea\t1.25\n'
                'driver_input\tcore/control[2]/Z\tcore/control[2]\tcore/control[2]/I\tcore/upstream\n')
        result = drc.parse_driver_inventory(text, ['core/control[2]/Z'])
        self.assertTrue(result['extraction_complete'])
        self.assertEqual(result['unique_driver_cells'], ['core/control[2]'])
        self.assertEqual(result['driver_records'][0]['reference'],'BUFV2RD_12TR40')
        for bad in (text.replace('\tcore/n4\t2\n','\tcore/n4\t3\n'),
                    text+'target\tcore/control[2]/Z\t1\t0\t0\n',
                    text.replace('\tpin\tout\t1','\tpin\tunknown\t1'),
                    text.replace('endpoint\tcore/control[2]/Z\tcore/n4\tcore/sink/A\tpin\tin\t0',
                                 'endpoint\tcore/control[2]/Z\tcore/n4\tcore/control[2]/Z\tpin\tout\t1'),
                    '\n'.join(line for line in text.splitlines() if not line.startswith('driver\t'))+'\n',
                    text.replace('target\tcore/control[2]/Z\t1\t0\t0\n','')):
            with self.assertRaises(ValueError):
                drc.parse_driver_inventory(bad, ['core/control[2]/Z'])

    def test_zero_matches_are_explicitly_unresolved(self):
        text = 'schema\tn1-drc-driver-query-v1\ntarget\tcore/missing\t0\t0\t0\n'
        result = drc.parse_driver_inventory(text,['core/missing'])
        self.assertFalse(result['extraction_complete'])
        self.assertEqual(result['unresolved_targets'],['core/missing'])
        self.assertTrue(drc.parse_driver_inventory('schema\tn1-drc-driver-query-v1\n',[])['extraction_complete'])
        with self.assertRaises(ValueError):drc.parse_driver_inventory(text,[])

    def test_tcl_complete_readonly_actual_names_and_safe_bus_brackets(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder); fake_databases(folder)
            text = drc.script(folder,['core/control[2]/Z','core/n4'])
            self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
            self.assertIn('foreach name {{core/control[2]/Z} {core/n4}}',text)
            self.assertIn('full_name == "%s"',text)
            self.assertIn('all_connected -leaf $net',text)
            self.assertIn(drc.MARKER,text)
            for bad in ('\ncompile ', '\nsize_cell ', '\nset_dont_touch ', '\nset_false_path ',
                        '\nset_max_transition ', '\nwrite ', 'U32684','U3777'):
                self.assertNotIn(bad,text)
            for target in ('foo} {bar','foo"bar','foo;bar','foo\\bar','foo\nbar'):
                with self.assertRaises(ValueError):drc.script(folder,[target])
            with self.assertRaises(ValueError):drc.script(folder,['core/n4','core/n4'])

    def test_original_manifest_supplements_missing_installer_trace_without_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); synth = root/'runs'/'run'/'n1_synth'; synth.mkdir(parents=True)
            relative = 'workspaces/arch03/scripts/install_systolic_b.py'
            installer = root/relative; installer.parent.mkdir(parents=True); installer.write_text('fixture')
            manifest = root/'manifest.json'
            manifest.write_text(json.dumps({'files':{relative:drc.sha(installer)}}))
            source = synth/'source_inputs.json'; source.write_text('{}')
            before = drc.sha(source)
            receipt = drc.dependency_identity(synth)
            self.assertFalse(receipt['listed_in_original_source_inputs'])
            self.assertEqual(receipt['sha256'],drc.sha(installer))
            self.assertEqual(drc.sha(source),before)
            installer.write_text('modified')
            with self.assertRaises(ValueError):drc.dependency_identity(synth)

    def test_query_control_flow_executes_against_collection_fixture(self):
        # This evaluates the generated query, including bus-name quoting,
        # optional-attribute fallback and driver/input emission. These mock
        # collections are not evidence that the installed DC accepts it.
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder); fake_databases(folder)
            generated = drc.script(folder,['core/control[2]/Z'])
            query = generated.split('    # Only get/report operations',1)[1].split(
                '    set out [open mapped_port_probe.tsv w]',1)[0]
            query = '    # Only get/report operations'+query
            tcl = tkinter.Tcl()
            tcl.eval(r'''
set records {}
proc open {args} {return fixture_output}
proc close {args} {}
proc puts {args} {
    if {[llength $args]==2 && [lindex $args 0] eq "fixture_output"} {
        lappend ::records [lindex $args 1]
    }
}
proc sizeof_collection {collection} {llength $collection}
proc get_object_name {object} {return $object}
proc foreach_in_collection {name collection body} {
    upvar 1 $name item
    foreach item $collection {uplevel 1 $body}
}
proc get_pins {args} {
    if {[lsearch -exact $args -hierarchical]>=0} {return {{core/control[2]/Z}}}
    return {{core/control[2]/I}}
}
proc get_nets {args} {
    if {[lsearch -exact $args -hierarchical]>=0} {return {}}
    if {[lindex $args end] eq {core/control[2]/I}} {return core/upstream}
    return core/n4
}
proc get_ports {args} {return {}}
proc get_cells {args} {return {{core/control[2]}}}
proc add_to_collection {flag left right} {return [lsort -unique [concat $left $right]]}
proc all_connected {flag net} {return {{core/control[2]/Z} core/sink/A}}
proc get_attribute {args} {
    set object [lindex $args end-1]
    set attribute [lindex $args end]
    if {$attribute eq "object_class"} {return pin}
    if {$attribute eq "direction"} {
        if {$object eq {core/control[2]/Z}} {return out}
        return in
    }
    if {$attribute eq "ref_name"} {return BUFV2RD_12TR40}
    if {$attribute eq "area"} {return 1.25}
    error {fixture attribute not available}
}
''')
            tcl.eval(query)
            text = tcl.eval('join $records "\n"')+'\n'
            receipt = drc.parse_driver_inventory(text,['core/control[2]/Z'])
            self.assertTrue(receipt['extraction_complete'])
            self.assertEqual(receipt['driver_records'][0]['pin'],'core/control[2]/Z')
            self.assertIn('\tmax_transition\tunavailable',text)
            self.assertIn('\tcore/control[2]/I\tcore/upstream',text)


if __name__ == '__main__':
    unittest.main()
