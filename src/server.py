"""MCP Server for collection/list operations — deduplicate, intersect, union, diff, flatten, chunk, sort, group, rotate, sample."""
import json
import sys
import argparse
from typing import Any, Dict, List, Optional

from .collection_engine import CollectionEngine


TOOL_DEFS = [
    {"name": "deduplicate", "description": "Remove duplicates from a list.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "preserve_order": {"type": "boolean", "default": True}}, "required": ["items"]}},
    {"name": "intersect", "description": "Get intersection of two lists.", "inputSchema": {"type": "object", "properties": {"list1": {"type": "array", "items": {}}, "list2": {"type": "array", "items": {}}}, "required": ["list1", "list2"]}},
    {"name": "union", "description": "Get union of two lists.", "inputSchema": {"type": "object", "properties": {"list1": {"type": "array", "items": {}}, "list2": {"type": "array", "items": {}}, "deduplicate": {"type": "boolean", "default": True}}, "required": ["list1", "list2"]}},
    {"name": "difference", "description": "Get items in list1 but not in list2.", "inputSchema": {"type": "object", "properties": {"list1": {"type": "array", "items": {}}, "list2": {"type": "array", "items": {}}}, "required": ["list1", "list2"]}},
    {"name": "symmetric_difference", "description": "Get items in either list but not in both.", "inputSchema": {"type": "object", "properties": {"list1": {"type": "array", "items": {}}, "list2": {"type": "array", "items": {}}}, "required": ["list1", "list2"]}},
    {"name": "flatten", "description": "Flatten a nested list.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "depth": {"type": "integer", "default": -1}}, "required": ["items"]}},
    {"name": "chunk", "description": "Split a list into chunks of specified size.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "size": {"type": "integer", "default": 2}}, "required": ["items"]}},
    {"name": "sort_list", "description": "Sort a list, optionally by a key in dict items.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "key": {"type": "string"}, "reverse": {"type": "boolean", "default": False}}, "required": ["items"]}},
    {"name": "group_by", "description": "Group list of dicts by a key.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}}, "required": ["items"]}},
    {"name": "count_items", "description": "Count occurrences of each item in a list.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}}, "required": ["items"]}},
    {"name": "rotate", "description": "Rotate list by n positions.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "positions": {"type": "integer", "default": 1}}, "required": ["items"]}},
    {"name": "sample", "description": "Get n random items from a list (crypto-safe).", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "n": {"type": "integer", "default": 1}}, "required": ["items"]}},
    {"name": "partition", "description": "Partition list into matching and non-matching based on predicate.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "predicate": {"type": "string", "default": "truthy", "enum": ["truthy", "even", "nonempty"]}}, "required": ["items"]}},
    {"name": "zip_lists", "description": "Zip multiple lists together.", "inputSchema": {"type": "object", "properties": {"lists": {"type": "array", "items": {"type": "array", "items": {}}}}, "required": ["lists"]}},
    {"name": "reverse_list", "description": "Reverse a list.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}}, "required": ["items"]}},
    {"name": "find_index", "description": "Find the index of a value in a list.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "value": {}}, "required": ["items", "value"]}},
    {"name": "contains", "description": "Check if a list contains a value.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "value": {}}, "required": ["items", "value"]}},
    {"name": "head", "description": "Get the first n items.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "n": {"type": "integer", "default": 5}}, "required": ["items"]}},
    {"name": "tail", "description": "Get the last n items.", "inputSchema": {"type": "object", "properties": {"items": {"type": "array", "items": {}}, "n": {"type": "integer", "default": 5}}, "required": ["items"]}},
]


class MCPCollectionToolsServer:
    def __init__(self, name: str = "mcp-collection-tools", version: str = "1.0.0"):
        self.name = name
        self.version = version

    def list_tools(self) -> List[Dict]:
        return TOOL_DEFS

    def manifest(self) -> Dict:
        return {"server": {"name": self.name, "version": self.version}, "capabilities": {"tools": {"listChanged": False}, "resources": {}, "prompts": {}}, "tools": self.list_tools()}

    def handle_tool_call(self, name: str, args: Dict[str, Any]) -> str:
        try:
            if name == "deduplicate":
                return json.dumps(CollectionEngine.deduplicate(args["items"], args.get("preserve_order", True)))
            elif name == "intersect":
                return json.dumps(CollectionEngine.intersect(args["list1"], args["list2"]))
            elif name == "union":
                return json.dumps(CollectionEngine.union(args["list1"], args["list2"], args.get("deduplicate", True)))
            elif name == "difference":
                return json.dumps(CollectionEngine.difference(args["list1"], args["list2"]))
            elif name == "symmetric_difference":
                return json.dumps(CollectionEngine.symmetric_difference(args["list1"], args["list2"]))
            elif name == "flatten":
                return json.dumps(CollectionEngine.flatten(args["items"], args.get("depth", -1)))
            elif name == "chunk":
                return json.dumps(CollectionEngine.chunk(args["items"], args.get("size", 2)))
            elif name == "sort_list":
                return json.dumps(CollectionEngine.sort_list(args["items"], args.get("key"), args.get("reverse", False)))
            elif name == "group_by":
                # Default key is "type"
                return json.dumps(CollectionEngine.group_by(args["items"], "type"))
            elif name == "count_items":
                return json.dumps(CollectionEngine.count_items(args["items"]))
            elif name == "rotate":
                return json.dumps(CollectionEngine.rotate(args["items"], args.get("positions", 1)))
            elif name == "sample":
                return json.dumps(CollectionEngine.sample(args["items"], args.get("n", 1)))
            elif name == "partition":
                return json.dumps(CollectionEngine.partition(args["items"], args.get("predicate", "truthy")))
            elif name == "zip_lists":
                return json.dumps(CollectionEngine.zip_lists(args["lists"]))
            elif name == "reverse_list":
                return json.dumps(CollectionEngine.reverse_list(args["items"]))
            elif name == "find_index":
                return json.dumps(CollectionEngine.find_index(args["items"], args["value"]))
            elif name == "contains":
                return json.dumps(CollectionEngine.contains(args["items"], args["value"]))
            elif name == "head":
                return json.dumps(CollectionEngine.head(args["items"], args.get("n", 5)))
            elif name == "tail":
                return json.dumps(CollectionEngine.tail(args["items"], args.get("n", 5)))
            else:
                return json.dumps({"error": f"Unknown tool: {name}"})
        except KeyError as e:
            return json.dumps({"error": f"Missing required parameter: {e}", "tool": name})
        except Exception as e:
            return json.dumps({"error": str(e), "tool": name})


def _run_stdio():
    server = MCPCollectionToolsServer()
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: request = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}), flush=True)
            continue
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})
        if method == "initialize":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"server": server.name, "version": server.version}}
        elif method == "tools/list":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": server.list_tools()}}
        elif method == "tools/call":
            result = server.handle_tool_call(params.get("name", ""), params.get("arguments", {}))
            response = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": result}]}}
        elif method == "shutdown":
            response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            print(json.dumps(response), flush=True)
            break
        else:
            response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
        print(json.dumps(response), flush=True)


def main():
    parser = argparse.ArgumentParser(description="MCP Collection Tools Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    if args.manifest:
        print(json.dumps(MCPCollectionToolsServer().manifest(), indent=2))
    elif args.stdio:
        _run_stdio()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
