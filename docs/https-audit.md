# Class 5 — NotesApp transit audit

**Operator:** 汪芮. Individual execution; no partner identity or classroom prediction is fabricated.
**Date:** 2026-10-22. Course source: [Traffic-in-transit audit](https://kristenpire.github.io/epita-security-labs/class5/https-lab/).

## Finding 1 — readable credentials on HTTP

- Evidence: actual tcpdump capture contained `username=alice&password=alicepw`.
- Capture location: the dedicated web container's eth0, TCP 5000, reached through localhost:8080.
- Exposure: an observer able to capture the network path can read credentials and session data.
  Merely being on the same switched/encrypted Wi-Fi does not by itself guarantee capture access.
- Severity: **High**, because disclosure enables account impersonation.
- Fix: nginx terminates TLS; `ports: !reset []` removes the Flask 8080 bypass. HTTP port 80 redirects to HTTPS.

## Retest

The same course credentials were sent to https://localhost. A real packet capture at
nginx's eth0 TCP 443 contained no readable username/password pair. The client verified
the certificate against the explicit local certificate file, without disabling TLS checks.
This capture observes the encrypted leg, not the decrypted nginx-to-Flask leg.

| Check | Actual result |
|---|---|
| HTTP capture | 5,537 bytes; test credentials visible |
| HTTPS capture | 18,183 bytes; test credentials not visible |
| HTTPS login page | HTTP 200 |
| HTTP /login | HTTP 301, Location: https://localhost/login |
| Direct 8080 | connection refused after overlay |
| nginx configuration | `nginx -t` passed |
| Published app ports | nginx only, 127.0.0.1:80 and :443 |

Capture metadata and SHA-256 fingerprints: [HTTP](evidence/http-capture.json),
[HTTPS](evidence/https-capture.json). Raw captures remain local as
`docs/evidence/login-http.pcap` and `login-https.pcap` and are intentionally excluded
from Git because HTTP/session captures contain authentication material. They can be
opened in Wireshark for the required before/after screenshot. No Wireshark screenshot
is claimed here: this run used tcpdump because macOS denied access to its BPF device.

## Finding 2 — certificate trust

- GitHub's observed issuer: **Sectigo Public Server Authentication CA DV E36**, Sectigo Limited (GB).
  The system trust store accepted its certificate. See [record](evidence/github-certificate.json).
- Our issuer and subject: **CN=localhost**. See [record](evidence/local-certificate.txt).
- SAN includes localhost, 127.0.0.1 and ::1. The system trust store rejected it as self-signed;
  explicitly trusting the generated certificate for this one test allowed the connection.
- Verdict: encryption protects traffic, but server identity additionally requires a trusted
  binding between the host name and public key. A self-signed lab certificate has no public
  CA chain. A real deployment requires appropriate certificate issuance and validation.

TLS protects the browser-to-nginx leg. Internal HTTP still relies on Docker-network and
host isolation; a compromised container or host can observe it. The deployment remains a
teaching app with other intentionally vulnerable features.

## Reproduce

```sh
python3 scripts/setup_secrets.py
scripts/generate_cert.sh  # once; refuses to overwrite an existing private key
# HTTP baseline, dedicated disposable course project only:
docker compose -p notesapp-course -f docker-compose.yml -f docker-compose.lab.yml up -d --build
docker exec notesapp-course-web-1 sh -c 'apt-get update -qq && apt-get install -y -qq tcpdump'
python3 scripts/capture_login.py http
# Enable TLS without deleting the database volume:
docker compose -p notesapp-course -f docker-compose.yml -f docker-compose.lab.yml -f docker-compose.https.yml up -d --build
docker exec notesapp-course-nginx-1 sh -c 'apt-get update -qq && apt-get install -y -qq tcpdump'
python3 scripts/capture_login.py https
curl --cacert nginx/certs/notesapp.crt https://localhost/login
```

A fresh container lacks tcpdump, so reinstall it before re-capturing. Private keys and
certificates are ignored; each clone generates its own. Do not disable browser certificate
checks globally or deploy this self-signed course stack as a public service.
