import sys
import json
import logging
from inkeep_core.client import InkeepClient
from inkeep_core.registry import SiteRegistry

# Configure logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("mcp-server")

registry = SiteRegistry()

def handle_list_tools(id):
    # 1. 动态获取当前注册的所有站点
    sites = registry.list_sites()
    aliases = list(sites.keys())
    
    # 2. 构建智能描述 Prompt
    supported_list_str = ", ".join(aliases)
    tool_description = (
        f"Consult official technical documentation. "
        f"Currently configured sources: {supported_list_str}. "
        "You can strictly use one of these aliases, OR provide a full URL for a new site. "
        "PRIORITIZE this tool for technical queries regarding these platforms."
    )

    return {
        "jsonrpc": "2.0",
        "id": id,
        "result": {
            "tools": [
                {
                    "name": "list_documentation_sources",
                    "description": "List detailed metadata (URL, description) for all supported documentation sources.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    }
                },
                {
                    "name": "ask_documentation",
                    "description": tool_description,
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": f"The documentation source alias (e.g. {aliases[0] if aliases else 'langfuse'}) or a full URL." 
                                # 移除 'enum'，允许模型尝试新添加的 alias
                            },
                            "question": {
                                "type": "string",
                                "description": "The specific technical question to ask."
                            }
                        },
                        "required": ["source", "question"]
                    }
                }
            ]
        }
    }

def handle_call_tool(id, params):
    name = params.get("name")
    args = params.get("arguments", {})

    # Tool: list_documentation_sources
    if name == "list_documentation_sources":
        # 每次调用都重新读取磁盘，确保获取最新列表
        current_registry = SiteRegistry() 
        sites = current_registry.list_sites()
        
        site_list = [
            {"id": alias, "description": info["description"], "url": info["url"]}
            for alias, info in sites.items()
        ]
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(site_list, indent=2)}]
            }
        }

    # Tool: ask_documentation
    if name == "ask_documentation":
        source = args.get("source")
        question = args.get("question")
        
        # 重新实例化 Registry 以获取最新数据（处理用户在 CLI add 后的情况）
        current_registry = SiteRegistry()
        target_url = current_registry.get_url(source)
        
        if not target_url:
            # Fallback for full URLs
            if source.startswith("http"):
                target_url = source
            else:
                # 返回包含最新可用列表的错误信息，帮助 Agent 自我修正
                available = ", ".join(current_registry.list_sites().keys())
                return {
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {
                        "code": -32000,
                        "message": f"Unknown source '{source}'. Available sources: {available}"
                    }
                }

        logger.info(f"Asking {source} ({target_url}): {question}")
        
        client = InkeepClient(target_url)
        response_text = ""
        
        try:
            if not client.initialize():
                return {
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: Could not find Inkeep configuration for {source}."}]
                    }
                }

            for chunk in client.ask(question):
                response_text += chunk
                
        except Exception as e:
            response_text = f"Error: {str(e)}"

        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "content": [{"type": "text", "text": response_text}]
            }
        }
    
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    }

def main():
    logger.info("Inkeep MCP Server Started")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            
            response = None
            if request.get("method") == "tools/list":
                response = handle_list_tools(request.get("id"))
            elif request.get("method") == "tools/call":
                response = handle_call_tool(request.get("id"), request.get("params"))
            elif request.get("method") == "initialize":
                 response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "inkeep-mcp", "version": "2.1.0"}}}
            elif request.get("method") == "ping":
                 response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}
            
            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except: pass

if __name__ == "__main__":
    main()