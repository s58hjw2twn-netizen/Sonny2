from sonny_one.runtime import SonnyOneRuntime
from sonny_one.learning import Experience

def test_end_to_end_isolated_runtime(tmp_path):
    runtime = SonnyOneRuntime(str(tmp_path/"runtime.db"))
    runtime.remember_confirmed("a", "Prefers clear summaries", "user", consent=True)
    for _ in range(5):
        runtime.record_outcome(Experience("summaries","structured-summary",True,True,"verified-test"))
    a = runtime.inspect("a", uncertainty=.8, novelty=.3)
    b = runtime.inspect("b")
    assert a.recalled == ("Prefers clear summaries",)
    assert b.recalled == ()
    assert a.proposed_strategies == ("structured-summary",)
    assert a.identity == "sonny-one-research"
