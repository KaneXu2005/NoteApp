"""Offline audit of six synthetic accounts from the course; no real user data."""
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ACCOUNTS={'liwei':'123456','sofia':'iloveyou','tomk':'qwerty123',
          'aisha':'password1','marie':'mariepw','raj':'Gv7#pLm2!xQ'}
root=Path(__file__).resolve().parent
words=[w.strip() for w in (root/'wordlist.txt').read_text().splitlines() if w.strip() and not w.startswith('#')]
dump={u:hashlib.md5(p.encode()).hexdigest() for u,p in ACCOUNTS.items()}
(root/'synthetic_dump.txt').write_text(''.join(f'{u}:{d}\n' for u,d in dump.items()))
start=time.perf_counter();cracked={}
for word in words:
    digest=hashlib.md5(word.encode()).hexdigest()
    for user,wanted in dump.items():
        if wanted==digest:cracked[user]=word
elapsed=time.perf_counter()-start
# Median rates, repeated sequentially in one process. Not a GPU benchmark.
md5_samples=[]
for _ in range(5):
    start=time.perf_counter()
    for i in range(100_000):hashlib.md5(b'guess').hexdigest()
    md5_samples.append(100_000/(time.perf_counter()-start))
ph=PasswordHasher()
stored=ph.hash('benchmark-target')
argon_samples=[]
for _ in range(5):
    start=time.perf_counter()
    try:ph.verify(stored,'guess')
    except VerifyMismatchError:pass
    argon_samples.append(time.perf_counter()-start)
md5=statistics.median(md5_samples);argon=1/statistics.median(argon_samples)
result={'platform':platform.platform(),'python':platform.python_version(),
        'wordlist_entries':len(words),'cracked':cracked,'held_out':sorted(set(ACCOUNTS)-set(cracked)),
        'dictionary_elapsed_ms':elapsed*1000,'md5_guesses_per_second':md5,
        'argon2_guesses_per_second':argon,'md5_guesses_per_day':md5*86400,
        'argon2_guesses_per_day':argon*86400,'slowdown_ratio':md5/argon,
        'argon2_parameters':{'time_cost':ph.time_cost,'memory_cost_kib':ph.memory_cost,'parallelism':ph.parallelism},
        'method':'median of 5 runs: MD5 100000 hashes per run; Argon2 one failed verification per run; sequential CPU estimates'}
(root/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
