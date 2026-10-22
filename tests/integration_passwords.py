"""Run only against the disposable notesapp-course DB, before other logins migrate alice."""
import json
import os
import sys
sys.path.insert(0,'/app')
from app import app,get_db
from passwords import ph
assert os.environ.get('NOTESAPP_TEST_DATABASE')=='1'
conn=get_db();cur=conn.cursor()
def stored(name):
    cur.execute('SELECT password FROM users WHERE username=%s',(name,))
    return cur.fetchone()['password']
client=app.test_client()
before=stored('alice')
assert client.post('/login',data={'username':'alice','password':'wrong'}).status_code==200
assert stored('alice')==before
assert client.post('/login',data={'username':'alice','password':'alicepw'}).status_code==302
after=stored('alice')
assert after.startswith('$argon2id$') and ph.verify(after,'alicepw')
assert b'My grades' in client.get('/dashboard').data
client.get('/logout')
assert client.post('/login',data={'username':'alice','password':'alicepw'}).status_code==302
assert stored('alice')==after
client.get('/logout')
assert client.post('/login',data={'username':'alice','password':'wrong'}).status_code==200
assert client.get('/dashboard').status_code==302
admin=app.test_client()
assert admin.post('/login',data={'username':'admin','password':'admin123'}).status_code==302
name='course_test_argon2'
cur.execute('SELECT id FROM users WHERE username=%s',(name,));assert cur.fetchone() is None
try:
    assert admin.post('/admin/users',data={'action':'create','username':name,'password':'test-only-秘密','role':'student'}).status_code==302
    hashed=stored(name);assert hashed.startswith('$argon2id$') and ph.verify(hashed,'test-only-秘密')
    assert client.post('/login',data={'username':name,'password':'test-only-秘密'}).status_code==302
finally:
    cur.execute('DELETE FROM users WHERE username=%s',(name,))
cur.execute("SELECT count(*) AS n FROM users WHERE password LIKE '$argon2id$%'")
print(json.dumps({'alice_was_legacy':not before.startswith('$argon2'),'alice_now_argon2id':True,
                  'wrong_password_does_not_migrate':True,'second_login_passed':True,
                  'new_account_hashed_at_creation':True,'migrated_accounts':cur.fetchone()['n']},indent=2))
conn.close()
