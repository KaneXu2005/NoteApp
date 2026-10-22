"""Normal role visits through the local HTTPS proxy, with explicit certificate trust."""
import http.cookiejar
import json
import ssl
import urllib.request
import urllib.parse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
context=ssl.create_default_context(cafile=str(root/'nginx/certs/notesapp.crt'))
results=[]
for username,password,paths in [('alice','alicepw',['/dashboard','/api/notes/1']),
                                ('prof.turing','teach123',['/teacher','/export.csv?class_id=1']),
                                ('admin','admin123',['/admin'])]:
    opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=context),
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    data=urllib.parse.urlencode({'username':username,'password':password}).encode()
    with opener.open('https://localhost/login',data=data,timeout=10) as r:
        assert not r.url.endswith('/login')
    for path in paths:
        with opener.open('https://localhost'+path,timeout=10) as r:
            body=r.read()
            assert r.status==200 and not r.url.endswith('/login')
            if path.startswith('/export'):assert b'# HMAC-SHA256:' in body
            results.append({'user':username,'path':path,'status':r.status})
    opener.open('https://localhost/logout').close()
print(json.dumps(results,indent=2))
(root/'docs/evidence/https-role-smoke.json').write_text(json.dumps(results,indent=2)+'\n')
