# CodeScribe AI

A full-stack AI-powered code analysis platform built with React, Go, Python, and FastAPI.

## Features

- 🔐 JWT-based authentication
- 🤖 AI-powered repository analysis using HuggingFace models
- 💬 Interactive chat interface for code queries
- 🔍 Repository code indexing and vector search
- 🐳 Docker containerization
- ☸️ Kubernetes deployment ready

## Tech Stack

### Frontend
- React 18 with TypeScript
- Vite for fast development
- TailwindCSS for styling
- Zustand for state management
- Axios for API calls

### Backend
- **Gateway Service**: Go with Gin framework
- **AI Core Service**: Python with FastAPI
- PostgreSQL database
- JWT authentication
- CORS enabled

### AI/ML
- LangChain for document processing
- HuggingFace Transformers
- Chroma vector database
- Sentence transformers for embeddings

## Getting Started

### Prerequisites
- Node.js 18+
- Go 1.23+
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/KartavyaChauhan/codescribe-ai.git
   cd codescribe-ai
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Backend Services**
   ```bash
   # Terminal 1 - Go Gateway
   cd services/gateway
   go run main.go

   # Terminal 2 - Python AI Core
   cd services/ai-core
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

4. **Database**
   ```bash
   docker-compose up postgres -d
   ```

### Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

### Kubernetes Deployment

1. **Build and push images**
   ```bash
   docker tag codescribe-ai-frontend:latest kartavya17/codescribe-frontend:latest
   docker tag codescribe-ai-gateway:latest kartavya17/codescribe-gateway:latest
   docker tag codescribe-ai-ai_core:latest kartavya17/codescribe-ai-core:latest
   
   docker push kartavya17/codescribe-frontend:latest
   docker push kartavya17/codescribe-gateway:latest
   docker push kartavya17/codescribe-ai-core:latest
   ```

2. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s/
   ```

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login

### Protected Routes
- `POST /api/analyze` - Analyze GitHub repository
- `POST /api/query` - Query analyzed repository

## Environment Variables

### Gateway Service (.env)
```
DB_URL=host=localhost user=user password=password dbname=codescribe_db port=5432 sslmode=disable
JWT_SECRET=your_very_secret_key_change_this
```

## Project Structure

```
codescribe-ai/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── store/          # Zustand stores
│   │   └── api.ts          # API client
│   ├── Dockerfile
│   └── nginx.conf
├── services/
│   ├── gateway/            # Go API Gateway
│   │   ├── main.go
│   │   ├── go.mod
│   │   └── Dockerfile
│   └── ai-core/           # Python AI Service
│       ├── main.py
│       ├── requirements.txt
│       └── Dockerfile
├── k8s/                   # Kubernetes manifests
│   ├── frontend.yaml
│   ├── gateway.yaml
│   ├── ai-core.yaml
│   └── postgres.yaml
├── docker-compose.yml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
