import json,subprocess,datetime,os,sys,re,hashlib
root=os.path.dirname(os.path.dirname(__file__))
r=subprocess.run([sys.executable,'-m','pytest','-q','tests/test_gate1.py'],cwd=root,text=True,capture_output=True)
out=r.stdout+r.stderr

# Each canonical G1 ID must have a named executable test.
# Extra adversarial tests may share a G1 prefix.
canonical=[f'G1-{i:02d}' for i in range(1,13)]

col=subprocess.run(
    [sys.executable,'-m','pytest','--collect-only','-q','tests/test_gate1.py'],
    cwd=root,text=True,capture_output=True
)
collected=col.stdout+col.stderr

results=[]
for tid in canonical:
    token='test_'+tid.replace('-','_')
    present=token in collected
    result='PASS' if (r.returncode==0 and present) else ('MISSING' if not present else 'FAIL')
    results.append({
        'test_id':tid,
        'result':result,
        'build':'0.1.0',
        'test_suite':'1.2'
    })

allpass=all(x['result']=='PASS' for x in results) and r.returncode==0

manifest={
    'build':'0.1.0',
    'sonny_core':'1.0',
    'database_schema':'1.1',
    'project_state_schema':'1',
    'memory_schema':'1',
    'host_model':'stub-local',
    'test_suite':'1.2',
    'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'disposition':'GATE_1_FUNCTIONAL_PASS' if allpass else 'GATE_1_FAIL',
    'evidence_scope':'local functional contract tests plus direct-identifier authorization/isolation tests; not independent security review, deployed-environment validation, or real host-model validation',
    'results':results,
    'pytest':out,
    'collected_tests':collected
}

os.makedirs(os.path.join(root,'evidence'),exist_ok=True)

mp=os.path.join(root,'evidence','manifest.json')
sp=os.path.join(root,'evidence','summary.md')

open(mp,'w').write(json.dumps(manifest,indent=2))

open(sp,'w').write(
    f"# Gate-1 Evidence\n\n"
    f"Disposition: **{manifest['disposition']}**\n\n"
    f"Scope: {manifest['evidence_scope']}.\n\n"
    f"Canonical G1 checks: {sum(x['result']=='PASS' for x in results)}/12 PASS.\n\n"
    f"A pilot-release Gate-1 PASS is intentionally not claimed yet.\n\n"
    f"```\n{manifest['pytest']}\n```\n"
)

print(json.dumps({
    'disposition':manifest['disposition'],
    'canonical_pass':sum(x['result']=='PASS' for x in results),
    'manifest':mp
},indent=2))

sys.exit(0 if allpass else 1)
