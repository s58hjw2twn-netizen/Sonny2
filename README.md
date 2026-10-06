# Sonny Assistant 0.1.0 — Project Co-Pilot

Canonical MVP reconstruction implementing the frozen Gate-1 contracts: isolated users/projects, versioned project state, explicit provenance memory lifecycle, structured next actions, runtime traces, and evidence generation.

## Run
```bash
python -m pip install -r requirements.txt
uvicorn sonny.app:app --reload
python evaluation/run_gate1.py
Commit the change to `main`, then tell me **“next file.”**
