# Sonny ONE Voice — model source review (candidate only)

No downloads, model execution, license approval, or installation have occurred.

## Speech recognition candidate
- Engine: ggml-org/whisper.cpp (official project: https://github.com/ggml-org/whisper.cpp)
- Candidate model: English `base.en`, ggml file `ggml-base.en.bin`.
- Official project documents the `base.en` model, approximately 142 MiB disk and ~388 MB model memory.
- Project model instructions: https://github.com/ggml-org/whisper.cpp/tree/master/models
- **Not approved for download yet.** The published model list contains a SHA-1 value; it is **not** a SHA-256 digest. Do not paste a SHA-1 into the SHA-256 manifest.
- Before download: select an immutable release or revision, verify code/model licensing, establish a trusted SHA-256 and exact byte count, and record provenance.

## Speech synthesis candidate
- Piper voices catalog: https://github.com/rhasspy/piper/blob/master/VOICES.md
- Candidate voice: `en_US-lessac-medium` (requires model ONNX and JSON config).
- Archived Piper implementation license: MIT (https://github.com/rhasspy/piper/blob/master/LICENSE.md).
- **Do not assume** that this license applies to newer maintained forks or to individual voice model weights.
- Read the exact voice's MODEL_CARD and select a commercial-compatible license before approving any asset.
- Model and config SHA-256 and sizes remain **unverified**.

## Acceptance evidence
For every binary/model/config record:
- Canonical upstream source and immutable revision
- License and commercial-use review, including voice/model license separately
- Verified SHA-256 and exact size, checked on the downloaded bytes
- Human owner approval before installation or downloads
- Reproducible Windows 11 CPU trial with measured transcript, audio, timings
- Independent network isolation and process restriction evidence

Do not label this candidate review as an approved manifest or live test.
