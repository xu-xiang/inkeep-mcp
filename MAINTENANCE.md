# Inkeep API 交互分析与维护指南

本文档记录了 `inkeep_chat.py` 和 `universal_inkeep.py` 脚本的设计原理，用于后续 API 变更时的维护。

## 1. 核心流程分析

脚本模拟了从集成了 Inkeep 的文档站点（如 Langfuse, Render, Clerk, Neon 等）发起的 AI 聊天请求。其核心难点在于 **Altcha 验证协议 (PoW)** 和 **动态 API Key 提取**。

### 1.1 动态 API Key (Authorization) 提取逻辑
脚本通过“深度扫描”目标网站的前端资源来获取 API Key。

- **扫描目标**：下载首页 HTML，正则提取所有 `<script src="...">` 链接。
- **文件优先级**：脚本会优先扫描最可能包含配置的文件：
    1. 包含 `inkeep` 关键字的文件
    2. 文档布局文件 (`docs/layout`, `app/layout`)
    3. 全局入口文件 (`_app`, `app/page`)
    4. 其他所有 `.js` 文件 (作为 fallback)
- **提取正则**：支持多种配置书写风格（单/双引号、对象嵌套等）：
    - `apiKey\s*:\s*["\']([a-f0-9]{32,})["\']` (标准模式)
    - `integrationId\s*:\s*["\']([a-zA-Z0-9_-]{20,})["\']` (部分站点使用 ID)
    - `organizationId\s*:\s*["\']([a-zA-Z0-9_-]{20,})["\']`

### 1.2 验证挑战 (X-INKEEP-CHALLENGE-SOLUTION)
这是最关键的反爬机制。
- **获取**：`GET https://api.inkeep.com/v1/challenge`。
- **返回**：`{challenge, salt, signature, maxnumber}`。
- **算法 (PoW)**：SHA-256 碰撞查找。
    - 目标：找到数字 `i` (0 <= i <= maxnumber)，使得 `SHA-256(salt + str(i)) == challenge`。
- **发送**：将计算出的 `number` 和服务器返回的 `signature` 重新封装成 JSON，经 **Base64** 编码后放入请求头的 `x-inkeep-challenge-solution` 中。

## 2. 报文详情

### 2.1 聊天请求
- **URL**: `POST https://api.inkeep.com/v1/chat/completions`
- **Headers**:
    - `Authorization`: `Bearer <API_KEY>`
    - `X-Inkeep-Challenge-Solution`: `<B64_JSON_PAYLOAD>`
    - `Origin/Referer`: 必须设为**目标文档站点的 Base URL** (如 `https://render.com`)，否则会被 CORS 拦截。
- **Body**: 标准 OpenAI 格式，但模型固定为 `inkeep-qa-expert`。

## 3. 已验证支持站点
以下站点已通过 `universal_inkeep.py` 测试：
- **Langfuse**: `https://langfuse.com/` (配置在 `_app-*.js`)
- **Render**: `https://render.com/docs/` (配置在 `app/docs/layout-*.js`)
- **Clerk**: `https://clerk.com/docs` (配置在 `_app-*.js`)
- **Neon**: `https://neon.com/docs/`

## 4. 维护与故障排除

### 4.1 提取失效 (No config found)
如果脚本提示 `Could not find API Key`：
1. 打开浏览器控制台，Network 面板搜索 `chat/completions` 请求。
2. 查看其 `Authorization` 头的值。
3. 在浏览器 Sources 面板或 View Source 中全局搜索该 Key。
4. 如果 Key 出现在非 JS 文件（如 JSON）或内联 Script 中，需更新 `fetch_api_key` 中的正则或 HTML 解析逻辑。

### 4.2 403 Forbidden (Challenge Error)
如果服务器返回 403 且提示 `Challenge solution is invalid`：
1. 检查 `solve_challenge` 函数。
2. 在浏览器中查看 `/v1/challenge` 的响应格式是否变化。
3. 检查 JSON 拼装逻辑，确保所有字段（包括 `signature`）都原样返回给了服务器。

### 4.3 401 Unauthorized
说明提取到的 API Key 无效。
- 可能是提取到了错误的 Key（例如提取到了 Segment 的 key 而非 Inkeep 的）。
- 检查正则是否过于宽泛。

---
*Last Updated: 2026-01-22*