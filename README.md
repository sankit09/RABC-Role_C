# README.md
"""
# RBAC Role Mining System

An automated system for generating RBAC roles from clustered user entitlement data using Azure OpenAI GPT-4o.

## Features

- **Automated Role Generation**: Uses LLM to generate professional role names, descriptions, and rationales
- **Batch Processing**: Process multiple clusters concurrently with rate limiting
- **Data Consolidation**: Combines cluster, user, and entitlement metadata
- **Review Workflow**: Approve/reject generated roles with feedback
- **Export Functionality**: Export roles to JSON or CSV formats
- **RESTful API**: FastAPI-based backend with comprehensive endpoints

## Project Structure

```
rbac-role-mining/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality (LLM client, prompts)
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   └── utils/         # Utilities
├── data/
│   ├── input/         # Input CSV/JSON files
│   └── output/        # Generated role exports
```

## Setup

### 1. Prerequisites

- Python 3.11+
- Azure OpenAI API access with GPT-4o deployment
- Docker (optional)

### 2. Installation

```bash
# Clone the repository
git clone <your-repo>
cd rbac-role-mining

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### 3. Data Preparation

Place your data files in `data/input/`:
- `entitlement_metadata.json`: Entitlement definitions
- `cluster_summary.csv`: Cluster information with entitlements
- `user_metadata.csv`: User-cluster mappings with job titles/departments

### 4. Running the Application

#### Local Development
```bash
uvicorn app.main:app --reload --port 8000
```

#### Using Docker
```bash
docker-compose up --build
```

## API Usage

### Health Check
```bash
GET /api/v1/health
```

### Upload Data Files
```bash
POST /api/v1/clusters/upload
Content-Type: multipart/form-data
- file: <your-file>
- file_type: cluster_summary|user_metadata|entitlement_metadata
```

### List All Clusters
```bash
GET /api/v1/clusters
```

### Generate Single Role
```bash
POST /api/v1/roles/generate
{
  "cluster_id": "C01",
  "force_regenerate": false
}
```

### Batch Generate Roles
```bash
POST /api/v1/roles/generate/batch
{
  "process_all": true,
  "concurrent_limit": 5
}
```

### Review Role
```bash
PUT /api/v1/roles/review/{cluster_id}
{
  "approved": true,
  "feedback": "Good role definition"
}
```

### Export Roles
```bash
GET /api/v1/roles/export?format=json
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Configuration

Key settings in `.env`:
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME`: GPT-4o deployment name
- `USE_LANGCHAIN`: Enable LangChain integration (optional)
- `MAX_CONCURRENT_LLM_CALLS`: Concurrent LLM call limit
- `LLM_TEMPERATURE`: Control creativity (0.0-1.0)

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/
```

## Production Considerations

1. **Authentication**: Add API key or OAuth2 authentication
2. **Database**: Replace in-memory storage with persistent database
3. **Caching**: Implement Redis for caching LLM responses
4. **Monitoring**: Add APM and logging aggregation
5. **Rate Limiting**: Implement per-user rate limiting
6. **Error Handling**: Enhanced error recovery mechanisms

## License

MIT License - See LICENSE file for details
"""