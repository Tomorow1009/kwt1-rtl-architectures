"""Sequence metadata/trap-boundary tests, never fake CPU execution evidence."""
import ast
import hashlib
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import build_dma16_sequence as seq


class SequenceContractTests(unittest.TestCase):
    def setUp(self):
        self.first=dict(source_id=0,shift=12,descriptor=12)
        self.second=dict(source_id=1,shift=11,descriptor=0x1000b)
        self.base=bytearray(262144)
        self.base[:4]=b'\x13\x00\x00\x00'

    def test_program_only_four_metadata_words(self):
        image=seq.metadata_image(self.base,self.first,self.second,8192)
        self.assertEqual(struct.unpack_from('<4I',image,0xfff0),(seq.MAGIC,12,0x1000b,8192))
        self.assertEqual(image[:0xfff0],self.base[:0xfff0])
        self.assertFalse(any(image[0x10000:]))

    def test_nonzero_task_region_and_metadata_base_rejected(self):
        for offset in (0xfff0,0x10000,262143):
            base=bytearray(self.base);base[offset]=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                seq.metadata_image(base,self.first,self.second,8192)

    def test_source_ids_shift_and_descriptor_must_agree(self):
        for bad in (dict(source_id=0,shift=11,descriptor=0x1000b),
                    dict(source_id=1,shift=32,descriptor=0x10020),
                    dict(source_id=1,shift=11,descriptor=11)):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                seq.metadata_image(self.base,self.first,bad,8192)

    def test_timeout_must_allow_actual_launch_but_remain_partial(self):
        for timeout in (0,1,4095,32769,True):
            with self.subTest(timeout=timeout),self.assertRaises(ValueError):
                seq.metadata_image(self.base,self.first,self.second,timeout)

    def test_exact_guard_instruction_and_resume_label(self):
        base=bytearray(self.base);struct.pack_into('<I',base,0x100,0x0062a023)
        symbols=dict(sequence_fault_store=0x80000100,sequence_fault_resume=0x80000104,
                     dma16_sequence_trap=0x800007c0,trap_entry=0x8000004c)
        with patch.object(seq,'symbols',return_value=symbols):
            result=seq.verify_fault_sites(b'',base)
            self.assertEqual(result['sequence_fault_store'],'0x80000100')
        for delta in (2,6):
            wrong=dict(symbols);wrong['sequence_fault_resume']=0x80000100+delta
            with patch.object(seq,'symbols',return_value=wrong),self.assertRaises(ValueError):
                seq.verify_fault_sites(b'',base)
        base[0x100]=0x13
        with patch.object(seq,'symbols',return_value=symbols),self.assertRaises(ValueError):
            seq.verify_fault_sites(b'',base)

    def test_missing_fault_symbols_are_rejected(self):
        with patch.object(seq,'symbols',return_value={}),self.assertRaises(ValueError):
            seq.verify_fault_sites(b'',self.base)

    def test_runtime_sources_require_both_bound_payloads(self):
        words=[0]*11744
        payload=struct.pack('<11744I',*words)
        canonical=('00000000\n'*11744).encode('ascii')
        task=dict(self.first,load_payload_sha256=hashlib.sha256(payload).hexdigest(),
                  load32_canonical_lf_sha256=hashlib.sha256(canonical).hexdigest())
        manifest=dict(run_mode='cpu_dma16_sequence_v1',tasks=dict(A=task,B=dict(task,**self.second)))
        with patch.object(seq,'hex_values',return_value=words),patch.object(seq,'sha',return_value='file-digest'):
            result=seq.verify_runtime_sources(manifest,'first.hex','second.hex')
            self.assertEqual(result['B']['descriptor'],0x1000b)
            self.assertEqual(result['A']['file_sha256'],'file-digest')
        bad=list(words);bad[100]=1
        with patch.object(seq,'hex_values',return_value=bad),self.assertRaises(ValueError):
            seq.verify_runtime_sources(manifest,'first.hex','second.hex')

    def test_python36_syntax_and_no_numeric_runtime_dependency(self):
        text=Path(seq.__file__).read_text(encoding='utf8')
        tree=ast.parse(text,feature_version=(3,6)) if sys.version_info>=(3,8) else ast.parse(text)
        names={item.names[0].name for item in ast.walk(tree) if isinstance(item,ast.Import)}
        self.assertFalse(names & {'numpy','tensorflow','numeric'})


if __name__=='__main__':unittest.main()
