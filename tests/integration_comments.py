"""Run only against a disposable course seed database, inside the web container."""
import os
import sys
sys.path.insert(0, '/app')
from app import app, get_db
from migrate_comments import migrate
from crypto_utils import PREFIX, decrypt_comment

assert os.environ.get('NOTESAPP_TEST_DATABASE') == '1', 'Use an isolated seed database'
conn = get_db()
cur = conn.cursor()
cur.execute('SELECT id, comment FROM notes ORDER BY id')
before = cur.fetchall()
assert all(r['comment'] is None or r['comment'].startswith(PREFIX) for r in before)
assert migrate() == 0
cur.execute('SELECT id, comment FROM notes ORDER BY id')
assert cur.fetchall() == before
student = app.test_client()
assert student.post('/login', data={'username':'alice','password':'alicepw'}).status_code == 302
assert b'My grades' in student.get('/dashboard').data
assert student.get('/api/notes/1').json['comment'] == 'Late submission, but good quality.'
teacher = app.test_client()
assert teacher.post('/login', data={'username':'prof.turing','password':'teach123'}).status_code == 302
assert b'All grades' in teacher.get('/teacher').data
assert b'Late submission, but good quality.' in teacher.get('/export.csv').data
new_id = None
try:
    text = 'Integration test: \u8bc4\u8bed, "quoted"\nsecond line'
    cur.execute('SELECT max(id) AS id FROM notes'); previous = cur.fetchone()['id']
    assert teacher.post('/grades', data={'student_id':'6','class_id':'1','grade':'12.5','comment':text}).status_code == 302
    cur.execute('SELECT id, comment FROM notes WHERE id > %s', (previous,))
    row = cur.fetchone(); new_id = row['id']
    assert row['comment'].startswith(PREFIX) and decrypt_comment(row['comment'],new_id)==text
    assert student.get(f'/api/notes/{new_id}').json['comment']==text
    assert teacher.post('/grades',data={'note_id':new_id,'grade':'13','comment':''}).status_code == 302
    assert student.get(f'/api/notes/{new_id}').json['comment']==''
finally:
    if new_id is not None: cur.execute('DELETE FROM notes WHERE id = %s',(new_id,))
    conn.close()
print(f'PASS: {len(before)} encrypted seed comments, repeatable migration, student/API/teacher/CSV reads, create/update.')
