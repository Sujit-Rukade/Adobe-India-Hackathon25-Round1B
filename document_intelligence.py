import json
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

from pdf_parser import PDFParser
from text_analyzer import TextAnalyzer
from heading_detector import HeadingDetector
from relevance_analyzer import RelevanceAnalyzer
from section_extractor import SectionExtractor
from subsection_analyzer import SubSectionAnalyzer

class DocumentIntelligenceService:
    """
    Main service for persona-driven document intelligence
    """
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.text_analyzer = TextAnalyzer()
        self.heading_detector = HeadingDetector()
        self.relevance_analyzer = RelevanceAnalyzer()
        self.section_extractor = SectionExtractor()
        self.subsection_analyzer = SubSectionAnalyzer()
    
    def process_document_collection(self, pdf_files: List[str], persona: str, 
                                  job_to_be_done: str, verbose: bool = False) -> Dict:
        """
        Process a collection of documents for persona-driven intelligence
        
        Args:
            pdf_files: List of PDF file paths
            persona: Description of the user persona
            job_to_be_done: Specific task to accomplish
            verbose: Enable verbose logging
            
        Returns:
            Analysis result in required JSON format
        """
        try:
            if verbose:
                print(f"Processing {len(pdf_files)} documents for persona analysis")
            
            # Step 1: Parse all documents and extract structure
            documents_data = []
            for pdf_file in pdf_files:
                if verbose:
                    print(f"Parsing document: {Path(pdf_file).name}")
                
                doc_data = self._parse_single_document(pdf_file, verbose)
                if doc_data:
                    documents_data.append(doc_data)
            
            if not documents_data:
                print("No documents could be parsed")
                return self._create_empty_result(pdf_files, persona, job_to_be_done)
            
            if verbose:
                print(f"Successfully parsed {len(documents_data)} documents")
            
            # Step 2: Analyze relevance for persona and job
            if verbose:
                print("Analyzing section relevance...")
            
            relevant_sections = self.relevance_analyzer.analyze_relevance(
                documents_data, persona, job_to_be_done
            )
            
            if verbose:
                print(f"Found {len(relevant_sections)} potentially relevant sections")
            
            # Step 3: Extract and rank sections
            if verbose:
                print("Extracting and ranking sections...")
            
            extracted_sections = self.section_extractor.extract_sections(
                documents_data, relevant_sections, persona, job_to_be_done
            )
            
            # Step 4: Perform sub-section analysis
            if verbose:
                print("Performing sub-section analysis...")
            
            subsection_analysis = self.subsection_analyzer.analyze_subsections(
                extracted_sections, documents_data, persona, job_to_be_done
            )
            
            # Step 5: Build final result
            result = self._build_result(
                pdf_files, persona, job_to_be_done, 
                extracted_sections, subsection_analysis
            )
            
            if verbose:
                print("Analysis completed successfully")
            
            return result
            
        except Exception as e:
            print(f"Error in document intelligence processing: {str(e)}")
            if verbose:
                import traceback
                traceback.print_exc()
            return self._create_empty_result(pdf_files, persona, job_to_be_done)
    
    def _parse_single_document(self, pdf_file: str, verbose: bool = False) -> Optional[Dict]:
        """Parse a single PDF document and extract structured content"""
        try:
            # Parse PDF
            pages_data = self.pdf_parser.parse_pdf(pdf_file)
            if not pages_data:
                return None
            
            # Analyze elements
            analyzed_elements = self.text_analyzer.analyze_elements(pages_data)
            
            # Detect headings
            headings = self.heading_detector.detect_headings(analyzed_elements)
            headings = self.heading_detector.filter_false_positives(headings)
            
            # Extract title
            title = self._extract_document_title(pages_data)
            
            # Build document structure
            document_data = {
                'file_path': pdf_file,
                'file_name': Path(pdf_file).name,
                'title': title,
                'pages_data': pages_data,
                'headings': headings,
                'analyzed_elements': analyzed_elements
            }
            
            if verbose:
                print(f"  - Title: {title[:60]}{'...' if len(title) > 60 else ''}")
                print(f"  - Pages: {len(pages_data)}")
                print(f"  - Headings: {len(headings)}")
            
            return document_data
            
        except Exception as e:
            print(f"Error parsing {pdf_file}: {str(e)}")
            return None
    
    def _extract_document_title(self, pages_data: List[Dict]) -> str:
        """Extract document title from first page"""
        if not pages_data:
            return ""
        
        first_page = pages_data[0]
        elements = first_page.get('elements', [])
        
        # Sort by position (top first)
        elements = sorted(elements, key=lambda e: (e.get('y_position', 0), e.get('x_position', 0)))
        
        for element in elements[:15]:  # Check first 15 elements
            text = element.get('text', '').strip()
            
            if len(text) < 5:
                continue
            
            # Skip obvious non-titles
            if re.match(r'^\d+$|^page\s+\d+|^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text.lower()):
                continue
            
            if any(word in text.lower() for word in [
                'copyright', 'version', 'draft', 'confidential'
            ]):
                continue
            
            # Good title candidate
            font_size = element.get('font_size', 12)
            is_bold = element.get('is_bold', False)
            
            if (len(text) > 10 and (font_size > 14 or is_bold)) or len(text) > 20:
                return text
        
        return ""
    
    def _build_result(self, pdf_files: List[str], persona: str, job_to_be_done: str,
                  extracted_sections: List[Dict], subsection_analysis: List[Dict]) -> Dict:
        """Build the final result in the required JSON format"""
        
        # Get document names from file paths
        document_names = [Path(pdf_file).name for pdf_file in pdf_files]
        
        # Create the final result
        result = {
            "metadata": {
                "input_documents": document_names,  # List of document names
                "persona": persona,  # Persona as a string
                "job_to_be_done": job_to_be_done,  # Job to be done as a string
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": extracted_sections,  # Extracted and ranked sections
            "subsection_analysis": subsection_analysis  # Subsection analysis
        }
        
        print(f"Final Result: {json.dumps(result, indent=2)}")  # Debugging line to check final result structure
        
        return result


        
        return result
    
    def _create_empty_result(self, pdf_files: List[str], persona: str, job_to_be_done: str) -> Dict:
        """Create empty result structure for error cases"""
        document_names = [Path(pdf_file).name for pdf_file in pdf_files]
        
        return {
            "metadata": {
                "input_documents": document_names,
                "persona": persona,  # Corrected to be a string
                "job_to_be_done": job_to_be_done,  # Corrected to be a string
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": [],
            "subsection_analysis": []  # Corrected to match the field name
        }
