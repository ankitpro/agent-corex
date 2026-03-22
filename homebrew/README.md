# agent-corex Homebrew Tap

This directory contains the Homebrew formula for agent-corex.

## Setup (one-time)

The formula lives in a **separate** GitHub repository named `homebrew-agent-corex`.
Create it, then copy `Formula/agent-corex.rb` into it.

```bash
# Create the tap repo on GitHub: ankitpro/homebrew-agent-corex
# Then copy the formula:
cp -r homebrew/* /path/to/homebrew-agent-corex/
```

## Install

```bash
brew tap ankitpro/agent-corex
brew install agent-corex
```

## Updating the formula

The `update-homebrew-tap.yml` workflow runs automatically after every release.
It fetches the `.sha256` sidecar files built by `build-binaries.yml` and patches
`Formula/agent-corex.rb` with the new version and hashes, then commits to the tap repo.

### Manual update

```bash
# In homebrew-agent-corex repo:
VERSION=1.2.0
sed -i '' "s/version \".*\"/version \"$VERSION\"/" Formula/agent-corex.rb
# Update sha256 values from the GitHub release .sha256 files
git commit -am "agent-corex $VERSION"
git push
```

## Required secret

Add `TAP_GITHUB_TOKEN` to the main repo's secrets:
- Go to: Settings → Secrets and variables → Actions → New repository secret
- Name: `TAP_GITHUB_TOKEN`
- Value: A GitHub PAT with `repo` scope, able to push to `ankitpro/homebrew-agent-corex`
