# splunk_saved_search_mcp_server.py
"""
MCP Server that retrieves Splunk Saved Search details from Splunk REST API
"""

import fastmcp
import json
import requests
import os
from typing import Dict, List
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create MCP server
mcp = fastmcp.FastMCP("splunk-saved-search-server")

class SplunkSavedSearchServer:
    """
    Server for retrieving Splunk Saved Search details via REST API
    """
    
    def __init__(self):
        self.splunk_host = os.getenv("SPLUNK_HOST", "localhost")
        self.splunk_port = os.getenv("SPLUNK_PORT", "8089")
        self.username = os.getenv("SPLUNK_USERNAME", "admin")
        self.password = os.getenv("SPLUNK_PASSWORD", "password")
        self.app_name = os.getenv("SPLUNK_APP", "search")
        
        # Base URL for Splunk REST API
        self.base_url = f"https://{self.splunk_host}:{self.splunk_port}"
        
        # Session for authentication
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False
        
        # Test connection silently
        try:
            response = self.session.get(
                f"{self.base_url}/services/server/info",
                params={"output_mode": "json"},
                timeout=5
            )
        except Exception as e:
            pass

# Create server instance
server = SplunkSavedSearchServer()

@mcp.tool()
def get_saved_searches_list(app: str = None) -> str:
    """
    Get list of all Saved Searches in the specified app
    Excludes disabled Saved Searches
    
    Args:
        app: App name (optional, uses default app if not specified)
    """
    if app is None:
        app = server.app_name
    
    try:
        url = f"{server.base_url}/servicesNS/admin/{app}/saved/searches"
        params = {
            "output_mode": "json",
            "count": 0
        }
        
        response = server.session.get(url, params=params)
        
        if response.status_code == 200:
            all_searches = response.json().get("entry", [])
            
            searches = []
            for entry in all_searches:
                content = entry.get("content", {})
                
                # Skip disabled searches
                is_disabled = content.get("disabled", False) == True
                if is_disabled:
                    continue
                
                search_info = {
                    "name": entry.get("name", ""),
                    "description": content.get("description", ""),
                    "owner": entry.get("acl", {}).get("owner", "")
                }
                searches.append(search_info)
            
            return json.dumps({
                "status": "success",
                "app": app,
                "count": len(searches),
                "saved_searches": searches
            }, indent=2)
        
        else:
            return json.dumps({
                "status": "error",
                "error": f"Failed to retrieve Saved Searches: {response.status_code}"
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool()
def get_saved_search_details(search_name: str, app: str = None) -> str:
    """
    Get detailed information about a specific Saved Search
    Includes name, description, and SPL
    
    Args:
        search_name: Name of the Saved Search
        app: App name (optional, uses default app if not specified)
    """
    if app is None:
        app = server.app_name
    
    if not search_name:
        return json.dumps({
            "status": "error",
            "error": "search_name is required"
        }, indent=2)
    
    try:
        encoded_search_name = quote(search_name, safe='')
        url = f"{server.base_url}/servicesNS/admin/{app}/saved/searches/{encoded_search_name}"
        params = {
            "output_mode": "json"
        }
        
        response = server.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("entry"):
                entry = data["entry"][0]
                content = entry.get("content", {})
                
                search_details = {
                    "name": entry.get("name", ""),
                    "description": content.get("description", ""),
                    "spl": content.get("search", ""),
                    "owner": entry.get("acl", {}).get("owner", ""),
                    "updated": entry.get("updated", ""),
                    "is_scheduled": content.get("is_scheduled", "0") == "1",
                    "cron_schedule": content.get("cron_schedule", "")
                }
                
                return json.dumps({
                    "status": "success",
                    "app": app,
                    "search": search_details
                }, indent=2)
        
        return json.dumps({
            "status": "error",
            "error": f"Saved Search '{search_name}' not found"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool()
def get_saved_searches_by_pattern(pattern: str, app: str = None) -> str:
    """
    Get Saved Searches matching a name pattern
    
    Args:
        pattern: Search name pattern to match (e.g., "network", "delay")
        app: App name (optional, uses default app if not specified)
    """
    if app is None:
        app = server.app_name
    
    if not pattern:
        return json.dumps({
            "status": "error",
            "error": "pattern is required"
        }, indent=2)
    
    try:
        url = f"{server.base_url}/servicesNS/admin/{app}/saved/searches"
        params = {
            "output_mode": "json",
            "count": 0
        }
        
        response = server.session.get(url, params=params)
        
        if response.status_code == 200:
            all_searches = response.json().get("entry", [])
            
            # Filter by pattern
            matching_searches = []
            for entry in all_searches:
                content = entry.get("content", {})
                
                # Skip disabled searches
                is_disabled = content.get("disabled", False) == True
                if is_disabled:
                    continue
                
                search_name = entry.get("name", "")
                if pattern.lower() in search_name.lower():
                    content = entry.get("content", {})
                    search_detail = {
                        "name": search_name,
                        "description": content.get("description", ""),
                        "spl": content.get("search", ""),
                        "disabled": content.get("disabled", False)
                    }
                    matching_searches.append(search_detail)
            
            return json.dumps({
                "status": "success",
                "app": app,
                "pattern": pattern,
                "count": len(matching_searches),
                "saved_searches": matching_searches
            }, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "error": f"Failed to retrieve Saved Searches: {response.status_code}"
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

if __name__ == "__main__":
    mcp.run()
