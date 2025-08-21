#!/usr/bin/env python3
"""
Test script to simulate ElevenLabs MCP connection
"""
import asyncio
import aiohttp
import json

async def test_mcp_connection():
    """Simulate how ElevenLabs might connect to an MCP server"""
    
    server_url = "http://localhost:5012"
    
    # First test the synchronous endpoint
    print("Testing synchronous endpoint for ElevenLabs compatibility...")
    session = aiohttp.ClientSession()
    
    try:
        # Test initialize
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "ElevenLabs",
                    "version": "1.0"
                }
            },
            "id": 1
        }
        
        async with session.post(f"{server_url}/", json=init_request) as response:
            print(f"Initialize Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Initialize Response: {json.dumps(data, indent=2)}")
        
        # Test tools/list
        tools_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        async with session.post(f"{server_url}/", json=tools_request) as response:
            print(f"\nTools/List Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Tools found: {len(data.get('result', {}).get('tools', []))}")
                for tool in data.get('result', {}).get('tools', []):
                    print(f"  - {tool.get('name')}: {tool.get('description')}")
    finally:
        await session.close()
    
    return
    
    # Original SSE test code below (now skipped)
    server_url = "http://localhost:5012"
    
    # Step 1: Connect to SSE endpoint
    print("Step 1: Connecting to SSE endpoint...")
    session = aiohttp.ClientSession()
    
    try:
        # Connect to SSE
        async with session.get(f"{server_url}/sse") as response:
            print(f"SSE Status: {response.status}")
            print(f"SSE Headers: {response.headers}")
            
            # Read first few messages
            messages_endpoint = None
            session_id = None
            
            async for data in response.content:
                line = data.decode('utf-8').strip()
                print(f"SSE Line: {line}")
                
                if line.startswith("data: /messages/"):
                    # Extract the messages endpoint
                    messages_endpoint = line.replace("data: ", "")
                    # Extract session ID
                    if "session_id=" in messages_endpoint:
                        session_id = messages_endpoint.split("session_id=")[1]
                    break
            
            if messages_endpoint and session_id:
                print(f"\nStep 2: Found messages endpoint: {messages_endpoint}")
                print(f"Session ID: {session_id}")
                
                # Step 2: Try both initialize and tools/list
                
                # First try initialize
                init_request = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "clientInfo": {
                            "name": "ElevenLabs",
                            "version": "1.0"
                        }
                    },
                    "id": 1
                }
                
                print(f"\nStep 3a: Sending initialize request...")
                async with session.post(
                    f"{server_url}/messages/?session_id={session_id}",
                    json=init_request,
                    headers={"Content-Type": "application/json"}
                ) as init_response:
                    print(f"Initialize Status: {init_response.status}")
                    response_text = await init_response.text()
                    print(f"Initialize Response: {response_text}")
                    
                    # Try to parse as JSON
                    try:
                        response_json = json.loads(response_text)
                        print(f"Parsed Response: {json.dumps(response_json, indent=2)}")
                        
                        # Check for tools
                        if "result" in response_json:
                            result = response_json["result"]
                            if "tools" in result:
                                print(f"\nFound {len(result['tools'])} tools:")
                                for tool in result["tools"]:
                                    print(f"  - {tool.get('name', 'Unknown')}")
                            else:
                                print("\nNo tools found in response")
                    except json.JSONDecodeError:
                        print("Response is not valid JSON")
                
                # Now try tools/list
                tools_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": 2
                }
                
                print(f"\nStep 3b: Sending tools/list request...")
                async with session.post(
                    f"{server_url}/messages/?session_id={session_id}",
                    json=tools_request,
                    headers={"Content-Type": "application/json"}
                ) as tools_response:
                    print(f"Tools/List Status: {tools_response.status}")
                    response_text = await tools_response.text()
                    print(f"Tools/List Response: {response_text}")
                    
                    try:
                        response_json = json.loads(response_text)
                        print(f"Parsed Response: {json.dumps(response_json, indent=2)}")
                        
                        if "result" in response_json:
                            result = response_json["result"]
                            if "tools" in result:
                                print(f"\nFound {len(result['tools'])} tools:")
                                for tool in result["tools"]:
                                    print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', '')[:50]}...")
                    except json.JSONDecodeError:
                        print("Response is not valid JSON")
                        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())