# Sonny ONE: First real coding-model experiment

**Status:** Not yet run with a live model. The existing Python tests use mocked
HTTP responses. A passing CI run does **not** establish that a coding model
produced a valid patch.

## Preconditions

- Work on `research/apl-001` in a disposable local checkout, never `main`.
- Python and the repository test dependencies must already be available.
- Ollama must already be installed and listening on **127.0.0.1:11434**.
- A coding model must already be present locally. No download, subscription,
  GitHub credential, secret, or public deployment is part of this procedure.
- The operator explicitly opts into local inference. Never run an untrusted
  patch on the host directly.

## 1. Establish a green baseline

From the repository root:

```sh
python -m unittest discover -s tests -p 'test_sonny_one_*.py' -v
```

Record the full commit SHA and the test results. Stop on any failure.

## 2. Check the local model without running inference

```sh
python -c "from sonny_one.development_controller.local_model_preflight import check_local_model; print(check_local_model('YOUR_INSTALLED_MODEL', enabled=True))"
```

Replace `YOUR_INSTALLED_MODEL` with the **exact** name already shown by
Ollama. The result must contain `available: True`. This checks model
discovery only, not whether inference or patch generation works.

## 3. Request one review-only patch

Choose a new filename that does not already exist:

```sh
python -m sonny_one.development_controller.local_model_cli --model YOUR_INSTALLED_MODEL --output proposal-001.json --allow-local-model
```

This makes one explicit local inference request. The output is a JSON
artifact, **not** an executable patch or a verified code change. A local
model can return invalid JSON, an invalid diff, or a patch rejected by
policy; treat those as recorded failures, not successes.

## 4. Review and independently validate

- Check the candidate ID, diff text, and path. The model adapter permits
  **only** `sonny_one/apl_targets/offline_strategy.py`.
- Review the actual diff for correctness and unwanted behavior.
- In a disposable checkout, use `git apply --check` before applying
  anything. Never apply a generated diff to the primary checkout.
- If moving to the APL runner, first satisfy its separate preregistration,
  sandbox, held-out-test custody, and policy requirements. This command
  does not supply those requirements.
- Keep generated code out of production and frozen benchmark files.

## 5. Record evidence without overstating it

Record: baseline SHA, model name, model availability, generation result,
candidate SHA-256, policy decision, `git apply --check` outcome, sandbox
results, held-out results, and any human review. A proposal is **not**
an independently verified commit, and does **not** mark a development task
done. The receipt verifier applies only after a separately authorized
commit with matching GitHub CI evidence.

## Stop conditions

Stop if the model is absent, a request fails, a patch touches another path,
the patch does not apply cleanly, the sandbox or held-out evaluation fails,
or the independent verifier cannot establish the claimed commit and CI
results. Do not weaken these gates to obtain a passing demonstration.

## Known limitations

- No live model execution has been demonstrated.
- The proposal prompt is generic and does not yet include the actual source
  file or a detailed acceptance criterion. Its usefulness may be limited.
- Local model inference is opt-in and may use substantial computer resources.
- No unattended coding, automatic patch promotion, or production deployment
  is authorized by this runbook.
