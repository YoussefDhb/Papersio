# Papersio

<p align="center">
   <img src="frontend/public/papersio-logo.svg" width="96" height="96" alt="Papersio logo">
</p>

**AI-Powered Multi-Agent Research Platform**

Papersio is a multi-agent research assistant that writes evidence-driven research reports with citations and real-time progress updates.

## Table of Contents

- Overview
- Features
- Architecture
- Getting Started
- Usage
- Configuration
- Deployment
- Project Structure
- Troubleshooting
- Contributing
- License

## Overview

Papersio orchestrates specialized agents to deliver research reports with citations and real-time progress updates. It supports web and academic sources, generates PDFs, and includes quality checks before finalizing results.

## Features

- Multi-agent workflow (Planner -> Analyst -> Writer -> Critic)
- Web and ArXiv search with smart routing
- WebSocket live progress updates
- LaTeX-based PDF report export
- Dockerized development and deployment
- Terraform-based AWS infrastructure

## Architecture

- Backend: FastAPI, LangGraph, ChromaDB, PostgreSQL (prod) or SQLite (dev)
- Frontend: Next.js 16, TypeScript, Tailwind
- LLM: Google Gemini (google-genai)
- Infra: Docker Compose for local, Terraform for AWS deployment

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker
- Google Gemini API key

### Quick Start (Docker)

1. Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key_here
   DEFAULT_PROVIDER=gemini
   # DEFAULT_MODEL=gemini-2.5-flash
   # HF_TOKEN=your_hf_token_here
   ```
2. Run:
   ```bash
   docker-compose up --build
   ```
3. Open http://localhost:3000

Health:
- Backend: http://localhost:8000/
- Docs: http://localhost:8000/docs

### Local Development

Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Open http://localhost:3000
2. Enter a research question
3. Start the workflow and monitor progress
4. Review the report and export to PDF if needed

## Configuration

Environment variables (project root .env):
- `GOOGLE_API_KEY` (required)
- `DEFAULT_PROVIDER` (default: gemini)
- `DEFAULT_MODEL` (optional)
- `HF_TOKEN` (optional, for embeddings)
- `LOG_LEVEL` (optional, for backend logs)

Frontend (optional):
- `NEXT_PUBLIC_BACKEND_URL` to override the backend URL in local development

## Deployment

### AWS (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars #then update it with your credentials
terraform init
terraform plan
terraform apply
```

Notes:
- Set images, secrets, and region in terraform.tfvars
- HTTPS and custom domain require ACM + Route 53
- See terraform/deployment.md for detailed guidance

## Project Structure

- backend/: FastAPI app, agents, tools, PDF generation
- frontend/: Next.js UI and API client
- terraform/: AWS infrastructure (ECS, ALB, RDS, VPC)
- docker-compose.yml: Local orchestration
- .github/workflows/ci_cd.yml: CI/CD pipeline


## Troubleshooting

- API key errors: confirm GOOGLE_API_KEY is set in .env
- WebSocket issues: ensure backend is running and ports 8000/3000 are free
- Docker errors: run docker-compose logs -f backend and docker-compose logs -f frontend

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a clear description

## License

MIT License. See LICENSE for details.
