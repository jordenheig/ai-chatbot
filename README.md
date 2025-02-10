# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows users to upload documents and chat with an AI that understands their content. Built with FastAPI, Celery, and React.

## Key Features

- 📑 **Document Management**
  - Upload multiple document formats (PDF, DOC, TXT)
  - Real-time processing status updates
  - Document list with status tracking
  - Delete/manage uploaded documents

- 💬 **Chat Interface**
  - Interactive chat with context from uploaded documents
  - Chat session management
  - Complete chat history in left sidebar
  - Start new chat sessions
  - Continue existing conversations

- 🔄 **Real-time Updates**
  - Document processing status
  - Chat message streaming
  - Session synchronization

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: React, TailwindCSS
- **Database**: PostgreSQL
- **Vector Store**: Qdrant
- **Message Queue**: Redis, Celery
- **Document Processing**: PyMuPDF, EasyOCR
- **Containerization**: Docker

## Project Structure

```
rag-chatbot/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   │   ├── core/           # Core configuration
│   │   │   ├── models/         # Database models
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── services/       # Business logic
│   │   ├── celery_worker/      # Celery tasks for async processing
│   │   └── tests/              # Backend tests
│   ├── frontend/               # React frontend application
│   │   ├── src/
│   │   │   ├── components/     # React components
│   │   │   ├── contexts/       # React contexts
│   │   │   ├── hooks/         # Custom hooks
│   │   │   ├── pages/         # Page components
│   │   │   └── services/      # API services
│   │   └── public/            # Static files
│   └── docker/                # Docker configuration files
```

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Server
    participant B as Background Worker
    participant R as Queue
    participant V as Vector Database
    participant P as Relational Database
    participant L as LLM Service
    
    %% Document Upload Flow
    C->>A: Upload Document
    A->>P: Store Document Metadata
    A->>R: Queue Processing Job
    A->>C: Return Upload ID
    B->>R: Poll for Jobs
    R->>B: Document Job
    B->>B: Process Document
    B->>V: Store Embeddings
    B->>P: Update Status
    
    %% Chat Flow
    C->>A: Send Chat Message
    A->>V: Search Relevant Docs
    V->>A: Return Matches
    A->>L: Generate Response
    L->>A: Return Response
    A->>P: Store Chat History
    A->>C: Stream Response

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
```

2. Set up environment variables:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Start with Docker (recommended):
```bash
docker-compose up --build
```

4. Or run services individually:

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Celery Worker:
```bash
cd backend
celery -A celery_worker.celery worker --loglevel=info
```

## Component Details

### Backend Components
- **api/**: Contains all API routes and endpoint definitions
- **core/**: Configuration settings, database setup, and security
- **models/**: SQLAlchemy database models
- **schemas/**: Pydantic models for request/response validation
- **services/**: Business logic implementation

### Frontend Components
- **components/**: Reusable UI components
- **contexts/**: React context providers for state management
- **hooks/**: Custom React hooks
- **pages/**: Main page components
- **services/**: API integration services

### Infrastructure
- **docker/**: Contains Dockerfile and docker-compose configuration
- **celery_worker/**: Async task processing for document handling

## Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

## Development

To run tests:
```bash
cd backend
pytest
```





