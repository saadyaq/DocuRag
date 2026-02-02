.PHONY: install test ingest clean

install:
	uv pip install -r requirements.txt

test:
	pytest tests/ -v

ingest:
	python -m src.ingestion.pipeline

clean:
	rm -rf data/processed/*
	find . -type d -name "__pycache__" -exec rm -rf {} +