"""Class 7 regressions: two old forgeries fail and real login still works."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))
with patch.dict(os.environ, {"JWT_SECRET": secrets.token_hex(32)}):
    import app as notesapp


def encode(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()


def token(header, payload, key=None):
    message = f"{encode(header)}.{encode(payload)}"
    signature = ""
    if key is not None:
        signature = base64.urlsafe_b64encode(
            hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
    return f"{message}.{signature}"


class JWTTests(unittest.TestCase):
    identity = {"user_id": 1, "username": "alice", "role": "student"}

    def test_two_old_forgeries_are_unauthorized(self):
        admin = {"user_id": 1, "username": "admin", "role": "admin"}
        for forged in (
            token({"alg": "none"}, admin),
            token({"alg": "HS256"}, admin, "s3cr3t"),
        ):
            with self.subTest(token=forged), patch.object(notesapp, "get_db") as db:
                self.assertIsNone(notesapp.verify_jwt(forged))
                client = notesapp.app.test_client()
                # Invalid explicit Bearer credentials must not fall back to a cookie.
                with client.session_transaction() as session:
                    session.update(self.identity)
                response = client.get("/api/notes/1", headers={"Authorization": f"Bearer {forged}"})
                self.assertEqual(response.status_code, 401)
                db.assert_not_called()

    def test_only_exact_hs256_is_allowed(self):
        for alg in ("none", "NONE", "hs256", "HS384", "RS256", None, ["HS256"]):
            with self.subTest(alg=alg):
                self.assertIsNone(notesapp.verify_jwt(
                    token({"alg": alg}, self.identity, notesapp.JWT_SECRET)))

    def test_valid_signature_and_tampering(self):
        valid = notesapp.make_jwt(self.identity)
        self.assertEqual(notesapp.verify_jwt(valid), self.identity)
        h, p, sig = valid.split(".")
        self.assertIsNone(notesapp.verify_jwt(
            f"{h}.{encode(dict(self.identity, role='admin'))}.{sig}"))
        self.assertIsNone(notesapp.verify_jwt(f"{h}.{p}."))
        self.assertIsNone(notesapp.verify_jwt(f"{h}.{p}.秘密"))

    def test_malformed_tokens_fail_closed(self):
        for value in (None, "", "a.b", "a.b.c.d", "!.!.!",
                      token([], self.identity), token({"alg": "HS256"}, [])):
            with self.subTest(value=value):
                self.assertIsNone(notesapp.verify_jwt(value))

    def test_normal_login_issues_usable_token(self):
        conn = MagicMock()
        conn.cursor.return_value.rowcount = 1
        conn.cursor.return_value.fetchone.return_value = {
            "id": 1, "username": "alice", "role": "student", "password": "alicepw",
        }
        with patch.object(notesapp, "get_db", return_value=conn):
            client = notesapp.app.test_client()
            response = client.post("/login", data={"username": "alice", "password": "alicepw"})
        self.assertEqual(response.status_code, 302)
        with client.session_transaction() as session:
            issued = session["token"]
        self.assertEqual(notesapp.verify_jwt(issued), self.identity)
        with notesapp.app.test_request_context(headers={"Authorization": f"Bearer {issued}"}):
            self.assertEqual(notesapp.current_identity(), self.identity)

    def test_missing_or_weak_key_prevents_startup(self):
        for key in (None, "s3cr3t"):
            env = dict(os.environ, PYTHONPATH=str(Path(notesapp.__file__).parent))
            env.pop("JWT_SECRET", None)
            if key is not None:
                env["JWT_SECRET"] = key
            result = subprocess.run([sys.executable, "-c", "import app"], env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("JWT_SECRET must be at least 32 bytes", result.stderr)


if __name__ == "__main__":
    unittest.main()
