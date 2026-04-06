## AI Agent Risk Platform : This project is a graph-powered AI risk analysis platform that models how user prompts propagate through AI agents, tools, and systems.


## Architecture:
User Prompt
↓
Agent Router
↓
Agents (GitHub / Terraform / etc.)
↓
Policy Engine
↓
Risk Engine
↓
TigerGraph (Graph Storage)


Graph Model (TigerGraph)

We model the system as a graph:

- **Prompt → Agent**
- **Agent → Tool**
- **Tool → Action**
- **Action → System**

This allows:
- Risk propagation tracking
- Attack path analysis
- System-level impact visibility



## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React (Vite)
- **Graph DB:** TigerGraph
- **Architecture:** Multi-Agent System


##Features 

- AI prompt risk analysis
- Multi-agent routing system
- Policy enforcement layer
- Risk scoring engine
- Graph-based logging (TigerGraph)


## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup environment
Create .env:
TG_HOST=
TG_GRAPH=
TG_SECRET=
TG_TOKEN=

### 3. Run backend
uvicorn api.main:app --reload --env-file .env

### 4. Open API docs
http://127.0.0.1:8000/docs
