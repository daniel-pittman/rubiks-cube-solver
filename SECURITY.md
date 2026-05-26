# Security Policy

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.** A public
issue discloses the problem before a fix is available.

Instead, use **GitHub Private Vulnerability Reporting**:

1. Go to the repository's **Security** tab.
2. Click **Report a vulnerability**.
3. Describe the issue, the impact, and steps to reproduce.

The maintainer will acknowledge the report, work on a fix, and coordinate a
disclosure timeline with you. `rubiks-cube-solver` is a local-only application
with no network service (the Flask web interface binds to localhost), so the
realistic threat surface is small — but reports are still welcome.

## Supported versions

Security fixes are applied to the latest release on the default branch and
shipped as patch releases on the 1.x line.

---

## Repository setup checklist (for maintainers)

The CI and review workflows in this repository are designed to be safe on a
**public** repository, but several protections cannot be committed as files —
they are GitHub repository settings. After creating the upstream repository,
a maintainer must apply all of the following:

### 1. Restrict fork pull-request workflows

**Settings → Actions → General → Fork pull request workflows from outside
collaborators** → set to **"Require approval for all outside collaborators"**.

This means a maintainer must approve each workflow run requested by an outside
contributor's PR, preventing drive-by Actions execution.

### 2. Require actions to be pinned to a full-length commit SHA

**Settings → Actions → General → "Require actions to be pinned to a full-length
commit SHA"** → enabled.

This backstops the manual SHA-pinning convention in every workflow file: the
repository refuses to accept workflow YAML that references actions by tag
(`@v4`) or branch (`@main`). Belt-and-suspenders against pin-discipline
regression as the project evolves.

### 3. Branch protection on `main` and `develop`

For **both** the `main` and `develop` branches (Settings → Branches → Add
branch protection rule):

- Require a pull request before merging.
- Require **1 approving review**.
- **Dismiss stale pull-request approvals when new commits are pushed.**
- Require status checks to pass before merging — select the **`test`** check
  from the CI workflow (one row per Python version in the matrix).
- Require **conversation resolution** before merging.
- Require **linear history**.
- Do **not** allow force pushes.
- Do **not** allow deletions.
- Require review from **Code Owners**, so `.github/` and other sensitive
  paths are gated by `CODEOWNERS`.
- `enforce_admins: false` — the solo-maintainer admin-override pattern. GitHub
  forbids self-approving your own PR, so `enforce_admins: true` strands a solo
  maintainer. Document admin-override merges in the commit message.

### 4. Verify the CODEOWNERS owner is a direct collaborator

The owner named in `.github/CODEOWNERS` must be a **direct collaborator** on
the repository — or a member of a team with direct repository access.
Permissions inherited only through an organization role do **not** satisfy
CODEOWNERS enforcement: GitHub silently treats the owner as invalid and the
review requirement does not block. Confirm the owner appears under
**Settings → Collaborators and teams**.

### 5. Enable secret scanning and push protection

**Settings → Code security and analysis**:

- Enable **Secret scanning**.
- Enable **Push protection** (blocks commits that contain detected secrets).
- Enable **Dependabot security updates**.

### 6. Configure the Claude review secrets

The repository ships three Claude-driven workflows. Each one is **inert**
until its secret is provisioned, so you can enable them independently as you
decide what's worth running.

#### `CLAUDE_CODE_OAUTH_TOKEN` — used by `claude-code-review.yml` and `claude.yml`

These two workflows draw against a Claude **subscription** (not metered API
billing). Provision the token by running

```
claude /install-github-app
```

from a local Claude Code session in this repository. The command installs the
official Claude Code GitHub App on the repo and writes the OAuth token to
**Settings → Secrets and variables → Actions** as `CLAUDE_CODE_OAUTH_TOKEN`.

When the install flow offers to drop in workflow files, **decline** — the
upstream defaults lack SHA-pinning, the author-association gate on `@claude`,
and the branch gate on security review. Use the hardened versions already in
`.github/workflows/`.

- `claude-code-review.yml` runs automatically on every pull request. The
  outside-collaborator approval gate (step 1 above) is what bounds drive-by
  subscription-quota burn from random fork PRs.
- `claude.yml` (the interactive `@claude` bot) runs only when the commenter /
  issue author has at least **COLLABORATOR** access on the repository. Random
  outside users cannot trigger it even by including `@claude` in their text.

#### `ANTHROPIC_API_KEY` — used by `claude-security-review.yml`

The security-review action does not currently support OAuth, so this workflow
uses a metered API key. Add it under **Settings → Secrets and variables →
Actions → New repository secret** as `ANTHROPIC_API_KEY`. The workflow runs
automatically on every PR whose base branch is `main` or `develop`, and can
also be dispatched manually.
