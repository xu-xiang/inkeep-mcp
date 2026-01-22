# 📚 Inkeep MCP: AI 开发者的文档“外挂”

[English](README.md) | [中文](README_zh.md)

> **将任何技术文档网站转化为 AI Agent 的智能知识库。让你的 Gemini/Claude 直接阅读 Langfuse、Render、Clerk 等主流产品的最新官方文档。**

[![MCP Compliant](https://img.shields.io/badge/MCP-Compliant-blue)](https://modelcontextprotocol.io/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🧐 背景与痛点

### 什么是 Inkeep？
[Inkeep](https://inkeep.com) 是目前全球最流行的**技术文档 AI 搜索服务**。许多你耳熟能详的技术产品——**Langfuse, Render, Clerk, Neon, PlanetScale, PostHog**——都在使用 Inkeep 来驱动它们官网右下角的 "Ask AI" 功能。因为它专门针对技术文档、API Reference 进行了优化，回答准确率极高，深受开发者喜爱。

### 我们遇到了什么问题？
虽然 Inkeep 很好用，但它**被“困”在了浏览器里**：
1.  **开发者的割裂感**：当你在终端或 IDE 里写代码报错时，你必须切出 IDE -> 打开浏览器 -> 搜官网 -> 点 Ask AI -> 问问题 -> 把代码复制回来。这打断了心流。
2.  **AI Agent 的无知**：你的 Gemini/Claude/Cursor 很聪明，但它们的训练数据是滞后的。它们不知道 Langfuse 昨天刚发布的 `v3` SDK 怎么用。更糟糕的是，它们无法通过标准方式去“使用”官网那个需要复杂的 JS 渲染和前端交互的 "Ask AI" 组件。

## 💡 我们的解决方案

**Inkeep MCP** 是一个基于 **Model Context Protocol (MCP)** 的桥梁工具。

它通过**协议分析**和**自动化封装技术**，将任意集成了 Inkeep 的文档网站，转化为一个标准的、可被 AI 调用的 **工具函数 (Tool)**。

### 核心价值
*   ✅ **赋予 AI "实时"阅读能力**：让你的 Agent 直接查询最新的官方文档，不再瞎编过时的 API。
*   ✅ **智能自愈系统**：内置自动重试与配置刷新机制。如果目标网站更新了 API Key，工具会自动检测并重新提取，全程无需人工干预。
*   ✅ **零配置黑科技**：无需申请 API Key。本项目实现了**智能前端扫描**，自动从文档网页中提取配置信息，并内置了 **PoW (工作量证明) 求解器** 来合规通过服务验证。
*   ✅ **开发流闭环**：直接在 Gemini CLI 或 Claude Desktop 中问 "Render 怎么部署 Docker？"，答案即刻呈现，无需离开当前工作流。

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

### Gemini CLI 配置 (`~/.gemini/config.json`)

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

### Claude Desktop 配置

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

## 📦 开箱即用的站点

默认已内置以下热门技术文档源，且支持无限扩展：

*   **Langfuse** (LLM Engineering)
*   **Render** (Cloud Hosting)
*   **Clerk** (Authentication)
*   **Neon** (Serverless Postgres)
*   *...任何使用 Inkeep 的网站均可添加！*

## 🤝 贡献

欢迎提交 PR 来改进提取算法或增加更多默认站点！

## 📄 许可证

MIT License.
