"""Deterministic brightness and contrast stress cases for translation search."""
from sonny_vision.quality.translation_search import estimate_translation


def photometric_stress_benchmark():
    pattern=[[.12,.77,.23],[.69,.34,.91],[.43,.58,.17]]
    cases=[]
    for label,gain,bias in [("unchanged",1.,0.),("brighter",1.,.07),
                            ("darker",1.,-.07),("contrast",.8,.1)]:
        a=[[0.]*9 for _ in range(9)]
        b=[[0.]*9 for _ in range(9)]
        for y in range(3):
            for x in range(3):
                a[3+y][3+x]=pattern[y][x]
                b[3+y][4+x]=max(0.,min(1.,pattern[y][x]*gain+bias))
        result=estimate_translation(a,b,(3,3,6,6),max_shift=1)
        cases.append({"condition":label,"accepted":result["accepted"],
                      "correct":result["accepted"] and result["dx"]==1 and result["dy"]==0})
    return {"cases":cases,"total":len(cases),
            "correct":sum(case["correct"] for case in cases),
            "real_photo_validation":False}
