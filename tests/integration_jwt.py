"""HTTP smoke test against the local, disposable course instance (stdlib only)."""
import base64
import hashlib
import hmac
import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080"


def encode(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()


def forged(alg, key=None):
    message = f'{encode({"alg": alg, "typ": "JWT"})}.{encode({"user_id": 1, "role": "admin"})}'
    signature = ""
    if key:
        signature = base64.urlsafe_b64encode(
            hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
    return f"{message}.{signature}"


def api_status(opener, token):
    req = urllib.request.Request(BASE + "/api/notes/1",
                                 headers={"Authorization": "Bearer " + token})
    try:
        with opener.open(req, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


if __name__ == "__main__":
    anonymous = urllib.request.build_opener()
    results = {}
    for name, value in (("unsigned_forgery", forged("none")),
                        ("old_secret_forgery", forged("HS256", "s3cr3t"))):
        results[name] = api_status(anonymous, value)
        assert results[name] == 401, results

    client = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    data = urllib.parse.urlencode({"username": "alice", "password": "alicepw"}).encode()
    with client.open(BASE + "/login", data=data, timeout=10) as response:
        page = response.read().decode()
        assert response.url == BASE + "/dashboard" and "My grades" in page
        results["real_login_dashboard"] = response.status
    match = re.search(r"const TOKEN = (\"[^\"]+\");", page)
    assert match, "Login did not issue a dashboard token"
    issued = json.loads(match.group(1))
    results["real_login_bearer_api"] = api_status(anonymous, issued)
    assert results["real_login_bearer_api"] == 200, results
    results["invalid_bearer_with_cookie"] = api_status(client, forged("none"))
    assert results["invalid_bearer_with_cookie"] == 401, results
    print(json.dumps(results, indent=2))
