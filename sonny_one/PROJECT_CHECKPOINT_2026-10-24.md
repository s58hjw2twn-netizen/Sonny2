# Sonny ONE — cross-project checkpoint (2026-10-24)

## Verified engineering state
- Repository: s58hjw2twn-netizen/Sonny2
- Active experimental branch: research/apl-001
- Last verified research commit: ab9aff816a055e214484359e4cc0d17c3400b9f3
- Both **Sonny ONE Tests** and **APL experimental policy checks** passed at that commit.
- GPT-6 in ChatGPT generated a restricted RES-001 change to `sonny_one/apl_targets/offline_strategy.py`: `mean([])` raises `ValueError`; independent regression tests were added.
- Research APL includes patch-policy gates, source fingerprints, disposable candidate/baseline evaluation, lineage records, and Docker-based sandbox design. Do not infer that a live model-produced patch was independently run in Docker.
- Local Ollama proposal producer and static proposal verifier exist, but **no actual Ollama model is connected**.
- Main-branch scheduler: `.github/workflows/sonny-research-scheduler.yml`, configured for 00:17, 06:17, 12:17, 18:17 UTC, runs read-only research planning/validation. First scheduled execution is not yet independently verified.
- No autonomous coding/commit loop has been activated. ChatGPT GPT-6 is a session-bound coding assistant, not an unattended GitHub inference service.
- Prototype and application exist in repo but are not a verified production AI companion.

## Product tracks and user priorities
1. **Sonny ONE:** commercial AI companion with persistent memory, personalized interaction, browser/iPhone app, security-first design; genuine measurable recursive self-improvement remains a research objective, not an achieved capability.
2. **Sonny Vision:** live-presence photo restoration with original facial identity preserved; conventional non-generative face processing and stronger scene enhancement; side-by-side identity verification and explicit user approval before delivery.
3. **Secure With Scott:** daily vertical cinematic relationship-healing reels, seven per week, five hashtags, Facebook/Instagram/TikTok/X; 10,000-follower/180-day target.
4. **Swinging With Scott & Tammy:** separate lifestyle brand, daily cinematic reels, approved real-photo circular black/gold logo, five hashtags, platform growth tracking kept separate.
5. **Harbor & Honey:** premium 45-second live-action coffee/cafe commercial and affordable AI-assisted commercial video production concept; seek commercially licensed footage and music; professional pacing, typography and color.
6. **Sonny AI Presenter:** later project for user-likeness, synchronized AI speech, iPhone vertical video.

## Guardrails
- Routine free research-branch engineering approved.
- No merge of experimental code to main, public deployment, paid API/service, secret access, or frozen baseline modification without explicit approval.
- Scheduler-only workflow on main was explicitly approved.
- Require independent verification before describing a change as successful; never claim continuous autonomous work while ChatGPT is inactive.

## Next engineering actions
1. Confirm first actual scheduled workflow run and inspect artifact.
2. Implement a bounded, independently verified model-generated patch -> sandbox test -> commit pipeline.
3. Connect a genuine unattended inference source (local user-controlled runner or explicitly approved service); no assumption that GitHub Actions supplies a free model.
4. Harden security, test rollback and fail-closed conditions, document measured reliability.
5. Keep all other product tracks separate and avoid inventing unverified deliverables.
