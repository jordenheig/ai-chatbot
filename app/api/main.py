"""FastAPI application entry point for the RAG Chatbot.

This module initializes and configures the FastAPI application with:
- API routes and endpoints
- Middleware configuration
- Static file serving
- WebSocket handling
- CORS settings
- Application events
"""

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.api.routes import chat, documents
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.websockets import WebSocketDisconnect
from typing import Dict, Set
from fastapi import Depends
from app.api.middleware import RequestLoggingMiddleware
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["chat"]
)
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}  # user_id -> connections
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
    
    async def send_document_update(self, user_id: int, document_id: int, status: str):
        """Send document status update to all user's connections."""
        if user_id in self.active_connections:
            message = {
                "type": "document_status",
                "document_id": document_id,
                "status": status
            }
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    continue

manager = ConnectionManager()

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user = Depends(get_current_user)):
    await manager.connect(websocket, user.id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)

@app.on_event("startup")
async def startup_event():
    """Execute startup tasks when application starts."""
    logger.info("Application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Execute cleanup tasks when application shuts down."""
    logger.info("Application shutting down") 