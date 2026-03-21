# GitHub Actions Setup Guide

Automated release and PyPI publishing with GitHub Actions.

---

## 📋 What's Included

### 3 Workflow Files

1. **publish.yml** - Build and publish to PyPI
2. **release.yml** - Create GitHub releases
3. **test-and-release.yml** - Complete CI/CD pipeline (recommended)

All workflows trigger automatically when you push a version tag.

---

## ⚙️ Setup Instructions

### Step 1: Add PyPI API Token

1. Go to [PyPI.org](https://pypi.org)
2. Click your account avatar → Settings
3. Click "API tokens" on the left
4. Click "Create API token"
5. Select scope: "Entire repository"
6. Copy the token

### Step 2: Add to GitHub Secrets

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Paste your PyPI token
5. Click "Add secret"

### Step 3: (Optional) Add TestPyPI Token

For pre-release testing (beta, rc, alpha versions):

1. Go to [test.pypi.org](https://test.pypi.org)
2. Click your account → Settings → API tokens
3. Create API token
4. Add to GitHub secrets as `TEST_PYPI_API_TOKEN`

---

## 🚀 How to Use

### Release a New Version

```bash
# Update version in setup.py or pyproject.toml
# Update RELEASE_NOTES.md with changelog

# Commit changes
git add .
git commit -m "Bump version to 1.0.1"

# Create and push tag
git tag v1.0.1
git push origin v1.0.1
```

That's it! GitHub Actions will automatically:
1. Run all tests
2. Build the distribution
3. Create a GitHub release
4. Publish to PyPI

### Monitor Progress

1. Go to GitHub repo → Actions tab
2. Watch the workflow run
3. See each step complete in real-time

---

## 📁 Workflow Files Location

```
agent-corex/
├── .github/
│   └── workflows/
│       ├── publish.yml              (Simple PyPI only)
│       ├── release.yml              (GitHub release only)
│       └── test-and-release.yml     (Full CI/CD - RECOMMENDED)
```

---

## 🔧 Workflow Details

### test-and-release.yml (RECOMMENDED)

**What it does**:
1. Runs tests on Python 3.8, 3.9, 3.10, 3.11
2. Builds distribution packages
3. Creates GitHub release
4. Publishes to PyPI

**Trigger**: Push any tag matching `v*` (e.g., v1.0.0, v1.0.1-rc1)

**Jobs**:
- `test` - Runs pytest on multiple Python versions
- `build` - Creates wheel and source distributions
- `create-release` - Creates GitHub release from RELEASE_NOTES.md
- `publish-pypi` - Publishes to PyPI
- `notify` - Sends completion notifications

**Duration**: ~5-10 minutes

---

### publish.yml (PyPI Only)

**What it does**:
- Builds and publishes to PyPI only
- Does NOT create GitHub release

**Use when**: You want a simpler workflow without tests

---

### release.yml (GitHub Release Only)

**What it does**:
- Creates GitHub release only
- Does NOT publish to PyPI

**Use when**: You want to create releases manually

---

## 📝 RELEASE_NOTES.md Format

The release workflow reads from RELEASE_NOTES.md:

```markdown
# Release Notes

## v1.0.1
- Fixed bug in ranking
- Improved performance
- Added new documentation

## v1.0.0
- Initial release
- Full MCP integration
- 45 comprehensive tests
```

---

## 🔍 Troubleshooting

### "API token invalid" Error

**Solution**:
1. Go to PyPI.org
2. Check if token is valid
3. Regenerate token if needed
4. Update GitHub secret

### "twine check" Failed

**Solution**:
1. Ensure setup.py/pyproject.toml is valid
2. Test locally: `python -m twine check dist/*`
3. Fix any validation errors

### "Test failed" Error

**Solution**:
1. Fix failing tests locally
2. Commit and push
3. Retry the tag push

### Workflow Not Triggering

**Solution**:
1. Ensure tag matches pattern `v*`
2. Examples: `v1.0.0`, `v1.0.1`, `v2.0.0-rc1`
3. Check if workflows are enabled (Settings → Actions)

---

## ✅ Pre-Release Checklist

Before pushing a tag:

```
[ ] Update setup.py with new version
[ ] Update RELEASE_NOTES.md with changelog
[ ] Run tests locally: pytest tests/ -v
[ ] Commit changes: git commit -m "Bump version"
[ ] Create tag: git tag v1.0.1
[ ] Push tag: git push origin v1.0.1
[ ] Watch Actions tab for completion
[ ] Verify on PyPI.org/project/agent-corex
[ ] Verify GitHub release created
```

---

## 📊 Version Tagging Strategy

### Production Releases
```bash
git tag v1.0.0   # First release
git tag v1.0.1   # Bug fix
git tag v1.1.0   # Minor feature
git tag v2.0.0   # Major release
```

### Pre-Releases
```bash
git tag v1.0.0-alpha   # Alpha version
git tag v1.0.0-beta    # Beta version
git tag v1.0.0-rc1     # Release candidate
```

**Note**: Pre-releases will:
- Publish to PyPI as pre-release
- Also publish to TestPyPI (if token configured)
- Be marked as prerelease on GitHub

---

## 🔐 Security Notes

### API Token Safety

✅ DO:
- Store token in GitHub Secrets (encrypted)
- Use repository-specific tokens
- Rotate tokens periodically
- Never commit token to git

❌ DON'T:
- Store token in code or config files
- Share token with other people
- Use the same token for multiple projects

### Restricting Access

1. Go to GitHub repo → Settings → Actions
2. Configure "Workflow permissions"
3. Limit to necessary scopes only

---

## 📈 Monitoring & Metrics

### View Workflow Runs

1. GitHub repo → Actions tab
2. Click on workflow name
3. See all historical runs
4. View logs for each step

### Automated Metrics

Each workflow run:
- ✅ Shows test results
- ✅ Reports coverage
- ✅ Logs build details
- ✅ Records publication status

---

## 🤖 Workflow Tips

### Skip a Step

Add to commit message:
```
[skip ci]
```

This prevents workflows from running.

### Debug Mode

Add step to print environment:
```yaml
- name: Debug info
  run: |
    echo "Tag: ${{ github.ref }}"
    echo "Version: ${GITHUB_REF#refs/tags/}"
```

### Manual Trigger (Optional)

To allow manual workflow dispatch:

```yaml
on:
  push:
    tags: ['v*']
  workflow_dispatch:  # Add this
```

Then trigger from Actions tab manually.

---

## 📚 Example Workflow

### Complete Release Process

```bash
# 1. Make changes
git checkout main
git pull origin main
git add .
git commit -m "Add new feature: semantic ranking"

# 2. Update version
nano setup.py  # Change version to 1.1.0

# 3. Update changelog
nano RELEASE_NOTES.md
# Add:
# ## v1.1.0
# - Added semantic ranking with embeddings
# - Improved performance by 2x
# - Added documentation

# 4. Commit
git add setup.py RELEASE_NOTES.md
git commit -m "Bump version to 1.1.0"

# 5. Create tag
git tag v1.1.0

# 6. Push everything
git push origin main
git push origin v1.1.0

# 7. Watch Actions
# Go to GitHub → Actions tab
# See workflows running automatically

# 8. Verify
# Check PyPI.org/project/agent-corex
# Check GitHub releases page
```

---

## 🎉 What Happens Automatically

When you push a tag:

```
Tag pushed (v1.0.0)
    ↓
Workflows trigger
    ↓
Tests run (all Python versions)
    ↓
Distribution built
    ↓
GitHub release created
    ↓
Published to PyPI
    ↓
All users can: pip install agent-corex==1.0.0
```

All automatic. No manual steps needed.

---

## 📞 Support

### Workflow Syntax
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-and-codecov/)

### Debugging
1. Check Actions tab for error messages
2. View detailed logs
3. Check PyPI API token is valid
4. Ensure workflow files are in `.github/workflows/`

---

## ✨ Next Steps

1. ✅ Copy `.github/workflows/` to your repo
2. ✅ Add `PYPI_API_TOKEN` to GitHub Secrets
3. ✅ Test with a pre-release tag (v1.0.0-test)
4. ✅ Verify workflow runs successfully
5. ✅ Push your first real release tag

---

**Status**: Ready to use
**Recommended**: test-and-release.yml for full CI/CD

See README.md for other documentation.
