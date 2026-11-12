"""Read-only B mapped-warning inventory, retaining all unresolved classes."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from dma16_structural_audit import classify,modules,sha,require


def no_load_drivers(text,mapped,ports):
    instances={}
    for name,module in mapped.items():
        values={}
        # Named pin continuations such as '.clk(clk), .rst(rst)' are not
        # instances. Restrict both leading tokens to Verilog identifiers,
        # including DC's escaped identifiers, and keep whitespace on one line.
        identifier=r'(?:[A-Za-z_$][A-Za-z_0-9$]*|\\\S+)'
        pattern=r'(?m)^[ \t]*('+identifier+r')[ \t]+('+identifier+r')[ \t]*\('
        for reference,instance in re.findall(pattern,module['logic']):
            instance=instance.lstrip('\\');reference=reference.lstrip('\\')
            require(instance not in values,'Duplicate mapped instance '+instance)
            values[instance]=reference
        instances[name]=values
    rows=[]
    for line in text.splitlines():
        # check_design also repeats the code in its final count table.
        if not line.startswith('Warning:') or '(LINT-2)' not in line:continue
        match=re.fullmatch(r"Warning: In design '([^']+)', net '(.*?)' driven by pin '(.*?)' has no loads\. \(LINT-2\)",line)
        require(match is not None,'Unreviewed LINT-2 format')
        design,net,pin=match.groups();target=design
        path,port=pin.rsplit('/',1)
        for instance in path.split('/'):
            require(target in instances and instance in instances[target],'Unresolved no-load hierarchy '+pin)
            target=instances[target][instance]
        rows.append(dict(design=design,net=net,driver_pin=pin,driver_design=target,driver_port=port))
    actual={(row['driver_design'],row['driver_port']) for row in rows}
    expected={(row['design'],row['port']) for row in ports if row['warning']=='LINT-8' and row['disposition']=='declaration_only'}
    return dict(count=len(rows),unique_driver_ports=len(actual),
        matches_declaration_only_unloaded_ports=actual==expected,
        extra=sorted(actual-expected),missing=sorted(expected-actual),rows=rows)


def audit(run,digest):
    run=Path(run).resolve();summary=run/'summary.json'
    require(sha(summary)==digest,'B synthesis digest mismatch')
    report=json.loads(summary.read_text())
    state=json.loads((run.parent/'state.json').read_text())['stages']['systolic_b_synth']
    require(state['status']=='passed' and state['summary_sha256']==digest and
        report['scope']=='systolic_b_whole_soc_task_mode_preliminary_synthesis','Wrong B synthesis provenance')
    tracked={str(summary):digest}
    for name in ('mapped.v','check_design_mapped.rpt'):
        tracked[str(run/name)]=report['artifacts'][name]
    require(all(sha(p)==h for p,h in tracked.items()),'Frozen B structural input changed')
    text=(run/'check_design_mapped.rpt').read_text();net=(run/'mapped.v').read_text()
    result=classify(text,net)
    result['no_load_drivers']=no_load_drivers(text,modules(net),result['ports'])
    result['other_warning_lines']=[line for line in text.splitlines() if line.startswith('Warning:') and
        not re.search(r'\(LINT-(?:2|8|28)\)',line)]
    result.update(schema='systolic-b-structural-inventory-v1',synthesis_run=str(run),
        synthesis_summary_sha256=digest,inputs_sha256=tracked,auditor_sha256=sha(__file__),
        parser_sha256=sha(Path(__file__).with_name('dma16_structural_audit.py')),
        netlist_modified=False,eda_started=False,timing_verified=False,
        remaining_review='Inspect unresolved ports, other warning classes, clocks and exceptions with same-netlist functional evidence')
    require(all(sha(p)==h for p,h in tracked.items()),'B structural input changed during audit')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--synth-run',type=Path,required=True)
    p.add_argument('--summary-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();require(not a.output.exists(),'Use a fresh structural output')
    result=audit(a.synth_run,a.summary_sha256)
    with a.output.open('x') as out:json.dump(result,out,indent=2)
    print('B_STRUCTURE_INVENTORIED timing_verified=false',result['disposition_counts'],
          result['no_load_drivers']['matches_declaration_only_unloaded_ports'])
