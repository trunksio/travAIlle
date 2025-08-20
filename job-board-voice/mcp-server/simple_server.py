#!/usr/bin/env python3
"""
Simplified MCP Server for Job Board Application
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server.sse import sse_server
except ImportError:
    logger.error("MCP not installed. Please run: pip install mcp")
    exit(1)

# Initialize the server
server = Server("job-board-mcp")

# Import Redis if available
try:
    import redis
    REDIS_AVAILABLE = True
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except ImportError:
    logger.warning("Redis not available. Using in-memory storage.")
    REDIS_AVAILABLE = False
    redis_client = None

# In-memory storage as fallback
memory_store = {}

@server.tool()
async def update_application_field(session_id: str, field_name: str, value: str) -> Dict[str, Any]:
    """Update a specific field in the job application form"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Store in Redis
            key = f"application:{session_id}"
            redis_client.hset(key, field_name, value)
            redis_client.expire(key, 3600)
            
            # Publish update
            update_message = json.dumps({
                "type": "field_update",
                "session_id": session_id,
                "field_name": field_name,
                "value": value,
                "timestamp": datetime.now().isoformat()
            })
            redis_client.publish(f"application_updates:{session_id}", update_message)
        else:
            # Store in memory
            if session_id not in memory_store:
                memory_store[session_id] = {}
            memory_store[session_id][field_name] = value
        
        logger.info(f"Updated {field_name} for session {session_id}")
        
        return {
            "success": True,
            "field_name": field_name,
            "value": value,
            "message": f"Updated {field_name} successfully"
        }
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        return {"success": False, "error": str(e)}

@server.tool()
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """Get details about a specific job posting"""
    try:
        if REDIS_AVAILABLE and redis_client:
            job_data = redis_client.hgetall(f"job:{job_id}")
        else:
            job_data = {}
        
        if not job_data:
            # Return default job for demo
            job_data = {
                "title": "Software Engineer",
                "company": "TechCorp",
                "description": "Join our innovative team",
                "requirements": "3+ years experience",
                "location": "Remote",
                "salary_range": "$100k-$150k"
            }
        
        return {"success": True, "job": job_data}
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        return {"success": False, "error": str(e)}

@server.tool()
async def submit_application(session_id: str, job_id: str) -> Dict[str, Any]:
    """Submit the completed job application"""
    try:
        if REDIS_AVAILABLE and redis_client:
            app_data = redis_client.hgetall(f"application:{session_id}")
        else:
            app_data = memory_store.get(session_id, {})
        
        if not app_data:
            return {"success": False, "error": "No application data found"}
        
        # Check required fields
        required = ["name", "email", "phone"]
        missing = [f for f in required if f not in app_data]
        
        if missing:
            return {
                "success": False,
                "error": f"Missing fields: {', '.join(missing)}",
                "missing_fields": missing
            }
        
        # Create application ID
        app_id = f"app_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if REDIS_AVAILABLE and redis_client:
            # Store application
            app_data["job_id"] = job_id
            app_data["application_id"] = app_id
            app_data["submitted_at"] = datetime.now().isoformat()
            redis_client.hset(f"submitted_application:{app_id}", mapping=app_data)
            redis_client.lpush(f"job_applications:{job_id}", app_id)
            
            # Publish submission event
            submission_message = json.dumps({
                "type": "application_submitted",
                "session_id": session_id,
                "application_id": app_id,
                "job_id": job_id,
                "timestamp": datetime.now().isoformat()
            })
            redis_client.publish(f"application_updates:{session_id}", submission_message)
            
            # Clean up
            redis_client.delete(f"application:{session_id}")
        
        logger.info(f"Submitted application {app_id}")
        
        return {
            "success": True,
            "application_id": app_id,
            "message": "Application submitted successfully!"
        }
    except Exception as e:
        logger.error(f"Error submitting: {e}")
        return {"success": False, "error": str(e)}

@server.tool()
async def get_application_status(session_id: str) -> Dict[str, Any]:
    """Get the current status of an application form"""
    try:
        if REDIS_AVAILABLE and redis_client:
            app_data = redis_client.hgetall(f"application:{session_id}")
        else:
            app_data = memory_store.get(session_id, {})
        
        required = ["name", "email", "phone"]
        filled_required = [f for f in required if f in app_data]
        missing_required = [f for f in required if f not in app_data]
        
        completion = (len(filled_required) / len(required)) * 100 if required else 0
        
        return {
            "success": True,
            "session_id": session_id,
            "filled_fields": list(app_data.keys()),
            "missing_required": missing_required,
            "completion_percentage": completion,
            "current_data": app_data,
            "ready_to_submit": len(missing_required) == 0
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Main entry point"""
    transport = os.getenv("MCP_TRANSPORT", "sse")
    
    if transport == "stdio":
        logger.info("Starting MCP server in stdio mode...")
        async with stdio_server() as streams:
            await server.run(streams[0], streams[1])
    else:
        # SSE mode
        host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_SERVER_PORT", 3000))
        logger.info(f"Starting MCP server in SSE mode on {host}:{port}")
        
        from aiohttp import web
        app = web.Application()
        sse_server(app, server, "/sse")
        
        # Add a health check endpoint
        async def health(request):
            return web.Response(text="OK")
        app.router.add_get("/health", health)
        
        # Add tools listing endpoint
        async def list_tools(request):
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
                for tool in server.tools.values()
            ]
            return web.json_response({"tools": tools})
        app.router.add_get("/tools", list_tools)
        
        web.run_app(app, host=host, port=port)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())