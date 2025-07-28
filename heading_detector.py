import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

class HeadingDetector:
    
    def __init__(self):
        self.min_heading_score = 1.5
        self.hierarchical_patterns = [
            r'^\d+\.?\s+',           
            r'^\d+\.\d+\.?\s+',      
            r'^\d+\.\d+\.\d+\.?\s+', 
            r'^\d+\.\d+\.\d+\.\d+',  
        ]
    
    def detect_headings(self, analyzed_elements: List[Dict]) -> List[Dict]:
        if not analyzed_elements:
            return []
        
        score_headings = self._detect_by_score(analyzed_elements)
        
        pattern_headings = self._detect_by_patterns(analyzed_elements)
        
        font_headings = self._detect_by_font_clustering(analyzed_elements)
        
        all_candidates = self._combine_strategies(
            score_headings, pattern_headings, font_headings
        )
        
        final_headings = self._assign_hierarchy_levels(all_candidates)
        
        final_headings.sort(key=lambda h: (h['page'], h.get('y_position', 0)))
        
        return final_headings
    
    def _detect_by_score(self, elements: List[Dict]) -> List[Dict]:
        headings = []
        
        for element in elements:
            score = element.get('heading_score', 0)
            if score >= self.min_heading_score:
                heading = self._create_heading_dict(element)
                heading['detection_method'] = 'score'
                heading['confidence'] = min(score / 5.0, 1.0)  
                headings.append(heading)
        
        return headings
    
    def _detect_by_patterns(self, elements: List[Dict]) -> List[Dict]:
        headings = []
        
        for element in elements:
            text = element.get('text', '').strip()
            
            for level, pattern in enumerate(self.hierarchical_patterns, 1):
                if re.match(pattern, text):
                    heading = self._create_heading_dict(element)
                    heading['detection_method'] = 'pattern'
                    heading['pattern_level'] = level
                    heading['confidence'] = 0.9
                    headings.append(heading)
                    break
        
        return headings
    
    def _detect_by_font_clustering(self, elements: List[Dict]) -> List[Dict]:
        font_groups = defaultdict(list)
        for element in elements:
            font_size = element.get('font_size', 12)
            font_groups[font_size].append(element)
        
        sorted_sizes = sorted(font_groups.keys(), reverse=True)
        
        headings = []
        for i, font_size in enumerate(sorted_sizes[:4]):  
            elements_with_size = font_groups[font_size]
            
            candidates = []
            for element in elements_with_size:
                text = element.get('text', '').strip()
                
                if len(text) > 200:
                    continue
                
                if re.match(r'^\d+$|^page\s+\d+', text.lower()):
                    continue
                
                candidates.append(element)
            
            if 2 <= len(candidates) <= 20:  
                for element in candidates:
                    heading = self._create_heading_dict(element)
                    heading['detection_method'] = 'font_cluster'
                    heading['font_level'] = i + 1
                    heading['confidence'] = 0.7 - (i * 0.15)  
                    headings.append(heading)
        
        return headings
    
    def _combine_strategies(self, *strategy_results: List[Dict]) -> List[Dict]:
        combined = {}
        
        for strategy_headings in strategy_results:
            for heading in strategy_headings:
                key = (heading['text'][:50], heading['page'])  
                
                if key in combined:
                    existing = combined[key]
                    existing['confidence'] = min(existing['confidence'] + 0.2, 1.0)
                    existing['detection_methods'] = existing.get('detection_methods', []) + [heading['detection_method']]
                else:
                    combined[key] = heading
                    heading['detection_methods'] = [heading['detection_method']]
        
        return list(combined.values())
    
    def _assign_hierarchy_levels(self, headings: List[Dict]) -> List[Dict]:
        if not headings:
            return []
        
        pattern_levels = {}
        for heading in headings:
            if 'pattern_level' in heading:
                level = heading['pattern_level']
                if level not in pattern_levels:
                    pattern_levels[level] = []
                pattern_levels[level].append(heading)
        
        for heading in headings:
            level = self._determine_heading_level(heading, headings)
            heading['level'] = f"H{level}"
        
        return headings
    
    def _determine_heading_level(self, heading: Dict, all_headings: List[Dict]) -> int:
        
        if 'pattern_level' in heading:
            return heading['pattern_level']
        
        font_size = heading.get('font_size', 12)
        font_sizes = [h.get('font_size', 12) for h in all_headings]
        unique_sizes = sorted(set(font_sizes), reverse=True)
        
        try:
            size_level = unique_sizes.index(font_size) + 1
            return min(size_level, 6)  
        except ValueError:
            return 3  
    
    def _create_heading_dict(self, element: Dict) -> Dict:
        return {
            'text': element.get('text', '').strip(),
            'page': element.get('page', 1),
            'font_size': element.get('font_size', 12),
            'is_bold': element.get('is_bold', False),
            'bbox': element.get('bbox', [0, 0, 0, 0]),
            'y_position': element.get('y_position', 0),
            'x_position': element.get('x_position', 0)
        }
    
    def filter_false_positives(self, headings: List[Dict]) -> List[Dict]:
        filtered = []
        
        for heading in headings:
            text = heading.get('text', '').strip()
            
            if len(text) < 3:
                continue
            
            if re.match(r'^\d+$', text):
                continue
            
            if any(pattern in text.lower() for pattern in [
                'page ', 'copyright', '©', 'draft', 'confidential',
                'version', 'rev', 'date:', 'author:'
            ]):
                continue
            
            if heading.get('confidence', 0) > 0.3:
                filtered.append(heading)
        
        return filtered