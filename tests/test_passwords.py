import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'web'))
from passwords import ph,verify_password
from argon2 import PasswordHasher

class Passwords(unittest.TestCase):
    def test_legacy_upgrade(self):
        self.assertEqual(verify_password('alicepw','wrong'),(False,None))
        ok,new=verify_password('alicepw','alicepw')
        self.assertTrue(ok);self.assertTrue(new.startswith('$argon2id$'))
        self.assertEqual(verify_password(new,'alicepw'),(True,None))
        self.assertEqual(verify_password(new,'wrong'),(False,None))

    def test_salts_and_unicode(self):
        first=ph.hash('秘密');second=ph.hash('秘密')
        self.assertNotEqual(first,second)
        self.assertTrue(verify_password(first,'秘密')[0])

    def test_malformed_and_rehash(self):
        for value in ('$argon2garbage',None,'$argon2id$v=19$broken'):
            self.assertEqual(verify_password(value,'pw'),(False,None))
        old=PasswordHasher(time_cost=1,memory_cost=8192,parallelism=1).hash('pw')
        ok,new=verify_password(old,'pw')
        self.assertTrue(ok);self.assertIsNotNone(new)
        self.assertFalse(ph.check_needs_rehash(new))
