import asyncio
from pathlib import Path
from datetime import datetime
import shutil
from concurrent.futures import ThreadPoolExecutor
from ...pydantic.file_tools_model import FileInfo, FileContent, ToolResult


class FileManager:
    def __init__(self,base_path:str = "./"):
        self.base_path = Path(base_path).resolve()
        self.max_file_size = 5 * 1024 * 1024  # 5 MB
        self.executor = ThreadPoolExecutor(max_workers=1)


    def safe_path(self, path: str):
        try:
            requested_path = Path(path)
            resolved_path = (self.base_path / requested_path).resolve()

            if not resolved_path.is_relative_to(self.base_path):
                return None, ToolResult(ok=False, message=f"Access denied: {path} is outside of the base directory.")
            
            return resolved_path ,None
        except Exception as e:
            return None, ToolResult(ok=False, message=f"Error resolving {path}: {e}.")

    async def read_file(self,path:str):
        safe_path ,error = self.safe_path(path)

        if error:
            return error

        if not safe_path or not safe_path.exists():
            return ToolResult(ok=False, message=f"{path} does not exist.")
        
        if not safe_path.is_file():
            return ToolResult(ok=False, message=f"{path} is not a file.")
        
        try:
            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(self.executor, safe_path.read_text,"utf-8")
            return ToolResult(ok=True, message=f"{path} read successfully.", data=FileContent(path=str(safe_path), content=content))
        except UnicodeDecodeError:
            return ToolResult(ok=False, message=f"File is binary: {path}.")
        except Exception as e:
            return ToolResult(ok=False, message=f"Error reading {path}: {e}")
        

    def get_file_info(self,path:str):
        safe_path,error  = self.safe_path(path)

        if error:
            return error

        if not safe_path or not safe_path.exists():
            return ToolResult(ok=False, message=f"{path} does not exist.")
        
        try:
            info = {
                "name": safe_path.name,
                "size": safe_path.stat().st_size,
                "created": datetime.fromtimestamp(safe_path.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(safe_path.stat().st_mtime).isoformat(),
                "is_file": safe_path.is_file(),
                "is_dir": safe_path.is_dir()
            }
            return ToolResult(ok=True, message=f"Info for {path} retrieved successfully.", data=FileInfo(**info))
        except Exception as e:
            return ToolResult(ok=False, message=f"Error getting info for {path}: {e}")

    async def create_file(self,path:str,content:str="",overwrite:bool=False):
        safe_path,error = self.safe_path(path)

        if error:
            return error
        
        if safe_path.exists() and not overwrite:
            return ToolResult(ok=False, message=f"{path} already exists.")
        
        try:
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, safe_path.write_text, content, "utf-8")
            return ToolResult(ok=True, message=f"{path} created successfully.")
        
        except Exception as e:
            return ToolResult(ok=False, message=f"Error creating {path}: {e}.")
        
    async def write_file(self,path:str,content:str,append:bool=False):
        safe_path,error = self.safe_path(path)

        if error:
            return error
        
        try:
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            loop = asyncio.get_running_loop()
            
            if append:
                current = await loop.run_in_executor(
                    self.executor,
                    safe_path.read_text,
                    "utf-8"
                ) if safe_path.exists() else ""
                new_content = current + content
            else:
                new_content = content
            
            await loop.run_in_executor(
                self.executor,
                safe_path.write_text,
                new_content,
                "utf-8"
            )
            return ToolResult(ok=True, message=f"{path} written successfully.")
        except Exception as e:
            return ToolResult(ok=False, message=f"Error writing {path}: {e}.")
        

    async def delete_file(self,path:str):
        safe_path,error = self.safe_path(path)

        if error:
            return error
        
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, safe_path.unlink)
            return ToolResult(ok=True, message=f"{path} deleted successfully.")
        except Exception as e:
            return ToolResult(ok=False, message=f"Error deleting {path}: {e}.")
        

    async def rename_file(self,old_path:str,new_path:str):
        safe_old_path, old_error = self.safe_path(old_path)
        safe_new_path, new_error = self.safe_path(new_path)

        if old_error:
            return old_error
        
        if new_error:
            return new_error

        if not safe_old_path or not safe_old_path.exists():
            return ToolResult(ok=False, message=f"{old_path} does not exist.")
        
        if not safe_new_path:
            return ToolResult(ok=False, message=f"Invalid new path: {new_path}.") 
        
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, shutil.move, str(safe_old_path), str(safe_new_path))
            return ToolResult(ok=True, message=f"{old_path} renamed to {new_path} successfully.")
        except Exception as e:
            return ToolResult(ok=False, message=f"Error renaming {old_path} to {new_path}: {e}.")


"""
Async functions:
create_file(file_name:str, content:str="", overwrite:bool=False) -> ToolResult
ToolResult contains the fields ok: bool, message: str

write_file(file_name:str, content:str, append:bool=False) -> ToolResult
ToolResult contains the fields ok: bool, message: str

read_file(file_name:str) -> ToolResult with FileContent data
ToolResult contains the fields ok: bool, message: str, data: FileContent
FileContent contains the fields path: str, content: str

reanme_file(old_name:str, new_name:str) -> ToolResult
ToolResult contains the fields ok: bool, message: str

delete_file(file_name:str) -> ToolResult
ToolResult contains the fields ok: bool, message: str

Sync functions:
get_file_info(file_name:str) -> ToolResult with FileInfo data
ToolResult contains the fields ok: bool, message: str, data: FileInfo
FileInfo contains the fields name: str, size: int, created: str, modified: str, is_file: bool, is_dir: bool
"""

"""
Create subagent for file management tasks given to the main agent that can create, read, write, rename, and delete files,
as well as get file info. All operations should be contained within a specified base directory for security.
return the status back to the main agent.
"""