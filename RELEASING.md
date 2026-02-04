# Releasing `mrpd` to PyPI

This repo uses GitHub Actions + PyPI Trusted Publishing (OIDC). No API token is stored in the repo.

## One-time setup (PyPI)

1. Create the project on PyPI (first release can create it automatically if allowed), or ensure `mrpd` exists.
2. In PyPI, go to:
   - Project → Settings → Publishing → **Trusted Publishers**
3. Add a trusted publisher:
   - **Owner**: `thorthur22`
   - **Repository**: `Moltrouter-Protocol-Daemon`
   - **Workflow filename**: `.github/workflows/publish-pypi.yml`
   - **Environment**: (leave blank)

## One-time setup (GitHub)

Nothing required beyond having the workflow file. The workflow requests `id-token: write` so PyPI can verify the GitHub OIDC identity.

## Release process

1. Bump `[project].version` in `pyproject.toml`.
2. Commit and push to `master`.
3. Create and push a matching tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The workflow will refuse to publish if the tag doesn't match `pyproject.toml`.

## Manual run

You can also run the workflow manually via GitHub Actions → "Publish to PyPI" → Run workflow.

(Note: manual runs still require the project version to be set appropriately.)
