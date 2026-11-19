# KinSight repository guide

- Use fictional fixtures or approved public examples. Keep real patient records out of development, logs and repository artifacts.
- `services/genetics/` owns deterministic calculations. `services/consent/` owns the default-deny policy and audit trail. `services/api/` exposes the workflow. `web/` renders the results and review controls.
- Enforce ownership and consent before reading sensitive data. Project only allowed fields and audit the decision.
- Hold complex findings for counsellor review. Show educational estimate labels next to risk figures and use neutral language.
- Follow the commands in [CONTRIBUTING.md](CONTRIBUTING.md). Add a focused regression test for consent, parsing, corrections, or release behavior when those contracts change.
