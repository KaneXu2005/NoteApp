import base64
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'web'))
from export_integrity import sign_export, verify_export

class Exports(unittest.TestCase):
    def setUp(self):
        p=patch.dict(os.environ, {'EXPORT_HMAC_KEY_B64':base64.b64encode(os.urandom(32)).decode()})
        p.start();self.addCleanup(p.stop)

    def test_authentic_and_modified(self):
        payload='student,class,grade,comment\r\nalice,Math,14,"中文\n# HMAC-SHA256: fake"\r\n'.encode()
        signed=sign_export(payload)
        self.assertTrue(verify_export(signed))
        for bad in (signed.replace(b',14,',b',18,'),signed[:-3],signed+b'\n',payload,signed.replace(b'\r\n',b'\n')):
            self.assertFalse(verify_export(bad))
        os.environ['EXPORT_HMAC_KEY_B64']=base64.b64encode(os.urandom(32)).decode()
        self.assertFalse(verify_export(signed))
