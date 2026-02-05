# 🔓 Inkeep MCP: Universal Documentation Bridge

[English](README.md) | [中文](README_zh.md)

> **Unlock the "Ask AI" capability from ANY Inkeep-powered documentation site. Connect your local AI Agent directly to the official docs of Langfuse, Render, Clerk, and countless others.**

[![MCP Compliant](https://img.shields.io/badge/MCP-Compliant-blue)](https://modelcontextprotocol.io/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Inkeep MCP** is a universal connector built on the **Model Context Protocol (MCP)**. It bridges the gap between your local AI tools (Gemini CLI, Claude Desktop) and the wealth of knowledge hidden behind the "Ask AI" buttons on modern documentation sites.

It simulates a browser to access Inkeep's services, allowing you to query **any** supported site without needing official API keys or manual configuration.

---

## 🧐 The "Why"

### The Problem: Locked Knowledge
Top-tier dev tools (Langfuse, Render, Neon...) use [Inkeep](https://inkeep.com) to power their excellent AI search. But this capability is locked inside their browser widgets.
*   **Developers** have to leave their terminal to search.
*   **AI Agents** (Gemini/Claude) can't access this high-quality, up-to-date knowledge base programmatically.

### The Solution: A Universal Bridge
This tool "liberates" that knowledge. It acts as a universal adapter that:
1.  **Scans** the target website (any website!) for Inkeep configuration.
2.  **Connects** using the site's own public credentials (simulating a visitor).
3.  **Streams** the answers back to your CLI or Agent.

**Result**: Your AI Agent gains the ability to "read" the official docs of any product that uses Inkeep.

---

## 🚀 Getting Started

### Installation

```bash
git clone https://github.com/xu-xiang/inkeep-mcp.git
cd inkeep-mcp
pip install -r requirements.txt
```

### CLI Usage (Human Mode)

You can use it as a standalone CLI tool to query docs from your terminal.

```bash
# Ask a question to Langfuse docs
python3 cli.py ask langfuse "How do I trace LangChain chains?"

# Start an interactive chat session with Render docs
python3 cli.py chat render

# Add a new documentation source
python3 cli.py add supabase https://supabase.com/docs --desc "Supabase Docs"
```

## 🤖 MCP Integration (Agent Mode)

Give your AI assistant the power to read docs.

### Gemini CLI

Add to your `~/.gemini/config.json`:

```json
{
  "mcpServers": {
    "inkeep": {
      "command": "python3",
      "args": ["/absolute/path/to/inkeep-mcp/mcp_server.py"],
      "env": {"PYTHONUNBUFFERED": "1"}
    }
  }
}
```

### Claude Desktop

Add to your `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "inkeep": {
      "command": "python3",
      "args": ["/absolute/path/to/inkeep-mcp/mcp_server.py"]
    }
  }
}
```

## 📖 How it Works

1.  **Registry**: Maintains a local map of aliases (`langfuse`) to URLs (`https://langfuse.com`). It automatically syncs with the latest built-in defaults on startup.
2.  **Extraction**: When connecting to a new site, it simulates a browser request, scanning frontend JS bundles to find the embedded Inkeep configuration.
3.  **Authentication**: It requests a Challenge from Inkeep and solves the SHA-256 PoW locally.
4.  **Query**: It streams the question to Inkeep's QA expert model and returns the result to your Agent.

## 📦 Supported Sites

*Auto-discovered by our miner:*

<!-- AUTO-GENERATED-SITES:START -->
*   **Langfuse** (Langfuse (LLM Engineering Platform) official documentation)
*   **Render** (Render (Cloud Hosting) official documentation)
*   **Clerk** (Clerk (Authentication) official documentation)
*   **Neon** (Neon (Serverless Postgres) official documentation)
*   **Teleport** (Teleport (Access Plane) official documentation)
*   **React** (The library for web and native user interfaces.)
*   **Bootstrap** (The most popular HTML, CSS, and JavaScript framework for dev)
*   **Ragflow** (RAGFlow is a leading open-source Retrieval-Augmented Generat)
*   **Node** (Everything required to run your own Base node)
*   **Socket-io** (Realtime application framework (Node.JS server))
*   **Sway** (🌴 Empowering everyone to build reliable and efficient smart )
*   **Bun** (Incredibly fast JavaScript runtime, bundler, test runner, and package manager.)
*   **Zod** (TypeScript-first schema validation with static type inference.)
*   **Novu** (The open-source notification Inbox infrastructure. E-mail, SMS, and Push.)
*   **Litellm** (Python SDK, Proxy Server (AI Gateway) to call 100+ LLM APIs.)
*   **Posthog** (🦔 PostHog is an all-in-one developer platform for building products.)
*   **Goose** (An open source, extensible AI agent that goes beyond code suggestions.)
*   **Frigate** (NVR with realtime local object detection for IP cameras.)
*   **Fingerprintjs** (The most advanced free and open-source browser fingerprinting.)
*   **Spacetimedb** (Multiplayer at the speed of light.)
*   **Nextra** (Simple, powerful and flexible site generation framework with Next.js.)
*   **Zitadel** (ZITADEL - Identity infrastructure, simplified for you.)
*   **Opal** (Policy and data administration, distribution, and real-time )
*   **Javascript** (Official JavaScript repository for Clerk authentication)
<!-- AUTO-GENERATED-SITES:END -->

*...and any other site you add via `cli.py add`!*

## 🤝 Contributing

We love contributions!
1.  Fork the repo.
2.  Add support for more static site generators in `extractor.py`.
3.  Submit a Pull Request.

## 📄 License

MIT License.