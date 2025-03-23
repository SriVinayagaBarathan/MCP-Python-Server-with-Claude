from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os
from bs4 import BeautifulSoup
load_dotenv()

mcp = FastMCP("docs")

USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
}

async def search_web(query: str) -> dict | None:
    payload = json.dumps({
        "q": query,
        "gl": "us"  # Specify country for more consistent results
    })

    headers = {
        "X-API-KEY": "59b94a2e02a38d80be2a944160418898123c5601",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Error making request: {e}")
            return {"organic": []}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {"organic": []}
  
async def fetch_url(url: str) -> str:
    """Fetch and extract text content from a URL."""
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
        try:
            response = await client.get(url, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator="\n")
            
            # Remove extra whitespace
            lines = (line.strip() for line in text.splitlines())
            text = "\n".join(line for line in lines if line)
            
            return text
        except httpx.TimeoutException:
            return "Error: Timeout while fetching URL"
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP status error {e.response.status_code} while fetching URL"
        except Exception as e:
            return f"Error: {str(e)} while fetching URL"

@mcp.tool()  
async def get_docs(query: str, library: str) -> str:
    """
    Search the latest docs for a given query and library.
    Supports langchain, openai, and llama-index.

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs
    """
    if library not in docs_urls:
        return f"Library {library} not supported. Supported libraries: {', '.join(docs_urls.keys())}"
    
    site_query = f"site:{docs_urls[library]} {query}"
    results = await search_web(site_query)
    
    # Check if we have organic results
    if not results or "organic" not in results or len(results["organic"]) == 0:
        return f"No documentation found for '{query}' in {library}."
    
    combined_text = ""
    urls_processed = []
    
    # Process the first 2-3 results only to avoid excessive response sizes
    for i, result in enumerate(results["organic"][:3]):
        if "link" not in result:
            continue
            
        url = result["link"]
        urls_processed.append(url)
        
        # Add separator between different sources
        if combined_text:
            combined_text += "\n\n" + "=" * 50 + "\n\n"
        
        # Add source information
        combined_text += f"SOURCE: {url}\n"
        if "title" in result:
            combined_text += f"TITLE: {result['title']}\n"
        combined_text += "-" * 50 + "\n\n"
        
        # Fetch and add content
        content = await fetch_url(url)
        # Truncate very long responses to a reasonable size
        if len(content) > 5000:
            content = content[:5000] + "...\n[Content truncated due to length]"
        combined_text += content
    
    if not urls_processed:
        return f"Found results for '{query}' in {library}, but couldn't extract content."
    
    return combined_text

if __name__ == "__main__":
    mcp.run(transport="stdio")