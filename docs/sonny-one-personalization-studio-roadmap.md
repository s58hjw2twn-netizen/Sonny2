# Sonny ONE — Personalization Studio roadmap

Status: approved product requirement; partial data-model implementation only.
Owner approval: add to Sonny ONE ecosystem roadmap. No authorization to merge to main, deploy, incur paid API costs, or bypass existing security.

## Product objective
Give each customer control over the visual Sonny character and the arrangement of their personal dashboard. Customization must never change account permissions, approval gates, action verification, or access to another customer's data.

## Customer-facing requirements
- Character presets: Classic, Professional, Friendly, Minimal, and No Avatar.
- Future character expansion: optional approved custom avatars, subject to explicit consent, likeness rights, moderation, and safe asset handling.
- Theme presets: Midnight, Light, High Contrast; accessible typography and reduced-motion options.
- Dashboard: drag-and-drop reorder, resize, show/hide, reset to default, and responsive layouts for desktop and iPhone.
- Widget catalog: Voice, Projects, GitHub, Business, Vision, Creative Studio, Meemaw & Papa, Social Studio, Memory, Calendar, System, Activity.
- Per-customer persistence and authenticated cross-device synchronization.
- Accessible keyboard/touch equivalents for every drag interaction.
- Safe versioned layout migrations; preserve existing preferences when new widgets are introduced.

## Security and data rules
- Derive customer identity from authenticated server-side session, never from an untrusted client-supplied account identifier.
- Authorize every settings read/write. A hidden widget does not disable security alerts or approvals.
- Validate widget IDs, sizes, bounds, and layout payload limits on the server.
- Isolate all user preferences and custom assets; never expose another customer's avatars, photos, or settings.
- Do not accept executable markup, scripts, arbitrary URLs, or untrusted code as theme/avatar definitions.
- Provide explicit reset and deletion controls; do not store unnecessary biometric information.
- Separate visual customization from Sonny's underlying model, memory, tool authorization, and action execution.

## Implementation checkpoints
P0 (existing): pure Python validation model in sonny/personalization.py; tests in tests/test_personalization.py. Not yet independently run.
P1: authenticated settings endpoints, durable per-user database storage, migrations, and access-control tests.
P2: responsive drag/drop + resize + show/hide editor, accessible keyboard controls, save/reset.
P3: character preset renderer and themes, including high contrast and reduced motion.
P4: cross-device synchronization and conflict handling.
P5: independent regression, security, accessibility, and HP/iPhone usability testing.
P6: owner review before any production release or main-branch merge.

## Acceptance criteria
- Two authenticated customers cannot read or overwrite each other's layouts or avatar choices.
- Preferences persist across logout/login and synchronize correctly between supported devices.
- Invalid, oversized, overlapping, or malicious layout payloads are rejected safely.
- Changing avatar/theme/layout never authorizes a tool action or suppresses mandatory approvals.
- Drag/drop and resize work via touch and keyboard and remain usable at phone widths.
- Default/reset behavior is predictable and reversible where appropriate.
- Claims of completion require test logs and device evidence, not only a GitHub commit.

## Roadmap placement
Cross-cutting feature of Sonny ONE Core and the iPhone companion; deliver initial personalization during the Core/companion build, then advanced avatar options after secure account settings and accessible dashboard editing are validated.
