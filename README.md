# Production-Grade RAG Python Application

A production-ready **Retrieval Augmented Generation (RAG)** system that enables seamless PDF ingestion, semantic search, and AI-powered question answering with built-in quality evaluation using RAGAS metrics.

## 🎯 Overview

This application demonstrates a complete RAG pipeline with:
- **PDF Document Management**: Upload, parse, and chunk PDFs efficiently
- **Semantic Search**: Vector-based retrieval using OpenAI embeddings and Qdrant vector database
- **AI-Powered Q&A**: GPT-4o-mini responses grounded in retrieved context
- **Async Workflows**: Event-driven architecture using Inngest for reliability and scalability
- **Quality Evaluation**: On-demand RAGAS-based metrics for answer quality assessment
- **User-Friendly Interface**: Streamlit web application for easy interaction

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                          │
│          (PDF Upload & Question Interface)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
   ┌────▼────────┐              ┌──────────▼──────┐
   │   FastAPI   │              │  Inngest Sync   │
   │   Server    │◄────────────►│  Service        │
   └────┬────────┘              └─────────────────┘
        │
        ├─────────────────┬────────────────────┐
        │                 │                    │
    ┌───▼────┐     ┌──────▼──────┐    ┌───────▼─────┐
    │  PDF   │     │   OpenAI    │    │   Qdrant    │
    │ Parser │     │ Embeddings  │    │Vector DB    │
    │(Llama  │     │ (3072-dim)  │    │             │
    │ Index) │     └─────────────┘    └─────────────┘
    └────────┘

                    ┌───────────────┐
                    │    RAGAS      │
                    │  Evaluation   │
                    │   (On-Demand) │
                    └───────────────┘
```

## 🚀 Features

### Core RAG Capabilities
- **Document Ingestion**: Automatically chunks PDFs into 1000-token segments with 200-token overlap
- **Semantic Embeddings**: Uses OpenAI's `text-embedding-3-large` (3072-dimensional) for high-quality representations
- **Vector Similarity Search**: Qdrant HNSW indexing for fast nearest-neighbor retrieval
- **Context-Grounded Generation**: LLM responses constrained to retrieved document context

### Production Features
- **Throttling & Rate Limiting**: 
  - Max 2 ingestions per minute globally
  - Max 1 ingestion per 4 hours per document source
- **Asynchronous Workflows**: Inngest-powered event-driven processing for reliability
- **Error Handling**: Graceful failure modes with detailed logging
- **Session Management**: Caching and state preservation for efficient UI interactions

### Evaluation & Quality Assurance
- **RAGAS Metrics** (on-demand evaluation):
  - **Faithfulness** (0-1): Is the answer consistent with the retrieved context?
  - **Answer Relevance** (0-1): Does the answer address the user's question?
  - **Context Relevance** (0-1): How relevant are the retrieved contexts?
  - **Context Recall** (0-1): Does context capture all needed information?
- **Detailed Reports**: Human-readable evaluation summaries with quality indicators
- **Color-Coded Metrics**: Visual feedback (🟢 Excellent / 🟡 Good / 🔴 Needs Improvement)

## 📋 Requirements

### System Requirements
- Python 3.13+
- Qdrant vector database (local or remote instance)
- OpenAI API key
- 2GB+ RAM recommended

### External Services
- **OpenAI API**: For embeddings and LLM inference
- **Qdrant**: Vector database (included in local setup)
- **Inngest**: Event workflow management (local dev mode or cloud)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone git@github.com:Johnny001-DS/ProductionGradeRAGPythonApp.git
cd ProductionGradeRAGPythonApp-main
```

### 2. Set Up Python Environment
```bash
# Using venv
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n rag-app python=3.13
conda activate rag-app
```

### 3. Install Dependencies
```bash
pip install -e .
```

Or install specific packages:
```bash
pip install fastapi uvicorn inngest llama-index-core llama-index-readers-file \
            openai python-dotenv qdrant-client ragas datasets streamlit
```

### 4. Set Up Environment Variables
```bash
cp .env.example .env  # If provided, or create .env manually
```

Add the following to `.env`:
```env
OPENAI_API_KEY=sk-your-api-key-here
INNGEST_API_BASE=http://127.0.0.1:8288/v1  # Local dev server
```

### 5. Start Qdrant Vector Database
```bash
# Using Docker (recommended)
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

# Or download Qdrant locally:
# https://qdrant.tech/documentation/quick-start/
```

### 6. Start Inngest Sync Service (Development)
```bash
# Install Inngest CLI
npm install -g inngest-cli

# Start the local dev server
inngest dev
```

## 📖 Usage

### Option A: Streamlit Web UI (Recommended for Users)
```bash
streamlit run streamlit_app.py
```

Features:
- Upload PDFs with automatic ingestion
- Ask questions with adjustable context retrieval (1-20 chunks)
- View answers with source citations
- Evaluate answer quality with one click

### Option B: FastAPI Server (For Integration)
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API Endpoints (via Inngest events):
- `POST /events` - Send `rag/ingest_pdf` or `rag/query_pdf_ai` events

### Example: Ingest a PDF
```python
import asyncio
import inngest

client = inngest.Inngest(app_id="rag_app", is_production=False)

async def ingest_pdf():
    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": "/path/to/document.pdf",
                "source_id": "document.pdf",
            },
        )
    )

asyncio.run(ingest_pdf())
```

### Example: Query with Evaluation
```python
from rag_evaluator import evaluate_query, generate_evaluation_report

# After getting an answer from the RAG system
metrics = evaluate_query(
    question="What is the capital of France?",
    answer="The capital of France is Paris.",
    contexts=["France is a country in Europe. Its capital is Paris, located on the Seine river."]
)

print(generate_evaluation_report(metrics))
```

## 📁 Project Structure

```
├── main.py                  # FastAPI server with Inngest functions
├── streamlit_app.py         # Web UI for PDF upload and Q&A
├── rag_evaluator.py         # RAGAS evaluation module (NEW)
├── data_loader.py           # PDF parsing and chunking
├── vector_db.py             # Qdrant vector database operations
├── custom_types.py          # Pydantic models and type definitions
├── pyproject.toml           # Project dependencies and metadata
├── README.md                # This file
├── qdrant_storage/          # Local Qdrant database (if using local instance)
├── uploads/                 # Temporary storage for uploaded PDFs
└── .env.example             # Environment variables template
```

## 🔄 How It Works

### PDF Ingestion Flow
```
1. User uploads PDF via Streamlit UI
   ↓
2. PDF saved to ./uploads/ directory
   ↓
3. Inngest event "rag/ingest_pdf" triggered
   ↓
4. Backend function executes:
   - Load PDF using LlamaIndex PDFReader
   - Split into chunks (1000 tokens, 200 overlap)
   - Generate embeddings via OpenAI API (3072-dim)
   - Store in Qdrant with source metadata
   ↓
5. User gets success confirmation
```

### Query & Answer Flow
```
1. User enters question + context retrieval count (top_k)
   ↓
2. Inngest event "rag/query_pdf_ai" triggered
   ↓
3. Backend function executes:
   - Embed the question (same model as documents)
   - Search Qdrant for top_k similar chunks
   - Format context from results
   ↓
4. Send to GPT-4o-mini with system prompt:
   "Answer using only the provided context"
   ↓
5. LLM generates grounded answer
   ↓
6. Results returned with sources and context count
```

### Evaluation Flow (On-Demand)
```
1. User clicks "Evaluate Answer" button
   ↓
2. RAGAS evaluation runs:
   - Faithfulness check: Does answer follow context?
   - Answer Relevance: Is answer addressing question?
   - Context Relevance: Are contexts useful for question?
   ↓
3. Scores (0.0 - 1.0) displayed with color coding
   ↓
4. Detailed report shown with improvement suggestions
```

## ⚙️ Configuration

### Environment Variables
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...                    # Required: OpenAI API key
EMBED_MODEL=text-embedding-3-large       # Embedding model (default)
EMBED_DIM=3072                            # Embedding dimension

# Qdrant Configuration
QDRANT_URL=http://localhost:6333         # Qdrant server URL
QDRANT_COLLECTION=docs                   # Collection name

# Inngest Configuration
INNGEST_API_BASE=http://127.0.0.1:8288/v1  # Dev server endpoint
INNGEST_APP_ID=rag_app                   # Application identifier

# Streamlit Configuration
STREAMLIT_CLIENT_LOGGER_LEVEL=info       # Logging level
```

### Tunable Parameters (in code)

**data_loader.py:**
```python
chunk_size=1000           # Tokens per chunk
chunk_overlap=200         # Overlap between chunks
```

**vector_db.py:**
```python
top_k=5                   # Default context chunks to retrieve
dim=3072                  # Embedding dimension (must match model)
```

**main.py:**
```python
throttle_count=2          # Max ingestions per period
throttle_period=60s       # Throttle time window
rate_limit=1 per 4 hours  # Per-source rate limit
temperature=0.2           # LLM response randomness (lower = more deterministic)
max_tokens=1024           # Max output length
```

## 🧪 Testing & Evaluation

### Manual Testing
```bash
# 1. Start all services
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant &
inngest dev &
uvicorn main:app --reload &

# 2. Run Streamlit UI
streamlit run streamlit_app.py

# 3. Upload a test PDF and ask questions
```

### Programmatic Testing
```python
from rag_evaluator import evaluate_batch

# Test multiple queries
test_cases = [
    {
        "question": "What is the main topic?",
        "answer": "The main topic is...",
        "contexts": ["Context 1...", "Context 2..."],
        "ground_truth": "Expected answer (optional)"
    },
    # ... more test cases
]

results = evaluate_batch(test_cases)
print(f"Average Faithfulness: {results['aggregate_scores']['faithfulness']['mean']:.3f}")
```

## 📊 Performance Metrics

### Typical Latencies (with local Qdrant)
- **PDF Ingestion**: 5-30 seconds (depends on PDF size)
- **Query Embedding**: 0.5-1.0 seconds
- **Vector Search**: 10-50ms
- **LLM Generation**: 2-5 seconds
- **RAGAS Evaluation**: 30-90 seconds (runs LLM evaluations)

### Throughput
- **Ingestion**: ~2 PDFs/minute (throttled)
- **Queries**: Limited by LLM rate limits (typically ~3-5 concurrent)
- **Evaluation**: 1 answer at a time (sequential)

## 🛡️ Production Deployment

### Recommended Setup
1. **Vector Database**: Use managed Qdrant Cloud or self-hosted with backups
2. **FastAPI Server**: Deploy with Gunicorn/Uvicorn on Kubernetes or cloud platform
3. **Inngest**: Use Inngest Cloud for production reliability
4. **Streamlit**: Deploy via Streamlit Cloud or containerized service
5. **Monitoring**: Add logging with ELK stack or cloud provider tools

### Docker Deployment
```bash
# Build image
docker build -t rag-app .

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e QDRANT_URL=qdrant:6333 \
  rag-app
```

## 🐛 Troubleshooting

### Issue: "Import ragas could not be resolved"
**Solution**: Install RAGAS: `pip install ragas datasets`

### Issue: Qdrant connection refused
**Solution**: 
- Ensure Qdrant is running: `docker ps | grep qdrant`
- Check URL: `curl http://localhost:6333/health`
- Update `QDRANT_URL` in `.env`

### Issue: OpenAI API timeout
**Solution**:
- Check API key validity
- Verify rate limits not exceeded
- Increase timeout in vector_db.py: `timeout=30`

### Issue: Streamlit "no module named inngest"
**Solution**: `pip install inngest`

### Issue: Evaluation takes very long
**Solution**:
- RAGAS runs multiple LLM evaluations (expected: 30-90s)
- Ensure OpenAI API is responsive
- Check network connectivity

## 📚 Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | GPT-4o-mini | Answer generation |
| **Embeddings** | OpenAI text-embedding-3-large | Semantic representation |
| **Vector DB** | Qdrant | Similarity search |
| **Document Parsing** | LlamaIndex | PDF extraction & chunking |
| **Web Framework** | FastAPI | REST API server |
| **UI** | Streamlit | User interface |
| **Async Jobs** | Inngest | Workflow orchestration |
| **Evaluation** | RAGAS | Quality metrics |

## 🔐 Security Considerations

- **API Keys**: Never commit `.env` files; use secret management systems
- **PDF Storage**: Implement access controls on uploaded PDFs
- **Context Injection**: LLM prompt prevents instruction injection with explicit instructions
- **Rate Limiting**: Prevents abuse and cost overruns
- **Error Messages**: Avoid exposing sensitive information in logs

## 📈 Future Enhancements

- [ ] Support for multiple file formats (DOCX, TXT, Web links)
- [ ] Batch query evaluation with CSV/JSON input
- [ ] Historical query analytics dashboard
- [ ] Fine-tuned embedding model for domain-specific search
- [ ] Multi-language support
- [ ] Caching layer for repeated questions
- [ ] Parallel document ingestion
- [ ] Interactive prompt optimization UI

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 💬 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation and troubleshooting section
- Review Inngest, Qdrant, and LlamaIndex documentation

## 👤 Author

**Karan Badlani**  
**Repository**: [ProductionGradeRAGPythonApp](https://github.com/Johnny001-DS/ProductionGradeRAGPythonApp)

---

**Last Updated**: March 2026  
**Version**: 1.0.0 with RAGAS Evaluation
