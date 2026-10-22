"""Exercise migration rollback on a disposable course DB; restore seed rows in finally."""
import base64
import os
import sys
sys.path.insert(0,'/app')
from app import get_db
from migrate_comments import migrate
assert os.environ.get('NOTESAPP_TEST_DATABASE')=='1'
conn=get_db();cur=conn.cursor()
cur.execute('SELECT id, comment FROM notes ORDER BY id');original=cur.fetchall()
key=os.environ['COMMENT_KEY_B64']
try:
    os.environ['COMMENT_KEY_B64']=base64.b64encode(os.urandom(32)).decode()
    try:migrate()
    except Exception:pass
    else:raise AssertionError('wrong key accepted')
    cur.execute('SELECT id, comment FROM notes ORDER BY id');assert cur.fetchall()==original
    os.environ['COMMENT_KEY_B64']=key
    # A prior row would be encrypted before the final corrupted row is encountered.
    cur.execute('UPDATE notes SET comment=%s WHERE id=%s',('legacy test text',original[0]['id']))
    cur.execute('UPDATE notes SET comment=%s WHERE id=%s',('aesgcm:v1:invalid',original[-1]['id']))
    try:migrate()
    except Exception:pass
    else:raise AssertionError('corruption accepted')
    cur.execute('SELECT comment FROM notes WHERE id=%s',(original[0]['id'],))
    assert cur.fetchone()['comment']=='legacy test text', 'partial migration was committed'
finally:
    os.environ['COMMENT_KEY_B64']=key
    for row in (original[0],original[-1]):
        cur.execute('UPDATE notes SET comment=%s WHERE id=%s',(row['comment'],row['id']))
    conn.close()
print('PASS: wrong key changes no rows; later corruption rolls back earlier migrated rows; originals restored.')
