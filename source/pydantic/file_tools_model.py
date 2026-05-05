from pydantic import BaseModel
from typing import Optional, Any


class ToolResult(BaseModel):
    ok: bool
    message: str
    data: Optional[Any] = None


class FileInfo(BaseModel):
    name: str
    size: int
    created: str
    modified: str
    is_file: bool
    is_dir: bool


class FileContent(BaseModel):
    path: str
    content: str