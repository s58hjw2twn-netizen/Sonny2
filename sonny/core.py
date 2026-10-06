CORE_VERSION="1.0"

def respond(project, memories, message):
    low=message.lower()

    if "remember" in low or "told you" in low or "what is my" in low:
        for m in memories:
            if m['value'].lower() in low or any(
                w in low
                for w in m['value'].lower().split()
                if len(w)>4
            ):
                return {
                    "text":m['value'],
                    "answer_state":"KNOWN",
                    "memory_proposal":None
                }

        return {
            "text":"I don't have that in the approved project state or memory.",
            "answer_state":"UNKNOWN",
            "memory_proposal":None
        }

    return {
        "text":f"For {project['name']}, a useful next step is to clarify the next concrete decision toward: {project['goal']}",
        "answer_state":"INFERRED",
        "memory_proposal":None
    }
