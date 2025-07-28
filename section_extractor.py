from typing import Dict, List, Tuple
import re

class SectionExtractor:
    """
    Extracts and ranks sections based on relevance analysis
    """
    
    def __init__(self):
        self.max_sections = 20  # Maximum sections to extract
        self.min_relevance_score = 0.2  # Minimum relevance threshold
    
    def extract_sections(self, documents_data: List[Dict], relevant_sections: List[Dict], 
                     persona: str, job_to_be_done: str) -> List[Dict]:
        """
        Extract and rank the most relevant sections
        """
        # Filter sections by minimum relevance score
        filtered_sections = [
            section for section in relevant_sections
            if section.get('relevance_score', 0) >= self.min_relevance_score
        ]

        # Rank sections by final score
        for section in filtered_sections:
            section['final_score'] = self._calculate_final_score(section, persona, job_to_be_done)
        
        # Sort sections by final score in descending order
        filtered_sections.sort(key=lambda x: x['final_score'], reverse=True)

        # Limit to top sections based on importance rank (importance_rank <= 5)
        top_sections = filtered_sections[:self.max_sections]

        # Format sections for output
        extracted_sections = []
        for i, section in enumerate(top_sections, 1):
            # Only include sections with importance rank <= 5
            if i <= 5:
                extracted_section = {
                    "document": section.get('document', ''),
                    "page_number": section.get('page_number', 1),
                    "section_title": self._clean_section_title(section.get('section_title', '')),
                    "importance_rank": i,  # Set importance rank
                }
                extracted_sections.append(extracted_section)

        print(f"Extracted Sections (Rank 5 and below): {extracted_sections}")  # Debugging line to check extracted sections
        
        return extracted_sections



    
    def _calculate_final_score(self, section: Dict, persona: str, job_to_be_done: str) -> float:
        """Calculate final ranking score with additional factors"""
        base_score = section.get('relevance_score', 0)
        
        # Additional scoring factors
        bonus = 0.0
        
        # Section length factor (moderate length preferred)
        content_length = len(section.get('content', '').split())
        if 50 <= content_length <= 500:
            bonus += 0.1
        elif content_length > 500:
            bonus += 0.05
        
        # Section level factor (higher level sections often more important)
        level = section.get('heading_level', 'H3')
        level_num = int(level[1:]) if level.startswith('H') else 3
        if level_num <= 2:
            bonus += 0.15
        elif level_num == 3:
            bonus += 0.05
        
        # Title quality factor
        title = section.get('section_title', '').lower()
        if any(word in title for word in ['introduction', 'overview', 'summary', 'conclusion']):
            bonus += 0.1
        
        # Specific persona bonuses
        if self._has_persona_specific_content(section, persona):
            bonus += 0.1
        
        # Job-specific bonuses
        if self._has_job_specific_content(section, job_to_be_done):
            bonus += 0.1
        
        return min(base_score + bonus, 1.0)
    
    def _has_persona_specific_content(self, section: Dict, persona: str) -> bool:
        """Check if section has persona-specific content"""
        content = section.get('content', '').lower()
        title = section.get('section_title', '').lower()
        
        # Fix: Extract the correct string value from persona dictionary
        persona_string = persona.get('role', '').lower()  # Assuming 'role' is the string to analyze
        
        persona_indicators = {
            'researcher': ['methodology', 'experiment', 'analysis', 'results', 'findings', 'study', 'research', 'data', 'statistical', 'empirical'],
            'student': ['example', 'exercise', 'practice', 'tutorial', 'concept', 'theory', 'learn', 'understand', 'definition', 'explanation'],
            'analyst': ['data', 'metrics', 'performance', 'trends', 'statistics', 'insights', 'report', 'analysis', 'comparison', 'benchmark'],
            'engineer': ['implementation', 'system', 'design', 'architecture', 'technical', 'specification', 'development', 'optimization', 'scalability'],
            'manager': ['strategy', 'planning', 'management', 'objectives', 'goals', 'resources', 'team', 'leadership', 'decision', 'business'],
            'salesperson': ['sales', 'revenue', 'customer', 'market', 'pricing', 'product', 'client', 'growth', 'competition', 'opportunity'],
            'journalist': ['news', 'report', 'investigation', 'facts', 'source', 'interview', 'story', 'coverage', 'update', 'event'],
            'entrepreneur': ['business', 'startup', 'innovation', 'market', 'opportunity', 'investment', 'growth', 'strategy', 'revenue', 'customer']
        }
        
        # Use persona_string instead of persona directly
        persona_lower = persona_string.lower()  # Now persona_string is a string
        
        for persona_type, indicators in persona_indicators.items():
            if persona_type in persona_lower:
                if any(indicator in content or indicator in title for indicator in indicators):
                    return True
        
        return False

    
    def _has_job_specific_content(self, section: Dict, job_to_be_done: str) -> bool:
        """Check if section has job-specific content"""
        content = section.get('content', '').lower()
        title = section.get('section_title', '').lower()
        
        # Fix: Extract the correct string value from job_to_be_done dictionary
        job_string = job_to_be_done.get('task', '').lower()  # Assuming 'task' is the string to analyze
        
        job_indicators = {
            'literature review': ['review', 'survey', 'comparison', 'analysis', 'methodology', 'findings', 'research', 'studies', 'approaches', 'techniques', 'evaluation', 'benchmarks'],
            'exam preparation': ['key', 'concepts', 'important', 'remember', 'understand', 'practice', 'example', 'problem', 'solution', 'theory', 'principle', 'formula', 'definition'],
            'financial analysis': ['revenue', 'profit', 'cost', 'expense', 'financial', 'performance', 'growth', 'investment', 'return', 'margin', 'cash', 'budget', 'forecast'],
            'market analysis': ['market', 'competition', 'trends', 'share', 'size', 'growth', 'opportunity', 'threat', 'customer', 'segment', 'positioning', 'strategy'],
            'technical implementation': ['implementation', 'design', 'architecture', 'system', 'technical', 'specification', 'requirements', 'development', 'coding', 'testing'],
            'summary': ['summary', 'overview', 'key points', 'highlights', 'conclusion', 'findings', 'results', 'insights'],
            'comparison': ['compare', 'comparison', 'versus', 'difference', 'similarity', 'contrast', 'alternative', 'option', 'choice', 'evaluation', 'assessment']
        }
        
        # Use job_string instead of job_to_be_done directly
        job_lower = job_string.lower()  # Now job_string is a string
        
        for job_type, indicators in job_indicators.items():
            if job_type in job_lower:
                if any(indicator in content or indicator in title for indicator in indicators):
                    return True
        
        return False

    
    def _clean_section_title(self, title: str) -> str:
        """Clean and normalize section title"""
        if not title:
            return "Untitled Section"
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        # Remove leading numbers/bullets
        title = re.sub(r'^\d+\.?\s*', '', title)
        title = re.sub(r'^[\u2022\u25cf\u25cb]\s*', '', title)
        
        # Capitalize first letter if not already
        if title and title[0].islower():
            title = title[0].upper() + title[1:]
        
        return title.strip()
