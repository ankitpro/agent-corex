# PyPI Publishing Guide for Agent-CoreX

## Overview

This guide explains how to publish Agent-CoreX v1.0.0 to PyPI using GitHub Actions and API Token authentication.

---

## Prerequisites

- PyPI account (create at https://pypi.org/account/register/)
- GitHub repository access (https://github.com/ankitpro/agent-corex)
- v1.0.0 tag already created in git

---

## Step 1: Create PyPI API Token

### 1.1 Go to PyPI

Visit: https://pypi.org/account/

### 1.2 Login

- Enter your PyPI username
- Enter your PyPI password

### 1.3 Create API Token

1. Click on **Account settings** (or go to https://pypi.org/account/token/)
2. Click **Create new token**
3. Fill in:
   - **Token name**: `github-actions-agent-corex`
   - **Scope**:
     - Select **Entire account** (more flexible)
     - OR select **Only this project** and choose `agent-corex` (more secure)
4. Click **Create token**
5. **Important**: Copy the full token immediately (you won't see it again!)

Token format: `pypi-AgXXXXXXXXXXXXXXXXXXXXXX...`

---

## Step 2: Add Token to GitHub Secrets

### 2.1 Go to GitHub Repository Settings

Visit: https://github.com/ankitpro/agent-corex/settings/secrets/actions

### 2.2 Create New Secret

1. Click **New repository secret**
2. Fill in:
   - **Name**: `PYPI_API_TOKEN`
   - **Secret**: Paste the token from Step 1.5
3. Click **Add secret**

### 2.3 Verify Secret

The secret should now appear in the secrets list (the value is masked).

---

## Step 3: Create GitHub Release

### 3.1 Go to Releases Page

Visit: https://github.com/ankitpro/agent-corex/releases

### 3.2 Create New Release

1. Click **Create a new release**

### 3.3 Fill in Release Details

- **Tag version**: `v1.0.0`
- **Release title**: `Agent-CoreX v1.0.0 - Production Release`
- **Description**: Copy and paste from `RELEASE_NOTES.md`
- **Check**: Mark as latest release

### 3.4 Publish Release

Click **Publish release**

---

## Step 4: Monitor GitHub Actions

### 4.1 Watch the Workflows

1. Go to: https://github.com/ankitpro/agent-corex/actions
2. You should see workflows running:
   - **test.yml**: Runs all tests (Python 3.8-3.12, all OS)
   - **publish.yml**: Builds and publishes to PyPI
   - **release.yml**: Creates release assets

### 4.2 Check Logs

If any workflow fails:
1. Click on the failed workflow
2. Click on the failed job
3. Check the logs for error details
4. Common issues and solutions below

---

## Step 5: Verify PyPI Publication

### 5.1 Check PyPI

Visit: https://pypi.org/project/agent-corex/

You should see:
- Version: 1.0.0
- Release notes
- Python versions supported
- Installation instructions

### 5.2 Test Installation

```bash
# Install the package
pip install agent-corex

# Verify installation
agent-corex version
# Should output: Agent-CoreX 1.0.0

# Try basic usage
agent-corex retrieve "edit a file" --top-k 3
```

### 5.3 Test in Python

```python
from agent_core import rank_tools

# Should work without errors
print("Agent-CoreX imported successfully!")
```

---

## Troubleshooting

### Issue: "invalid-publisher" Error

**Cause**: GitHub Actions can't authenticate with PyPI

**Solution**:
1. Verify PYPI_API_TOKEN is set in GitHub secrets
2. Verify token is not expired (tokens don't expire by default)
3. Verify token has correct scope (entire account or agent-corex project)

### Issue: "Unauthorized" Error

**Cause**: Token is invalid or has wrong permissions

**Solution**:
1. Go to https://pypi.org/account/
2. Revoke the old token
3. Create a new token with correct scope
4. Update PYPI_API_TOKEN secret in GitHub

### Issue: "already exists on PyPI" Error

**Cause**: Version 1.0.0 already published

**Solution**:
1. Version numbers can only be published once
2. To re-publish, bump version in pyproject.toml
3. Create new tag (e.g., v1.0.1)
4. Create new GitHub release

### Issue: Tests Failing

**Cause**: Code changes broke tests

**Solution**:
1. Check test logs in GitHub Actions
2. Fix failing tests locally
3. Commit and push fixes
4. Re-create GitHub release from updated tag

### Issue: Build Verification Failed

**Cause**: twine check found issues in package metadata

**Solution**:
1. Check logs for specific validation errors
2. Fix issues in pyproject.toml or setup.py
3. Commit fixes and push
4. Re-create GitHub release

---

## Workflows Explained

### test.yml

**Trigger**: Push to main, pull requests

**Jobs**:
1. Run tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
2. Run on Ubuntu, macOS, Windows
3. Generate coverage reports

**Result**: All tests must pass for publishing

### publish.yml

**Trigger**: GitHub Release published, workflow_dispatch

**Jobs**:
1. Build distribution (wheel + source)
2. Verify with twine check
3. Publish to PyPI (or TestPyPI if specified)
4. Create release assets

**Requirements**:
- PYPI_API_TOKEN secret configured
- All tests passing

### release.yml

**Trigger**: GitHub Release published

**Jobs**:
1. Build distribution
2. Verify package
3. Publish to PyPI
4. Attach assets to GitHub release

---

## Manual Publishing (If Needed)

If GitHub Actions fails and you need to publish manually:

```bash
# Install publishing tools
pip install build twine

# Build distribution
python -m build

# Verify package
twine check dist/*

# Publish to TestPyPI (for testing)
twine upload dist/* \
  --repository testpypi \
  --username __token__ \
  --password pypi-YOUR_TOKEN_HERE

# Publish to PyPI (production)
twine upload dist/* \
  --username __token__ \
  --password pypi-YOUR_TOKEN_HERE
```

---

## Security Notes

- **Token Scope**: Use "entire account" for simplicity, or "agent-corex project" for security
- **Token Expiration**: PyPI tokens don't expire by default, but you can set expiration
- **GitHub Secrets**: Always use GitHub Actions secrets, never hardcode tokens in workflows
- **Revocation**: You can revoke tokens at any time from https://pypi.org/account/

---

## What Users See

After publishing, users can:

```bash
# Installation
pip install agent-corex

# CLI usage
agent-corex retrieve "edit a file"
agent-corex start --host 0.0.0.0 --port 8000

# Python usage
from agent_core import rank_tools
tools = rank_tools("query", all_tools)

# Version
pip show agent-corex
```

---

## References

- PyPI Help: https://pypi.org/help/
- twine Documentation: https://twine.readthedocs.io/
- GitHub Actions: https://docs.github.com/en/actions
- Python Packaging: https://packaging.python.org/
