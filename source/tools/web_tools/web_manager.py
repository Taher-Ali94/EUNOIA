from ddgs import DDGS
from concurrent.futures import ThreadPoolExecutor
import asyncio
import httpx
from bs4 import BeautifulSoup
from ...pydantic.web_search_model import WebSearchResult, PageContent ,WebSearchResults, ToolResult

class WebManager:
    def __init__(self,timeout:int=10):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.ddgs = DDGS(timeout=self.timeout)
        self.executor = ThreadPoolExecutor(max_workers=1)

    def search_ddgs(self,query:str,max_results:int=5):
        results = []
        try:
            for result in self.ddgs.text(query, max_results=max_results,safesearch="off",region="wt-wt"):
                results.append({
                    "title": result.get("title"),
                    "url": result.get("href"),
                    "snippet": result.get("body")
                })
            return results
        except Exception as e:
            return [ToolResult(ok=False, message=f"Error during DDGS search: {e}")]

        

    async def search(self,query:str,max_results:int=5) -> ToolResult:
        loop = asyncio.get_running_loop()
        try:
            
            results = await loop.run_in_executor(self.executor, self.search_ddgs, query, max_results)
            return ToolResult(
                ok=True,
                message=f"Search completed for query: {query}",
                data=WebSearchResults(
                    query=query,
                    count=len(results),
                    results=[WebSearchResult(**result) for result in results]
                )
            )
            
        except Exception as e:
            return ToolResult(ok=False, message=f"Error during web search: {e}")
        

    async def get_page_content(self, url: str) -> ToolResult:
        try:
        
            response = await self.client.get(
                url,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for script in soup(["script", "style"]):
                    script.extract()
                return ToolResult(ok=True, message=f"Content fetched from {url}", data=PageContent(content=soup.get_text(separator='\n', strip=True)))
            else:
                return ToolResult(ok=False, message=f"Failed to fetch content from {url}. Status code: {response.status_code}")
        
        except Exception as e:
            return ToolResult(ok=False, message=f"Error fetching page content: {e}")

    def search_ddgs_news(self,query:str,max_results:int=5):
        results = []
        try:
            for result in self.ddgs.news(query, max_results=max_results,safesearch="off",region="wt-wt"):
                results.append({
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "snippet": result.get("body")
                })
            return results
        except Exception as e:
            return [ToolResult(ok=False, message=f"Error during DDGS news search: {e}")]

        

    async def search_news(self,query:str,max_results:int=5) -> ToolResult:
        loop = asyncio.get_running_loop()
        try:
            results = await loop.run_in_executor(self.executor, self.search_ddgs_news, query, max_results)
            return ToolResult(
                ok=True,
                message=f"News search completed for query: {query}",
                data=WebSearchResults(
                    query=query,
                    count=len(results),
                    results=[WebSearchResult(**result) for result in results]
                )
            )
        except Exception as e:
            return ToolResult(ok=False, message=f"Error during news search: {e}")
    
    async def close(self):
        self.executor.shutdown(wait=False)
        await self.client.aclose()

"""
search(query,max_results) -> ToolResult with WebSearchResults data
ToolResult contains the fields ok: bool, message: str, data: WebSearchResults
data -> contains query: str, count: int, results: List[WebSearchResult]
WebSearchResult contains the fields title: str, url: str, snippet: str

get_page_content(url) -> ToolResult with PageContent data
ToolResult contains the fields ok: bool, message: str, data: PageContent
PageContent contains the field content: str

search_news(query,max_results) -> ToolResult with WebSearchResults data
ToolResult contains the fields ok: bool, message: str, data: WebSearchResults
data -> contains query: str, count: int, results: List[WebSearchResult]
WebSearchResult contains the fields title: str, url: str, snippet: str

"""

"""
create a subagent for web_search that can search for content and news and fetch page content.
The subagent will then return the entire summary with relevant links and content to the main agent
which can then use that information to answer the user's query. The subagent should be able to handle
multiple queries and return results in a structured format that the main agent can easily parse and use.
"""