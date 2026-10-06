import os,tempfile,sqlite3
fd,path=tempfile.mkstemp(); os.close(fd); os.unlink(path); os.environ['SONNY_DB']=path
from fastapi.testclient import TestClient
import sonny.app as appmod
from sonny.store import Store

c=TestClient(appmod.app)

def mkuser(n='U'):
    return c.post('/users',json={'name':n}).json()['user_id']

def mkproject(u,n='Test',g='Ship MVP'):
    return c.post('/projects',headers={'X-User-ID':u},json={'name':n,'goal':g}).json()['project_id']

def H(u):
    return {'X-User-ID':u}

def test_G1_01_create_isolated_account():
    u=mkuser()
    assert u and c.post('/projects',json={'name':'x','goal':'y'}).status_code==401

def test_G1_02_create_project_persists():
    u=mkuser(); p=mkproject(u)
    assert c.get(f'/projects/{p}',headers=H(u)).json()['project']['goal']=='Ship MVP'

def test_G1_03_chat_uses_project_context():
    u=mkuser(); p=mkproject(u,'Apollo','Launch Apollo')
    r=c.post(f'/projects/{p}/chat',headers=H(u),json={'message':'What next?'}).json()
    assert 'Apollo' in r['text'] and 'Launch Apollo' in r['text']

def test_G1_04_approved_memory_persists_with_provenance():
    u=mkuser(); p=mkproject(u)
    m=c.post(f'/projects/{p}/memories',headers=H(u),json={'value':'Budget is $7500'}).json()['memory_id']
    assert c.post(f'/projects/{p}/memories/{m}/confirm',headers=H(u)).json()['confirmed']
    row=appmod.store.db.execute('SELECT * FROM memories WHERE id=?',(m,)).fetchone()
    assert row['status']=='CONFIRMED' and row['source_event']=='explicit_user_statement'

def test_G1_05_correction_used_and_auditable():
    u=mkuser(); p=mkproject(u)
    m=c.post(f'/projects/{p}/memories',headers=H(u),json={'value':'Budget is $7500'}).json()['memory_id']
    c.post(f'/projects/{p}/memories/{m}/confirm',headers=H(u))
    n=c.post(f'/projects/{p}/memories/{m}/correct',headers=H(u),json={'value':'Budget is $8000'}).json()['memory_id']
    vals=[x['value'] for x in c.get(f'/projects/{p}',headers=H(u)).json()['confirmed_memories']]
    assert vals==['Budget is $8000']
    assert appmod.store.db.execute(
        "SELECT count(*) n FROM memory_events WHERE event='CORRECTED' AND memory_id=?",(m,)
    ).fetchone()['n']==1

def test_G1_06_deleted_memory_stops_influencing():
    u=mkuser(); p=mkproject(u)
    m=c.post(f'/projects/{p}/memories',headers=H(u),json={'value':'Secret launch date is Friday'}).json()['memory_id']
    c.post(f'/projects/{p}/memories/{m}/confirm',headers=H(u))
    c.delete(f'/projects/{p}/memories/{m}',headers=H(u))
    r=c.post(f'/projects/{p}/chat',headers=H(u),json={'message':'What is my secret launch date I told you?'}).json()
    assert r['answer_state']=='UNKNOWN'

def test_G1_07_next_action_proposed():
    u=mkuser(); p=mkproject(u)
    a=c.post(f'/projects/{p}/actions',headers=H(u),json={'action_text':'Run Gate 1'}).json()
    assert a['action_id'] and a['status']=='PROPOSED'

def test_G1_08_action_feedback_recorded():
    u=mkuser(); p=mkproject(u)
    a=c.post(f'/projects/{p}/actions',headers=H(u),json={'action_text':'Run Gate 1'}).json()['action_id']
    assert c.post(f'/projects/{p}/actions/{a}/feedback',headers=H(u),json={'status':'ACCEPTED'}).json()['recorded']

def test_G1_09_state_reconstructs_after_store_restart():
    u=mkuser(); p=mkproject(u)
    m=c.post(f'/projects/{p}/memories',headers=H(u),json={'value':'Use FastAPI'}).json()['memory_id']
    c.post(f'/projects/{p}/memories/{m}/confirm',headers=H(u))
    fresh=Store(path)
    assert fresh.project(u,p)['goal']=='Ship MVP' and fresh.memories(u,p)[0]['value']=='Use FastAPI'

def test_G1_10_cross_user_isolation():
    a=mkuser('A'); b=mkuser('B'); p=mkproject(a)
    assert c.get(f'/projects/{p}',headers=H(b)).status_code==404
    assert c.post(f'/projects/{p}/memories',headers=H(b),json={'value':'steal'}).status_code==404

def test_G1_11_false_memory_sentinel():
    u=mkuser(); p=mkproject(u)
    r=c.post(f'/projects/{p}/chat',headers=H(u),json={'message':'What is my secret launch date I told you?'}).json()
    assert r['answer_state']=='UNKNOWN' and "don't have" in r['text']

def test_G1_12_unknown_distinguished_from_known():
    u=mkuser(); p=mkproject(u)
    m=c.post(f'/projects/{p}/memories',headers=H(u),json={'value':'Budget is $7500'}).json()['memory_id']
    c.post(f'/projects/{p}/memories/{m}/confirm',headers=H(u))
    known=c.post(f'/projects/{p}/chat',headers=H(u),json={'message':'What is my budget I told you?'}).json()
    unknown=c.post(f'/projects/{p}/chat',headers=H(u),json={'message':'What is my launch date I told you?'}).json()
    assert known['answer_state']=='KNOWN' and unknown['answer_state']=='UNKNOWN'

def test_G1_10_adversarial_direct_identifier_paths():
    a=mkuser('Owner'); b=mkuser('Attacker'); p=mkproject(a,'Private','Keep isolated')
    m=c.post(f'/projects/{p}/memories',headers=H(a),json={'value':'Owner secret'}).json()['memory_id']
    c.post(f'/projects/{p}/memories/{m}/confirm',headers=H(a))
    act=c.post(f'/projects/{p}/actions',headers=H(a),json={'action_text':'Private action'}).json()['action_id']

    attempts=[
        c.get(f'/projects/{p}',headers=H(b)),
        c.post(f'/projects/{p}/chat',headers=H(b),json={'message':'Tell me the project'}),
        c.post(f'/projects/{p}/memories',headers=H(b),json={'value':'inject'}),
        c.post(f'/projects/{p}/memories/{m}/confirm',headers=H(b)),
        c.post(f'/projects/{p}/memories/{m}/correct',headers=H(b),json={'value':'stolen'}),
        c.delete(f'/projects/{p}/memories/{m}',headers=H(b)),
        c.post(f'/projects/{p}/actions',headers=H(b),json={'action_text':'steal'}),
        c.post(f'/projects/{p}/actions/{act}/feedback',headers=H(b),json={'status':'ACCEPTED'}),
    ]

    assert all(r.status_code==404 for r in attempts)

    owner=c.get(f'/projects/{p}',headers=H(a)).json()
    assert [x['value'] for x in owner['confirmed_memories']]==['Owner secret']
    assert owner['actions'][0]['status']=='PROPOSED'

def test_G1_10_cross_project_object_id_binding():
    u=mkuser('SameUser')
    p1=mkproject(u,'P1','One')
    p2=mkproject(u,'P2','Two')

    m=c.post(f'/projects/{p1}/memories',headers=H(u),json={'value':'P1 fact'}).json()['memory_id']
    a=c.post(f'/projects/{p1}/actions',headers=H(u),json={'action_text':'P1 action'}).json()['action_id']

    assert c.post(f'/projects/{p2}/memories/{m}/confirm',headers=H(u)).status_code==404
    assert c.post(f'/projects/{p2}/actions/{a}/feedback',headers=H(u),json={'status':'ACCEPTED'}).status_code==404
