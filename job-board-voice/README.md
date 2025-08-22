# Internal Career Mobility Platform with Claude AI Assistant

An AI-powered internal job mobility platform that helps employees explore growth opportunities within the organization. Features an interactive chat assistant powered by Claude to help craft compelling job applications in both English and German.

## Overview

This platform transforms the internal job application process by providing:
- A professional portal for browsing internal opportunities
- Claude AI chat assistant that helps employees articulate their skills and experience
- Real-time form updates based on chat conversation
- Supportive, encouraging interaction to build confidence

## Features

- 🏢 **Internal Job Board**: Browse growth opportunities across departments
- 💬 **Claude AI Chat**: Interactive career coach helping with applications
- 🌍 **Bilingual Support**: Full English and German language support (EN/DE)
- 🔄 **Real-time Updates**: Form fields populate automatically from chat
- 📝 **CV Analysis**: Paste your CV and get tailored application help
- 💼 **Career Growth Focus**: Emphasis on professional development paths
- 🤝 **Encouraging Experience**: Builds confidence in internal mobility
- 🇩🇪 **German Jobs**: Includes German-specific positions in Berlin and Munich

## Port Configuration

The application uses ports in the 5010-5013 range to avoid conflicts with common services:

| Service | Internal Port | External Port | Description |
|---------|--------------|---------------|-------------|
| Backend API | 8000 | 5010 | FastAPI server with Claude integration |
| Frontend | 80 | 5011 | Web interface with chat UI |
| Redis | 6379 | None | Internal only |
| Reserved | - | 5012-5013 | Future expansion |

Note: Redis is only accessible within the Docker network to avoid conflicts with host Redis installations.

## Architecture

### Components

1. **Frontend** (HTML/JavaScript)
   - Corporate-themed career portal
   - Three-column application layout with chat interface
   - Real-time WebSocket updates
   - Claude-powered chat assistant

2. **Backend** (Python/FastAPI)
   - Internal job positions API
   - Application session management
   - WebSocket server for real-time updates
   - Redis integration for data persistence

3. **MCP Server** (Python/FastMCP)
   - Tools: get_job_details, submit_key_skills, submit_personal_statement
   - Supportive AI personality configuration
   - SSE transport for real-time communication

4. **Data Store** (Redis)
   - Job postings storage
   - Application session management
   - Real-time message broadcasting

## Prerequisites

- Docker and Docker Compose
- Elevenlabs account with agent configured
- Python 3.11+ (optional, for local development)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd job-board-voice
```

### 2. Configure Environment

Create a `.env` file with your Elevenlabs credentials:

```env
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_AGENT_ID=agent_0501k33r4vzkf9mth850sc5tm2n2
```

### 3. Start with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Application

- **Career Portal**: http://localhost:5011
- **Backend API**: http://localhost:5010
- **MCP Server**: http://localhost:5012

## Elevenlabs Configuration

The platform uses Elevenlabs Conversational AI with agent ID: `agent_0501k33r4vzkf9mth850sc5tm2n2`

### Agent Setup Instructions

Configure your Elevenlabs agent with these MCP tools:

1. **get_job_details**
   - Input: job_id (string)
   - Returns job information to understand the role

2. **submit_key_skills**
   - Input: session_id (string), skills (string)
   - Updates the key skills field

3. **submit_personal_statement**
   - Input: session_id (string), statement (string)
   - Updates the personal statement field

### Recommended Agent Personality

The AI assistant should be:
- Warm and encouraging
- Professional yet approachable
- Focused on helping employees recognize their value
- Supportive of career growth within the organization

## Application Flow

1. **Browse Opportunities**: Employees visit the portal to explore internal positions
2. **Select Role**: Click "Apply for This Role" on any position
3. **Manual Information**: Fill in contact details (name, employee ID, email, phone)
4. **AI Assistance**: The voice assistant helps with:
   - Key skills and experience relevant to the role
   - Personal statement about why they're a good fit
5. **Real-time Updates**: Watch the form populate as you speak
6. **Submit Application**: Review and submit when ready

## Project Structure

```
job-board-voice/
├── backend/                      # FastAPI backend
│   └── main.py                  # Internal job positions API
├── mcp-server/                  # MCP server
│   └── internal_mobility_server.py  # Supportive AI tools
├── frontend/                    # Web interface
│   ├── index.html              # Career portal home
│   ├── apply.html              # Application form with AI
│   ├── css/
│   │   └── corporate-styles.css  # Professional blue theme
│   └── js/
│       ├── internal-jobs.js      # Job listings logic
│       └── internal-application.js  # Application form logic
├── docker/                      # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.mcp
│   └── Dockerfile.frontend
├── docker-compose.yml          # Service orchestration
└── .env                        # Environment variables (gitignored)
```

## Available Internal Positions

The platform includes sample positions across departments:
- Senior Software Engineer (Technology)
- Product Owner (Digital Innovation)
- Team Lead - Customer Success (Customer Experience)
- Lead Data Analyst (Finance)
- Marketing Specialist (Marketing & Communications)

Each position includes:
- Department and location
- Role description
- Required skills
- Career growth path
- Team size information

## API Endpoints

### Backend API

- `GET /api/jobs` - List internal positions
- `GET /api/jobs/{job_id}` - Get position details
- `POST /api/sessions/create` - Create application session
- `WS /ws/{session_id}` - WebSocket for real-time updates

### MCP Tools

- `get_job_details(job_id)` - Retrieve position information
- `submit_key_skills(session_id, skills)` - Update skills field
- `submit_personal_statement(session_id, statement)` - Update personal statement

## Development

### Local Backend Development

```bash
cd backend
pip install fastapi uvicorn redis websockets
python main.py
```

### Local MCP Server Development

```bash
cd mcp-server
pip install fastmcp mcp redis pydantic
python internal_mobility_server.py
```

### Frontend Development

```bash
cd frontend
python -m http.server 5011
# Visit http://localhost:5011
```

## Monitoring

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f mcp-server
docker-compose logs -f frontend
```

### Check Service Health

```bash
# View running services
docker-compose ps

# Test backend API
curl http://localhost:5010/api/jobs

# Check MCP server
curl http://localhost:5012/
```

## Troubleshooting

### Voice Assistant Not Appearing
- Verify Elevenlabs agent ID in `.env`
- Check browser console for errors
- Ensure agent is configured with MCP tools

### Form Not Updating
- Check WebSocket connection in browser console
- Verify MCP server is running
- Review MCP server logs for tool execution

### Application Not Submitting
- Ensure all required fields are filled
- Check backend logs for errors
- Verify Redis connection

## Production Deployment

### Reverse Proxy Configuration

The application can be deployed behind a reverse proxy (Apache2 or Nginx) for production use. Example configuration files are provided:

#### Apache2
```bash
# Enable required modules
sudo a2enmod proxy proxy_http proxy_wstunnel headers rewrite

# Copy and enable configuration
sudo cp apache2-proxy.conf /etc/apache2/sites-available/job-portal.conf
sudo a2ensite job-portal
sudo systemctl reload apache2
```

Access the portal at: `http://your-domain.com/job-portal`

#### Nginx
```bash
# Copy configuration
sudo cp nginx-proxy.conf /etc/nginx/sites-available/job-portal
sudo ln -s /etc/nginx/sites-available/job-portal /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

Both configurations support:
- Path-based routing (`/job-portal`)
- WebSocket connections for real-time updates
- Server-Sent Events (SSE) for MCP communication
- Static asset caching
- Security headers
- HTTPS/SSL setup (commented examples included)

## Security Considerations

- `.env` file is gitignored to protect credentials
- Use HTTPS in production environments
- Implement authentication for production
- Add rate limiting for API endpoints
- Validate all user inputs
- Configure proper CORS headers when using reverse proxy
- Use firewall rules to restrict direct Docker port access

## Support

For issues or questions:
1. Check service logs with `docker-compose logs`
2. Verify all services are running with `docker-compose ps`
3. Review browser console for client-side errors

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [Elevenlabs](https://elevenlabs.io) for conversational AI technology
- [MCP](https://modelcontextprotocol.io) for tool integration protocol
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework
- [FastMCP](https://github.com/jlowin/fastmcp) for simplified MCP server creation