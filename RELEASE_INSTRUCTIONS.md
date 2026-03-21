# Agent-CoreX Release Instructions

## Overview

Agent-CoreX uses GitHub Releases and GitHub Actions to automatically publish to PyPI. The release process is fully automated once you create a GitHub Release.

---

## Prerequisites

1. **PyPI Account**: Have a PyPI account at https://pypi.org/
2. **PyPI API Token**: Generate at https://pypi.org/manage/account/token/
3. **GitHub Secret**: Store token as `PYPI_API_TOKEN` in GitHub repo settings

---

## Step-by-Step Release Process

### Step 1: Verify Everything is Ready

```bash
# Make sure all changes are committed
git status

# Verify package version in pyproject.toml
grep "version = " pyproject.toml

# Make sure v1.0.0 tag exists locally
git tag -l
```

### Step 2: Update Version (if needed)

Edit `pyproject.toml`:
```toml
[project]
name = "agent-corex"
version = "1.1.0"  # Increment version
```

Then commit:
```bash
git add pyproject.toml
git commit -m "Bump version to 1.1.0"
git push origin main
```

### Step 3: Create GitHub Release

1. Go to: https://github.com/ankitpro/agent-corex/releases
2. Click "Create a new release"
3. Fill in:
   - **Tag version**: v1.0.0 (or v1.1.0 if you updated)
   - **Release title**: "Agent-CoreX v1.0.0 - Production Release"
   - **Description**: Copy from `RELEASE_NOTES.md`
   - **Mark as latest**: Check this
4. Click "Publish release"

### Step 4: GitHub Actions Automatically:

- ✅ Triggers test workflow
- ✅ Runs tests on Python 3.8-3.12 (all OS)
- ✅ Builds distribution
- ✅ Publishes to PyPI
- ✅ Attaches assets to release

---

## Monitoring the Release

### Check GitHub Actions

1. Go to: https://github.com/ankitpro/agent-corex/actions
2. Look for "Publish to PyPI" workflow
3. Wait for it to complete (usually 2-5 minutes)
4. Verify all checks pass

### Verify PyPI Publication

1. Visit: https://pypi.org/project/agent-corex/
2. Verify version is live
3. Check release notes are correct
4. Test installation:
   ```bash
   pip install --upgrade agent-corex
   agent-corex version
   ```

---

## GitHub Actions Workflows

### 1. Test Workflow (test.yml)

Automatically runs on:
- Push to main
- Pull requests

Tests:
- Python 3.8-3.12
- macOS, Linux, Windows
- Full test suite
- Code coverage

### 2. Publish Workflow (publish.yml)

Automatically runs on:
- GitHub release published
- Manual workflow dispatch (for testing)

Publishes to:
- PyPI (on release)
- TestPyPI (on workflow dispatch with testpypi option)

### 3. Release Workflow (release.yml)

Automatically runs on:
- GitHub release published

Creates:
- Release assets (wheels, source)
- GitHub release attachments

---

## GitHub Secrets Configuration

Set these in your GitHub repo: Settings → Secrets and variables → Actions

### Required Secrets

1. **PYPI_API_TOKEN**
   - Type: Repository secret
   - Value: PyPI API token from https://pypi.org/manage/account/token/
   - Scope: api, upload

---

## Common Release Commands

```bash
# Create local tag (before releasing)
git tag -a v1.0.0 -m "Release v1.0.0"

# Push tag to GitHub
git push origin v1.0.0

# Check latest releases
git tag -l --sort=-version:refname | head -5

# Delete local tag (if needed)
git tag -d v1.0.0

# Delete remote tag (if needed)
git push origin --delete v1.0.0
```

---

## Troubleshooting

### Release not publishing to PyPI

1. Check GitHub Actions logs:
   - Go to Actions tab
   - Click on "Publish to PyPI" workflow
   - Check logs for errors

2. Common issues:
   - PYPI_API_TOKEN not set or expired
   - Version already exists on PyPI
   - Build errors (check test logs)
   - Package name conflict

### Tests failing before publish

1. GitHub Actions runs tests first
2. If tests fail, publish is skipped
3. Fix failing tests:
   ```bash
   pytest tests/ -v
   ```
4. Commit fix and push
5. Create new release tag

### Package already exists on PyPI

Each version can only be published once. To re-release:

```bash
# Increment version
# Edit pyproject.toml: version = "1.0.1"
git add pyproject.toml
git commit -m "Bump version to 1.0.1"
git push origin main

# Create new release tag
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1

# Create GitHub release from v1.0.1 tag
```

---

## Release Checklist

Before creating a GitHub Release:

- [ ] All tests passing locally
- [ ] Version updated in pyproject.toml
- [ ] RELEASE_NOTES.md updated
- [ ] Commit history is clean
- [ ] All changes pushed to main
- [ ] Tag created (optional, GitHub creates it)
- [ ] PYPI_API_TOKEN secret configured

---

## Publishing Manually (if needed)

If GitHub Actions fails, you can publish manually:

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Verify package
twine check dist/*

# Upload to PyPI
twine upload dist/* --repository pypi --username __token__ --password $PYPI_API_TOKEN
```

---

## Versioning Strategy

Use Semantic Versioning: MAJOR.MINOR.PATCH

- **1.0.0** → 1 = major, 0 = minor, 0 = patch
- **1.1.0** → Minor version bump (features)
- **1.0.1** → Patch version bump (bug fixes)
- **2.0.0** → Major version bump (breaking changes)

---

## Post-Release

After successful PyPI publication:

1. ✅ Verify on PyPI
2. ✅ Test installation
3. ✅ Update GitHub release if needed
4. ✅ Announce release (social media, etc.)
5. ✅ Start working on next version

---

## Reference

- PyPI: https://pypi.org/project/agent-corex/
- GitHub: https://github.com/ankitpro/agent-corex
- GitHub Actions Docs: https://docs.github.com/en/actions
- Python Packaging: https://packaging.python.org/
