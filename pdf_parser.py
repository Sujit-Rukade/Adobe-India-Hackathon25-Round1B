import fitz  
from typing import List, Dict, Tuple
import re

class PDFParser:
    
    def __init__(self):
        self.min_font_size = 6
        self.max_font_size = 72
    
    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_data = self._extract_page_elements(page, page_num)
                pages_data.append(page_data)
            
            doc.close()
            return pages_data
            
        except Exception as e:
            print(f"Error parsing PDF: {str(e)}")
            return []
    
    def _extract_page_elements(self, page, page_num: int) -> Dict:
        elements = []
        
        blocks = page.get_text("dict")
        
        for block in blocks.get("blocks", []):
            if "lines" not in block:  
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    
                    if not text or len(text) < 2:
                        continue
                    
                    element = {
                        "text": text,
                        "page": page_num + 1,
                        "bbox": span.get("bbox", [0, 0, 0, 0]),
                        "font_size": round(span.get("size", 12), 1),
                        "font_name": span.get("font", ""),
                        "flags": span.get("flags", 0),
                        "color": span.get("color", 0)
                    }
                    
                    element.update(self._analyze_element_properties(element))
                    elements.append(element)
        
        return {
            "page_number": page_num + 1,
            "elements": elements
        }
    
    def _analyze_element_properties(self, element: Dict) -> Dict:
        flags = element.get("flags", 0)
        
        properties = {
            "is_bold": bool(flags & 2**4),
            "is_italic": bool(flags & 2**1),
            "is_caps": element["text"].isupper(),
            "line_height": self._calculate_line_height(element),
            "x_position": element["bbox"][0],
            "y_position": element["bbox"][1],
            "width": element["bbox"][2] - element["bbox"][0],
            "height": element["bbox"][3] - element["bbox"][1]
        }
        
        text = element["text"]
        properties.update({
            "word_count": len(text.split()),
            "char_count": len(text),
            "has_numbers": bool(re.search(r'\d', text)),
            "starts_with_number": bool(re.match(r'^\d', text)),
            "ends_with_period": text.endswith('.'),
            "is_short": len(text) < 100,
            "is_single_line": '\n' not in text
        })
        
        return properties
    
    def _calculate_line_height(self, element: Dict) -> float:
        bbox = element.get("bbox", [0, 0, 0, 0])
        return bbox[3] - bbox[1] if len(bbox) >= 4 else element.get("font_size", 12)