"""Class 4 examples: SHA-256, HMAC, toy RSA and real RSA-PSS signatures."""
import hashlib
import hmac
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

message=b'alice,14,good work\r\n'
changed=message.replace(b',14,',b',18,')
assert hashlib.sha256(message).digest() == hashlib.sha256(message).digest()
assert hashlib.sha256(message).digest() != hashlib.sha256(changed).digest()
key=os.urandom(32)
tag=hmac.digest(key,message,'sha256')
assert not hmac.compare_digest(tag,hmac.digest(key,changed,'sha256'))
print('PASS: SHA-256 is deterministic; editing the grade changes the hash and HMAC.')
# Textbook RSA arithmetic from the lecture, not a usable encryption construction.
cipher=pow(42,17,3233)
assert cipher==2557 and pow(cipher,2753,3233)==42
print('Toy RSA: 42 -> 2557 -> 42 (educational only; no padding).')
private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
pss=padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.MAX_LENGTH)
signature=private.sign(message,pss,hashes.SHA256())
private.public_key().verify(signature,message,pss,hashes.SHA256())
try: private.public_key().verify(signature,changed,pss,hashes.SHA256())
except InvalidSignature: print('PASS: RSA-PSS authentic signature verified; changed grade rejected.')
else: raise AssertionError('Modified message accepted')
print('HMAC authenticates shared-key possession; it does not distinguish holders or give non-repudiation.')
