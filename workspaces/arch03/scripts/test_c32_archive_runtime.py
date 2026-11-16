"""Exercise archive launch provenance without creating an archive or using EDA."""
import json
from pathlib import Path
import tempfile
import unittest
import c32_archive_runtime as runtime
import c32_archive_contract as contract
from test_c32_archive_contract import fixture,export,save


class LaunchIdentity(unittest.TestCase):
    def test_own_initial_finish_sources_and_request_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle=Path(directory);a=fixture(bundle,'initial');b=fixture(bundle,'finish')
            proof=contract.joined_queues(a,b);run,digest,_=export(bundle,proof)
            request=dict(bundle_manifest_sha256='a'*64,report_run=str(run),report_sha256=digest)
            for role,p in [('initial',a),('finish',b)]:
                name='c32_qualification.py' if role=='initial' else 'c32_finish.py'
                source=bundle/'workspaces/arch03/scripts'/name;source.parent.mkdir(parents=True,exist_ok=True)
                source.write_text('# fixture, not executable evidence\n')
                req=dict(schema='c32-qualification-v1' if role=='initial' else 'c32-final-netlist-finish-v1',
                    bundle=str(bundle),bundle_manifest_sha256='a'*64,queue_sha256=runtime.paths.digest(source))
                if role=='finish':req['synthesis']=b['state']['synthesis']
                queue=Path(p['queue']);save(queue/'request.json',req)
                request[role]=dict(queue=str(queue),state_sha256=runtime.paths.digest(queue/'state.json'))
            result=runtime.evidence(request,bundle);self.assertFalse(result['archive_implies_acceptance'])
            path=Path(a['queue'])/'request.json';req=json.loads(path.read_text());req['queue_sha256']='b'*64;save(path,req)
            with self.assertRaisesRegex(ValueError,'launch identity'):runtime.evidence(request,bundle)


if __name__=='__main__':unittest.main()
