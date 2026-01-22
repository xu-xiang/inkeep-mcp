# Inkeep MCP 技术维护指南

本文档记录了 `inkeep-mcp` 的设计原理与协议细节，供后续维护与功能扩展参考。

## 1. 系统架构

项目已从单一脚本重构为模块化架构：
- **`cli.py`**: 人类交互入口，支持别名管理与交互式聊天。
- **`mcp_server.py`**: 标准 MCP Server，通过 Stdio 提供 JSON-RPC 接口。
- **`inkeep_core/`**: 核心逻辑包。
    - `client.py`: 处理请求生命周期，包括 **401 自动重试与自愈**。
    - `extractor.py`: 负责从目标站点前端代码中**动态提取**配置。
    - `pow.py`: 实现 Altcha **PoW (Proof of Work)** 破解算法。
    - `registry.py`: 负责本地站点注册表与内置“黄金站点”的同步。

## 2. 核心协议分析

### 2.1 动态配置提取 (Extraction)
工具不依赖官方 API Key，而是模拟浏览器行为：
1. 下载目标文档站首页 HTML。
2. 扫描所有 `<script src="...">`。
3. 深度分析 JS Bundle (重点是 Webpack chunks)。
4. 使用正则提取 `apiKey` 或 `integrationId`。这些值通常在前端 JS 中硬编码，且长期有效。

### 2.2 验证挑战 (X-INKEEP-CHALLENGE-SOLUTION)
Inkeep 使用 Altcha 协议进行服务保护：
- **获取**: `GET https://api.inkeep.com/v1/challenge`。
- **算法**: `SHA-256(salt + str(number)) == challenge`。
- **破解**: `pow.py` 通过从 0 到 `maxnumber` 的暴力碰撞，在本地毫秒级计算出 `number`。
- **提交**: 将结果封装为 JSON 并进行 **Base64** 编码，放入 Header。

### 2.3 自愈机制 (Self-Healing)
- **401 错误**: 当 Inkeep 返回 401（Token 过期）时，`client.py` 会自动清除本地缓存，重新触发 `extractor.py` 扫描最新 Key，并自动重试请求。
- **重定向**: 自动处理域名迁移（如从 `.tech` 迁移到 `.com`），确保 `Origin` 和 `Referer` 头始终与当前站点匹配。

## 3. 维护与排障

### 3.1 提取失效
如果 `extractor.py` 无法找到 Key：
1. 确认该网站是否仍在使用 Inkeep (检查右下角图标)。
2. 在浏览器 Network 面板查看 `chat/completions` 请求的 `Authorization` 头。
3. 如果 Key 存在但在 JS 中位置变了，需更新 `extractor.py` 中的正则模式。

### 3.2 403 Forbidden
通常是 PoW 算法变更或 `Origin` 校验失败。
1. 检查 `pow.py` 逻辑是否与 Altcha 最新标准一致。
2. 确保 `registry.py` 中的 URL 与网站实际运行的域名完全一致。

### 3.3 依赖更新
如果 Inkeep 升级了其辅助请求头（如 `x-stainless-*` 系列），需在 `client.py` 中同步更新。

---
*上次更新日期: 2026-01-22*
