# Agent-Corex Deployment Guide

Complete guide for deploying Agent-Corex to PyPI, Homebrew, and GitHub Releases (PyInstaller binaries).

---

## Release Workflow

### Prerequisites

1. **GitHub Secrets Configured:**
   - `PYPI_API_TOKEN` - PyPI API token for publishing packages
   - `TAP_GITHUB_TOKEN` - GitHub personal access token for Homebrew tap updates

2. **Homebrew Tap Repository:**
   - Repository: `ankitpro/homebrew-agent-corex`
   - Contains: `Formula/agent-corex.rb`

3. **Local Git Setup:**
   ```bash
   git config user.name "Your Name"
   git config user.email "your.email@example.com"
   ```

---

## Steps to Release

### Step 1: Update Version

Update `pyproject.toml`:
```toml
version = "1.1.3"  # Increment from current
```

### Step 2: Add Release Notes

Update or create `RELEASE_NOTES.md`:
```markdown
## 1.1.3 (Date)

### ✨ New Features
- Feature 1
- Feature 2

### 🔧 Improvements
- Improvement 1

### 📦 Downloads
- Binaries available for Linux, macOS, Windows
```

### Step 3: Commit Changes

```bash
git add pyproject.toml RELEASE_NOTES.md
git commit -m "chore: prepare release v1.1.3"
git push origin main
```

### Step 4: Create and Push Version Tag

```bash
git tag -a v1.1.3 -m "Release v1.1.3: description"
git push origin v1.1.3
```

**This single tag push triggers:**
1. ✅ Test workflow (Python 3.8-3.12)
2. ✅ Build distribution (wheel + sdist)
3. ✅ Publish to PyPI
4. ✅ Build binaries (Linux, macOS, Windows)
5. ✅ Create GitHub Release with binaries
6. ✅ Update Homebrew tap formula

---

## Automated Workflows

### 1. **test.yml** - Unit Tests
- Runs on: Tag push (`v*`)
- Tests on: Python 3.8, 3.9, 3.10, 3.11, 3.12
- Uploads coverage to CodeCov

### 2. **publish.yml** - PyPI Publication
- Triggered by: Version tag
- Steps:
  1. Build wheel + source distribution
  2. Validate with twine
  3. Publish to PyPI
  4. Generates PyPI link in summary

### 3. **build-binaries.yml** - Binary Build
- Triggered by: Version tag or manual dispatch
- Builds for:
  - Linux x86_64 (Ubuntu 22.04)
  - macOS arm64 (macOS 15)
  - Windows x86_64 (Windows 2022)
- Excludes ML dependencies (torch, sklearn, scipy, etc.)
- Generates SHA256 checksums

### 4. **update-homebrew-tap.yml** - Homebrew
- Triggered by: `build-binaries.yml` completion
- Steps:
  1. Downloads SHA256 files from release
  2. Checks out Homebrew tap repo
  3. Updates `Formula/agent-corex.rb`
  4. Commits and pushes formula update
  5. Homebrew automatically serves new version

### 5. **release.yml** - GitHub Release
- Triggered by: Version tag
- Creates GitHub Release with changelog from RELEASE_NOTES.md

---

## Installation Methods

### After Release, Users Can Install Via:

#### 1. PyPI (Recommended for Python users)
```bash
pip install agent-corex==1.1.3
```

#### 2. Homebrew (macOS)
```bash
brew install ankitpro/agent-corex/agent-corex
```

#### 3. Binary Download
Visit: https://github.com/ankitpro/agent-corex/releases/tag/v1.1.3
- `agent-corex-linux-x86_64`
- `agent-corex-macos-arm64`
- `agent-corex-windows-x86_64.exe`

#### 4. From Source
```bash
pip install git+https://github.com/ankitpro/agent-corex.git@v1.1.3
```

---

## Workflow Status Checks

### 1. Check GitHub Actions
Visit: https://github.com/ankitpro/agent-corex/actions

Look for workflows:
- ✅ `Test, Release & Publish` (if using test-and-release.yml)
- ✅ `Build and Publish to PyPI`
- ✅ `Build Binaries`
- ✅ `Update Homebrew Tap`

### 2. Verify PyPI
```bash
pip index versions agent-corex
# Should show version 1.1.3
```

### 3. Verify Homebrew
```bash
brew search agent-corex
brew info agent-corex/agent-corex/agent-corex
# Version should be 1.1.3
```

### 4. Verify GitHub Release
https://github.com/ankitpro/agent-corex/releases/tag/v1.1.3
- Should have binaries attached
- Changelog visible

---

## Troubleshooting

### PyPI Publication Fails
1. Check `PYPI_API_TOKEN` secret exists
2. Verify token has write permissions
3. Check `dist/` artifacts exist
4. Ensure wheel/sdist names match expected pattern

**Debug:**
```bash
python -m build
twine check dist/*
```

### Homebrew Update Fails
1. Check `TAP_GITHUB_TOKEN` secret exists
2. Verify tap repo is `ankitpro/homebrew-agent-corex`
3. Check SHA256 files are downloaded correctly
4. Ensure formula file exists at `Formula/agent-corex.rb`

**Manual update:**
```bash
git clone https://github.com/ankitpro/homebrew-agent-corex.git
cd homebrew-agent-corex
# Edit Formula/agent-corex.rb manually
git commit -am "agent-corex 1.1.3"
git push
```

### Binary Build Fails
1. Ensure PyInstaller dependencies are installed
2. Check Python version compatibility (3.8+)
3. Verify all hidden imports listed in workflow
4. Check excluded modules are not needed

**Test locally:**
```bash
pip install pyinstaller
pyinstaller --onefile agent_core/cli/main.py
```

### Tests Fail on Tag
1. All tests must pass before release
2. Check Python version matrix (3.8-3.12)
3. Ensure dependencies in `pyproject.toml` are correct
4. Fix failing tests before creating tag

**Debug:**
```bash
pytest tests/ -v
```

---

## Release Checklist

Before creating a tag, verify:

- [ ] Version updated in `pyproject.toml`
- [ ] RELEASE_NOTES.md created/updated
- [ ] All tests pass locally: `pytest tests/ -v`
- [ ] Build works locally: `python -m build`
- [ ] Binaries build locally: `pyinstaller ...`
- [ ] Git is clean: `git status`
- [ ] Changes committed: `git log --oneline -5`
- [ ] `PYPI_API_TOKEN` secret is set
- [ ] `TAP_GITHUB_TOKEN` secret is set
- [ ] Homebrew tap repo is `ankitpro/homebrew-agent-corex`

---

## Manual Release (If Workflows Fail)

### Publish to PyPI Manually
```bash
python -m build
twine upload dist/*
```

### Update Homebrew Manually
```bash
git clone https://github.com/ankitpro/homebrew-agent-corex.git
cd homebrew-agent-corex

# Edit Formula/agent-corex.rb
# Update version and SHA256 hashes

git add Formula/agent-corex.rb
git commit -m "agent-corex 1.1.3"
git push
```

### Create GitHub Release Manually
```bash
gh release create v1.1.3 \
  --title "agent-corex v1.1.3" \
  --notes-file RELEASE_NOTES.md
```

---

## Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Examples:
- `1.1.2` → `1.1.3` (patch fix)
- `1.1.3` → `1.2.0` (new feature)
- `1.2.0` → `2.0.0` (breaking change)

---

## Common Release Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| PyPI token invalid | Wrong secret set | Update `PYPI_API_TOKEN` in GitHub |
| Tap update fails | Token permissions | Create new token with `repo` scope |
| Binary build times out | Large dependencies | Exclude ML libs (torch, sklearn, etc.) |
| Release not found on PyPI | Artifact upload failed | Check `dist/` directory in workflow |
| Homebrew formula outdated | SHA256 mismatch | Re-download from release assets |
| Tests fail at tag | Code issues | Fix and force-push (with caution) |

---

## Post-Release

### Announcements
1. Update GitHub releases page with announcement
2. Update README with new version
3. Announce in project discussions
4. Update documentation if needed

### Monitoring
1. Check PyPI download stats
2. Monitor GitHub issues for problems
3. Watch for version adoption
4. Collect user feedback

### Next Release Prep
1. Plan next feature set
2. Create GitHub issues for next version
3. Update milestone tracker
4. Begin development cycle

---

## Quick Release Command

```bash
# Update version
sed -i 's/version = "1.1.2"/version = "1.1.3"/' pyproject.toml

# Update RELEASE_NOTES.md (manually)
# ... add release notes ...

# Commit
git add pyproject.toml RELEASE_NOTES.md
git commit -m "chore: prepare release v1.1.3"
git push origin main

# Create tag and trigger workflows
git tag -a v1.1.3 -m "Release v1.1.3: description"
git push origin v1.1.3

# Monitor workflows
echo "Workflows triggered! Check: https://github.com/ankitpro/agent-corex/actions"
```

---

## Support

- **Issues**: https://github.com/ankitpro/agent-corex/issues
- **Discussions**: https://github.com/ankitpro/agent-corex/discussions
- **Author**: Ankit Agarwal (@ankitpro)

---

**Last Updated**: March 27, 2026
**Current Version**: 1.1.3
