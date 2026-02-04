# Inkeep MCP Web Demo & API

这个目录包含了 **Inkeep MCP** 的官方展示网页和演示用 API 后端。

## 🌟 特性

- **实时交互终端**：直接在浏览器中测试 20+ 个官方技术文档的 AI 问答。
- **自动 PoW 破解**：前端展示了本地自动计算并绕过 Inkeep 人机验证（Altcha）的过程。
- **Markdown 支持**：完美渲染代码高亮、表格和富文本，提供一流的阅读体验。
- **双语支持**：一键切换中英文。
- **现代化架构**：基于 Next.js 15, Tailwind CSS, Framer Motion 和 FastAPI。

## 🏗️ 目录结构

- `src/`: Next.js 前端源代码。
- `backend/`: Python FastAPI 后端，负责调用核心 `InkeepClient`。
- `public/`: 静态资源文件。

## 🚀 快速开始

### 1. 启动后端 API

确保您位于项目根目录，并已安装所有依赖：

```bash
pip install fastapi uvicorn requests beautifulsoup4
python3 web/backend/main.py
```

后端将默认运行在 `http://localhost:3002`。

### 2. 启动前端页面

进入 `web` 目录并运行：

```bash
cd web
npm install
npm run dev
```

访问 `http://localhost:3000` 即可预览效果。

## 💡 注意事项

- **已测试站点**：目前注册表中预置了 22 个顶级开发工具站点。
- **通用性**：本 Demo 仅作展示，原则上任何集成了 Inkeep 的网站都可以通过本项目的核心逻辑进行访问。
- **生产使用**：如需在 Claude/Gemini 等 AI 助手中使用，请参考根目录的 MCP 配置指南。

---
由 [Inkeep-MCP](https://github.com/xu-xiang/inkeep-mcp) 核心驱动。