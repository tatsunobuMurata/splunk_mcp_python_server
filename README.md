# Extention of Splunk MCP Server Python Code
This is an extention of Splunk MCP Server to retrieve the information from the saved searches.

## Setup

### Splunk
You need to have a running Splunk instance, either Splunk Cloud or Splunk Enterprise.
The simplest setup is to install Splunk Enterprise on your own laptop.
Next, create an app with the ID mcp_demo, and define the following saved searches in that app.
- mcp_get_slow_network_nodes
```
| makeresults count=10
| streamstats count
| eval node = "mel_node".count region="melbourne"
| eval latency = (random() % 1000) + 1
| search latency > $latency$ region=$region$
```
- mcp_get_network_topologies
```
| makeresults count=10
| streamstats count
| streamstats current=f last(count) as prev_count
| eval node_from = "mel_node".prev_count
| eval node_to = "mel_node".count
| fields - _time
| fields node_from node_to
```
Please note that these saved searches are only mock examples because we do not have actual network latency data.
You can replace them with real searches once you have real network data in your Splunk environment.

### Splunk MCP Server
You also need to install the official Splunk MCP Server in your Splunk environment.
If you are running Splunk Cloud, you must enable the Splunk MCP Server service for your stack.
If you are running Splunk Enterprise, download and install the on-premises version of the MCP Server from https://splunkbase.splunk.com/app/7931.
For more details, refer to [Leveraging Splunk MCP and AI for enhanced IT operations and security investigations](https://lantern.splunk.com/Splunk_Platform/Product_Tips/Extending_the_Platform/Leveraging_Splunk_MCP_and_AI_for_enhanced_IT_operations_and_security_investigations).

### Splunk MCP Server Python Code
Clone this Git repository to your laptop, and then run the following commands to set up the Python environment:
```
cd <<YOUR_LOCAL_REPO_DIRECTORY>>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Claude Desktop
The easiest way to run an MCP client with user-prompting capability is to use Claude Desktop.
Install Claude Desktop on your laptop and configure it to deploy Splunk MCP Server and Python Code.
Below is an exmple of the configuration file. 
You need to change `https://localhost:8089` with the appropriate URI to access your MCP Server, and `/Users/tatmurat/Code/mcp/splunk/` with the path where you cloned the repository.
You also need to set `SPLUNK_HOST`, `SPLUNK_PORT`, `SPLUNK_USERNAME`, and `SPLUNK_PASSWORD` to the appropriate values so that the Python MCP Server use them to access the Splunk to retrieve the saved search information.
```
{
    "mcpServers": {
        "splunk-mcp-server": {
            "command": "npx",
            "args": [
                "-y",
                "mcp-remote",
                "https://localhost:8089/services/mcp/",
                "--header",
                "Authorization: Bearer ${AUTH_TOKEN}"
            ],
            "env": {
                "AUTH_TOKEN": "<<YOUR_SPLUNK_ACCESS_TOKEN>>",
                "NODE_TLS_REJECT_UNAUTHORIZED": "0"
            }
        },
        "splunk-saved-search-server": {
            "command": "/Users/tatmurat/Code/mcp/splunk/venv/bin/python",
            "args": [
                "/Users/tatmurat/Code/mcp/splunk/splunk_saved_search_mcp_server.py"
            ],
            "env": {
                "SPLUNK_HOST": "localhost",
                "SPLUNK_PORT": "8089",
                "SPLUNK_USERNAME": "admin",
                "SPLUNK_PASSWORD": "password",
                "SPLUNK_APP": "mcp_demo"
            }
        }	
    }
}
```
You have to have node.js installed on your laptop to access `npx` MCP Server.



