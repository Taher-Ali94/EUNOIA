# source/tasks/directory_manager.py
import asyncio
from importlib.resources import path
from pathlib import Path
from datetime import datetime
import shutil
from concurrent.futures import ThreadPoolExecutor

from requests.help import info
from ...pydantic.directory_tools_model import DirectoryEntry, DirectoryListing, DirectoryInfo, ToolResult

class DirectoryManager:
    def __init__(self, base_path: str = "./"):
        self.base_path = Path(base_path).resolve()
        self.executor = ThreadPoolExecutor(max_workers=1)

    def safe_path(self, path: str):

        try:
            requested_path = Path(path)
            resolved_path = (self.base_path / requested_path).resolve()

            if not resolved_path.is_relative_to(self.base_path):
                return None
            
            return resolved_path
        except Exception as e:
            print(f"Error resolving path: {e}")
            return None

    async def list_files(
        self,
        path: str = ".",
        recursive: bool = False,
        pattern: str = "*"
    ):
        safe_path = self.safe_path(path)

        if not safe_path or not safe_path.is_dir():
            return  ToolResult(ok=False, message=f"{path} is not a directory or does not exist.")
        
        try:
            loop = asyncio.get_running_loop()
            files = await loop.run_in_executor(
                self.executor,
                self._list_files_sync,
                safe_path,
                recursive,
                pattern
            )
            
            return ToolResult(
                ok=True,
                message=f"Listed files in {path}.",
                data=DirectoryListing(
                    directory=str(safe_path),
                    count=len(files),
                    files=[DirectoryEntry(**f) for f in files]
                )
            )
        except Exception as e:
            print(f"Error listing files: {e}")
            return ToolResult(ok=False, message=f"Error listing files in {path}.")

    def _list_files_sync(
        self,
        path: Path,
        recursive: bool,
        pattern: str
    ):
        files = []
        
        glob_method = path.rglob if recursive else path.glob
        
        for file_path in sorted(glob_method(pattern)):
            try:
                stat = file_path.stat()
                
                files.append({
                    "name": file_path.name,
                    "type": "directory" if file_path.is_dir() else "file",
                    "path": str(file_path.relative_to(self.base_path)),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_symlink": file_path.is_symlink(),
                })
                return files
            except Exception as e:
                print(f"Error accessing {file_path}: {e}")
                continue
        


    async def create_directory(self, path: str) :

        safe_path = self.safe_path(path)

        if not safe_path:
            return ToolResult(ok=False, message=f"Invalid path: {path}.")
        
        if safe_path.exists():
            if safe_path.is_dir():
                return ToolResult(ok=False, message=f"{path} already exists.")
            else:
                return ToolResult(ok=False, message=f"{path} exists but is not a directory.")
        
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self.executor,
                safe_path.mkdir,
                True, 
                True   
            )
            return ToolResult(ok=True, message=f"Directory {path} created successfully.")
        except Exception as e:
            print(f"Error creating directory: {e}")
            return ToolResult(ok=False, message=f"Error creating {path}.")

    async def delete_directory(
        self,
        path: str,
        recursive: bool = False
    ):

        safe_path = self.safe_path(path)

        if not safe_path or not safe_path.exists():
            return ToolResult(ok=False, message=f"{path} does not exist.")
        
        if not safe_path.is_dir():
            return ToolResult(ok=False, message=f"{path} is not a directory.")
        
        try:
            loop = asyncio.get_running_loop()
            
            if recursive:
                await loop.run_in_executor(
                    self.executor,
                    shutil.rmtree,
                    str(safe_path)
                )
            else:
                await loop.run_in_executor(
                    self.executor,
                    safe_path.rmdir
                )
            
            return ToolResult(ok=True, message=f"Directory {path} deleted successfully.")
        except Exception as e:
            print(f"Error deleting directory: {e}")
            return ToolResult(ok=False, message=f"Error deleting {path}.")

    async def get_directory_info(self, path: str = "."):

        safe_path = self.safe_path(path)

        if not safe_path or not safe_path.exists():
            return ToolResult(ok=False, message=f"{path} does not exist.")
        
        if not safe_path.is_dir():
            return ToolResult(ok=False, message=f"{path} is not a directory.")
        
        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(
                self.executor,
                self._get_directory_info_sync,
                safe_path
            )
            return ToolResult(
                ok=True,
                message=f"Directory info retrieved for {path}.",
                data=DirectoryInfo(**info)
            )
        except Exception as e:
            print(f"Error getting directory info: {e}")
            return ToolResult(ok=False, message=f"Error getting info for {path}.")

    def _get_directory_info_sync(self, path: Path):
        try:
            stat = path.stat()

            total_files = 0
            total_dirs = 0
            total_size = 0
            
            for item in path.rglob("*"):
                try:
                    if item.is_file():
                        total_files += 1
                        total_size += item.stat().st_size
                    elif item.is_dir():
                        total_dirs += 1
                except Exception:
                    continue
            
            return {
                "name": path.name,
                "path": str(path),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "total_files": total_files,
                "total_directories": total_dirs,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            }
        except Exception as e:
            print(f"Error calculating directory info: {e}")


    async def rename_directory(self, old_path: str, new_path: str):
        
        safe_old_path = self.safe_path(old_path)

        if not safe_old_path or not safe_old_path.is_dir():
            return ToolResult(ok=False, message=f"{old_path} is not a directory or does not exist.")
        
        try:
            new_full_path = self.safe_path(str(safe_old_path.parent / new_path))

            if not new_full_path:
                return ToolResult(ok=False, message=f"Invalid new path: {new_path}.")
            
            if not str(new_full_path).startswith(str(self.base_path)):
                return ToolResult(ok=False, message=f"Invalid new path: {new_path}.")
            
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self.executor,
                safe_old_path.rename,
                new_full_path
            )
            
            return ToolResult(ok=True, message=f"Directory renamed from {old_path} to {new_path} successfully.")
        except Exception as e:
            print(f"Error renaming directory: {e}")
            return ToolResult(ok=False, message=f"Error renaming {old_path}.")
