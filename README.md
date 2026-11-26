# Adversarial Launch Audit

Agent skill and Python 3 stdlib CLI for running unfiltered pre-launch QA reviews: i18n/localization key parity checks, Android/web permission & release hygiene scans, edge-case permutation matrices, and App Store / Play Store submission gates.

## Install as an Agent Skill

```bash
npx skills add prasadabhishek/adversarial-launch-audit
```

## Standalone CLI Usage

```bash
uv run scripts/launch_audit.py i18n --root /path/to/repo --output /tmp/i18n.json
uv run scripts/launch_audit.py hygiene --root /path/to/repo --output /tmp/hygiene.json
```

## License

MIT

---
Built by [Abhishek Prasad](https://abhishekprasad.fyi)
