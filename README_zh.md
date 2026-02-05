# 🔓 Inkeep MCP: 通用文档 AI 桥接器

[English](README.md) | [中文](README_zh.md)

> **解锁任意 Inkeep 文档站点的 "Ask AI" 能力。让你的 Gemini/Claude 直接连接 Langfuse、Render 等无数产品的官方知识库。**

[![MCP Compliant](https://img.shields.io/badge/MCP-Compliant-blue)](https://modelcontextprotocol.io/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Inkeep MCP** 是一个基于 **Model Context Protocol (MCP)** 的通用连接器。它在你的本地 AI 工具（Gemini CLI, Claude Desktop）与现代文档网站强大的 AI 搜索功能之间架起了一座桥梁。

它通过模拟浏览器的访问行为，允许你查询 **任何** 集成了 Inkeep 的网站，无需申请 API Key，也无需人工配置。

---

## 🧐 为什么需要它？

### 问题：知识被锁在浏览器里
Langfuse, Render, Neon 等顶尖开发工具都使用 [Inkeep](https://inkeep.com) 来提供极高质量的 AI 问答。但这些能力被锁在官网的 UI 组件里。
*   **开发者**必须离开终端去网页搜索。
*   **AI Agent** 无法通过编程方式访问这些最新的、官方验证过的知识。

### 方案：通用桥接器
本工具旨在“解放”这些知识。它作为一个通用适配器：
1.  **扫描**：自动分析目标网站（任意支持的网站）的前端代码，提取 Inkeep 配置。
2.  **连接**：使用该网站公开的访客身份进行连接（模拟正常访问）。
3.  **流式传输**：将官方的高质量问答实时转发给你的 CLI 或 Agent。

**结果**：你的 AI Agent 瞬间获得了阅读任意 Inkeep 驱动文档的能力。

---

## 🚀 快速开始

### 1. 安装

确保已安装 Python 3.8+。

```bash
git clone https://github.com/xu-xiang/inkeep-mcp.git
cd inkeep-mcp
pip install -r requirements.txt
```

### 2. 命令行使用 (CLI)

如果你想手动查询，可以直接使用 CLI 工具。

```bash
# 列出支持的文档源
python3 cli.py list

# 快速提问 (使用别名)
python3 cli.py ask langfuse "How to trace LangChain chains?"

# 交互式聊天模式
python3 cli.py chat render

# 添加任意支持 Inkeep 的新网站 (例如 Supabase)
python3 cli.py add supabase https://supabase.com/docs --desc "Supabase Docs"
```

---

## 🤖 集成到 AI Agent (MCP)

这是本项目的核心玩法。配置后，你的 AI 助手将获得“查阅文档”的技能。

### Gemini CLI

修改配置文件 `~/.gemini/config.json`:

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

### Claude Desktop

修改配置文件 `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

### ✨ 使用效果

配置完成后，你可以直接对 AI 说：

> **User**: "我想用 Langfuse 监控我的 Python 应用，怎么做？"
>
> **AI (Thinking)**:
> 1. *发现用户提到了 Langfuse。*
> 2. *调用 `ask_documentation(source="langfuse", question="python integration guide")`。*
> 3. *Inkeep MCP **模拟原文档网站身份** 连接 Inkeep 服务，完成安全验证，并流式获取最新文档解答。*
>
> **AI (Response)**: "根据 Langfuse 官方文档，你需要先安装 `pip install langfuse`，然后初始化..."

---

## 🛠️ 技术原理

1.  **智能注册表 (Registry)**: 维护一个本地映射表（`~/.inkeep/registry.json`），将简短别名 (`render`) 映射到文档 URL。启动时会自动合并最新的默认配置。
2.  **动态提取 (Dynamic Extraction)**: 连接新站点时，脚本会模拟正常浏览器访问行为，解析前端 JS Bundle，智能定位并提取 Inkeep 服务所需的配置信息。
3.  **自动过盾 (Auto-PoW)**: Inkeep 使用 Altcha 进行人机验证。本项目内置了 SHA-256 碰撞算法，能在本地毫秒级算出 Challenge 的解，合规通过服务验证。

## 📦 支持的站点

*自动化机器人发现列表：*

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
*   **Vectordbbench** (Benchmark for vector databases.)
*   **Eon** (An open-source chart and map framework for realtime data.)
*   **Kit** (Solana JavaScript SDK)
*   **Lemonsqueezy-js** (Official JavaScript SDK for Lemon Squeezy.)
<!-- AUTO-GENERATED-SITES:END -->

*...以及任何你通过 `cli.py add` 添加的站点！*

## 🤝 贡献

欢迎提交 PR 来改进提取算法或增加更多默认站点！

## 📄 许可证

MIT License.
