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
*   ✅ **Real-time Reading**: Empowers your Agent to query the latest official docs. No more hallucinating outdated APIs.
*   ✅ **Self-Healing System**: Built-in auto-retry and config refresh. If a site updates its API Key, the tool automatically detects and re-extracts it—zero manual intervention.
*   ✅ **Zero-Config**: No API Key registration required. It implements **intelligent frontend scanning** to extract configurations and includes a **PoW (Proof of Work) solver** to pass service verification legitimately.
*   ✅ **Workflow Loop**: Ask "How to deploy Docker on Render?" directly in Gemini CLI. The answer appears instantly without leaving your terminal.

---

## 🚀 Getting Started

### 1. Installation

Requires Python 3.8+.

```bash
git clone https://github.com/xu-xiang/inkeep-mcp.git
cd inkeep-mcp
pip install -r requirements.txt
```

### 2. CLI Usage (Human Mode)

Use it as a standalone tool to query docs from your terminal.

```bash
# List supported sources
python3 cli.py list

# Quick question (using alias)
python3 cli.py ask langfuse "How to trace LangChain chains?"

# Interactive chat mode
python3 cli.py chat render

# Add any new Inkeep-powered site (e.g., Supabase)
python3 cli.py add supabase https://supabase.com/docs --desc "Supabase Docs"
```

---

## 🤖 AI Agent Integration (MCP)

This is the core of the project. Give your AI assistant the "Read Docs" skill.

### Gemini CLI Configuration (`~/.gemini/config.json`)

```json
{
  "mcpServers": {
    "inkeep-docs": {
      "command": "python3",
      "args": ["/absolute/path/to/inkeep-mcp/mcp_server.py"],
      "env": {"PYTHONUNBUFFERED": "1"}
    }
  }
}
```

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "inkeep-docs": {
      "command": "python3",
      "args": ["/absolute/path/to/inkeep-mcp/mcp_server.py"]
    }
  }
}
```

### ✨ Experience

Once configured, just tell your AI:

> **User**: "I want to monitor my Python app with Langfuse, how?"
>
> **AI (Thinking)**:
> 1. *Identifies 'Langfuse'.*
> 2. *Calls `ask_documentation(source="langfuse", question="python integration guide")`.*
> 3. *Inkeep MCP **simulates the original doc site identity** to connect to Inkeep, solves security challenges, and streams the latest answer.*
>
> **AI (Response)**: "According to Langfuse docs, install `pip install langfuse`, then..."

---

## 🛠️ Technical Principles

1.  **Smart Registry**: Maintains a local mapping (`~/.inkeep/registry.json`) of aliases to URLs. Syncs with latest defaults on startup.
2.  **Dynamic Extraction**: Simulates legitimate browser behavior to parse frontend JS bundles and extract Inkeep service credentials (e.g., API ID).
3.  **Auto-PoW**: Inkeep uses Altcha for bot protection. We've built-in a SHA-256 solver to find the solution in milliseconds locally.

## 📦 Supported Sites (Out of the Box)

*   **Langfuse** (LLM Engineering)
*   **Render** (Cloud Hosting)
*   **Clerk** (Authentication)
*   **Neon** (Serverless Postgres)
*   *...and any site you add!*

## 🤝 Contributing

PRs are welcome to improve extraction or add default sites!

## 📄 License

MIT License.
