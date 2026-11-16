"""Read-only linked-net connectivity for every declared unknown SAIF net.

This distinguishes hierarchy-only aliases from actual leaf connections.
It does not assign activity, change a netlist, or approve connected unknowns.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import time


def require(ok, message):
    if not ok:raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024**2), b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def inventory_targets(references, netlist, netlist_sha):
    names, layers, inputs = set(), set(), {}
    counts = Counter()
    for ref in references:
        directory = Path(ref['run']);summary = directory/'summary.json'
        require(sha(summary) == ref['sha256'], 'Unknown inventory summary changed')
        inv = read(summary)
        require(Path(inv['netlist']) == Path(netlist) and inv['netlist_sha256'] == netlist_sha,
                'Unknown inventory belongs to a different netlist')
        require(inv['status'] == 'complete_existing_unknown_inventory_review_required'
                and inv['full_unknown_inventory_complete'], 'Unknown inventory incomplete')
        inputs[str(summary)] = ref['sha256']
        for case in inv['cases']:
            name = case['case'];require(name not in layers, 'Repeated layer');layers.add(name)
            path = directory/case['unknown_file']
            require(path.parent == directory and sha(path) == case['unknown_file_sha256'], 'Unknown list changed')
            inputs[str(path)] = case['unknown_file_sha256'];number = 0
            with gzip.open(str(path), 'rt') as stream:
                for line in stream:
                    row = json.loads(line);number += 1
                    require(row['section'] == 'NET', 'Non-NET unknown needs separate handling')
                    prefix = 'tb_top/u_e203_soc_top/'
                    full = row['saif_name']
                    require(full.startswith(prefix), 'Unknown outside DUT')
                    target = full[len(prefix):]
                    require(target and not re.search(r'[\t\r\n]', target), 'Invalid linked-net name')
                    names.add(target);counts[row['mapping']['disposition']] += 1
            require(number == case['unknown_rows'], 'Unknown rows differ')
    require(layers == {'layer_%02d' % i for i in range(1, 13)}, 'Need complete twelve-layer inventory')
    return sorted(names), dict(counts), inputs


def query_script(synthesis, libraries, targets_file):
    def word(value):
        value = str(value);require(not re.search(r'[{}\r\n]', value), 'Unsafe Tcl path')
        return '{'+value+'}'
    return r'''
proc unknown_connections {} {
    set_app_var sh_continue_on_error false
    set_app_var link_library [list * @LIBS@]
    read_ddc @DDC@
    current_design e203_soc_top
    if {![link]} {error "Original mapped design did not link"}
    set targets [dict create]
    set input [open @TARGETS@ r]
    while {[gets $input name] >= 0} {
        if {$name eq "" || [dict exists $targets $name]} {error "Invalid/duplicate query target"}
        dict set targets $name 0
    }
    close $input
    set out [open unknown_connections.tsv w]
    puts $out "schema\tsaif-unknown-linked-connections-v1"
    foreach_in_collection net [get_nets -hierarchical *] {
        set name [get_object_name $net]
        if {![dict exists $targets $name]} {continue}
        if {[dict get $targets $name]} {error "Ambiguous mapped net name"}
        dict set targets $name 1
        set direct [sizeof_collection [all_connected $net]]
        set leaves [all_connected -leaf $net]
        puts $out "net\t$name\t$direct\t[sizeof_collection $leaves]"
        foreach_in_collection endpoint $leaves {
            set class [get_attribute $endpoint object_class]
            set direction [get_attribute $endpoint direction]
            set ref top_port
            if {$class eq "pin"} {
                set cell [get_cells -of_objects $endpoint]
                if {[sizeof_collection $cell] != 1} {error "Ambiguous leaf endpoint cell"}
                set ref [get_attribute $cell ref_name]
            }
            puts $out "endpoint\t$name\t[get_object_name $endpoint]\t$class\t$direction\t$ref"
        }
    }
    dict for {name found} $targets {
        if {!$found} {puts $out "unresolved\t$name"}
    }
    close $out
    puts "SAIF_UNKNOWN_LINKED_CONNECTIONS_COMPLETE"
}
if {[catch {unknown_connections} message]} {
    puts stderr "Error: UNKNOWN_CONNECTION_QUERY_ABORT $message"
    exit 1
}
quit
'''.replace('@LIBS@', ' '.join(word(p) for p in libraries)).replace('@DDC@', word(synthesis/'mapped.ddc')).replace('@TARGETS@', word(targets_file))


def parse_connections(text, targets):
    lines = text.splitlines();require(lines and lines[0] == 'schema\tsaif-unknown-linked-connections-v1', 'Wrong proof header')
    nets, unresolved, ends, endpoints, loads = {}, set(), Counter(), set(), Counter()
    for line in lines[1:]:
        row = line.split('\t');kind, name = row[:2]
        require(name in targets, 'Unexpected proof net')
        if kind in ('net', 'unresolved'):
            require(name not in nets and name not in unresolved, 'Duplicate net proof')
            if kind == 'unresolved':require(len(row) == 2, 'Invalid unresolved row');unresolved.add(name)
            else:
                require(len(row) == 4 and all(re.fullmatch(r'\d+', x) for x in row[2:]), 'Invalid counts')
                nets[name] = tuple(map(int, row[2:]))
        else:
            require(kind == 'endpoint' and len(row) == 6 and name in nets, 'Invalid endpoint proof')
            require((name, row[2]) not in endpoints, 'Duplicate leaf endpoint')
            endpoints.add((name, row[2]))
            require(row[3] in ('pin', 'port') and row[4] in ('in', 'out', 'inout'), 'Unknown endpoint type')
            if (row[3] == 'pin' and row[4] in ('in', 'inout')) or (row[3] == 'port' and row[4] in ('out', 'inout')):
                loads[name] += 1
            ends[name] += 1
    require(set(nets) | unresolved == set(targets), 'Incomplete target proof')
    require(all(ends[n] == value[1] for n, value in nets.items()), 'Leaf endpoint count differs')
    return dict(targets=len(targets), resolved=len(nets), unresolved=sorted(unresolved),
        isolated_zero_direct_and_leaf=sorted(n for n, counts in nets.items() if counts == (0, 0)),
        hierarchy_only_no_leaf=sorted(n for n, counts in nets.items() if counts[0] and not counts[1]),
        leaf_connected=sorted(n for n, counts in nets.items() if counts[1]),
        no_receiving_leaf=sorted(n for n, counts in nets.items() if counts[1] and not loads[n]),
        receiving_leaf=sorted(n for n in nets if loads[n]),
        system_power_verified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--request-sha256', required=True)
    a = p.parse_args();require(sha(a.request) == a.request_sha256, 'Request changed');req = read(a.request)
    import n1_paths
    import server_run as common
    from n1_process import ProcessLedger, atomic_save, now
    from soc_power import power_databases
    import c80_review_contract as contract
    profile, cfg = contract.configure(req, common)
    common.inputs()
    require(re.fullmatch(r'[a-zA-Z0-9_-]+', req['session']), 'Invalid session')
    session = common.ROOT/'runs'/req['session'];require(not session.exists(), 'Preserve old session')
    lock = Path(cfg['server_root'])/'.arch02_team_lock';ledger = ProcessLedger(common, lock, session)
    while True:
        if lock.exists():time.sleep(20);continue
        try:ledger.acquire();break
        except OSError as error:
            if error.errno != 28 or lock.exists():raise
            print('WAIT_INITIAL_SHARED_LOCK_STORAGE', flush=True);time.sleep(30)
    state = dict(schema='arch03-'+profile.lower()+'-server-state-v1', status='running', started=now(),
        pid=os.getpid(), jobs=[], stages={}, system_power_verified=False,
        request_sha256=a.request_sha256, source_sha256=sha(__file__))
    stage = None
    try:
        session.mkdir();ledger.initialize();atomic_save(session/'request.json', req)
        for job in req['jobs']:
            require(job['name'] in (('B0', 'N1') if profile == 'N1' else (profile,)) and
                    job['name'] not in [x['name'] for x in state['jobs']], 'Invalid job name')
            stage = profile.lower()+'_unknown_' + job['name'].lower()
            state['stages'][stage] = dict(status='running', started=now())
            atomic_save(session/'state.json', state)
            run = session/stage;run.mkdir();synthesis = Path(job['synthesis']['run'])
            summary = synthesis/'summary.json';require(sha(summary) == job['synthesis']['sha256'], 'Synthesis changed')
            report = read(summary);inputs = {str(summary):sha(summary)}
            if profile != 'N1':contract.synthesis_identity(report, profile)
            for name in ('mapped.ddc', 'mapped.v'):
                require(sha(synthesis/name) == report['artifacts'][name], 'Mapped input changed')
                inputs[str(synthesis/name)] = report['artifacts'][name]
            names, classes, unknown_inputs = inventory_targets(job['unknown_inventories'], synthesis/'mapped.v',
                                                               report['artifacts']['mapped.v'])
            inputs.update(unknown_inputs);libs = power_databases(synthesis)
            inputs.update({str(path):sha(path) for path in libs})
            targets = run/'targets.txt';targets.write_text('\n'.join(names)+'\n')
            script = run/'query.tcl';script.write_text(query_script(synthesis, libs, targets))
            atomic_save(run/'source_inputs.json', inputs)
            log = ledger.call([cfg['tools']['dc_shell'], '-f', str(script)], run, 'query.log')
            require('SAIF_UNKNOWN_LINKED_CONNECTIONS_COMPLETE' in log, 'No completion marker')
            result = parse_connections((run/'unknown_connections.tsv').read_text(), set(names))
            require(all(sha(path) == digest for path, digest in inputs.items()), 'Input changed during query')
            result.update(name=job['name'], local_classes=classes, input_files=inputs,
                proof_sha256=sha(run/'unknown_connections.tsv'), log_sha256=sha(run/'query.log'),
                source_sha256=sha(__file__), netlist_modified=False, activity_modified=False)
            atomic_save(run/'summary.json', result)
            state['stages'][stage].update(status='passed', finished=now(),
                summary_sha256=sha(run/'summary.json'), run=str(run),
                acceptance_scope='connectivity collection only, not power acceptance')
            state['jobs'].append(dict(name=job['name'], summary_sha256=sha(run/'summary.json'),
                targets=result['targets'], resolved=result['resolved'], leaf_connected=len(result['leaf_connected']),
                unresolved=len(result['unresolved'])))
            atomic_save(session/'state.json', state)
        common.inputs()
        state['status'] = 'connections_collected_review_required'
    except BaseException as error:
        if stage is not None:
            state['stages'][stage].update(status='failed', finished=now(), error=str(error))
        state.update(status='failed', error=str(error));raise
    finally:
        state['finished'] = now()
        try:
            if session.is_dir():atomic_save(session/'state.json', state)
        finally:ledger.release()


if __name__ == '__main__':main()
