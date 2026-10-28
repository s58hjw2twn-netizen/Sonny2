"""Deterministic synthetic translation benchmark for the research-only estimator."""
from sonny_vision.quality.translation_search import estimate_translation


def run_translation_benchmark():
    cases = []
    pattern = [[.11,.83,.24],[.72,.36,.95],[.41,.64,.17]]
    for dx,dy in [(0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1)]:
        a = [[0.]*9 for _ in range(9)]
        b = [[0.]*9 for _ in range(9)]
        for y in range(3):
            for x in range(3):
                a[3+y][3+x] = pattern[y][x]
                b[3+y+dy][3+x+dx] = pattern[y][x]
        result = estimate_translation(a,b,(3,3,6,6),max_shift=1)
        cases.append({"expected":[dx,dy],"accepted":result["accepted"],
                      "correct":result["accepted"] and [result["dx"],result["dy"]]==[dx,dy]})
    flat = [[.5]*9 for _ in range(9)]
    rejected = estimate_translation(flat,flat,(3,3,6,6),max_shift=1)
    correct = sum(case["correct"] for case in cases)
    return {"synthetic_cases":len(cases),"correct":correct,
            "accuracy":correct/len(cases),"flat_rejected":not rejected["accepted"],
            "real_photo_validation":False,"identity_verified":False}
