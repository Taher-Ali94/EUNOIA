import json
from .file_tools.file_manager import FileManager
from .file_tools.directory_manager import DirectoryManager
from .web_tools.web_search import WebSearchTool
from typing import Any

def model_to_dict(value: Any):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [model_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {k: model_to_dict(v) for k, v in value.items()}
    return value

class ToolRegistry:
    def __init__(self, base_path: str = "./sandbox"):
        self.file_manager = FileManager(base_path)
        self.directory_manager = DirectoryManager(base_path)
        self.web_manager = WebSearchTool()

    def parse_json_input(self,raw :str | None):
        if raw is None:
            return {}
        
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception as e:
                return raw.strip()
            
        return raw
    
    async def execute(self,tool_name:str,raw_input:str | None):
        input_data = self.parse_json_input(raw_input)

        if tool_name == "web_search":
            query = input_data.get("query") if isinstance(input_data, dict) else None
            max_results = input_data.get("max_results", 5) if isinstance(input_data, dict) else 5
            result = await self.web_manager.search(query, max_results)
            return model_to_dict(result)
        
        if tool_name == "search_news":
            query = input_data.get("query") if isinstance(input_data, dict) else str(input_data)
            max_results = input_data.get("max_results", 5) if isinstance(input_data, dict) else 5
            result = await self.web_manager.search_news(query=query, max_results=max_results)
            return model_to_dict(result)
        
        if tool_name == "get_page_content":
            url = input_data.get("url") if isinstance(input_data, dict) else str(input_data)
            result = await self.web_manager.get_page_content(url=url)
            return model_to_dict(result)

        if tool_name == "read_file":
            path = input_data.get("path") if isinstance(input_data, dict) else str(input_data)
            result = await self.file_manager.read_file(path=path)
            return model_to_dict(result)

        if tool_name == "write_file":
            if not isinstance(input_data, dict):
                return {"ok": False, "message": "write_file requires JSON input with path and content."}
            result = await self.file_manager.write_file(
                path=input_data.get("path", ""),
                content=input_data.get("content", ""),
                append=input_data.get("append", True),
            )
            return model_to_dict(result)

        if tool_name == "list_files":
            if isinstance(input_data, dict):
                result = await self.directory_manager.list_files(
                    path=input_data.get("path", "."),
                    recursive=input_data.get("recursive", False),
                    pattern=input_data.get("pattern", "*"),
                )
            else:
                result = await self.directory_manager.list_files(path=str(input_data))
            return model_to_dict(result)

        if tool_name == "get_directory_info":
            path = input_data.get("path", ".") if isinstance(input_data, dict) else str(input_data)
            result = await self.directory_manager.get_directory_info(path=path)
            return model_to_dict(result)

        if tool_name == "create_directory":
            path = input_data.get("path") if isinstance(input_data, dict) else str(input_data)
            result = await self.directory_manager.create_directory(path=path)
            return model_to_dict(result)

        if tool_name == "delete_directory":
            path = input_data.get("path") if isinstance(input_data, dict) else str(input_data)
            result = await self.directory_manager.delete_directory(path=path)
            return model_to_dict(result)
        
        if tool_name == "rename_directory":
            if not isinstance(input_data, dict):
                return {"ok": False, "message": "rename_directory requires JSON input with old_path and new_path."}
            result = await self.directory_manager.rename_directory(
                old_path=input_data.get("old_path", ""),
                new_path=input_data.get("new_path", "")
            )
            return model_to_dict(result)

        return {"ok": False, "message": f"Unknown tool: {tool_name}"}
    
    async def close(self):
        await self.web_manager.close()
