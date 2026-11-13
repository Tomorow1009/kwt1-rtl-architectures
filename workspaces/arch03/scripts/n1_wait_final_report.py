"""Wait for the specific existing power recovery, then run read-only export."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

OPS = Path('/tmp/s4_21usr_n1_20261113_0210/light-light126-n1-precisionops02-20261113_090845')


def main():
    recovery = OPS/'power_recovery02'
    tools = OPS/'recovery_report_tools_1135'
    source = tools/'n1_finish_recovery_report.py'
    template = tools/'base_request.json'
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    require = lambda ok: None if ok else (_ for _ in ()).throw(ValueError('Pinned final-report input/state changed'))
    require(sha(source) == '9d9fbb49c06668b058a5f19431664fa085a66003bb90b4daa58a751d3bb59c6a')
    template_sha = '42459be86393c8e4617ab84092b448f2267c896f7ddf10545d187f82d97e315e'
    require(sha(template) == template_sha)
    output = OPS/'final_report_wait01'
    output.mkdir()
    state = dict(status='waiting_existing_power_recovery', pid=os.getpid(), child_pid=None,
                 started=datetime.datetime.now().isoformat(), n2_allowed=False)
    def save():
        temp = output/'state.tmp'
        temp.write_text(json.dumps(state, indent=2)+'\n')
        temp.replace(output/'state.json')
    save()
    try:
        while True:
            record = json.loads((recovery/'state.json').read_text())
            require(record['pid'] == 84627 and record['runner_sha256'] ==
                    '3eb31fa2c6556623de25bb72d90c8edb237cd4c4b8158fdf460ba88cdf881dac')
            if record['status'] == 'failed':raise ValueError('Original power recovery failed; do not restart')
            if record['status'] == 'numbers_ready_independent_review_required':
                if not Path('/proc/84627').exists() and not Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/.arch02_team_lock').exists():break
            time.sleep(20)
        require(sha(source) == '9d9fbb49c06668b058a5f19431664fa085a66003bb90b4daa58a751d3bb59c6a'
                and sha(template) == template_sha)
        digest = sha(recovery/'state.json')
        command = [sys.executable, '-B', '-u', str(source), '--template', str(template),
                   '--template-sha256', template_sha, '--recovery', str(recovery), '--recovery-sha256', digest]
        state.update(status='export_running', command=command, recovery_state_sha256=digest)
        save()
        with (output/'export.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            state['child_pid'] = child.pid;save()
            code = child.wait()
        state.update(child_pid=None, exit_code=code)
        require(code == 0)
        state['status'] = 'export_and_inventory_ready_independent_review_required'
    except BaseException as exc:
        state.update(status='failed', error=str(exc))
        raise
    finally:
        state['finished'] = datetime.datetime.now().isoformat();save()


if __name__ == '__main__':main()
