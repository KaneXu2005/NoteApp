# Class 7 — Fix the Login

Prediction: **NO**. After the fix, neither old forged token should work.

Changes:

- `verify_jwt` accepts exactly `HS256` and requires a valid HMAC-SHA256 signature.
  Unsigned `none` tokens and all other algorithms are rejected.
- Invalid Bearer credentials return unauthorized, even when a session cookie exists.
- The hard-coded `s3cr3t` fallback is removed. Startup requires `JWT_SECRET` to
  contain at least 32 bytes. `scripts/setup_secrets.py` generates a missing secret
  from 32 cryptographically random bytes and preserves existing local keys.
- Docker Compose reads the secret from the ignored `.env`; the image no longer
  contains the old JWT key in its sample configuration file.

## Run

```sh
python3 scripts/setup_secrets.py
docker compose up -d --build
```

If a local `.env` already contains a weak or disclosed `JWT_SECRET`, replace that
entry with a newly generated value before restarting. Never commit it. Changing
the key invalidates existing JWTs; log in again to obtain a new one.

## Verify

With the application dependencies installed:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

`tests/test_jwt.py` checks both old forgeries against the protected API (401),
algorithm restrictions, payload tampering, malformed tokens, missing/weak secret
configuration, and the real login route with a mocked database. A normal login
must issue a token that passes verification. No live secrets or tokens are stored.

For the disposable local Docker instance using `docker-compose.lab.yml`, run
`python3 tests/integration_jwt.py` to exercise the real HTTP login and database.

Verified on 2026-10-30: all 13 unit tests passed. The isolated HTTP smoke test
returned 401 for the unsigned forgery and the old-secret forgery, 200 for the
normal login dashboard and its newly issued Bearer token, and 401 for an invalid
Bearer token even with a valid session cookie.

This completes the slide's JWT exercise. Other intentional teaching flaws remain
outside this change; this is not a claim that the whole application is secure.
