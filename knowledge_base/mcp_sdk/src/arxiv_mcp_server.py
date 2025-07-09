from mcp_sdk import MCPServerStdio
import os

# Set custom storage path
storage_path = "/Users/lucasmuller/Desktop/Githubg/MAAI_Tryout/mcp_server_data"

# Create the directory if it doesn't exist
os.makedirs(storage_path, exist_ok=True)

# ArXiv MCP Server Configuration
mcp_arxiv = MCPServerStdio(
    name="arxiv-mcp-server",
    params={
        "command": "uv",
        "args": [
            "tool",
            "run",
            "arxiv-mcp-server",
            "--storage-path",
            storage_path
        ],
        "env": {
            "ARXIV_STORAGE_PATH": storage_path
        }
    }
)

# Available tools:
# 1. search_papers: Search for papers with filters
#    - query: Search term
#    - max_results: Maximum number of results (default: 10)
#    - date_from: Start date (YYYY-MM-DD)
#    - categories: List of arXiv categories (e.g., ["cs.AI", "cs.LG"])
#
# 2. download_paper: Download a paper by arXiv ID
#    - paper_id: arXiv ID (e.g., "2401.12345")
#
# 3. list_papers: View all downloaded papers
#
# 4. read_paper: Access content of a downloaded paper
#    - paper_id: arXiv ID
#
# Special Prompts:
# - deep-paper-analysis: Comprehensive paper analysis workflow
#   - paper_id: arXiv ID to analyze 