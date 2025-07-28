import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class SubSectionAnalyzer:
    """
    Analyzes sub-sections within relevant sections for granular insights
    """
    
    def __init__(self):
        self.min_subsection_length = 30  # Minimum words for a subsection
        self.max_subsections_per_section = 5  # Maximum subsections per section
        self.sentence_endings = r'[.!?]'
        
    def analyze_subsections(self, extracted_sections: List[Dict], documents_data: List[Dict], 
                        persona: str, job_to_be_done: str) -> List[Dict]:
        """
        Analyze subsections within the extracted sections
        
        Args:
            extracted_sections: Top-level extracted sections
            documents_data: Original document data for content extraction
            persona: User persona description
            job_to_be_done: Specific task description
            
        Returns:
            List of subsection analyses in required format
        """
        subsection_analyses = []

        # Create document lookup for quick access
        doc_lookup = {doc['file_name']: doc for doc in documents_data}

        for section in extracted_sections:
            document_name = section.get('document', '')
            page_number = section.get('page_number', 1)
            section_title = section.get('section_title', '')

            if document_name not in doc_lookup:
                continue

            # Find the full content for this section
            section_content = self._find_section_content(
                doc_lookup[document_name], section_title, page_number
            )

            if not section_content:
                continue

            # Debugging: Print section content to verify it's being extracted correctly
            print(f"Processing Section: {section_title}, Content: {section_content[:100]}...")  # Preview content

            # Extract and analyze subsections
            subsections = self._extract_subsections(section_content, persona, job_to_be_done)
            
            # Debugging: Print subsections to check if they're being correctly generated
            print(f"Subsections for Section '{section_title}': {subsections}")
            
            for subsection in subsections:
                subsection_analysis = {
                    "document": document_name,
                    "section_title": section_title,
                    "refined_text": subsection['refined_text'],
                    "page_number": page_number,
                    "relevance_score": subsection['relevance_score'],
                    "key_insights": subsection.get('key_insights', [])
                }
                subsection_analyses.append(subsection_analysis)

        # Sort by relevance score
        subsection_analyses.sort(key=lambda x: x['relevance_score'], reverse=True)

        return subsection_analyses

    def _find_section_content(self, doc_data: Dict, section_title: str, page_number: int) -> str:
        """Find the full content for a specific section"""
        headings = doc_data.get('headings', [])
        pages_data = doc_data.get('pages_data', [])
        
        # Find the matching heading
        target_heading = None
        for heading in headings:
            if (self._normalize_text(heading.get('text', '')) == self._normalize_text(section_title) and
                heading.get('page', 0) == page_number):
                target_heading = heading
                break
        
        if not target_heading:
            # Fallback: extract content from the specified page
            for page_data in pages_data:
                if page_data.get('page_number', 0) == page_number:
                    return self._extract_page_text(page_data)
            return ""
        
        # Extract content from heading to next heading or end of document
        content = self._extract_section_content_by_heading(target_heading, headings, pages_data)
        return content
    
    def _extract_section_content_by_heading(self, current_heading: Dict, 
                                          all_headings: List[Dict], 
                                          pages_data: List[Dict]) -> str:
        """Extract content between current heading and next heading of same or higher level"""
        start_page = current_heading.get('page', 1)
        start_y = current_heading.get('y_position', 0)
        current_level = int(current_heading.get('level', 'H1')[1:])
        
        # Find next heading of same or higher level
        next_heading = None
        for heading in all_headings:
            if (heading.get('page', 0) > start_page or 
                (heading.get('page', 0) == start_page and heading.get('y_position', 0) > start_y)):
                heading_level = int(heading.get('level', 'H1')[1:])
                if heading_level <= current_level:
                    next_heading = heading
                    break
        
        # Extract content
        content_parts = []
        for page_data in pages_data:
            page_num = page_data.get('page_number', 1)
            
            if page_num < start_page:
                continue
            
            if next_heading and page_num > next_heading.get('page', float('inf')):
                break
            
            # Extract text from this page
            elements = page_data.get('elements', [])
            for element in elements:
                y_pos = element.get('y_position', 0)
                
                # Check if element is within section bounds
                if page_num == start_page and y_pos <= start_y:
                    continue
                
                if (next_heading and page_num == next_heading.get('page') and 
                    y_pos >= next_heading.get('y_position', 0)):
                    break
                
                text = element.get('text', '').strip()
                if text:
                    content_parts.append(text)
        
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
    
    def _extract_subsections(self, content: str, persona: str, job_to_be_done: str) -> List[Dict]:
        """Extract meaningful subsections from content"""
        if not content or len(content.split()) < self.min_subsection_length:
            return []

        # Split content into paragraphs and sentences
        paragraphs = self._split_into_paragraphs(content)
        subsections = []

        # Debugging: Print paragraphs to ensure they're correctly split
        print(f"Paragraphs: {paragraphs[:3]}")  # Preview of first few paragraphs

        for paragraph in paragraphs:
            if len(paragraph.split()) >= self.min_subsection_length:
                # Analyze this paragraph as a subsection
                refined_text = self._refine_text(paragraph)
                relevance_score = self._calculate_subsection_relevance(
                    refined_text, persona, job_to_be_done
                )
                key_insights = self._extract_key_insights(refined_text, persona, job_to_be_done)

                if relevance_score > 0.3:  # Minimum relevance threshold
                    subsections.append({
                        'refined_text': refined_text,
                        'relevance_score': relevance_score,
                        'key_insights': key_insights
                    })
        
        # If no good paragraphs, try sentence-based approach
        if not subsections:
            sentences = self._split_into_sentences(content)
            current_subsection = []

            for sentence in sentences:
                current_subsection.append(sentence)

                if len(' '.join(current_subsection).split()) >= self.min_subsection_length:
                    subsection_text = ' '.join(current_subsection)
                    refined_text = self._refine_text(subsection_text)
                    relevance_score = self._calculate_subsection_relevance(
                        refined_text, persona, job_to_be_done
                    )

                    if relevance_score > 0.3:
                        key_insights = self._extract_key_insights(refined_text, persona, job_to_be_done)
                        subsections.append({
                            'refined_text': refined_text,
                            'relevance_score': relevance_score,
                            'key_insights': key_insights
                        })

                    current_subsection = []

        # Debugging: Print subsections after processing
        print(f"Extracted Subsections: {subsections}")

        # Sort by relevance and take top subsections
        subsections.sort(key=lambda x: x['relevance_score'], reverse=True)
        return subsections[:self.max_subsections_per_section]

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs"""
        # Split by double newlines or clear paragraph breaks
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Clean and filter paragraphs
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and len(paragraph.split()) >= 10:  # Minimum paragraph length
                cleaned_paragraphs.append(paragraph)
        
        return cleaned_paragraphs
    
    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences"""
        # Simple sentence splitting
        sentences = re.split(self.sentence_endings, content)
        
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence.split()) >= 5:  # Minimum sentence length
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _refine_text(self, text: str) -> str:
        """Refine and clean text for output"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'^\s*[\u2022\u25cf\u25cb]\s*', '', text)
        
        # Ensure proper sentence ending
        if text and not text.endswith(('.', '!', '?', ':')):
            text += '.'
        
        return text.strip()
    
    def _calculate_subsection_relevance(self, text: str, persona: str, job_to_be_done: str) -> float:
        """Calculate relevance score for a subsection"""
        text_lower = text.lower()
        
        # Fix: Extract the correct string value from persona dictionary
        persona_string = persona.get('role', '').lower()  # Assuming 'role' is the string to analyze
        
        # Fix: Extract the correct string value from job_to_be_done dictionary
        job_string = job_to_be_done.get('task', '').lower()  # Assuming 'task' is the string to analyze
        
        job_lower = job_string.lower()  # Now job_string is a string
        
        score = 0.0
        
        # Extract keywords from persona and job
        persona_keywords = self._extract_keywords(persona_string)
        job_keywords = self._extract_keywords(job_lower)
        
        # Count keyword matches
        text_words = set(re.findall(r'\b\w+\b', text_lower))
        persona_matches = len(persona_keywords.intersection(text_words))
        job_matches = len(job_keywords.intersection(text_words))
        
        # Calculate normalized scores
        if len(text_words) > 0:
            score += (persona_matches / len(text_words)) * 0.4
            score += (job_matches / len(text_words)) * 0.6
        
        # Bonus for exact phrase matches
        for keyword in persona_keywords:
            if len(keyword.split()) > 1 and keyword in text_lower:
                score += 0.1
        
        for keyword in job_keywords:
            if len(keyword.split()) > 1 and keyword in text_lower:
                score += 0.15
        
        return min(score, 1.0)  # Cap at 1.0


    
    def _extract_key_insights(self, text: str, persona: str, job_to_be_done: str) -> List[str]:
        """Extract key insights from the text"""
        insights = []
        
        # Look for sentences with key insight indicators
        sentences = re.split(self.sentence_endings, text)
        
        insight_indicators = [
            'important', 'key', 'significant', 'critical', 'essential', 'main',
            'primary', 'fundamental', 'crucial', 'major', 'notable', 'remarkable'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence.split()) >= 8 and 
                any(indicator in sentence.lower() for indicator in insight_indicators)):
                insights.append(sentence + '.')
        
        # If no insights found, extract sentences with numbers or specific terms
        if not insights:
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence.split()) >= 8 and 
                    (re.search(r'\d+', sentence) or 
                     any(term in sentence.lower() for term in ['result', 'finding', 'conclusion', 'shows', 'indicates']))):
                    insights.append(sentence + '.')
        
        return insights[:3]  # Return top 3 insights
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text"""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = set()
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.add(word)
        
        return keywords
    
    def _has_technical_content(self, text: str) -> bool:
        """Check if text has technical content"""
        technical_indicators = [
            'method', 'approach', 'technique', 'algorithm', 'system', 'model',
            'framework', 'process', 'procedure', 'implementation', 'analysis'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in technical_indicators)
    
    def _has_quantitative_content(self, text: str) -> bool:
        """Check if text has quantitative content"""
        return bool(re.search(r'\d+', text))
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        return re.sub(r'\s+', ' ', text.lower().strip())