# Inkeep MCP Web Demo & API (Next.js Edge)

这个目录包含了 **Inkeep MCP** 的官方展示网页和演示用 API 后端。

🚀 **核心升级**：本项目已重构为纯 TypeScript 全栈架构，完全基于 Next.js + Edge Runtime 运行。无需 Python 后端，直接在浏览器边缘实现与 Inkeep 官方 API 的真实安全握手。

## 🌟 特性

- **真实连接**：通过 Next.js Edge Functions 直接与 Inkeep 建立加密连接，非模拟数据。
- **自动 PoW 破解**：利用 Web Crypto API (SHA-256) 在边缘侧毫秒级破解 Inkeep 的 Altcha 人机验证。
- **动态配置提取**：实时深度扫描目标网站的 JS 资源，智能提取最新的 `apiKey` 或 `integrationId`。
- **Markdown 引擎**：内置 VS Code 风格的代码高亮和 GFM 排版支持。
- **双语支持**：一键切换中英文。

## 🏗️ 目录结构

- `src/app/api`: Edge API 路由 (代替了原有的 Python Server)。
  - `/chat`: 核心问答接口，流式返回 (SSE)。
  - `/sites`: 返回支持的文档站点列表。
- `src/lib/inkeep`: 核心 SDK (TypeScript 版)。
  - `client.ts`: 负责协议握手、请求伪装和流式解析。
  - `extractor.ts`: 基于 Cheerio 的智能配置提取器。
  - `pow.ts`: SHA-256 工作量证明求解器。
- `src/app`: 前端 UI (Next.js App Router)。

## 🚀 快速开始

### 本地运行

无需 Python 环境，只需 Node.js 18+。

```bash
cd web
npm install
npm run dev
```

访问 `http://localhost:3000` 即可预览效果。

### 部署到 Cloudflare Pages

本项目针对 Cloudflare Pages 进行了深度优化。

1. Fork 本仓库。
2. 登录 Cloudflare Dashboard -> Pages -> Connect to Git。
3. 选择仓库，**Framework Preset** 选择 `Next.js`。
4. 部署即可。无需任何额外配置。

## 💡 注意事项

- **Edge Runtime**: API 路由运行在 Edge 环境，拥有极低的冷启动延迟。
- **WAF 策略**: 尽管我们模拟了浏览器指纹，但某些高防护站点仍可能对云端 IP 进行风控拦截。
- **生产使用**: 如需在 Claude/Gemini 等 AI 助手中使用，建议使用项目根目录下的 Python CLI 工具，以利用您本地 IP 的高信誉度。

---
由 [Inkeep-MCP](https://github.com/xu-xiang/inkeep-mcp) 核心驱动。
