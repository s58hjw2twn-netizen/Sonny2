# Sonny ONE — Windows 11 local-model pilot (not yet activated)

Target machine: HP OmniBook 7, Intel Core Ultra 7 258V, 32 GB RAM,
1 TB SSD, Windows 11. This is a local, owner-operated evaluation; it
does not deploy Sonny ONE or grant access to anyone on the network.

## Prerequisites (when owner is ready)

1. Install Ollama for Windows from https://ollama.com/download/windows
2. Install Git for Windows from https://git-scm.com/install/windows
3. Verify in PowerShell: `ollama --version` and `git --version`
4. Before downloading any model, verify the exact model version's
   redistribution, commercial-use, and derivative-training license.
   Record the model identifier, license URL, model file digest, and date.
5. Choose one small quantized model (roughly 3B–4B parameters) initially.
   Model selection is provisional until license and hardware tests pass.

## Local-only baseline checks

- Confirm the local service is listening on loopback, not on a LAN/public
  interface. Do not open firewall ports, configure port forwarding, or
  publish API keys.
- Confirm the machine has enough free disk space for the selected model.
- Use the official Ollama CLI to fetch the approved model. Downloading a
  model requires internet and storage; it is not done by repository code.
- Start with a short manual chat using `ollama run MODEL_NAME`.
- Measure warm/cold first-token latency, tokens per second, memory usage,
  response accuracy, and error behavior for at least 20 representative
  prompts. Keep test prompts free of passwords and private data.
- Repeat each representative task with identical settings where practical.
  Record model version, quantization, prompt, settings, timing, and outcome.

## Integration gate

The dormant modules `sonny_one/ollama_local.py` and
`sonny_one/ollama_text_model.py` are not automatically connected to
the web app. `ModelRouter` rejects models unless they are explicitly
approved, license-verified, available, and local. These metadata flags
are application policy inputs, **not** cryptographic proof of licensing
or actual availability. Owner review is required before activation.

Never expose the local Ollama port through GitHub Pages or a public
reverse proxy. Any future mobile access needs separate authenticated,
encrypted, rate-limited architecture and threat modeling.

## Acceptance criteria

- The approved model works locally without paid inference calls.
- Model license and provenance are recorded.
- Performance measurements are reproducible.
- Offline and invalid-response tests remain passing.
- No provider activation, public deployment, or research baseline changes
  occur as part of this pilot.
