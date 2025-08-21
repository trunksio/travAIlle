#!/usr/bin/env python3
"""
Test MCP protocol with SSE - following the standard MCP pattern
"""
import asyncio
import aiohttp
import json

async def test_mcp_sse():
    """Test MCP SSE protocol like ElevenLabs would"""
    
    base_url = "https://ui.agentorientedarchitecture.dev/job-portal/mcp"
    
    print("Connecting to MCP SSE endpoint...")
    session = aiohttp.ClientSession()
    
    try:
        # Connect to SSE endpoint
        async with session.get(f"{base_url}/sse") as response:
            print(f"SSE Status: {response.status}")
            
            if response.status != 200:
                print(f"Error: {await response.text()}")
                return
            
            # Read the endpoint message
            session_id = None
            messages_endpoint = None
            
            async for data in response.content:
                line = data.decode('utf-8').strip()
                if line.startswith("data: /messages/"):
                    messages_endpoint = line.replace("data: ", "")
                    if "session_id=" in messages_endpoint:
                        session_id = messages_endpoint.split("session_id=")[1]
                    print(f"Got session ID: {session_id}")
                    break
            
            if not session_id:
                print("Failed to get session ID")
                return
            
            # Now send a tools/list request
            print("\nSending tools/list request via POST...")
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }
            
            async with session.post(
                f"{base_url}/messages/?session_id={session_id}",
                json=tools_request,
                headers={"Content-Type": "application/json"}
            ) as post_response:
                print(f"POST Status: {post_response.status}")
                post_text = await post_response.text()
                print(f"POST Response: {post_text}")
                
                # The response should come through SSE, not the POST response
                # In a real implementation, we'd need to listen to the SSE stream
                # for the response with matching ID
                
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_mcp_sse())