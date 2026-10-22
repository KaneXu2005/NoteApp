"""Caesar cipher and key recovery by English letter-frequency chi-square scoring."""
import argparse
from collections import Counter

FREQUENCIES = [8.167,1.492,2.782,4.253,12.702,2.228,2.015,6.094,6.966,
               .153,.772,4.025,2.406,6.749,7.507,1.929,.095,5.987,6.327,
               9.056,2.758,.978,2.360,.150,1.974,.074]
EXAMPLE = ('The security of a system depends on careful design and regular testing. '
           'People should protect their passwords and keep private information safe. '
           'Encryption protects the contents of a message while authentication checks '
           'the identity of its sender. A secret key must be stored separately from '
           'the encrypted data. This example contains enough ordinary English text '
           'to demonstrate how letter frequencies can reveal a simple substitution.')


def encrypt(text, shift):
    def letter(c):
        if 'a' <= c <= 'z': return chr((ord(c)-97+shift)%26+97)
        if 'A' <= c <= 'Z': return chr((ord(c)-65+shift)%26+65)
        return c
    return ''.join(map(letter,text))


def crack(ciphertext):
    """Return (score, key, plaintext), ranked best first; no known key is used."""
    counts = Counter(c.lower() for c in ciphertext if c.isascii() and c.isalpha())
    n = sum(counts.values())
    if not n: raise ValueError('Frequency analysis requires ASCII letters')
    candidates = []
    for key in range(26):
        score = sum((counts[chr((i+key)%26+97)]-n*f/100)**2/(n*f/100)
                    for i,f in enumerate(FREQUENCIES))
        candidates.append((score,key,encrypt(ciphertext,-key)))
    return sorted(candidates)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ciphertext', help='Analyze supplied ciphertext instead of the built-in example')
    args = p.parse_args()
    cipher = args.ciphertext or encrypt(EXAMPLE,17)
    print('Ciphertext:',cipher)
    for score,key,plain in crack(cipher)[:3]:
        print(f'Candidate key={key}, chi-square={score:.2f}\n{plain}')
    if not args.ciphertext:
        assert crack(cipher)[0][2] == EXAMPLE
        assert all(encrypt(encrypt(EXAMPLE,k),-k)==EXAMPLE for k in range(26))
        print('PASS: recovered the example without supplying the key; all 26 round trips passed.')
