# Deployment & Distribution Guide

Agent-Core is now ready for professional open-source distribution via PyPI, with CLI tools and multiple installation methods.

---

## Publishing to PyPI

### 1. Automated Publishing (Recommended)

GitHub Actions automatically publishes to PyPI when you create a GitHub release.

**Steps:**

```bash
# 1. Make sure everything is committed
git status  # Should be clean

# 2. Create a git tag
git tag -a v1.0.0 -m "Release v1.0.0"

# 3. Push the tag
git push origin v1.0.0

# 4. Create GitHub Release via UI or CLI:
gh release create v1.0.0 \
  --title "Version 1.0.0" \
  --notes-file RELEASE_NOTES.md

# GitHub Actions will automatically:
# ✓ Run all tests
# ✓ Build the package
# ✓ Publish to PyPI
# ✓ Upload release assets
```

**That's it!** Users can now install:
```bash
pip install agent-corex
```

### 2. Manual Publishing

For testing or if you prefer manual control:

```bash
# 1. Build the distribution
pip install build
python -m build

# This creates:
# - dist/agent_core-1.0.0.whl          (wheel)
# - dist/agent_core-1.0.0.tar.gz       (source)

# 2. Verify the build
pip install twine
twine check dist/*

# 3. Upload to TestPyPI (recommended first)
twine upload --repository testpypi dist/*

# Test installation:
pip install --index-url https://test.pypi.org/simple/ agent-corex

# 4. Upload to PyPI (production)
twine upload dist/*
```

---

## Distribution Channels

### PyPI (Official Python Package Index)

**Status:** Ready
**Users install:** `pip install agent-corex`

```bash
# After publishing to PyPI, users can:
pip install agent-corex                    # Latest version
pip install agent-corex==1.0.0             # Specific version
pip install agent-corex>=1.0.0             # Version constraint
pip install agent-corex[redis]             # With optional deps
pip install agent-corex[dev]               # With dev tools
```

**PyPI Package Info:**
- Name: `agent-corex`
- Home Page: https://github.com/your-org/agent-corex
- Documentation: https://github.com/your-org/agent-corex#readme
- Source: https://github.com/your-org/agent-corex
- License: MIT

### Installation Scripts

**Instant Install (curl):**
```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/your-org/agent-corex/main/install-curl.sh | bash

# Windows (PowerShell)
iex ((New-Object System.Net.WebClient).DownloadString('https://...install.bat'))
```

These scripts:
- Check Python version
- Create virtual environment (optional)
- Install from PyPI
- Verify installation
- Show next steps

### GitHub Releases

**Download Executable Packages:**
- `agent-corex-1.0.0.whl` - Wheel distribution
- `agent-corex-1.0.0.tar.gz` - Source distribution
- `agent-corex-1.0.0.zip` - Windows package

Users can also install directly:
```bash
pip install https://github.com/your-org/agent-corex/releases/download/v1.0.0/agent_core-1.0.0-py3-none-any.whl
```

### Docker

**Official Docker Image (coming):**
```bash
docker pull agent-corex:latest
docker run -p 8000:8000 agent-corex:latest
```

**Build locally:**
```bash
git clone https://github.com/your-org/agent-corex
cd agent-corex
docker build -t agent-corex:latest .
docker run -p 8000:8000 agent-corex:latest
```

### Homebrew (Coming)

```bash
brew install agent-corex
```

Add this to your Homebrew tap once available.

---

## Version Management

### Semantic Versioning

Agent-Core follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes (v1.0.0 → v2.0.0)
- **MINOR**: New features, backward compatible (v1.0.0 → v1.1.0)
- **PATCH**: Bug fixes (v1.0.0 → v1.0.1)

**Current Version:** `1.0.0`

Located in:
- `pyproject.toml`: `version = "1.0.0"`
- `agent_core/__init__.py`: `__version__ = "1.0.0"`

### Updating Version

```bash
# Update version string
sed -i 's/version = "1.0.0"/version = "1.1.0"/' pyproject.toml
sed -i 's/__version__ = "1.0.0"/__version__ = "1.1.0"/' agent_core/__init__.py

# Commit
git commit -m "Bump version to 1.1.0"
git tag v1.1.0
git push origin main v1.1.0

# Create release (auto-publishes to PyPI)
gh release create v1.1.0 --title "Version 1.1.0" --generate-notes
```

---

## Continuous Integration & Deployment

### GitHub Actions Workflows

**`.github/workflows/test.yml`** - Runs on every push/PR
- Tests on Python 3.8-3.12
- Tests on macOS, Linux, Windows
- Code quality checks (black, flake8, mypy)
- Coverage reporting
- Build verification

**`.github/workflows/publish.yml`** - Runs on release
- Builds distribution
- Verifies package
- Publishes to PyPI
- Uploads assets to GitHub release

### Local Testing Before Release

```bash
# 1. Run all tests
pytest tests/ -v

# 2. Check code quality
black --check agent_core tests
flake8 agent_core tests
mypy agent_core

# 3. Build locally
python -m build

# 4. Verify build
twine check dist/*

# 5. Test installation
pip install dist/agent_core-*.whl
agent-corex version

# 6. Test CLI
agent-corex retrieve "test" --help
```

---

## Enterprise Distribution

For organizations with internal PyPI:

### PyPI Mirror / Private Registry

**Option 1: Internal PyPI Proxy**
```bash
# Configure pip to use internal registry
pip install -i https://internal-pypi.company.com/simple/ agent-corex
```

**Option 2: Vendoring (Embed in Your Package)**
```bash
git clone https://github.com/your-org/agent-corex
cd agent-corex
pip install -e .
# Or distribute as submodule/dependency
```

**Option 3: Container Registry**
```bash
# Push to Docker Hub or ECR
docker tag agent-corex:latest your-registry.com/agent-corex:latest
docker push your-registry.com/agent-corex:latest

# Users pull from your registry
docker pull your-registry.com/agent-corex:latest
```

---

## Monetization Setup (Phase 2)

### Free Tier
- OSS package on PyPI
- All ranking methods
- Self-hosted API
- Full documentation

### Premium Tier
- Managed API hosting
- Pre-indexed tool libraries
- Analytics dashboard
- Priority support

### API Key System
```python
# Enterprise package will add:
from agent_core import Client

client = Client(api_key="sk_live_...")  # Premium API key
results = client.retrieve("query")
```

---

## Release Checklist

Before publishing v2.0.0 or later:

- [ ] Update version in `pyproject.toml`
- [ ] Update version in `agent_core/__init__.py`
- [ ] Update `RELEASE_NOTES.md` with changes
- [ ] Run `pytest tests/ -v` - all pass
- [ ] Run `black agent_core tests`
- [ ] Run `flake8 agent_core tests`
- [ ] Run `mypy agent_core`
- [ ] Build locally: `python -m build`
- [ ] Verify: `twine check dist/*`
- [ ] Test install: `pip install dist/*.whl`
- [ ] Commit: `git commit -am "Bump version to X.Y.Z"`
- [ ] Tag: `git tag vX.Y.Z`
- [ ] Push: `git push origin main vX.Y.Z`
- [ ] Create release: `gh release create vX.Y.Z`
- [ ] Watch GitHub Actions publish to PyPI
- [ ] Verify on PyPI: https://pypi.org/project/agent-corex/

---

## Monitoring Distribution

### PyPI Stats

Check your package stats:
- https://pypi.org/project/agent-corex/#history
- Download statistics
- Version history
- Release timeline

### GitHub Release Download Tracking

Monitor release downloads:
```bash
gh api repos/your-org/agent-corex/releases -q '.[] | "\(.tag_name): \(.download_count) downloads"'
```

### User Feedback

- GitHub Issues: https://github.com/your-org/agent-corex/issues
- Discussions: https://github.com/your-org/agent-corex/discussions
- Email: hello@agent-corex.ai

---

## Troubleshooting

### Package Not Found on PyPI

```bash
# Check if published
pip search agent-corex  # (deprecated, use pip index)
pip index versions agent-corex

# If not found, check GitHub Actions logs
gh run list -w publish.yml
gh run view <run_id> --log
```

### Installation Fails

```bash
# Verbose installation
pip install -v agent-corex

# Force reinstall
pip install --force-reinstall --no-cache-dir agent-corex

# Check dependencies
pip show agent-corex
```

### Build Verification Fails

```bash
# Check if twine is installed
pip install --upgrade twine

# Verify distribution
twine check dist/*

# Common issues:
# - Invalid metadata (check pyproject.toml)
# - Missing files (check MANIFEST.in)
# - Version mismatch (check consistency)
```

---

## Support & Updates

### Security Updates

For critical security issues:
1. Create a patch release (e.g., v1.0.1)
2. Publish immediately
3. Announce via GitHub Security Advisory
4. Update README with security notice

### Breaking Changes

For major version updates (v1.0.0 → v2.0.0):
1. Add deprecation warnings in v1.x
2. Document migration guide
3. Update BREAKING_CHANGES.md
4. Release major version
5. Maintain v1.x in maintenance mode

---

## Next Steps

1. **Immediate**: Create GitHub release for v1.0.0
2. **Short term**: Monitor PyPI downloads and feedback
3. **Medium term**: Plan Phase 2 monetization
4. **Long term**: Enterprise features and support

See: CONTRIBUTING.md for community contribution guidelines

---

## Resources

- PyPI: https://pypi.org
- Python Packaging Guide: https://packaging.python.org
- GitHub Actions: https://docs.github.com/en/actions
- Semantic Versioning: https://semver.org
- PEP 621: https://www.python.org/dev/peps/pep-0621/
