# Document Intelligence System - Execution Instructions

## Prerequisites

- Docker installed on your system
- PDF documents to analyze
- Configuration file with persona and job requirements

## Setup and Execution

### 1. Build Docker Image

```bash
docker build -t document-intelligence .
```

### 2. Prepare Input Directory Structure

Create the following directory structure:

```
input/
└── Collection 2/
    ├── challenge1b_input.json
    └── PDFs/
        ├── document1.pdf
        ├── document2.pdf
        └── document3.pdf
```

### 3. Configuration File Format

Create `challenge1b_input.json` with the following structure:

```json
{
    "documents": [
        {"filename": "document1.pdf"},
        {"filename": "document2.pdf"},
        {"filename": "document3.pdf"}
    ],
    "persona": "PhD Researcher in Computational Biology",
    "job_to_be_done": "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks"
}
```

### 4. Run the Application

#### Option A: Using Docker Volume Mounts

```bash
docker run -v /path/to/your/input:/app/input -v /path/to/your/output:/app/output document-intelligence
```

#### Option B: Copy Files into Container

```bash
# Create and run container
docker run --name doc-intel -d document-intelligence sleep infinity

# Copy input files
docker cp /path/to/your/input/. doc-intel:/app/input/

# Run the analysis
docker exec doc-intel python main.py

# Copy results back
docker cp doc-intel:/app/output/. /path/to/your/output/

# Clean up
docker rm -f doc-intel
```

### 5. Expected Output

The system will generate `output/analysis_result.json` with the following structure:

```json
{
    "metadata": {
        "input_documents": ["document1.pdf", "document2.pdf"],
        "persona": "PhD Researcher in Computational Biology",
        "job_to_be_done": "Prepare a comprehensive literature review...",
        "processing_timestamp": "2024-01-15T10:30:00"
    },
    "extracted_sections": [
        {
            "document": "document1.pdf",
            "page_number": 3,
            "section_title": "Methodology",
            "importance_rank": 1
        }
    ],
    "subsection_analysis": [
        {
            "document": "document1.pdf",
            "section_title": "Methodology",
            "refined_text": "The methodology section describes...",
            "page_number": 3,
            "relevance_score": 0.85,
            "key_insights": ["Key finding 1", "Key finding 2"]
        }
    ]
}
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all dependencies in `requirements.txt` are properly installed
2. **PDF Parsing Errors**: Verify PDF files are not corrupted and are readable
3. **Permission Issues**: Ensure Docker has permission to access input/output directories
4. **Memory Issues**: For large documents, consider increasing Docker memory limits

### Debug Mode

Run with verbose output:

```bash
docker run -v /path/to/input:/app/input -v /path/to/output:/app/output document-intelligence python main.py --verbose
```

### Log Access

To view detailed logs:

```bash
docker run -v /path/to/input:/app/input -v /path/to/output:/app/output document-intelligence 2>&1 | tee analysis.log
```

## Performance Considerations

- Processing time depends on document size and complexity
- Recommended: 2GB RAM minimum for medium-sized documents
- Large document collections may require increased timeout values