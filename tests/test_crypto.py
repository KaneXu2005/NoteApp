import base64
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.exceptions import InvalidTag
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'web'))
from crypto_utils import encrypt_comment, decrypt_comment, PREFIX


class Comments(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'COMMENT_KEY_B64': base64.b64encode(os.urandom(32)).decode()})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_roundtrip_and_random_nonce(self):
        for plain in ('', '评语, "quoted"\nnext line', None):
            c = encrypt_comment(plain, 7)
            self.assertEqual(decrypt_comment(c, 7), plain)
        self.assertNotEqual(encrypt_comment('same',7),encrypt_comment('same',7))

    def test_tamper_wrong_key_and_row_swap(self):
        c = encrypt_comment('private',7)
        with self.assertRaises(InvalidTag): decrypt_comment(c,8)
        raw = bytearray(base64.b64decode(c[len(PREFIX):])); raw[-1] ^= 1
        with self.assertRaises(InvalidTag): decrypt_comment(PREFIX+base64.b64encode(raw).decode(),7)
        os.environ['COMMENT_KEY_B64'] = base64.b64encode(os.urandom(32)).decode()
        with self.assertRaises(InvalidTag): decrypt_comment(c,7)

    def test_fail_closed(self):
        for bad in ('plaintext', PREFIX+'?', PREFIX+'AA=='):
            with self.assertRaises(ValueError): decrypt_comment(bad,7)
        os.environ['COMMENT_KEY_B64']=''
        with self.assertRaises(ValueError): encrypt_comment('text',7)
