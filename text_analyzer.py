"""
Text Analyzer Module
Analyzes text elements to identify potential headings
"""

import re
import statistics
from typing import List, Dict, Set
from collections import Counter

class TextAnalyzer:
    """Analyzes text elements for heading characteristics"""
    
    def __init__(self):
        # Common heading patterns
        self.heading_patterns = [
            r'^\d+\.?\s+[A-Z]',  # "1. Introduction" or "1 Introduction"
            r'^\d+\.\d+\.?\s+',  # "1.1 Subsection" or "1.1. Subsection"
            r'^\d+\.\d+\.\d+',   # "1.1.1 Sub-subsection"
            r'^[A-Z][a-z]+:',    # "Chapter:", "Section:"
            r'^[IVX]+\.?\s+[A-Z]', # Roman numerals
            r'^[A-Z]\.?\s+[A-Z]',  # "A. Section" or "A Section"
            r'^Chapter\s+\d+',   # "Chapter 1"
            r'^Section\s+\d+',   # "Section 1"
            r'^Appendix\s+[A-Z]' # "Appendix A"
        ]
        
        # Words commonly found in headings
        self.heading_keywords = {
            'introduction', 'conclusion', 'summary', 'overview', 'background',
            'methodology', 'method', 'approach', 'results', 'discussion',
            'chapter', 'section', 'appendix', 'references', 'bibliography',
            'abstract', 'objectives', 'goals', 'requirements', 'specifications',
            'implementation', 'analysis', 'evaluation', 'recommendations',
            'acknowledgments', 'acknowledgements', 'contents', 'index'
        }
        
        # Common non-heading patterns to exclude
        self.exclude_patterns = [
            r'^\d+$',  # Just page numbers
            r'^page\s+\d+',  # "Page 1"
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Dates
            r'^copyright\s+',  # Copyright notices
            r'^©\s*\d{4}',  # Copyright symbols
            r'^\s*$',  # Empty or whitespace
            r'^[a-z]+@[a-z]+\.',  # Email addresses
            r'^https?://',  # URLs
        ]
    
    def analyze_elements(self, pages_data: List[Dict]) -> List[Dict]:
        """
        Analyze all text elements across pages
        
        Args:
            pages_data: List of page dictionaries from PDF parser
            
        Returns:
            List of analyzed elements with heading scores
        """
        all_elements = []
        
        # Collect all elements
        for page_data in pages_data:
            for element in page_data.get('elements', []):
                all_elements.append(element)
        
        if not all_elements:
            return []
        
        # Calculate document-wide statistics
        font_sizes = [el.get('font_size', 12) for el in all_elements]
        avg_font_size = statistics.mean(font_sizes)
        median_font_size = statistics.median(font_sizes)
        font_size_std = statistics.stdev(font_sizes) if len(font_sizes) > 1 else 0
        
        # Analyze each element
        analyzed_elements = []
        for element in all_elements:
            analyzed = self._analyze_single_element(
                element, avg_font_size, median_font_size, font_size_std
            )
            analyzed_elements.append(analyzed)
        
        return analyzed_elements
    
    def _analyze_single_element(self, element: Dict, avg_font: float, 
                               median_font: float, font_std: float) -> Dict:
        """Analyze a single text element for heading characteristics"""
        
        # Copy original element
        analyzed = element.copy()
        
        text = element.get('text', '').strip()
        font_size = element.get('font_size', 12)
        
        # Calculate heading score
        score = 0.0
        features = {}
        
        if font_size > avg_font:
            score += min((font_size - avg_font) / max(font_std, 1), 3.0)
            features['large_font'] = True
        else:
            features['large_font'] = False
        
        x_pos = element.get('x_position', 0)
        if x_pos < 100:  # Left-aligned
            score += 0.5
            features['left_aligned'] = True
        
        # Text pattern analysis
        pattern_score = self._analyze_text_patterns(text)
        score += pattern_score
        features['pattern_score'] = pattern_score
        
        if len(text) < 100:
            score += 0.5
        if len(text) < 50:
            score += 0.5
            
        # Word characteristics
        words = text.split()
        if len(words) <= 10: 
            score += 0.5
        
        # Keyword analysis
        if any(keyword in text.lower() for keyword in self.heading_keywords):
            score += 1.0
            features['has_heading_keywords'] = True
        
        if element.get('is_bold', False):
            score += 1.0
            features['is_bold'] = True
            
        if element.get('is_caps', False) and len(text) > 3:
            score += 0.5
            features['is_caps'] = True
        
        if self._matches_exclude_patterns(text):
            score -= 2.0
            features['excluded_pattern'] = True
        
        analyzed['heading_score'] = max(0, score)
        analyzed['heading_features'] = features
        
        return analyzed
    
    def _analyze_text_patterns(self, text: str) -> float:
        """Analyze text for common heading patterns"""
        score = 0.0
        
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                score += 1.5
                break
        
        if re.match(r'^\d+\.', text):
            score += 1.0
        elif re.match(r'^\d+\.\d+', text):
            score += 1.2
        elif re.match(r'^\d+\.\d+\.\d+', text):
            score += 1.0
        
        return score
    
    def _matches_exclude_patterns(self, text: str) -> bool:
        """Check if text matches patterns that should exclude it from being a heading"""
        for pattern in self.exclude_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def get_document_stats(self, elements: List[Dict]) -> Dict:
        """Get overall document statistics for analysis"""
        if not elements:
            return {}
        
        font_sizes = [el.get('font_size', 12) for el in elements]
        
        return {
            'total_elements': len(elements),
            'avg_font_size': statistics.mean(font_sizes),
            'median_font_size': statistics.median(font_sizes),
            'font_size_range': (min(font_sizes), max(font_sizes)),
            'unique_fonts': len(set(el.get('font_name', '') for el in elements))
        }