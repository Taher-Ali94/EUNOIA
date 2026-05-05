from pydantic import BaseModel,Field
from typing import Any, Optional


class WebSearchResult(BaseModel):
    title: str = Field(..., description="The title of the search result")
    url: str = Field(..., description="The URL of the search result")
    snippet: str = Field(..., description="A brief snippet or summary of the search result")

class PageContent(BaseModel):
    content: str = Field(..., description="The textual content of the page")

class WebSearchResults(BaseModel):
    query: str
    count: int
    results: list[WebSearchResult]


class ToolResult(BaseModel):
    ok: bool
    message: str
    data: Optional[Any] = None