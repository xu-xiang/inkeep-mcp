import argparse
import sys
from inkeep_core.client import InkeepClient
from inkeep_core.registry import SiteRegistry

def main():
    parser = argparse.ArgumentParser(description="Inkeep AI Documentation Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # --- Registry Commands ---
    
    # List
    subparsers.add_parser("list", help="List all saved documentation sources")

    # Add
    add_parser = subparsers.add_parser("add", help="Add a new documentation source to registry")
    add_parser.add_argument("alias", help="Short name (e.g. 'supabase')")
    add_parser.add_argument("url", help="Documentation URL (e.g. 'https://supabase.com/docs')")
    add_parser.add_argument("--desc", help="Description", default="")

    # Remove
    rm_parser = subparsers.add_parser("remove", help="Remove a source from registry")
    rm_parser.add_argument("alias", help="Short name to remove")

    # --- Interaction Commands ---

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("source", help="Alias (e.g. 'langfuse') or URL")
    ask_parser.add_argument("question", help="The question to ask")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")
    chat_parser.add_argument("source", help="Alias (e.g. 'langfuse') or URL")

    # Clean cache
    clean_parser = subparsers.add_parser("clean", help="Clear config cache for a site")
    clean_parser.add_argument("source", help="Alias or URL")

    args = parser.parse_args()
    registry = SiteRegistry()

    # --- Handle Registry Commands ---

    if args.command == "list":
        sites = registry.list_sites()
        if not sites:
            print("Registry is empty.")
        else:
            print(f"📚 Available Documentation Sources ({len(sites)}):")
            # Calculate padding for pretty printing
            max_alias = max(len(k) for k in sites.keys())
            for alias, info in sites.items():
                print(f"  • {alias.ljust(max_alias + 2)} : {info['description']} ({info['url']})")
        return

    if args.command == "add":
        registry.add_site(args.alias, args.url, args.desc)
        print(f"✅ Added '{args.alias}' -> {args.url}")
        return

    if args.command == "remove":
        if registry.remove_site(args.alias):
            print(f"🗑️ Removed '{args.alias}'")
        else:
            print(f"❌ Alias '{args.alias}' not found.")
        return

    # --- Handle Interaction Commands ---

    if args.command in ["ask", "chat", "clean"]:
        # Resolve source to URL
        target_url = registry.get_url(args.source)
        if not target_url:
            print(f"❌ Error: Could not resolve source '{args.source}'.")
            print("Please provide a valid URL or add it to the registry using 'add'.")
            sys.exit(1)

        client = InkeepClient(target_url)

        if args.command == "clean":
            client.cache.clear_config(target_url)
            print(f"🧹 Cache cleared for {target_url}")
            return
        
        # Initialize (scan/load config)
        print(f"🔌 Connecting to {target_url} ...", end=" ")
        if not client.initialize():
            print("\n❌ Failed to initialize client. Could not find Inkeep configuration on the site.")
            sys.exit(1)
        print("Connected.")

        if args.command == "ask":
            print(f"\n❓ Asking: {args.question}\n")
            print("🤖 Answer: ", end="", flush=True)
            for chunk in client.ask(args.question):
                print(chunk, end="", flush=True)
            print("\n")
        
        elif args.command == "chat":
            print(f"\n💬 Chatting with {client.domain}")
            print("Type 'exit' to quit.\n")
            while True:
                try:
                    q = input(f"You: ")
                    if q.lower() in ['exit', 'quit']: break
                    if not q.strip(): continue
                    
                    print("AI: ", end="", flush=True)
                    for chunk in client.ask(q):
                        print(chunk, end="", flush=True)
                    print("\n")
                except KeyboardInterrupt:
                    print("\nBye!")
                    break
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
