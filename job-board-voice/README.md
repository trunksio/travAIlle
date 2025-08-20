# Job Board with Voice Application

A modern job board application featuring AI-powered voice interviews using Elevenlabs conversational AI and real-time form updates via MCP (Model Context Protocol).

## Features

- 🎯 **Job Listings**: Browse available positions with detailed descriptions
- 🎤 **Voice Applications**: Apply for jobs using natural voice conversation
- 🔄 **Real-time Updates**: Watch your application form fill automatically as you speak
- 🤖 **AI Interview Assistant**: Conversational AI guides you through the application process
- 📝 **MCP Integration**: Seamless tool execution for form field updates
- 🚀 **WebSocket Communication**: Instant updates between voice agent and web form

## Architecture

### Components

1. **Frontend** (HTML/JavaScript)
   - Job listing page
   - Voice-enabled application form
   - Real-time WebSocket updates
   - Elevenlabs widget integration

2. **Backend** (Python/FastAPI)
   - Job management API
   - Application submission handling
   - WebSocket server for real-time updates
   - Redis integration for data storage

3. **MCP Server** (Python)
   - Custom tools for form field updates
   - SSE transport for real-time communication
   - Integration with Elevenlabs agent

4. **Data Store** (Redis)
   - Job postings storage
   - Application data management
   - Real-time session handling

## Prerequisites

- Docker and Docker Compose
- Elevenlabs account (for voice features)
- Node.js (optional, for local development)
- Python 3.11+ (optional, for local development)

## Quick Start

### 1. Clone the Repository

```bash
cd job-board-voice
```

### 2. Configure Environment

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Elevenlabs credentials:

```env
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here
```

### 3. Start with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Application

- **Job Board**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **MCP Server**: http://localhost:3000/sse

## Elevenlabs Setup

### Creating an Elevenlabs Agent

1. Sign up at [elevenlabs.io](https://elevenlabs.io)
2. Navigate to "Conversational AI" or "Agents"
3. Create a new agent with these settings:

#### Agent Configuration

**System Prompt**:
```
You are a friendly job application assistant conducting interviews for job positions. 
You have access to MCP tools to update application forms in real-time.

When interviewing candidates:
1. Introduce yourself and the position
2. Ask for their information progressively:
   - Full name
   - Email address
   - Phone number
   - Years of experience
   - Key skills
   - Why they're interested in the position
3. Use the update_application_field tool after each response
4. Be conversational and encouraging
5. Confirm information before submission
6. Use submit_application when complete
```

**Tools Configuration**:
Add the MCP server endpoint to your agent:
- Server URL: `http://your-server:3000`
- Available tools will be automatically discovered

### Testing Without Elevenlabs

The application includes a demo mode for testing without voice:

1. Open the application page
2. Click "Fill Demo Data" to simulate voice input
3. Watch the form populate with sample data

## Development

### Local Development Setup

#### Backend Development

```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

#### MCP Server Development

```bash
cd mcp-server
pip install mcp fastmcp redis
python server.py
```

#### Frontend Development

Simply open `frontend/index.html` in a browser or use a local server:

```bash
cd frontend
python -m http.server 3001
```

### Project Structure

```
job-board-voice/
├── backend/              # FastAPI backend
│   └── main.py          # API endpoints and WebSocket
├── mcp-server/          # MCP server
│   └── server.py        # MCP tools for form updates
├── frontend/            # Web interface
│   ├── index.html       # Job listings
│   ├── apply.html       # Application form
│   ├── css/            # Styles
│   └── js/             # JavaScript logic
├── docker/              # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.mcp
│   └── Dockerfile.frontend
├── docker-compose.yml   # Service orchestration
└── .env.example        # Environment template
```

## API Endpoints

### Backend API

- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details
- `POST /api/sessions/create` - Create application session
- `GET /api/sessions/{session_id}/status` - Get application status
- `POST /api/applications/submit` - Submit application
- `WS /ws/{session_id}` - WebSocket for real-time updates

### MCP Tools

- `update_application_field` - Update a form field
- `get_job_details` - Get job information
- `submit_application` - Submit completed application
- `get_application_status` - Check application progress

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ELEVENLABS_API_KEY` | Your Elevenlabs API key | Required |
| `ELEVENLABS_AGENT_ID` | Your Elevenlabs agent ID | Required |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `BACKEND_PORT` | Backend server port | `8000` |
| `MCP_SERVER_PORT` | MCP server port | `3000` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Troubleshooting

### Common Issues

1. **Voice assistant not appearing**
   - Check Elevenlabs credentials in `.env`
   - Verify agent ID is correct
   - Check browser console for errors

2. **Form not updating in real-time**
   - Verify WebSocket connection in browser console
   - Check MCP server is running: `curl http://localhost:3000/sse`
   - Ensure Redis is running: `docker-compose ps`

3. **Cannot submit application**
   - Ensure all required fields are filled
   - Check backend logs: `docker-compose logs backend`
   - Verify Redis connection

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f mcp-server
```

### Testing MCP Server

```bash
# Check if MCP server is running
curl http://localhost:3000/sse

# Test tool listing
curl http://localhost:3000/tools
```

## Demo Workflow

1. **Browse Jobs**: Open http://localhost:3001 to see available positions
2. **Select a Job**: Click "Apply with Voice" on any job card
3. **Start Interview**: Click "Start Conversation" in the voice assistant
4. **Answer Questions**: Speak naturally to provide your information
5. **Watch Updates**: See form fields populate in real-time
6. **Review & Submit**: Check your information and submit when complete

## Security Considerations

- Never commit `.env` files with real credentials
- Use HTTPS in production
- Implement rate limiting for API endpoints
- Add authentication for production deployments
- Validate and sanitize all user inputs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs with `docker-compose logs`
3. Open an issue on GitHub

## Acknowledgments

- [Elevenlabs](https://elevenlabs.io) for conversational AI
- [MCP](https://modelcontextprotocol.io) for tool integration
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework
- [Redis](https://redis.io) for data storage