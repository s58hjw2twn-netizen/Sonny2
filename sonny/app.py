import os,time,uuid
from fastapi import FastAPI,Header,HTTPException
from pydantic import BaseModel
from .store import Store
from .core import respond,CORE_VERSION

app=FastAPI(title="Sonny Assistant",version="0.1.0")
store=Store(os.getenv("SONNY_DB","sonny.db"))

class UserIn(BaseModel): name:str
class ProjectIn(BaseModel): name:str; goal:str
class ChatIn(BaseModel): message:str
class MemoryIn(BaseModel): value:str; type:str="fact"
class CorrectionIn(BaseModel): value:str
class ActionIn(BaseModel): action_text:str; reason:str="Sonny next step"; source_response_id:str|None=None
class FeedbackIn(BaseModel): status:str

def user(x_user_id:str|None):
    if not x_user_id: raise HTTPException(401,"X-User-ID required")
    return x_user_id

def require_project(u,pid):
    p=store.project(u,pid)
    if not p: raise HTTPException(404)
    return p

@app.get('/health')
def health():
    return {"ok":True,"build":"0.1.0","core":CORE_VERSION}

@app.post('/users')
def users(b:UserIn):
    return {"user_id":store.create_user(b.name)}

@app.post('/projects')
def projects(b:ProjectIn,x_user_id:str|None=Header(None)):
    return {"project_id":store.create_project(user(x_user_id),b.name,b.goal)}

@app.get('/projects/{pid}')
def get_project(pid:str,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    p=require_project(u,pid)
    return {
        "project":p,
        "confirmed_memories":store.memories(u,pid),
        "actions":store.actions(u,pid)
    }

@app.post('/projects/{pid}/chat')
def chat(pid:str,b:ChatIn,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    p=require_project(u,pid)
    t=time.time()
    out=respond(p,store.memories(u,pid),b.message)
    rid=str(uuid.uuid4())
    latency=int((time.time()-t)*1000)
    store.trace(
        rid,u,pid,"stub-local",CORE_VERSION,p['state_version'],
        out['answer_state'],bool(out.get('memory_proposal')),
        bool(out.get('next_action')),latency,0.0
    )
    return {"response_id":rid,**out,"state_version":p['state_version']}

@app.post('/projects/{pid}/memories')
def propose_memory(pid:str,b:MemoryIn,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    require_project(u,pid)
    m=store.propose_memory(u,pid,b.value,b.type)
    return {"memory_id":m,"status":"PROPOSED"}

@app.post('/projects/{pid}/memories/{mid}/confirm')
def confirm(pid:str,mid:str,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    require_project(u,pid)
    if not store.confirm_memory(u,pid,mid):
        raise HTTPException(404)
    return {"confirmed":True}

@app.post('/projects/{pid}/memories/{mid}/correct')
def correct(pid:str,mid:str,b:CorrectionIn,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    require_project(u,pid)
    n=store.correct_memory(u,pid,mid,b.value)
    if not n:
        raise HTTPException(404)
    return {"memory_id":n,"status":"CONFIRMED"}

@app.delete('/projects/{pid}/memories/{mid}')
def delete(pid:str,mid:str,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    require_project(u,pid)
    if not store.delete_memory(u,pid,mid):
        raise HTTPException(404)
    return {"deleted":True}

@app.post('/projects/{pid}/actions')
def action(pid:str,b:ActionIn,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    require_project(u,pid)
    a=store.propose_action(u,pid,b.action_text,b.reason,b.source_response_id)
    return {"action_id":a,"status":"PROPOSED"}

@app.post('/projects/{pid}/actions/{aid}/feedback')
def feedback(pid:str,aid:str,b:FeedbackIn,x_user_id:str|None=Header(None)):
    u=user(x_user_id)
    require_project(u,pid)
    if not store.action_feedback(u,pid,aid,b.status):
        raise HTTPException(404)
    return {"recorded":True}
