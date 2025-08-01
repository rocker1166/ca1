import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.slide_schema import Slide, Deck
from services.layout_intelligence import LayoutIntelligence
from services.ppt_builder import PPTBuilder
from services.theme_manager import ThemeManager
from core.logger import get_logger

logger = get_logger("test_layout_intelligence")

# Ensure NLTK downloads are available
try:
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
except Exception as e:
    logger.error(f"Error downloading NLTK resources: {str(e)}")

def test_layout_intelligence():
    """Test the layout intelligence feature with a math presentation"""
    
    try:
        # Create a test deck with math content
        deck = Deck(
            title="Introduction to Linear Algebra",
            slides=[
                # Title slide
                Slide(
                    title="Introduction to Linear Algebra",
                    subtitle="Understanding Vector Spaces and Linear Transformations",
                    type="title"
                ),
                # Vector slide with equation
                Slide(
                    title="Vector Spaces",
                    bullets=[
                        "A vector space V is a collection of objects called vectors",
                        "Vectors can be added together and multiplied by scalars",
                        "For all u, v, w ∈ V and scalars c, d: $u + v = v + u$",
                        "$c(u + v) = cu + cv$",
                        "$(c + d)v = cv + dv$"
                    ]
                ),
                # Matrix slide
                Slide(
                    title="Matrix Operations",
                    bullets=[
                        "Matrix addition: $(A + B)_{ij} = A_{ij} + B_{ij}$",
                        "Scalar multiplication: $(cA)_{ij} = c \\cdot A_{ij}$",
                        "Matrix multiplication: $(AB)_{ij} = \\sum_{k} A_{ik} B_{kj}$",
                        "For an n×n matrix A, the determinant is denoted as det(A) or |A|"
                    ]
                ),
                # Eigenvalues slide
                Slide(
                    title="Eigenvalues and Eigenvectors",
                    bullets=[
                        "An eigenvector of a square matrix A is a non-zero vector v such that:",
                        "$Av = \\lambda v$ for some scalar λ",
                        "λ is called the eigenvalue corresponding to v",
                        "To find eigenvalues, solve: $det(A - \\lambda I) = 0$",
                        "This is called the characteristic equation"
                    ]
                ),
                # Conclusion slide
                Slide(
                    title="Summary",
                    bullets=[
                        "Linear algebra provides tools for working with linear equations",
                        "Key concepts: vectors, matrices, determinants, eigenvalues",
                        "Applications include computer graphics, machine learning, and physics",
                        "Next steps: singular value decomposition, principal component analysis"
                    ],
                    type="conclusion"
                )
            ]
        )
        
        # Apply layout intelligence
        layout_engine = LayoutIntelligence()
        processed_deck = layout_engine.determine_optimal_layouts(deck)
        
        # Print results
        print("\nLayout Intelligence Results:")
        print("----------------------------")
        print(f"Detected subject area: {layout_engine._detect_subject_area(deck)}")
        
        for i, slide in enumerate(processed_deck.slides):
            print(f"\nSlide {i+1}: {slide.title}")
            print(f"  - Original type: {deck.slides[i].type}")
            print(f"  - Selected layout: {slide.type}")
        
        # Test with PPTBuilder
        theme = ThemeManager.suggest_theme_for_subject(layout_engine._detect_subject_area(deck))
        print(f"\nSuggested theme for this subject: {theme}")
        
        builder = PPTBuilder(theme=theme)
        output_path = builder.build(processed_deck, use_template=False)
        print(f"\nPresentation built successfully at: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error in test_layout_intelligence: {str(e)}")
        print(f"\nERROR: {str(e)}")
        print("\nTIP: Run the NLTK setup script first: python setup_nltk.py")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    output_file = test_layout_intelligence()
    print(f"\nOpen the output file to see the results: {output_file}")
