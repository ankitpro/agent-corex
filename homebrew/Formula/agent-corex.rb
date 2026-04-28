# typed: false
# frozen_string_literal: true

# Homebrew formula for agent-corex.
#
# Tap:    brew tap ankitpro/agent-corex
# Install: brew install agent-corex
#
# This formula installs the pre-built binary released on GitHub.
# No Python or extra dependencies required.

class AgentCorex < Formula
  desc "Thin CLI + MCP client for Agent-CoreX — execute any task with a single query"
  homepage "https://github.com/ankitpro/agent-corex"
  version "4.4.5"
  license "MIT"

  on_macos do
    # arm64 binary; runs on Intel Macs via Rosetta 2
    url "https://github.com/ankitpro/agent-corex/releases/download/v#{version}/agent-corex-macos-arm64"
    sha256 "PLACEHOLDER_ARM64_SHA256"
  end

  on_linux do
    url "https://github.com/ankitpro/agent-corex/releases/download/v#{version}/agent-corex-linux-x86_64"
    sha256 "PLACEHOLDER_LINUX_SHA256"
  end

  def install
    if OS.mac?
      bin.install "agent-corex-macos-arm64" => "agent-corex"
    else
      bin.install "agent-corex-linux-x86_64" => "agent-corex"
    end
  end

  def caveats
    <<~EOS
      Get started:
        agent-corex login --key <your-api-key>
        agent-corex mcp add railway        # install an MCP server locally
        agent-corex run "list my railway projects"
        agent-corex serve                  # start MCP server for Claude/Cursor

      Manage local MCP servers:
        agent-corex mcp list               # show available servers
        agent-corex mcp add <server>       # add a server
        agent-corex mcp remove <server>    # remove a server
        agent-corex mcp show               # show your enabled servers

      MCP config (Claude Desktop / Cursor):
        {"agent-corex": {"command": "agent-corex", "args": ["serve"]}}

      Docs: https://github.com/ankitpro/agent-corex
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/agent-corex version")
  end
end
