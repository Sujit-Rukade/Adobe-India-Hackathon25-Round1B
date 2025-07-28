import re
import math
from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict

class RelevanceAnalyzer:
    """
    Analyzes relevance of document sections to persona and job-to-be-done
    """
    
    def __init__(self):
        # Domain-specific keywords for different personas
        self.persona_keywords = {
            'researcher': ['research', 'study', 'analysis', 'methodology', 'experiment', 'findings', 'literature', 'survey', 'review', 'academic', 'publication', 'dataset', 'benchmark', 'evaluation', 'metrics'],
            'student': ['learn', 'study', 'understand', 'concept', 'theory', 'practice', 'example', 'exercise', 'problem', 'solution', 'tutorial', 'guide', 'basics', 'fundamentals', 'introduction'],
            'analyst': ['analysis', 'data', 'trends', 'metrics', 'performance', 'report', 'insights', 'statistics', 'comparison', 'evaluation', 'assessment', 'strategy', 'planning', 'forecast'],
            'engineer': ['implementation', 'design', 'architecture', 'system', 'technical', 'specification', 'requirements', 'development', 'engineering', 'performance', 'optimization', 'scalability'],
            'manager': ['strategy', 'planning', 'management', 'decision', 'leadership', 'team', 'project', 'resource', 'budget', 'timeline', 'risk', 'stakeholder', 'business', 'objective'],
            'salesperson': ['sales', 'revenue', 'customer', 'market', 'competition', 'pricing', 'product', 'service', 'client', 'prospect', 'deal', 'negotiation', 'relationship', 'growth'],
            'journalist': ['news', 'report', 'story', 'investigation', 'interview', 'source', 'fact', 'event', 'update', 'coverage', 'article', 'publication', 'media', 'press'],
            'entrepreneur': ['business', 'startup', 'opportunity', 'market', 'innovation', 'investment', 'funding', 'growth', 'strategy', 'competition', 'revenue', 'customer', 'product', 'scale']
        }
        
        # Job-specific keywords
        self.job_keywords = {
            'literature_review': ['review', 'survey', 'comparison', 'analysis', 'methodology', 'findings', 'research', 'studies', 'approaches', 'techniques', 'evaluation', 'benchmarks'],
            'exam_preparation': ['key', 'concepts', 'important', 'remember', 'understand', 'practice', 'example', 'problem', 'solution', 'theory', 'principle', 'formula', 'definition'],
            'financial_analysis': ['revenue', 'profit', 'cost', 'expense', 'financial', 'performance', 'growth', 'investment', 'return', 'margin', 'cash', 'budget', 'forecast'],
            'market_analysis': ['market', 'competition', 'trends', 'share', 'size', 'growth', 'opportunity', 'threat', 'customer', 'segment', 'positioning', 'strategy'],
            'technical_implementation': ['implementation', 'design', 'architecture', 'system', 'technical', 'specification', 'requirements', 'development', 'coding', 'testing'],
            'summary': ['summary', 'overview', 'key', 'main', 'important', 'highlights', 'conclusion', 'findings', 'results', 'insights', 'takeaways'],
            'comparison': ['compare', 'comparison', 'versus', 'difference', 'similarity', 'contrast', 'alternative', 'option', 'choice', 'evaluation', 'assessment']
        }
    
    def analyze_relevance(self, documents_data: List[Dict], persona: str, job_to_be_done: str) -> List[Dict]:
        """
        Analyze relevance of all sections across documents
        """
        # Fix: Extract the correct string value from persona dictionary
        persona_string = persona.get('role', '').lower()  # Assuming 'role' is the string to analyze
        
        # Fix: Extract the correct string value from job_to_be_done dictionary
        job_string = job_to_be_done.get('task', '').lower()  # Assuming 'task' is the string to analyze
        
        # Extract keywords from persona and job description
        persona_keywords = self._extract_keywords_from_text(persona_string)  # Use the correct string
        job_keywords = self._extract_keywords_from_text(job_string)  # Use the correct string
        
        # Add domain-specific keywords
        persona_keywords.update(self._get_persona_specific_keywords(persona_string))  # Use the correct string
        job_keywords.update(self._get_job_specific_keywords(job_string))  # Use the correct string
        
        relevant_sections = []
        
        for doc_data in documents_data:
            doc_sections = self._extract_document_sections(doc_data)
            
            for section in doc_sections:
                relevance_score = self._calculate_relevance_score(
                    section, persona_keywords, job_keywords, persona_string, job_string
                )
                
                # Ensure we only add relevant sections with a non-zero relevance score
                if relevance_score > 0.1:  # Minimum threshold for relevance
                    section['relevance_score'] = relevance_score
                    section['document'] = doc_data['file_name']
                    relevant_sections.append(section)
        
        # Sort by relevance score in descending order
        relevant_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return relevant_sections

    
    def _extract_document_sections(self, doc_data: Dict) -> List[Dict]:
        """Extract sections from a document based on headings"""
        sections = []
        headings = doc_data.get('headings', [])
        pages_data = doc_data.get('pages_data', [])
        
        if not headings:
            # If no headings, treat each page as a section
            for i, page_data in enumerate(pages_data):
                page_text = self._extract_page_text(page_data)
                if page_text.strip():
                    sections.append({
                        'section_title': f"Page {i + 1}",
                        'page_number': i + 1,
                        'content': page_text,
                        'heading_level': 'H1'
                    })
            return sections
        
        # Create sections based on headings
        for i, heading in enumerate(headings):
            section_content = self._extract_section_content(
                heading, headings[i+1:], pages_data
            )
            
            if section_content.strip():
                sections.append({
                    'section_title': heading.get('text', ''),
                    'page_number': heading.get('page', 1),
                    'content': section_content,
                    'heading_level': heading.get('level', 'H1')
                })
        
        return sections
    
    def _extract_section_content(self, current_heading: Dict, 
                                remaining_headings: List[Dict], 
                                pages_data: List[Dict]) -> str:
        """Extract content for a specific section"""
        start_page = current_heading.get('page', 1)
        start_y = current_heading.get('y_position', 0)
        
        # Find next heading to determine section boundary
        next_heading = None
        current_level = int(current_heading.get('level', 'H1')[1:])
        
        for heading in remaining_headings:
            heading_level = int(heading.get('level', 'H1')[1:])
            if heading_level <= current_level:
                next_heading = heading
                break
        
        # Extract content between headings
        content_parts = []
        
        for page_data in pages_data:
            page_num = page_data.get('page_number', 1)
            
            # Skip pages before section start
            if page_num < start_page:
                continue
            
            # Stop at next section if on different page
            if next_heading and page_num > next_heading.get('page', float('inf')):
                break
            
            # Extract relevant text from page
            page_content = self._extract_page_text_for_section(
                page_data, start_y if page_num == start_page else 0,
                next_heading.get('y_position', float('inf')) if next_heading and page_num == next_heading.get('page') else float('inf')
            )
            
            if page_content.strip():
                content_parts.append(page_content)
        
        return ' '.join(content_parts)
    
    def _extract_page_text(self, page_data: Dict) -> str:
        """Extract all text from a page"""
        elements = page_data.get('elements', [])
        text_parts = []
        
        for element in elements:
            text = element.get('text', '').strip()
            if text:
                text_parts.append(text)
        
        return ' '.join(text_parts)
    
    def _extract_page_text_for_section(self, page_data: Dict, start_y: float, end_y: float) -> str:
        """Extract text from a page within specific y-coordinate range"""
        elements = page_data.get('elements', [])
        text_parts = []
        
        for element in elements:
            y_pos = element.get('y_position', 0)
            if start_y <= y_pos < end_y:
                text = element.get('text', '').strip()
                if text:
                    text_parts.append(text)
        
        return ' '.join(text_parts)
    
    def _calculate_relevance_score(self, section: Dict, persona_keywords: Set[str], 
                                 job_keywords: Set[str], persona: str, job_to_be_done: str) -> float:
        """Calculate relevance score for a section"""
        content = section.get('content', '').lower()
        title = section.get('section_title', '').lower()
        
        score = 0.0
        
        # Title relevance (higher weight)
        title_persona_matches = len([kw for kw in persona_keywords if kw in title])
        title_job_matches = len([kw for kw in job_keywords if kw in title])
        score += (title_persona_matches * 0.3) + (title_job_matches * 0.4)
        
        # Content relevance
        content_words = set(re.findall(r'\b\w+\b', content))
        persona_matches = len(persona_keywords.intersection(content_words))
        job_matches = len(job_keywords.intersection(content_words))
        
        # Normalize by content length
        content_length = len(content_words)
        if content_length > 0:
            score += (persona_matches / content_length) * 0.2
            score += (job_matches / content_length) * 0.3
        
        # Boost for exact phrase matches
        for keyword in persona_keywords:
            if len(keyword.split()) > 1 and keyword in content:
                score += 0.1
        
        for keyword in job_keywords:
            if len(keyword.split()) > 1 and keyword in content:
                score += 0.15
        
        # Section level bonus (higher level sections are often more important)
        level = section.get('heading_level', 'H3')
        level_num = int(level[1:]) if level.startswith('H') else 3
        level_bonus = max(0, (4 - level_num) * 0.05)
        score += level_bonus
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract keywords from text using simple NLP techniques"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Extract words and filter
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = set()
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.add(word)
        
        # Extract meaningful phrases (2-3 words)
        words_list = [w for w in words if w not in stop_words and len(w) > 2]
        for i in range(len(words_list) - 1):
            phrase = ' '.join(words_list[i:i+2])
            if len(phrase) > 5:
                keywords.add(phrase)
        
        return keywords
    
    def _get_persona_specific_keywords(self, persona: str) -> Set[str]:
        """Get domain-specific keywords based on persona"""
        persona_lower = persona.lower()
        keywords = set()
        
        for persona_type, type_keywords in self.persona_keywords.items():
            if persona_type in persona_lower:
                keywords.update(type_keywords)
        
        return keywords
    
    def _get_job_specific_keywords(self, job_to_be_done: str) -> Set[str]:
        """Get task-specific keywords based on job description"""
        job_lower = job_to_be_done.lower()
        keywords = set()
        
        for job_type, type_keywords in self.job_keywords.items():
            if any(keyword in job_lower for keyword in job_type.split('_')):
                keywords.update(type_keywords)
        
        return keywords
