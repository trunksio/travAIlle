#!/bin/sh

# Inject environment variables into JavaScript files
cat > /usr/share/nginx/html/js/config.js <<EOF
// Auto-generated configuration
window.BACKEND_URL = "${BACKEND_URL:-http://localhost:8000}";
window.MCP_SERVER_URL = "${MCP_SERVER_URL:-http://localhost:3000}";
window.ELEVENLABS_AGENT_ID = "${ELEVENLABS_AGENT_ID}";
EOF

# Add config script to HTML files
for file in /usr/share/nginx/html/*.html; do
    if [ -f "$file" ]; then
        sed -i 's|</head>|<script src="js/config.js"></script></head>|' "$file"
    fi
done

# Execute the original command
exec "$@"