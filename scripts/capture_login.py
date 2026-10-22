"""Capture only a local course login at the container's ingress (no unrelated host traffic)."""
import argparse
import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import ssl

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('mode',choices=['http','https'])
a=p.parse_args()
container='notesapp-course-web-1' if a.mode=='http' else 'notesapp-course-nginx-1'
port='5000' if a.mode=='http' else '443'
out=Path(__file__).resolve().parents[1]/'docs'/'evidence'
out.mkdir(parents=True,exist_ok=True)
raw=out/f'login-{a.mode}.pcap'
# Install tcpdump in this disposable container before running this script.
subprocess.run(['docker','exec','-d',container,'sh','-c',f'tcpdump -i eth0 -U -w /tmp/login.pcap tcp port {port} & echo $! > /tmp/notesapp-capture.pid; wait'],check=True)
try:
    time.sleep(1)
    url='http://127.0.0.1:8080/login' if a.mode=='http' else 'https://localhost/login'
    context=ssl.create_default_context(cafile=str(out.parents[1]/'nginx/certs/notesapp.crt')) if a.mode=='https' else None
    req=urllib.request.Request(url,data=b'username=alice&password=alicepw')
    with urllib.request.urlopen(req,context=context,timeout=10) as r:
        status=r.status
    time.sleep(1)
finally:
    subprocess.run(['docker','exec',container,'sh','-c','kill -INT "$(cat /tmp/notesapp-capture.pid)"'],check=True)
    time.sleep(.5)
subprocess.run(['docker','cp',container+':/tmp/login.pcap',str(raw)],check=True)
data=raw.read_bytes()
visible=b'username=alice&password=alicepw' in data
assert visible == (a.mode=='http')
result={'mode':a.mode,'capture_point':container+' eth0 TCP '+port,'login_final_status':status,
        'capture_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
        'test_credentials_visible_in_capture':visible,
        'credential_excerpt':'username=alice&password=alicepw' if visible else None,
        'method':'tcpdump packet capture; HTTPS validated against the explicit local certificate, not -k'}
(out/f'{a.mode}-capture.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
