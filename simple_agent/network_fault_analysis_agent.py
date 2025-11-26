# network_fault_analysis_agent.py
"""
Simple Network Fault Analysis Agent using Splunk MCP Server
Demonstrates slot-based analysis with Saved Searches
"""

from mcp.server import Server
import json
import requests
from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class Slot:
    """Represents a slot to be filled during analysis"""
    name: str
    description: str
    search_name: str
    filled: bool = False
    value: Optional[Any] = None

class NetworkFaultAnalysisAgent:
    """
    MCP Agent for network fault diagnosis
    Uses Saved Searches to fill slots for analysis
    """
    
    def __init__(self, splunk_mcp_url: str, auth_token: str):
        self.server = Server("network-fault-analysis-agent")
        self.splunk_mcp_url = splunk_mcp_url
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # Define required slots for network fault analysis
        self.slots = {
            "delayed_nodes": Slot(
                name="delayed_nodes",
                description="Network nodes experiencing high latency",
                search_name="get_delayed_nodes"
            ),
            "network_topology": Slot(
                name="network_topology",
                description="Network topology and connection status",
                search_name="get_network_topology"
            )
        }
        
        self.setup_tools()
    
    def setup_tools(self):
        """Register MCP tools"""
        
        @self.server.call_tool()
        async def analyze_network_fault(arguments: dict) -> str:
            """
            Analyze network fault using slot-based approach
            
            Arguments:
                time_range: Time range for analysis (default: 24h)
            """
            time_range = arguments.get("time_range", "24h")
            
            # Execute analysis workflow
            result = await self._analyze_network_fault(time_range)
            
            return json.dumps(result, indent=2)
        
        @self.server.call_tool()
        async def get_delayed_nodes(arguments: dict) -> str:
            """
            Retrieve delayed nodes data
            Fills the 'delayed_nodes' slot
            
            Arguments:
                time_range: Time range for search
            """
            time_range = arguments.get("time_range", "24h")
            
            # Execute Saved Search
            result = await self._execute_saved_search(
                "get_delayed_nodes",
                time_range
            )
            
            # Update slot
            self.slots["delayed_nodes"].value = result
            self.slots["delayed_nodes"].filled = True
            
            return json.dumps({
                "slot": "delayed_nodes",
                "status": "filled",
                "data": result
            }, indent=2)
        
        @self.server.call_tool()
        async def get_network_topology(arguments: dict) -> str:
            """
            Retrieve network topology data
            Fills the 'network_topology' slot
            
            Arguments:
                time_range: Time range for search
            """
            time_range = arguments.get("time_range", "24h")
            
            # Execute Saved Search
            result = await self._execute_saved_search(
                "get_network_topology",
                time_range
            )
            
            # Update slot
            self.slots["network_topology"].value = result
            self.slots["network_topology"].filled = True
            
            return json.dumps({
                "slot": "network_topology",
                "status": "filled",
                "data": result
            }, indent=2)
        
        @self.server.call_tool()
        async def generate_diagnosis_report(arguments: dict) -> str:
            """
            Generate diagnosis report after all slots are filled
            Provides recommendations based on collected data
            """
            # Check if all slots are filled
            unfilled_slots = [
                name for name, slot in self.slots.items()
                if not slot.filled
            ]
            
            if unfilled_slots:
                return json.dumps({
                    "error": "Not all slots are filled",
                    "unfilled_slots": unfilled_slots,
                    "message": "Please collect data first using get_delayed_nodes and get_network_topology"
                })
            
            # Generate diagnosis report
            report = self._generate_diagnosis_report()
            
            return json.dumps(report, indent=2)
        
        @self.server.call_tool()
        async def get_slot_status(arguments: dict) -> str:
            """
            Get current slot filling status
            Shows which slots are filled and which need data
            """
            status = {
                "total_slots": len(self.slots),
                "filled_slots": sum(1 for s in self.slots.values() if s.filled),
                "slots": {
                    name: {
                        "filled": slot.filled,
                        "description": slot.description
                    }
                    for name, slot in self.slots.items()
                }
            }
            
            return json.dumps(status, indent=2)
    
    async def _analyze_network_fault(self, time_range: str) -> Dict:
        """
        Execute network fault analysis workflow
        Fills slots sequentially
        """
        # Fill delayed_nodes slot
        delayed_nodes_data = await self._execute_saved_search(
            "get_delayed_nodes",
            time_range
        )
        self.slots["delayed_nodes"].value = delayed_nodes_data
        self.slots["delayed_nodes"].filled = True
        
        # Fill network_topology slot
        topology_data = await self._execute_saved_search(
            "get_network_topology",
            time_range
        )
        self.slots["network_topology"].value = topology_data
        self.slots["network_topology"].filled = True
        
        # Generate analysis result
        result = {
            "status": "analysis_complete",
            "delayed_nodes": delayed_nodes_data,
            "network_topology": topology_data,
            "diagnosis": self._diagnose_fault(
                delayed_nodes_data,
                topology_data
            )
        }
        
        return result
    
    async def _execute_saved_search(self, search_name: str, time_range: str) -> Dict:
        """
        Execute a Splunk Saved Search via MCP Server
        """
        try:
            payload = {
                "saved_search_name": search_name,
                "time_range": time_range
            }
            
            response = requests.post(
                f"{self.splunk_mcp_url}search",
                headers=self.headers,
                json=payload,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Search execution failed: {response.status_code}",
                    "search_name": search_name
                }
        
        except Exception as e:
            return {
                "error": f"Exception during search execution: {str(e)}",
                "search_name": search_name
            }
    
    def _diagnose_fault(self, delayed_nodes: Dict, topology: Dict) -> Dict:
        """
        Diagnose network fault based on collected data
        Simple logic-based diagnosis
        """
        diagnosis = {
            "primary_issue": None,
            "affected_nodes": [],
            "recommendations": []
        }
        
        # Check for delayed nodes
        delayed_node_list = delayed_nodes.get("results", [])
        if delayed_node_list:
            diagnosis["primary_issue"] = "High network latency detected"
            diagnosis["affected_nodes"] = [
                node.get("device_name", "unknown")
                for node in delayed_node_list
            ]
            diagnosis["recommendations"].append(
                "Investigate network device performance on affected nodes"
            )
        
        # Check topology changes
        topology_results = topology.get("results", [])
        critical_issues = [
            t for t in topology_results
            if t.get("status") == "critical"
        ]
        
        if critical_issues:
            diagnosis["primary_issue"] = "Network connectivity issue detected"
            diagnosis["recommendations"].append(
                "Check network device status and connectivity"
            )
        
        # Add general recommendations
        diagnosis["recommendations"].extend([
            "Monitor network performance continuously",
            "Check for capacity saturation",
            "Verify routing configurations"
        ])
        
        return diagnosis
    
    def _generate_diagnosis_report(self) -> Dict:
        """
        Generate a diagnosis report for presentation
        """
        delayed_nodes_data = self.slots["delayed_nodes"].value
        topology_data = self.slots["network_topology"].value
        
        diagnosis = self._diagnose_fault(delayed_nodes_data, topology_data)
        
        report = {
            "report_type": "Network Fault Analysis",
            "status": "completed",
            "findings": {
                "delayed_nodes": delayed_nodes_data.get("results", []),
                "network_topology": topology_data.get("results", [])
            },
            "diagnosis": diagnosis,
            "next_steps": [
                "1. Review affected nodes in detail",
                "2. Check network device logs",
                "3. Implement mitigation measures if needed",
                "4. Monitor for recurring issues"
            ]
        }
        
        return report
    
    def run(self):
        """Start the MCP server"""
        self.server.run()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    SPLUNK_MCP_URL = os.getenv("SPLUNK_MCP_URL")
    AUTH_TOKEN = os.getenv("AUTH_TOKEN")
    
    agent = NetworkFaultAnalysisAgent(SPLUNK_MCP_URL, AUTH_TOKEN)
    agent.run()
