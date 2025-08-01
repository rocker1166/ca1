import re
import os
import sys
from services.slide_schema import Slide, Deck
from core.logger import get_logger

# Initialize logger early for error reporting
logger = get_logger("layout_intelligence")

# Try to import NLTK with graceful fallback
try:
    import nltk
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    
    # Set NLTK data path if nltk_data exists in project
    project_nltk_data = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nltk_data')
    if os.path.exists(project_nltk_data):
        nltk.data.path.append(project_nltk_data)
        logger.info(f"Using NLTK data from: {project_nltk_data}")
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available. Using simplified text analysis.")

# Simple word tokenization function to avoid NLTK dependencies if needed
def simple_tokenize(text):
    """Simple tokenizer that splits on whitespace and punctuation"""
    # Replace punctuation with spaces
    for char in '.,;:!?()[]{}""\'':
        text = text.replace(char, ' ')
    # Split on whitespace and filter empty strings
    return [token for token in text.split() if token]

class LayoutIntelligence:
    """Analyzes content and determines optimal slide layouts for academic presentations"""
    
    # Class variable to track if NLTK resources have been downloaded
    _nltk_resources_downloaded = False
    
    def __init__(self):
        # Academic subject keywords for context detection
        self.subject_keywords = {
            'mathematics': ['equation', 'theorem', 'proof', 'formula', 'calculus', 'algebra', 'geometry'],
            'computer_science': ['algorithm', 'programming', 'data structure', 'code', 'function', 'class'],
            'biology': ['cell', 'organism', 'species', 'protein', 'dna', 'evolution', 'ecosystem'],
            'chemistry': ['reaction', 'molecule', 'compound', 'element', 'acid', 'base'],
            'physics': ['force', 'energy', 'motion', 'quantum', 'relativity', 'particle'],
            'history': ['century', 'war', 'revolution', 'civilization', 'empire', 'dynasty'],
            'literature': ['novel', 'poetry', 'author', 'character', 'theme', 'symbolism'],
        }
        
        # Initialize NLTK resources only if NLTK is available
        if NLTK_AVAILABLE and not LayoutIntelligence._nltk_resources_downloaded:
            logger.info("Initializing NLTK resources")
            try:
                # Download all required resources
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                # Mark as downloaded to avoid redundant downloads
                LayoutIntelligence._nltk_resources_downloaded = True
                logger.info("NLTK resources initialized successfully")
            except Exception as e:
                logger.error(f"Failed to download NLTK resources: {e}")
                # If download fails, still mark as attempted to avoid repeated errors
                LayoutIntelligence._nltk_resources_downloaded = True  # Mark as true anyway to prevent repeated attempts
    
    def determine_optimal_layouts(self, deck: Deck) -> Deck:
        """Analyze deck and determine the best layout for each slide"""
        # Determine overall subject area
        subject_area = self._detect_subject_area(deck)
        
        # Process each slide
        for i, slide in enumerate(deck.slides):
            # Skip title slide (keep default layout)
            if i == 0 or slide.type == "title":
                continue
                
            # Choose layout based on content analysis
            layout = self._select_layout_for_slide(slide, subject_area, i, len(deck.slides))
            slide.type = layout
            
        return deck
    
    def _detect_subject_area(self, deck: Deck) -> str:
        """Detect the academic subject area of the presentation"""
        # Combine all text content for analysis
        all_text = deck.title + " "
        for slide in deck.slides:
            all_text += slide.title + " "
            
            # Add bullet points
            if slide.content:
                for point in slide.content:
                    if hasattr(point, 'text'):
                        all_text += point.text + " "
                    else:
                        all_text += str(point) + " "
            elif slide.bullets:
                all_text += " ".join(slide.bullets) + " "
        
        # Use our simple tokenization function
        all_text = all_text.lower()
        tokens = simple_tokenize(all_text)
        
        # Load stopwords if NLTK is available, otherwise use a simple list
        if NLTK_AVAILABLE:
            try:
                stop_words = set(stopwords.words('english'))
                logger.debug("Using NLTK stopwords")
            except Exception as e:
                logger.warning(f"Failed to load NLTK stopwords: {e}")
                # Fall back to simple stopwords
                stop_words = self._get_basic_stopwords()
        else:
            # Use simple stopword list
            stop_words = self._get_basic_stopwords()
            
    def _get_basic_stopwords(self):
        """Return a basic set of English stopwords as fallback when NLTK is not available"""
        return {'and', 'the', 'is', 'in', 'it', 'of', 'to', 'for', 'a', 'on', 'with', 
                'this', 'that', 'an', 'are', 'as', 'at', 'be', 'by', 'from', 'has', 
                'have', 'he', 'she', 'they', 'was', 'were', 'will', 'with', 'about',
                'after', 'all', 'also', 'am', 'an', 'any', 'because', 'been', 'before',
                'being', 'between', 'both', 'but', 'can', 'did', 'do', 'does', 'doing',
                'during', 'each', 'few', 'had', 'has', 'have', 'having', 'here', 'how',
                'if', 'into', 'just', 'more', 'most', 'no', 'not', 'now', 'only', 'or',
                'other', 'our', 'out', 'over', 'some', 'such', 'than', 'then', 'there',
                'these', 'they', 'those', 'through', 'under', 'until', 'very', 'what',
                'when', 'where', 'which', 'while', 'who', 'why', 'would', 'you', 'your'}
        
        filtered_tokens = [w for w in tokens if w not in stop_words]
        
        # Count subject keyword matches
        subject_scores = {}
        for subject, keywords in self.subject_keywords.items():
            score = sum(1 for token in filtered_tokens for keyword in keywords if keyword in token)
            subject_scores[subject] = score
        
        # Return highest scoring subject, default to 'general' if none found
        if not subject_scores or max(subject_scores.values()) == 0:
            return 'general'
        return max(subject_scores, key=subject_scores.get)
    
    def _select_layout_for_slide(self, slide: Slide, subject_area: str, position: int, total_slides: int) -> str:
        """Select the optimal layout for a slide based on content and context"""
        # Content characteristics
        has_image = slide.image_url or (slide.images and len(slide.images) > 0)
        has_diagram = slide.diagram_type and slide.diagram_data
        content_length = self._estimate_content_length(slide)
        
        # Check for mathematical content that might need equation layout
        has_equations = self._contains_equations(slide)
        
        # Check for code content that might need code layout
        has_code = self._contains_code(slide)
        
        # Special handling for conclusion slides
        if position >= total_slides - 2 or slide.type == "conclusion":
            return "conclusion"
            
        # Special handling by subject
        if subject_area == 'mathematics' and has_equations:
            return "equation"
            
        if subject_area == 'computer_science' and has_code:
            return "code"
            
        if subject_area == 'biology' and self._contains_classification(slide):
            return "taxonomy"
            
        # General logic based on content
        if has_image and has_diagram:
            if content_length > 200:
                return "compact_mixed"
            return "mixed"
            
        if has_image:
            if content_length < 100:
                return "image_focus"
            return "image"
            
        if has_diagram:
            if slide.diagram_type:
                return "diagram"
            
        # Text-only layouts
        if content_length > 300:
            return "text_dense"
        if content_length < 100:
            return "text_sparse"
            
        return "title_bullets"
    
    def _get_slide_text(self, slide: Slide) -> str:
        """Extract all text content from a slide for analysis"""
        text_content = slide.title + " "
        
        if slide.content:
            for point in slide.content:
                if hasattr(point, 'text'):
                    text_content += point.text + " "
                    if hasattr(point, 'sub_points') and point.sub_points:
                        for sub in point.sub_points:
                            text_content += str(sub) + " "
                else:
                    text_content += str(point) + " "
        elif slide.bullets:
            text_content += " ".join(slide.bullets) + " "
            
        return text_content
    
    def _estimate_content_length(self, slide: Slide) -> int:
        """Estimate the content length to determine layout density"""
        return len(self._get_slide_text(slide))
    
    def _contains_equations(self, slide: Slide) -> bool:
        """Check if slide likely contains mathematical equations"""
        try:
            # Look for LaTeX-like patterns or equation indicators
            equation_patterns = [
                r'\$\$.*?\$\$',          # LaTeX display math
                r'\$.*?\$',              # LaTeX inline math
                r'\\frac{',              # Fractions
                r'\\sum',                # Summation
                r'\\int',                # Integral
                r'=[^=]',                # Equal signs (not part of ==)
                r'matrix|matrices',      # Matrix terms
                r'\\cdot',               # LaTeX dot product
                r'\\prod',               # Product operator
                r'\w+_{[a-zA-Z0-9]+}',   # Subscript notation
                r'\w+\^',                # Superscript notation
                r'det\(.*?\)',           # Determinant
                r'\|.*?\|',              # Absolute value / determinant notation
                r'\\lambda',             # Lambda (eigenvalues)
                r'\\mathbf',             # Bold math
                r'\\mathrm',             # Roman math
                r'\\nabla',              # Nabla operator
                r'\\partial',            # Partial derivative
                r'[a-zA-Z]_\{?[a-zA-Z0-9]+\}?',  # Subscripted variables
                r'\(\s*[a-zA-Z0-9]+\s*[+\-*/]\s*[a-zA-Z0-9]+\s*\)', # Simple expressions in parentheses
                r'[a-zA-Z]_{[a-zA-Z]+}',  # Subscript with letters
            ]
            
            text_to_check = self._get_slide_text(slide)
            
            # Check against regular expression patterns
            for pattern in equation_patterns:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    logger.debug(f"Found equation pattern: {pattern}")
                    return True
            
            # Check for mathematical term clusters
            math_terms = ["vector", "scalar", "matrix", "theorem", "equation", "calculus", 
                        "derivative", "integral", "function", "operator", "polynomial", 
                        "eigenvalue", "eigenvector", "determinant", "linear", "algebra",
                        "multiplication", "addition", "subtraction"]
            
            # Count how many math terms appear in the text
            math_term_count = sum(1 for term in math_terms if term.lower() in text_to_check.lower())
            
            # If at least 2 different math terms are present, consider it mathematical
            if math_term_count >= 2:
                logger.debug(f"Found {math_term_count} math terms")
                return True
        except Exception as e:
            logger.error(f"Error in equation detection: {e}")
            # If there's an error, take a conservative approach
            
        return False
    
    def _contains_code(self, slide: Slide) -> bool:
        """Check if slide likely contains code snippets"""
        try:
            # Look for code indicators
            code_patterns = [
                r'```',          # Markdown code blocks
                r'def\s+\w+\(',   # Python function definitions
                r'function\s+\w+\(', # JavaScript function
                r'class\s+\w+[:{]', # Class definitions
                r'import\s+\w+',  # Import statements
                r'for\s*\(',      # For loops
                r'if\s*\(',       # If statements
                r'while\s*\(',    # While loops
                r'switch\s*\(',   # Switch statements
                r'return\s+\w+',  # Return statements
                r'<[a-z]+>.*?</[a-z]+>', # HTML tags
                r'[a-z]+\.[a-z]+\(.*?\)', # Method calls
                r'var\s+\w+\s*=', # Variable declarations
                r'let\s+\w+\s*=', # JS let declarations
                r'const\s+\w+\s*=', # JS const declarations
            ]
            
            text_to_check = self._get_slide_text(slide)
            
            for pattern in code_patterns:
                if re.search(pattern, text_to_check):
                    logger.debug(f"Found code pattern: {pattern}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error in code detection: {e}")
            
        return False
    
    def _contains_classification(self, slide: Slide) -> bool:
        """Check if slide contains classification/taxonomy content"""
        try:
            # Look for classification indicators
            taxonomy_patterns = [
                r'kingdom',
                r'phylum',
                r'class',
                r'order',
                r'family',
                r'genus',
                r'species',
                r'taxonomy',
                r'classification',
                r'categorization',
                r'hierarchy',
                r'taxonomic',
                r'biological',
                r'phylogeny',
                r'phylogenetic',
                r'cladogram',
                r'evolutionary tree'
            ]
            
            text_to_check = self._get_slide_text(slide).lower()
            
            for pattern in taxonomy_patterns:
                if pattern in text_to_check:
                    logger.debug(f"Found taxonomy pattern: {pattern}")
                    return True
        except Exception as e:
            logger.error(f"Error in classification detection: {e}")
            
        return False
