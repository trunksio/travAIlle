// Configuration for the frontend application

// Backend API URL - adjust based on your deployment
const BACKEND_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5010' 
    : `${window.location.protocol}//${window.location.hostname}:5010`;

// WebSocket URL
const WS_URL = BACKEND_URL.replace('http://', 'ws://').replace('https://', 'wss://');

// Configuration flags
const CONFIG = {
    enableDebugLogging: false,
    autoSaveInterval: 30000, // Auto-save every 30 seconds
    maxChatHistory: 50, // Maximum number of messages to keep in history
};