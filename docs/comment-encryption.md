# Session 03 homework — comments at rest

Run `python3 scripts/setup_secrets.py` once before `docker compose up -d --build`.
The ignored `.env` supplies an independent 256-bit AES key. Keep an offline backup;
losing this key means losing encrypted comments. Never regenerate it to repair an error.

The web container migrates existing comments at startup in one transaction, then
starts Flask. Repeated starts authenticate existing ciphertext without encrypting it twice.
A wrong key or damaged ciphertext aborts startup and rolls back that transaction.
Back up the database before migrating an existing non-disposable installation.

Storage is `aesgcm:v1:` followed by Base64(nonce || ciphertext || authentication tag).
Each write gets a fresh 12-byte random nonce. The version, column purpose and note ID
are authenticated as AAD, so copying a comment ciphertext to another note fails too.
New records obtain an ID and encrypt the comment within the same transaction.
Dashboard, teacher page, JSON details and CSV exports decrypt only at the application boundary.
Plaintext fallback is forbidden in normal reads. NULL remains NULL and empty strings are encrypted.

Scope: the comment column only. Grades, names, old external backups and authorized
exports remain readable. A compromised running app can still use its key. Encryption
at rest does not fix the course's remaining authorization, XSS or JWT weaknesses.
The legacy seed file deliberately remains a teaching fixture; startup encrypts its DB copy.

Validation: `python -m unittest discover -s tests -v`. Tests cover Unicode, empty/NULL,
nonce variation, altered ciphertext, the wrong key, record swaps and missing keys.

Docker verification on 2026-10-22: all 60 seed comments encrypted; repeat migration
changed 0 rows. Student dashboard/API, teacher page/CSV, new grade and empty-comment
update passed. Test-created grade removed afterward. Reproduce with:

```sh
docker compose -p notesapp-course -f docker-compose.yml -f docker-compose.lab.yml up -d --build
docker cp tests/integration_comments.py notesapp-course-web-1:/tmp/integration_comments.py
docker exec -e NOTESAPP_TEST_DATABASE=1 notesapp-course-web-1 python /tmp/integration_comments.py
```
