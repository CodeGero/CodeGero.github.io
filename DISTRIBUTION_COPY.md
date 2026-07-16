# Distribution copy — kryptorious-pipeguard (post these yourself; agent cannot use your social accounts)

## Product
**kryptorious-pipeguard** — a CI/CD pipeline security linter for GitHub Actions and GitLab CI.
Catch the misconfigs that turn a CI runner into a supply-chain attack vector *before* they ship.

- Detects `pull_request_target` + untrusted-checkout secret exfil (PRT-001)
- Missing least-privilege `permissions` blocks (PERM-001)
- Hardcoded AWS/generic secrets (SEC-001)
- Unpinned action/image refs (IMG-001 / GL-IMG-001)
- GitLab plaintext secrets in `variables` (GL-SEC-001)
- Outputs table / `--json` / `--sarif` (GitHub code scanning)
- CI exit-code gate: exits 1 on any error-severity finding

Install: `pip install kryptorious-pipeguard`
GitHub: https://github.com/CodeGero/kryptorious-pipeguard
PyPI: https://pypi.org/project/kryptorious-pipeguard/

---

## Hacker News (show mode)
Title: Show HN: pipeguard – a CI/CD security linter for GitHub Actions and GitLab CI

Body:
I kept seeing CI pipelines that hand broad token scope to `pull_request_target`
workflows or check out attacker-controlled PR refs. One misconfig and a fork PR
exfiltrates your secrets. So I wrote a small linter that scans `.github/workflows`
and `.gitlab-ci.yml` for exactly that class of bug.

It flags:
- pull_request_target + checkout of pull_request.head.ref (secret-exfil path)
- missing permissions block (broad default GITHUB_TOKEN scope)
- hardcoded AWS/generic secrets
- unpinned action/image refs (mutable tags)
- GitLab plaintext secrets in variables

Outputs a table, --json, or SARIF 2.1.0 for GitHub code scanning, and exits 1
on any error so you can drop it straight into a CI gate.

pip install kryptorious-pipeguard
https://github.com/CodeGero/kryptorious-pipeguard

Not another 50MB SAST suite — it's ~14KB and checks the specific CI footguns
that show up constantly in real repos. Feedback / rule requests welcome.

---

## r/Python
Title: [Project] pipeguard — catch CI/CD secret-exfil misconfigs in GitHub Actions & GitLab

Body:
Sharing a small tool I built after reviewing too many pipelines that leak
secrets via `pull_request_target`. pipeguard scans your CI definitions for the
specific misconfigurations that turn a runner into an attack vector:

- PRT-001: pull_request_target + untrusted checkout (fork PR runs with your secrets)
- PERM-001: no explicit permissions block
- SEC-001: hardcoded credentials
- IMG-001 / GL-IMG-001: unpinned action/image refs
- GL-SEC-001: GitLab plaintext secrets

`pipeguard check .` prints a table; `--sarif` drops a SARIF file for code
scanning; it exits 1 on errors so it works as a CI gate.

pip install kryptorious-pipeguard
GitHub: https://github.com/CodeGero/kryptorious-pipeguard

MIT licensed. Happy to add rules if there's a gap I missed.

---

## dev.to (technical post)
Title: Your pull_request_target Workflow Is Probably Leaking Secrets

Hook: A forked PR shouldn't be able to read your production secrets. With one
common misconfiguration, it can. Here's the pattern and a 14KB linter that
catches it.

(Post walks through the PRT-001 vuln, shows a vulnerable workflow, shows the
pipeguard output, links install + repo. ~600 words. Source: verified local
behavior + README examples — no invented benchmarks.)

---

NOTE: Do NOT claim download counts, revenue, customers, or "AI-powered."
Every claim above maps to shipped, test-covered code.
