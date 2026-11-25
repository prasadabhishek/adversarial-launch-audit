---
name: adversarial-launch-audit
description: >-
  Runs a structured multi-angle pre-launch red-team QA audit for mobile and web
  apps: automated localization/i18n key parity checks, Android/web permission
  and debug-flag inspection, edge-case permutation test matrix, and App Store /
  Play Store submission readiness checklist. Use before shipping a new app
  release or when asking for an unfiltered adversarial product review.
---

# Adversarial Launch Audit

## Overview

Acts as an unfiltered red-team QA and customer review board before you ship. Combines programmatic repo checks (i18n key parity, dangerous permissions, leftover debug/placeholder strings) with a structured multi-cohort adversarial review protocol (QA engineers + first-time users + accessibility/power-user personas) and store submission gate.

## Quick Start

```bash
# 1. Automated i18n/localization key parity check (Android strings.xml or JSON locale files)
uv run scripts/launch_audit.py i18n --root /path/to/repo --output /tmp/i18n-audit.json

# 2. Pre-release hygiene scan (permissions, debuggable flags, hardcoded localhost/TODOs)
uv run scripts/launch_audit.py hygiene --root /path/to/repo --output /tmp/hygiene-audit.json
```

## Utility Scripts

`scripts/launch_audit.py` uses Python 3 standard library only.

### Subcommands
- **`i18n --root <dir> --output <path.json>`**: Discovers Android `values*/strings.xml` and/or JSON locale files (`locales/*.json`), compares every locale against the base locale, and reports missing keys, extra orphan keys, and untranslated identical strings.
- **`hygiene --root <dir> --output <path.json>`**: Inspects `AndroidManifest.xml` (permissions, `android:debuggable`, `usesCleartextTraffic`, exported components) and scans source files for `TODO`/`FIXME`, hardcoded `http://localhost`, and placeholder package IDs (`com.example.*`).

## Workflow

1. **Automated Static Gates:** Run `launch_audit.py i18n` and `launch_audit.py hygiene`. Fix any missing localization keys, unintended `INTERNET`/sensitive permissions, or `debuggable=true` flags.
2. **Build & Real-Device E2E Baseline:** Run the project's real build/test command (e.g., `./gradlew test`, `npm run build`) and verify both portrait and landscape layouts.
3. **Adversarial Multi-Persona Review:** Evaluate the app harshly from 4 distinct lenses:
   - **Cold First-Time User:** Confusing labels, fake/decorative UI pretending to be functional, onboarding friction.
   - **Edge-Case QA Matrix:** Offline mode, rapid rotation, dark/light/high-contrast themes, empty states, font scaling (200%).
   - **Privacy & Permission Honesty:** Does the app request `INTERNET` or location/camera permissions it doesn't strictly need?
   - **Store Submission Gate (Play Store / App Store):** `targetSdk` compliance, release signing config, privacy policy URL, accurate store screenshots, data safety form parity.
4. **Ship-Blocker Report:** Rank findings as **P0 Ship-Blocker**, **P1 High-Friction**, or **P2 Polish** with concrete file paths and fixes.

## Common Mistakes

- **Rubber-stamping your own app:** Actively hunt for "makes no sense" UI elements, fake instrumentation, and contradictory settings.
- **Shipping with partial translations:** One missing key in `values-es/strings.xml` silently falls back to English mid-screen.
- **Skipping landscape & large-font permutations:** Most layout overflows only appear in landscape or 1.5×–2.0× accessibility font scale.
