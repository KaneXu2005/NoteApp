# Class 5 — Password storage audit

Operator: 汪芮. Date: 2026-10-22. No partner or pre-experiment prediction is invented.
Course instructions: https://kristenpire.github.io/epita-security-labs/class5/password-audit/
The live lab has changed since the slide example: it now supplies about 190 common
passwords, of which this downloaded file contains 170 nonempty entries.
The result below comes from this actual file, not the slides' illustrative “6/6”.

## Finding 1 — unsalted MD5

- Cracked **4/6** synthetic accounts in **0.089 ms**.
- Fell: liwei, sofia, tomk, aisha. Their passwords occur in the public teaching wordlist.
- Held out: marie (`mariepw`, a predictable username-based password absent from the list)
  and raj (a long, random-looking password absent from the list).
- Severity: **High**. Fast unsalted hashes allow cheap offline guesses and reuse each
  guess across all accounts. MD5 collision attacks are not the mechanism used here.
- Fix: per-password salt and Argon2id, plus stronger passwords. Surviving this one tiny
  wordlist is not proof that a password is uncrackable. Argon2 raises cost but cannot
  rescue a password at the very beginning of a common-password dictionary.

## Finding 2 — measured cost

| Algorithm | Guesses / second | Guesses / day (extrapolated) |
|---|---:|---:|
| MD5 | 4,320,471 | 373,288,688,168 |
| Argon2id | 51.90 | 4,484,458 |

On this run Argon2id was approximately **83,241 times slower** per guess.
Parameters: 64 MiB, 3 iterations, parallelism 4. Median of five batches, each MD5 batch
containing 100,000 hashes and each Argon2 batch one failed verification. Sequential CPU
measurements inside the local ARM64 Docker container, not GPU or attacker hardware
predictions. The per-day numbers are linear extrapolations, not 24-hour experiments.
Absolute values depend on hardware, parallelism, warm-up and system load.

## Applied remediation

Login retrieves the stored password by username, verifies Argon2 hashes, and upgrades
legacy plaintext only after a successful comparison. Failed logins do not migrate.
Changed Argon2 parameters trigger rehash after successful verification. The update uses
a compare-and-swap condition to avoid overwriting a concurrent password change.
Admin-created users are hashed immediately. Malformed Argon2 values fail authentication.

Actual DB checks: alice changed from plaintext to Argon2id, then logged in again;
wrong passwords failed; a new test account was hashed on creation and removed after the test.
See [migration evidence](evidence/password-migration.json). Dormant accounts remain legacy
until their next successful login. Course seed files and old backups are not retroactively
sanitized. This is an incremental teaching migration, not a fully remediated password estate.

As explicitly required by Class 5, username SQL concatenation stays unchanged for the
later SQL-injection lesson. Other course flaws remain out of scope for this stage.

## Reproduce

```sh
docker cp labs/class05 notesapp-course-web-1:/tmp/class05
docker exec notesapp-course-web-1 python /tmp/class05/password_audit.py
docker cp notesapp-course-web-1:/tmp/class05/results.json labs/class05/results.json
```

The script only attacks its six locally generated course accounts. The source wordlist is
https://kristenpire.github.io/epita-security-labs/class5/assets/common-passwords.txt .
Full measurements are in [results.json](../labs/class05/results.json).
