# Sonny ONE Voice — Windows 11 HP preflight

## Scope
This preflight gathers hardware and basic toolchain availability only. It does not
install software, fetch model weights, start audio capture, or prove sandboxing.

## Run
1. On your Windows 11 HP, open PowerShell (no administrator elevation required).
2. Download `scripts/sonny_voice_windows_preflight.ps1` from the **voice development branch** in the Sonny2 repository. Inspect the file before running.
3. In PowerShell, change to the folder containing the script.
4. Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\sonny_voice_windows_preflight.ps1`.

The execution-policy override applies only to this process; it does not alter
machine-wide policy. Do not run an uninspected script from an untrusted source.

## Review before sharing
The output may contain hardware identifiers and disk information. Do not share
serial numbers, usernames, local paths, device IDs, or other personal identifiers.
You can provide only CPU name, RAM GiB, GPU names, free disk GiB, Python and Git
availability, and the Windows version.

## Acceptance criteria
- Script exits successfully with valid JSON.
- Reported CPU, RAM and GPU match the HP's Windows settings.
- No changes to installed applications or Windows configuration.
- No claim of speech inference, microphone operation, or network isolation.

## Next gate
After hardware preflight, select exact engine/model versions and licenses,
obtain owner approval before downloads, verify checksums, and perform a
network-restricted real-audio trial. Keep all credentials out of GitHub.
