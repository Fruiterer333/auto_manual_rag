# V1 Evaluation

## Environment

- PDF: data/raw/train_a.pdf
- Pages: 354
- Chunks: 377
- Vector DB: Chroma
- LLM: qwen2.5:7b
- Embedding: BAAI/bge-small-zh-v1.5

## Status

- PDF loading: passed
- Chunking: passed
- Chroma indexing: passed
- FastAPI: passed
- Streamlit: passed
- CLI query: passed

## Known Issues

1. Citation quote currently uses chunk beginning, may not show the most relevant sentence.
2. Retrieval result does not expose score.
3. Some answers may include slight common-sense expansion beyond cited manual text.
4. Chunk count is low: 354 pages only produced 377 chunks, close to page-level chunking.

## Next Version

V1.1: retrieval debug and citation quality improvement.