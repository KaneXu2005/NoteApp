"""Create missing local cryptographic keys without overwriting existing keys."""
import base64
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = root / '.env'
existing = p.read_text() if p.exists() else ''
names = {line.split('=',1)[0].strip() for line in existing.splitlines() if '=' in line}
missing = [n for n in ('COMMENT_KEY_B64','EXPORT_HMAC_KEY_B64','JWT_SECRET') if n not in names]
if missing:
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd,'w') as f:
        if existing and not existing.endswith('\n'): f.write('\n')
        for name in missing:
            f.write(name+'='+base64.b64encode(os.urandom(32)).decode()+'\n')
    os.chmod(p,0o600)
print('Local .env ready. Existing keys preserved. Back up this file separately from the database.')
