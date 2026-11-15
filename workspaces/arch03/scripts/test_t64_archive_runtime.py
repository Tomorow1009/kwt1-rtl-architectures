"""Copy/readback and stage identity for T64's independent durable archive."""
import json
from pathlib import Path
import tempfile
import unittest

import t64_archive_runtime as archive


class T64ArchiveTests(unittest.TestCase):
    def test_readback_preserves_source_and_detects_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent=Path(temporary).resolve();root=parent/'t64_runtime';root.mkdir()
            (root/'empty').mkdir();source=root/'capture.bin';source.write_bytes(bytes(range(256))*20)
            rows=archive.inventory(root,root.stat().st_uid);out=parent/'archive.tar.gz'
            with out.open('wb') as stream:archive.tar.stream_archive(rows,archive.tar.Sink(stream,parent))
            self.assertEqual(archive.tar.verify_archive(out,rows),dict(regular=1,directory=2,symlink=0))
            self.assertEqual(archive.inventory(root,root.stat().st_uid),rows)
            source.write_bytes(b'changed')
            with self.assertRaises(ValueError):archive.tar.stream_archive(rows,archive.tar.Sink())
            self.assertEqual(source.read_bytes(),b'changed')

    def test_active_or_other_architecture_stage_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle=Path(temporary).resolve();session=bundle/'runs/session';session.mkdir(parents=True)
            f=session/'state.json';summary=session/'t64_soc/summary.json';summary.parent.mkdir()
            summary.write_text('{}');digest=archive.paths.digest(summary)
            row=dict(status='passed',finished='fixture',summary_sha256=digest)
            for name,record in [('t80_soc',row),('t64_soc',dict(row,status='running'))]:
                f.write_text(json.dumps(dict(stages={name:record})))
                with self.assertRaisesRegex(ValueError,'Nonterminal T64'):archive.terminal_sessions(bundle,bundle/'no_queue')
            f.write_text(json.dumps(dict(stages={'t64_soc':row})))
            self.assertEqual(len(archive.terminal_sessions(bundle,bundle/'no_queue')),1)
            summary.write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,'summary changed'):archive.terminal_sessions(bundle,bundle/'no_queue')


if __name__=='__main__':unittest.main()
