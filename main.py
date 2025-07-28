import os
import json
from pathlib import Path
from document_intelligence import DocumentIntelligenceService
import sys

def process_documents():
    """Main processing function for Round 1B"""
    input_dir = Path("input/Collection 2")
    output_dir = Path("output")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Look for configuration file
    config_file = input_dir / "challenge1b_input.json"
    if not config_file.exists():
        print("Error: config.json not found in input directory")
        print("Expected format:")
        print("""{
    "documents": ["doc1.pdf", "doc2.pdf", "doc3.pdf"],
    "persona": "PhD Researcher in Computational Biology",
    "job_to_be_done": "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks"
}""")
        return
    
    # Load configuration
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {str(e)}")
        return
    
    # Validate configuration
    required_fields = ["documents", "persona", "job_to_be_done"]
    for field in required_fields:
        if field not in config:
            print(f"Error: Missing required field '{field}' in config.json")
            return
    
    # Check if documents exist
    pdf_files = []
    for doc_entry in config["documents"]:
        doc_name = doc_entry["filename"] if isinstance(doc_entry, dict) else doc_entry
        doc_path = input_dir / "PDFs" / doc_name
        if doc_path.exists():
            pdf_files.append(str(doc_path))
        else:
            print(f"Warning: Document {doc_name} not found in input directory")
    
    if not pdf_files:
        print("No valid PDF documents found")
        return
    
    print(f"Processing {len(pdf_files)} documents...")
    print(f"Persona: {config['persona']}")
    print(f"Job to be done: {config['job_to_be_done']}")
    
    # Initialize document intelligence service
    service = DocumentIntelligenceService()
    
    try:
        # Process documents
        result = service.process_document_collection(
            pdf_files=pdf_files,
            persona=config["persona"],
            job_to_be_done=config["job_to_be_done"],
            verbose=True
        )
        
        if result:
            # Save result
            output_file = output_dir / "analysis_result.json"
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Analysis completed successfully")
            print(f"✓ Results saved to {output_file}")
            print(f"✓ Found {len(result.get('extracted_sections', []))} relevant sections")
            print(f"✓ Generated {len(result.get('sub_section_analysis', []))} sub-section analyses")
            
            # Print sample results for verification
            extracted_sections = result.get('extracted_sections', [])
            if extracted_sections:
                print(f"\nTop 3 extracted sections:")
                for i, section in enumerate(extracted_sections[:3], 1):
                    print(f"  {i}. {section.get('section_title', 'Untitled')} (Page {section.get('page_number', 'N/A')})")
            
            sub_section_analysis = result.get('sub_section_analysis', [])
            if sub_section_analysis:
                print(f"\nTop 3 sub-section analyses:")
                for i, subsection in enumerate(sub_section_analysis[:3], 1):
                    text = subsection.get('refined_text', '')[:100]
                    print(f"  {i}. {text}{'...' if len(subsection.get('refined_text', '')) > 100 else ''}")
        else:
            print("✗ Analysis failed")
            
    except Exception as e:
        print(f"✗ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

def create_sample_config():
    """Create a sample config file for testing"""
    input_dir = Path("input")
    input_dir.mkdir(parents=True, exist_ok=True)
    
    sample_config = {
        "documents": ["sample1.pdf", "sample2.pdf", "sample3.pdf"],
        "persona": "PhD Researcher in Computational Biology",
        "job_to_be_done": "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks"
    }
    
    config_file = input_dir / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print(f"Sample config created at {config_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-sample":
        create_sample_config()
    else:
        print("Starting Round 1B Document Intelligence Processing...")
        process_documents()
        print("Processing completed.")