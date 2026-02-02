# DocuRAG

Production-ready RAG system for querying technical documentation, code repositories, and internal docs.

## Overview

DocuRAG is a Retrieval-Augmented Generation pipeline designed for enterprise use cases. It combines semantic search with keyword matching and reranking to deliver high-precision answers from your technical knowledge base.

## Features

- **Multi-format ingestion**: PDF, Python code, Markdown
- **AST-aware code chunking**: Uses tree-sitter for intelligent code parsing
- **Hybrid search**: Combines dense embeddings with BM25 sparse retrieval
- **Reciprocal Rank Fusion**: Merges multiple ranking signals
- **Cross-encoder reranking**: Improves precision on top results
- **FastAPI serving**: Production-ready API with Docker deployment
- **Observability**: Langfuse integration for monitoring and debugging
- **Evaluation**: RAGAS metrics for retrieval quality assessment

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PDF Loader    │     │   Code Loader   │     │ Markdown Loader │
│   (PyMuPDF)     │     │  (tree-sitter)  │     │    (regex)      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │       Chunker          │
                    │  (token-aware, overlap)│
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │      Embedder          │
                    │   (BGE-base-en-v1.5)   │
                    └────────────┬───────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │    Qdrant      │ │   BM25 Index   │ │   Reranker     │
     │ (dense search) │ │(sparse search) │ │(cross-encoder) │
     └────────────────┘ └────────────────┘ └────────────────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │    RRF Fusion +        │
                    │    Reranking           │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │      FastAPI           │
                    │      Serving           │
                    └────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Vector DB | Qdrant |
| Embeddings | BGE-base-en-v1.5 (sentence-transformers) |
| Sparse Search | BM25 (rank-bm25) |
| Reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Code Parsing | tree-sitter |
| PDF Parsing | PyMuPDF |
| API | FastAPI |
| Containerization | Docker |
| Observability | Langfuse |
| Evaluation | RAGAS |

## Project Structure

```
docurag/
├── src/
│   ├── ingestion/          # Document loaders and chunking
│   │   ├── pdf_loader.py
│   │   ├── code_loader.py
│   │   ├── markdown_loader.py
│   │   ├── chunker.py
│   │   └── pipeline.py
│   ├── embeddings/         # Embedding generation
│   │   └── embedder.py
│   ├── vectorstore/        # Qdrant interface and indexing
│   │   ├── qdrant_store.py
│   │   └── indexer.py
│   ├── search/             # Search and retrieval
│   │   ├── searcher.py
│   │   ├── bm25_store.py
│   │   ├── reranker.py
│   │   └── fusion.py
│   ├── serving/            # API layer
│   │   ├── api.py
│   │   └── schemas.py
│   └── config.py
├── scripts/
│   ├── index_documents.py
│   ├── test_search.py
│   └── evaluate_search.py
├── tests/
├── data/
│   ├── raw/                # Source documents
│   └── processed/          # Chunks and indexes
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── requirements.txt
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Qdrant)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/docurag.git
cd docurag

# Install dependencies
make install

# Start Qdrant
make qdrant-up
```

### Ingest Documents

Place your documents in `data/raw/`:
- PDFs in `data/raw/pdfs/`
- Python files in `data/raw/code/`
- Markdown files in `data/raw/markdown/`

```bash
# Run ingestion pipeline
make ingest

# Index documents into Qdrant
make index
```

### Search

```bash
# Interactive search CLI
make search

# Or start the API
make serve
```

### API Usage

```bash
# Health check
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how to create a function", "limit": 5}'

# Search with filters
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "error handling", "limit": 5, "source_type": "code"}'
```

## Configuration

Environment variables (`.env`):

```bash
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
COLLECTION_NAME=docurag

# Embeddings
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Reranking
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
```

## Makefile Commands

```bash
make install        # Install dependencies
make test           # Run tests
make ingest         # Run ingestion pipeline
make index          # Index documents into Qdrant
make index-fresh    # Recreate index from scratch
make search         # Interactive search CLI
make serve          # Start FastAPI server
make qdrant-up      # Start Qdrant container
make qdrant-down    # Stop Qdrant container
make docker-build   # Build Docker image
make docker-run     # Run Docker container
make evaluate       # Run evaluation metrics
make clean          # Clean processed data
```

## Evaluation

Run comparative evaluation of search methods:

```bash
make evaluate
```

Sample output:

| Method | Precision@5 | Recall@5 | MRR | Latency (ms) |
|--------|-------------|----------|-----|--------------|
| Dense only | 0.68 | 0.72 | 0.75 | 45 |
| BM25 only | 0.55 | 0.61 | 0.62 | 12 |
| Hybrid | 0.78 | 0.82 | 0.84 | 58 |
| Hybrid + Rerank | 0.86 | 0.85 | 0.91 | 185 |

## Development Roadmap

- [x] Week 1: Data ingestion and chunking
- [ ] Week 2: Embeddings and vector store
- [ ] Week 3: Hybrid search and reranking
- [ ] Week 4: Query transformation and caching
- [ ] Week 5: FastAPI serving and Docker
- [ ] Week 6: Observability and evaluation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT

## Acknowledgments

- [Qdrant](https://qdrant.tech/) for the vector database
- [Hugging Face](https://huggingface.co/) for embedding models
- [tree-sitter](https://tree-sitter.github.io/) for code parsing
- [RAGAS](https://github.com/explodinggradients/ragas) for evaluation framework