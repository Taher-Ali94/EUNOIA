from pydantic import BaseModel
from typing import Optional, Any

class DirectoryEntry(BaseModel):
    name: str
    type: str
    path: str
    size: int
    size_mb: float
    created: str
    modified: str
    is_symlink: bool

class DirectoryListing(BaseModel):
    directory: str
    count: int
    files: list[DirectoryEntry]

class DirectoryInfo(BaseModel):
    name: str
    path: str
    created: str
    modified: str
    total_files: int
    total_directories: int
    total_size: int
    total_size_mb: float
    total_size_gb: float

class ToolResult(BaseModel):
    ok: bool
    message: str
    data: Optional[Any] = None