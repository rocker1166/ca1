import os
import uuid
import requests
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from services.slide_schema import Deck, Slide, BulletPoint
from services.layout_intelligence import LayoutIntelligence
from services.theme_manager import ThemeManager
from core.logger import get_logger
from io import BytesIO
from PIL import Image

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'template.pptx')
logger = get_logger("ppt_builder")

# --- Diagram service stub ---
def generate_diagram_image(description: str) -> BytesIO:
    # TODO: Implement with Mermaid, Graphviz, or external API
    # For now, return a blank image
    from PIL import Image
    img = Image.new('RGB', (400, 200), color = (255, 255, 255))
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# --- Plugin-style layout system ---
class BaseLayout:
    def render(self, slide_data: Slide, pptx_slide):
        raise NotImplementedError

class TitleBulletsLayout(BaseLayout):
    def render(self, slide_data: Slide, pptx_slide):
        title_shape = pptx_slide.shapes.title
        title_shape.text = slide_data.title
        title_shape.text_frame.paragraphs[0].font.size = Pt(32)
        title_shape.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
        if slide_data.bullets:
            content_shape = None
            for shape in pptx_slide.shapes:
                if shape.has_text_frame and shape != title_shape:
                    content_shape = shape
                    break
            if content_shape:
                tf = content_shape.text_frame
                tf.clear()
                for bullet in slide_data.bullets:
                    p = tf.add_paragraph()
                    p.text = bullet
                    p.font.size = Pt(20)
                    p.level = 0
                    p.alignment = PP_ALIGN.LEFT
        if slide_data.notes:
            pptx_slide.notes_slide.notes_text_frame.text = slide_data.notes
        # Images handled by PPTBuilder

class ImageLayout(BaseLayout):
    def render(self, slide_data: Slide, pptx_slide):
        title_shape = pptx_slide.shapes.title
        title_shape.text = slide_data.title
        title_shape.text_frame.paragraphs[0].font.size = Pt(32)
        title_shape.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
        # Insert first image (if any)
        if slide_data.images:
            img_url = slide_data.images[0]
            try:
                img_bytes = requests.get(img_url, timeout=5).content
                image_stream = BytesIO(img_bytes)
                # Place image in center of slide
                pptx_slide.shapes.add_picture(image_stream, Inches(2), Inches(2), width=Inches(4))
            except Exception as e:
                logger.error(f"Failed to embed image: {img_url} - {e}")
        if slide_data.notes:
            pptx_slide.notes_slide.notes_text_frame.text = slide_data.notes

class DiagramLayout(BaseLayout):
    def render(self, slide_data: Slide, pptx_slide):
        title_shape = pptx_slide.shapes.title
        title_shape.text = slide_data.title
        title_shape.text_frame.paragraphs[0].font.size = Pt(32)
        title_shape.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
        # Insert first diagram (if any)
        if slide_data.diagrams:
            desc = slide_data.diagrams[0]
            try:
                diagram_img = generate_diagram_image(desc)
                pptx_slide.shapes.add_picture(diagram_img, Inches(2), Inches(2), width=Inches(4))
            except Exception as e:
                logger.error(f"Failed to embed diagram: {desc} - {e}")
        if slide_data.notes:
            pptx_slide.notes_slide.notes_text_frame.text = slide_data.notes

# Import academic layouts
from services.academic_layouts import (
    EquationLayout, CodeLayout, TaxonomyLayout,
    TextDenseLayout, TextSparseLayout, ConclusionLayout
)

# Layout registry
LAYOUT_REGISTRY = {
    # Basic layouts
    "title_bullets": TitleBulletsLayout(),
    "image": ImageLayout(),
    "diagram": DiagramLayout(),
    
    # Academic layouts
    "equation": EquationLayout(),
    "code": CodeLayout(),
    "taxonomy": TaxonomyLayout(),
    "text_dense": TextDenseLayout(),
    "text_sparse": TextSparseLayout(),
    "conclusion": ConclusionLayout()
}

def get_layout(slide_data: Slide):
    if slide_data.type and slide_data.type in LAYOUT_REGISTRY:
        return LAYOUT_REGISTRY[slide_data.type]
    if slide_data.images:
        return LAYOUT_REGISTRY["image"]
    if slide_data.diagrams:
        return LAYOUT_REGISTRY["diagram"]
    return LAYOUT_REGISTRY["title_bullets"]

class PPTBuilder:
    def __init__(self, template_path: str = TEMPLATE_PATH, theme: str = "professional"):
        self.template_path = template_path
        
        # Get theme colors from ThemeManager
        theme_data = ThemeManager.get_theme_colors(theme)
        self.colors = {
            'primary': theme_data['primary'],
            'secondary': theme_data['secondary'],
            'accent': theme_data['accent'],
            'background': theme_data['background'],
            'text': theme_data['text'],
            'light_text': RGBColor(127, 140, 141)  # Light gray (keeping for backward compatibility)
        }
        self.fonts = {
            'title': theme_data['title_font'],
            'body': theme_data['body_font']
        }

    def build(self, deck: Deck, use_template: bool = True, job_id: str = None) -> BytesIO:
        try:
            logger.info(f"Building PPTX. use_template={use_template}, slides={len(deck.slides)}")
            
            # Emit streaming event if job_id provided
            if job_id:
                from services.streaming_service import streaming_service
                streaming_service.emit_event(job_id, "layout_processing", {
                    "message": "Applying intelligent layout selection...",
                    "step": "layout_analysis"
                })
            
            # Apply intelligent layout selection
            layout_engine = LayoutIntelligence()
            deck = layout_engine.determine_optimal_layouts(deck)
            logger.info(f"Applied intelligent layout selection to deck")
            
            # Pre-process slides to handle content overflow
            processed_deck = self._preprocess_slides_for_overflow(deck)
            logger.info(f"Pre-processed slides to handle overflow. Original slides: {len(deck.slides)}, Processed slides: {len(processed_deck.slides)}")
            
            if job_id:
                streaming_service.emit_event(job_id, "slides_processing", {
                    "message": f"Processing {len(processed_deck.slides)} slides...",
                    "total_slides": len(processed_deck.slides),
                    "step": "slide_processing"
                })
            
            if use_template:
                if not os.path.exists(self.template_path):
                    raise FileNotFoundError(f"PPTX template not found: {self.template_path}")
                prs = Presentation(self.template_path)
            else:
                prs = Presentation()
            
            # Clear existing slides if using template
            slide_count = len(prs.slides)
            for i in range(slide_count - 1, -1, -1):
                self._delete_slide(prs, i)
            
            for i, slide_data in enumerate(processed_deck.slides):
                logger.info(f"Processing slide {i+1}: {slide_data.title} (type: {slide_data.type})")
                
                # Emit progress for each slide
                if job_id:
                    streaming_service.emit_event(job_id, "slide_progress", {
                        "message": f"Creating slide {i+1}: {slide_data.title}",
                        "slide_number": i + 1,
                        "slide_title": slide_data.title,
                        "slide_type": slide_data.type,
                        "progress": round((i + 1) / len(processed_deck.slides) * 100, 1),
                        "step": "slide_creation"
                    })
                
                self._create_enhanced_slide(prs, slide_data)
            
            if job_id:
                streaming_service.emit_event(job_id, "finalizing", {
                    "message": "Finalizing presentation...",
                    "step": "finalization"
                })
            
            # Save to BytesIO instead of local file
            pptx_stream = BytesIO()
            prs.save(pptx_stream)
            pptx_stream.seek(0)
            logger.info(f"PPTX generated in memory")
            return pptx_stream
        except Exception as e:
            logger.error(f"Failed to build PPTX: {e}")
            raise
            
    def _preprocess_slides_for_overflow(self, deck: Deck) -> Deck:
        """Pre-process slides to handle content overflow by splitting extremely content-heavy slides"""
        from copy import deepcopy
        
        processed_deck = deepcopy(deck)
        new_slides = []
        
        # Analyze each slide for potential overflow
        for i, slide in enumerate(processed_deck.slides):
            # Skip title slide
            if i == 0 or slide.type == "title":
                new_slides.append(slide)
                continue
                
            # Check if slide has excessive content
            needs_splitting = False
            content_length = 0
            bullet_count = 0
            
            if slide.content:
                bullet_count = len(slide.content) if isinstance(slide.content, list) else 0
                for point in slide.content:
                    if hasattr(point, 'text'):
                        if hasattr(point.text, '__len__'):
                            content_length += len(point.text)
                        else:
                            content_length += len(str(point.text))
                        if hasattr(point, 'sub_points') and point.sub_points and isinstance(point.sub_points, list):
                            bullet_count += len(point.sub_points)
                            for sub in point.sub_points:
                                content_length += len(str(sub))
                    else:
                        content_length += len(str(point))
            elif slide.bullets:
                bullet_count = len(slide.bullets) if isinstance(slide.bullets, list) else 0
                if isinstance(slide.bullets, list):
                    content_length = sum(len(str(bullet)) for bullet in slide.bullets)
                else:
                    content_length = 0
            
            # Determine if slide needs splitting
            needs_splitting = (content_length > 800 or bullet_count > 9)
            
            if needs_splitting and (slide.content or slide.bullets):
                logger.info(f"Splitting content-heavy slide: {slide.title} ({content_length} chars, {bullet_count} bullets)")
                
                # Create split slides
                if slide.content and isinstance(slide.content, list):
                    # Split complex content
                    midpoint = len(slide.content) // 2
                    
                    # First part
                    first_slide = deepcopy(slide)
                    first_slide.content = slide.content[:midpoint]
                    first_slide.title = slide.title
                    new_slides.append(first_slide)
                    
                    # Second part
                    second_slide = deepcopy(slide)
                    second_slide.content = slide.content[midpoint:]
                    second_slide.title = f"{slide.title} (continued)"
                    new_slides.append(second_slide)
                    
                elif slide.bullets and isinstance(slide.bullets, list):
                    # Split simple bullets
                    midpoint = len(slide.bullets) // 2
                    
                    # First part
                    first_slide = deepcopy(slide)
                    first_slide.bullets = slide.bullets[:midpoint]
                    first_slide.title = slide.title
                    new_slides.append(first_slide)
                    
                    # Second part
                    second_slide = deepcopy(slide)
                    second_slide.bullets = slide.bullets[midpoint:]
                    second_slide.title = f"{slide.title} (continued)"
                    new_slides.append(second_slide)
            else:
                # No need to split
                new_slides.append(slide)
        
        # Update deck with new slide sequence
        processed_deck.slides = new_slides
        return processed_deck
    
    def _delete_slide(self, prs, slide_index):
        """Delete slide by index"""
        xml_slides = prs.slides._sldIdLst
        slides = list(xml_slides)
        xml_slides.remove(slides[slide_index])
    
    def _create_enhanced_slide(self, prs, slide_data: Slide):
        """Create a slide with enhanced formatting"""
        slide_type = slide_data.type or 'content'
        
        if slide_type == 'title':
            self._create_title_slide(prs, slide_data)
        elif slide_type == 'conclusion':
            self._create_conclusion_slide(prs, slide_data)
        else:
            self._create_content_slide(prs, slide_data)
    
    def _create_title_slide(self, prs, slide_data: Slide):
        """Create title slide with enhanced styling"""
        slide_layout = prs.slide_layouts[0]  # Title slide layout
        slide = prs.slides.add_slide(slide_layout)
        
        # Title formatting
        title = slide.shapes.title
        title.text = slide_data.title
        title_paragraph = title.text_frame.paragraphs[0]
        title_paragraph.font.size = Pt(44)
        title_paragraph.font.bold = True
        title_paragraph.font.color.rgb = self.colors['primary']
        title_paragraph.alignment = PP_ALIGN.CENTER
        
        # Subtitle formatting
        if len(slide.placeholders) > 1:
            subtitle = slide.placeholders[1]
            subtitle.text = slide_data.subtitle or slide_data.notes or ""
            if subtitle.text:
                subtitle_paragraph = subtitle.text_frame.paragraphs[0]
                subtitle_paragraph.font.size = Pt(24)
                subtitle_paragraph.font.color.rgb = self.colors['secondary']
                subtitle_paragraph.alignment = PP_ALIGN.CENTER
    
    def _create_content_slide(self, prs, slide_data: Slide):
        """Create content slide with bullet points and formatting"""
        slide_layout = prs.slide_layouts[1]  # Title and content layout
        slide = prs.slides.add_slide(slide_layout)
        
        # Title formatting
        title = slide.shapes.title
        title.text = slide_data.title
        self._format_title(title)
        
        # Determine layout based on content
        has_image = slide_data.image_url or (slide_data.images and len(slide_data.images) > 0)
        has_diagram = slide_data.diagram_type and slide_data.diagram_data
        
        if has_image and has_diagram:
            # Both image and diagram - use compact layout
            self._create_mixed_content_layout(slide, slide_data)
        elif has_image:
            # Image only - use side-by-side layout
            self._create_image_content_layout(slide, slide_data)
        elif has_diagram:
            # Diagram only - use full width for diagram
            self._create_diagram_content_layout(slide, slide_data)
        else:
            # Text only - use full content area
            self._create_text_only_layout(slide, slide_data)
        
        # Add notes
        if slide_data.notes:
            slide.notes_slide.notes_text_frame.text = slide_data.notes
    
    def _create_text_only_layout(self, slide, slide_data: Slide):
        """Create layout with text content only and overflow protection"""
        # Use full content area for text
        content_placeholder = slide.placeholders[1] if len(slide.placeholders) > 1 else None
        
        if content_placeholder:
            # Adjust content area to use full width with margins to prevent edge overflow
            content_placeholder.left = Inches(0.5)
            content_placeholder.width = Inches(9)
            content_placeholder.top = Inches(1.5)
            content_placeholder.height = Inches(5)
            
            # Apply overflow protection based on content density
            is_dense = self._is_content_dense(slide_data)
            
            if is_dense:
                # For very dense content, create a text box with more control over overflow
                self._create_overflow_safe_textbox(slide, slide_data)
            else:
                # Normal content handling with auto-fit protection
                if slide_data.content:
                    self._add_enhanced_bullet_points(content_placeholder, slide_data.content)
                else:
                    self._add_simple_bullet_points(content_placeholder, slide_data.bullets)
    
    def _create_image_content_layout(self, slide, slide_data: Slide):
        """Create layout with image and text side by side with overflow protection"""
        # Adjust content area for text (left side)
        content_placeholder = slide.placeholders[1] if len(slide.placeholders) > 1 else None
        
        if content_placeholder:
            # Resize content area to left side with safe margins
            content_placeholder.left = Inches(0.5)
            content_placeholder.width = Inches(4.3)  # Slightly narrower to ensure margin
            content_placeholder.top = Inches(1.5)
            content_placeholder.height = Inches(5)
            
            # Check if content is very dense
            is_dense = self._is_content_dense(slide_data)
            
            if is_dense:
                # Create a custom text box for better overflow control
                txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4.3), Inches(5))
                tf = txBox.text_frame
                tf.word_wrap = True
                tf.auto_size = 1  # Auto-fit text to shape
                
                # Use more aggressive content truncation
                if slide_data.content:
                    max_points = min(5, len(slide_data.content))
                    for i, point in enumerate(slide_data.content[:max_points]):
                        if i == 0:
                            p = tf.paragraphs[0]
                        else:
                            p = tf.add_paragraph()
                            
                        # Extract text with stricter length limits
                        if hasattr(point, 'text'):
                            # Add safety check for point.text being string-like
                            if hasattr(point.text, '__len__'):
                                text = point.text[:120] + "..." if len(point.text) > 120 else point.text
                            else:
                                text = str(point.text)
                        else:
                            text = str(point)[:120] + "..." if len(str(point)) > 120 else str(point)
                        
                        p.text = text
                        p.font.size = Pt(14)  # Smaller font for side-by-side with image
                else:
                    # Handle simple bullets with truncation
                    max_bullets = min(6, len(slide_data.bullets or []))
                    bullets = slide_data.bullets or []
                    for i, bullet in enumerate(bullets[:max_bullets]):
                        if i == 0:
                            p = tf.paragraphs[0]
                        else:
                            p = tf.add_paragraph()
                        
                        bullet_text = str(bullet)[:120] + "..." if len(str(bullet)) > 120 else str(bullet)
                        p.text = bullet_text
                        p.font.size = Pt(14)
            else:
                # Normal content handling with existing methods
                if slide_data.content:
                    self._add_enhanced_bullet_points(content_placeholder, slide_data.content)
                else:
                    self._add_simple_bullet_points(content_placeholder, slide_data.bullets)
        
        # Add image to right side
        image_url = slide_data.image_url or (slide_data.images[0] if slide_data.images else None)
        if image_url:
            self._add_image_to_slide(slide, image_url, 'right')
    
    def _create_diagram_content_layout(self, slide, slide_data: Slide):
        """Create layout with diagram and minimal text"""
        # Small content area for key points
        content_placeholder = slide.placeholders[1] if len(slide.placeholders) > 1 else None
        
        if content_placeholder:
            # Compact content area at top
            content_placeholder.left = Inches(0.5)
            content_placeholder.width = Inches(9)
            content_placeholder.top = Inches(1.5)
            content_placeholder.height = Inches(2)
            
            # Show only first 3 points to save space
            content = slide_data.content[:3] if slide_data.content else slide_data.bullets[:3]
            if slide_data.content:
                self._add_enhanced_bullet_points(content_placeholder, content)
            else:
                self._add_simple_bullet_points(content_placeholder, content)
        
        # Add diagram below text
        self._add_diagram_to_slide(slide, slide_data)
    
    def _create_mixed_content_layout(self, slide, slide_data: Slide):
        """Create compact layout with text, image, and diagram"""
        # Very compact text area
        content_placeholder = slide.placeholders[1] if len(slide.placeholders) > 1 else None
        
        if content_placeholder:
            # Compact content area at top left
            content_placeholder.left = Inches(0.5)
            content_placeholder.width = Inches(3.5)
            content_placeholder.top = Inches(1.5)
            content_placeholder.height = Inches(2)
            
            # Show only first 2 points
            content = slide_data.content[:2] if slide_data.content else slide_data.bullets[:2]
            if slide_data.content:
                self._add_enhanced_bullet_points(content_placeholder, content)
            else:
                self._add_simple_bullet_points(content_placeholder, content)
        
        # Add small image to top right
        image_url = slide_data.image_url or (slide_data.images[0] if slide_data.images else None)
        if image_url:
            self._add_compact_image_to_slide(slide, image_url)
        
        # Add compact diagram below
        self._add_compact_diagram_to_slide(slide, slide_data)
    
    def _create_conclusion_slide(self, prs, slide_data: Slide):
        """Create conclusion slide"""
        self._create_content_slide(prs, slide_data)  # Same as content slide
    
    def _format_title(self, title_shape):
        """Format slide title with auto-fit to ensure text stays within bounds"""
        # Enable auto-fit to prevent overflow
        text_frame = title_shape.text_frame
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        
        # Apply formatting to paragraph
        title_paragraph = text_frame.paragraphs[0]
        title_paragraph.font.size = Pt(36)  # Initial size, will auto-decrease if needed
        title_paragraph.font.bold = True
        title_paragraph.font.color.rgb = self.colors['primary']
    
    def _add_enhanced_bullet_points(self, content_shape, bullet_points):
        """Add formatted bullet points with enhanced structure and text overflow prevention"""
        text_frame = content_shape.text_frame
        text_frame.clear()
        
        # Configure text frame to prevent overflow
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        
        # Calculate how many points we can fit safely
        max_points = min(7, len(bullet_points))  # Limit total points if excessive
        
        for i, point in enumerate(bullet_points[:max_points]):
            if isinstance(point, dict):
                # Handle BulletPoint structure
                main_text = point.get('text', str(point))
                sub_points = point.get('sub_points', [])
                level = point.get('level', 0)
            elif hasattr(point, 'text'):  # BulletPoint object
                main_text = point.text
                sub_points = point.sub_points or []
                level = point.level
            else:
                # Handle simple string
                main_text = str(point)
                sub_points = []
                level = 0
            
            # Ensure text doesn't overflow
            if len(main_text) > 200:  # Truncate extremely long bullet points
                main_text = main_text[:197] + "..."
                
            # Add main bullet point
            if i == 0:
                p = text_frame.paragraphs[0]
            else:
                p = text_frame.add_paragraph()
            
            p.text = main_text
            p.level = level
            self._format_bullet_point(p, level)
            
            # Limit sub-points if there are too many
            max_sub_points = min(3, len(sub_points))  # Limit sub-points per point
            
            # Add sub-points
            for j, sub_point in enumerate(sub_points[:max_sub_points]):
                sub_text = str(sub_point)
                if len(sub_text) > 150:  # Truncate long sub-points
                    sub_text = sub_text[:147] + "..."
                
                sub_p = text_frame.add_paragraph()
                sub_p.text = sub_text
                sub_p.level = level + 1
                self._format_bullet_point(sub_p, level + 1)
                
        # Add ellipsis if we truncated the list
        if len(bullet_points) > max_points:
            p = text_frame.add_paragraph()
            p.text = "..."
            p.level = 0
            self._format_bullet_point(p, 0)
    
    def _add_simple_bullet_points(self, content_shape, bullets):
        """Add simple bullet points with auto-fit to prevent text overflow"""
        text_frame = content_shape.text_frame
        text_frame.clear()
        
        # Configure text frame to prevent overflow
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        
        for i, bullet in enumerate(bullets):
            if i == 0:
                p = text_frame.paragraphs[0]
            else:
                p = text_frame.add_paragraph()
            
            # Ensure text doesn't overflow by setting max length if extremely long
            bullet_text = str(bullet)
            if len(bullet_text) > 300:  # Extremely long text might still cause issues
                bullet_text = bullet_text[:297] + "..."
                
            p.text = bullet_text
            p.level = 0
            self._format_bullet_point(p, 0)
    
    def _format_bullet_point(self, paragraph, level=0):
        """Format individual bullet point with adaptive sizing"""
        # Base font sizes for different levels
        base_font_sizes = [20, 18, 16]  # Different sizes for different levels
        colors = [self.colors['text'], self.colors['light_text'], self.colors['light_text']]
        
        # Adjust font size based on text length for better fitting
        text_length = len(paragraph.text)
        
        # Calculate adaptive font size (reduce for longer text)
        level_idx = min(level, len(base_font_sizes) - 1)
        base_size = base_font_sizes[level_idx]
        
        # Adaptive sizing based on content length
        if text_length > 150:
            font_size = max(base_size - 4, 12)  # Minimum 12pt
        elif text_length > 100:
            font_size = max(base_size - 2, 14)  # Minimum 14pt
        else:
            font_size = base_size
            
        # Enable word wrap for the paragraph
        paragraph.alignment = PP_ALIGN.LEFT
        
        paragraph.font.size = Pt(font_size)  # Use our calculated adaptive font size
        paragraph.font.color.rgb = colors[min(level, 2)]
        
        # Bold for main points
        if level == 0:
            paragraph.font.bold = True
    
    def _is_content_dense(self, slide_data: Slide) -> bool:
        """Determine if slide content is very dense and needs special handling"""
        # Calculate total text length
        total_length = len(slide_data.title)
        
        if slide_data.content:
            for point in slide_data.content:
                if hasattr(point, 'text'):
                    if hasattr(point.text, '__len__'):
                        total_length += len(point.text)
                    else:
                        total_length += len(str(point.text))
                    if hasattr(point, 'sub_points') and point.sub_points:
                        for sub in point.sub_points:
                            total_length += len(str(sub))
                else:
                    total_length += len(str(point))
        elif slide_data.bullets:
            total_length += sum(len(bullet) for bullet in slide_data.bullets)
        
        # Dense threshold - more than 500 chars is considered very dense
        return total_length > 500 or (slide_data.content and len(slide_data.content) > 8)
    
    def _create_overflow_safe_textbox(self, slide, slide_data: Slide):
        """Create a custom text box that ensures content never overflows slide boundaries"""
        from pptx.util import Pt, Inches
        
        # Create a custom text box with strict boundaries
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(9)
        height = Inches(5)
        
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_top = 0
        tf.margin_bottom = 0
        
        logger.info(f"Creating overflow-safe text box for dense content")
        
        # Add content with tight formatting
        if slide_data.content:
            # Use more aggressive truncation for dense slides
            max_points = min(6, len(slide_data.content))
            for i, point in enumerate(slide_data.content[:max_points]):
                if i == 0:
                    p = tf.paragraphs[0]
                else:
                    p = tf.add_paragraph()
                
                # Extract point text with strict length limits
                if hasattr(point, 'text'):
                    if hasattr(point.text, '__len__'):
                        point_text = point.text[:150] + "..." if len(point.text) > 150 else point.text
                    else:
                        point_text = str(point.text)
                else:
                    point_text = str(point)[:150] + "..." if len(str(point)) > 150 else str(point)
                    
                p.text = point_text
                p.level = 0
                
                # Apply compact formatting
                font = p.font
                font.size = Pt(16)  # Smaller font for dense slides
                font.bold = True
                
                # Handle sub-points more aggressively for dense slides
                if hasattr(point, 'sub_points') and point.sub_points:
                    # Limit to 2 sub-points for dense slides
                    max_sub = min(2, len(point.sub_points))
                    for j, sub in enumerate(point.sub_points[:max_sub]):
                        sub_p = tf.add_paragraph()
                        sub_text = str(sub)[:100] + "..." if len(str(sub)) > 100 else str(sub)
                        sub_p.text = sub_text
                        sub_p.level = 1
                        
                        # Apply compact formatting for sub-points
                        sub_font = sub_p.font
                        sub_font.size = Pt(14)
                        sub_font.bold = False
            
            # Add ellipsis if content was truncated
            if len(slide_data.content) > max_points:
                p = tf.add_paragraph()
                p.text = "(Additional content has been condensed)"
                p.font.italic = True
                p.font.size = Pt(12)
        
        elif slide_data.bullets:
            # Process simple bullets with strict truncation
            max_bullets = min(8, len(slide_data.bullets))
            for i, bullet in enumerate(slide_data.bullets[:max_bullets]):
                if i == 0:
                    p = tf.paragraphs[0]
                else:
                    p = tf.add_paragraph()
                
                # Truncate long bullets
                bullet_text = str(bullet)[:150] + "..." if len(str(bullet)) > 150 else str(bullet)
                p.text = bullet_text
                
                # Apply compact formatting
                font = p.font
                font.size = Pt(16)
            
            # Add ellipsis if bullets were truncated
            if len(slide_data.bullets) > max_bullets:
                p = tf.add_paragraph()
                p.text = "(Additional bullets have been condensed)"
                p.font.italic = True
                p.font.size = Pt(12)
    
    def _add_image_to_slide(self, slide, image_url, position='right'):
        """Add image to slide with proper positioning"""
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image_stream = BytesIO(response.content)
            
            # Position calculations - avoid overlap with text
            if position == 'right':
                left = Inches(5.5)  # Move further right
                top = Inches(1.8)   # Below title
                width = Inches(3.8)
                height = Inches(4.5)
            elif position == 'center':
                left = Inches(2.5)
                top = Inches(4)     # Below text content
                width = Inches(5)
                height = Inches(3)
            else:  # left
                left = Inches(0.3)
                top = Inches(1.8)
                width = Inches(3.8)
                height = Inches(4.5)
            
            # Add image
            slide.shapes.add_picture(image_stream, left, top, width, height)
            
        except Exception as e:
            logger.error(f"Failed to add image: {e}")
            # Add placeholder text instead
            self._add_image_placeholder(slide, position)
    
    def _add_compact_image_to_slide(self, slide, image_url):
        """Add smaller image for mixed layouts"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image_stream = BytesIO(response.content)
            
            # Compact image position
            left = Inches(4.5)
            top = Inches(1.8)
            width = Inches(2.8)
            height = Inches(2)
            
            slide.shapes.add_picture(image_stream, left, top, width, height)
            
        except Exception as e:
            logger.error(f"Failed to add compact image: {e}")
            self._add_compact_image_placeholder(slide)
    
    def _add_compact_image_placeholder(self, slide):
        """Add compact image placeholder"""
        left, top, width, height = Inches(4.5), Inches(1.8), Inches(2.8), Inches(2)
        
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, left, top, width, height
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(240, 240, 240)
        shape.line.color.rgb = RGBColor(200, 200, 200)
        
        text_frame = shape.text_frame
        text_frame.text = "Image"
        paragraph = text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.font.size = Pt(12)
        paragraph.font.color.rgb = RGBColor(100, 100, 100)
        text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    
    def _add_image_placeholder(self, slide, position='right'):
        """Add image placeholder when image fails to load"""
        if position == 'right':
            left, top, width, height = Inches(5.5), Inches(1.8), Inches(3.8), Inches(4.5)
        elif position == 'center':
            left, top, width, height = Inches(2.5), Inches(4), Inches(5), Inches(3)
        else:  # left
            left, top, width, height = Inches(0.3), Inches(1.8), Inches(3.8), Inches(4.5)
        
        # Add rectangle shape as placeholder
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, left, top, width, height
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(240, 240, 240)
        shape.line.color.rgb = RGBColor(200, 200, 200)
        
        # Add "Image" text
        text_frame = shape.text_frame
        text_frame.text = "Image Placeholder"
        paragraph = text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.font.size = Pt(14)
        paragraph.font.color.rgb = RGBColor(100, 100, 100)
        text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    
    def _add_diagram_to_slide(self, slide, slide_data: Slide):
        """Add diagram to slide"""
        diagram_type = slide_data.diagram_type
        diagram_data = slide_data.diagram_data or []
        
        if diagram_type == 'process':
            self._create_process_diagram(slide, diagram_data)
        elif diagram_type == 'comparison':
            self._create_comparison_diagram(slide, diagram_data)
        elif diagram_type == 'hierarchy':
            self._create_hierarchy_diagram(slide, diagram_data)
    
    def _create_process_diagram(self, slide, steps):
        """Create process flow diagram with proper sizing"""
        if not steps:
            return
        
        # Calculate diagram dimensions based on slide size (10" x 7.5")
        max_steps_per_row = min(len(steps), 4)  # Max 4 steps per row
        step_width = Inches(1.8)
        step_height = Inches(0.7)
        arrow_width = Inches(0.4)
        
        # Calculate total width and ensure it fits
        total_width = max_steps_per_row * step_width + (max_steps_per_row - 1) * arrow_width
        if total_width > Inches(9):  # Slide content area is ~9 inches
            # Reduce step width if too wide
            step_width = Inches(1.4)
            arrow_width = Inches(0.3)
            total_width = max_steps_per_row * step_width + (max_steps_per_row - 1) * arrow_width
        
        # Center the diagram horizontally
        start_left = (Inches(10) - total_width) / 2
        top = Inches(4)  # Position below text content
        
        for i, step in enumerate(steps[:max_steps_per_row]):  # Limit to max steps
            # Calculate position
            left = start_left + i * (step_width + arrow_width)
            
            # Add step box
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, left, top, step_width, step_height
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.colors['secondary']
            shape.line.color.rgb = self.colors['primary']
            shape.line.width = Pt(1)
            
            # Add step text
            text_frame = shape.text_frame
            text_frame.margin_left = Pt(6)
            text_frame.margin_right = Pt(6)
            text_frame.margin_top = Pt(6)
            text_frame.margin_bottom = Pt(6)
            
            step_text = step.get('step', str(step)) if isinstance(step, dict) else str(step)
            # Truncate long text
            if len(step_text) > 15:
                step_text = step_text[:12] + "..."
            
            text_frame.text = step_text
            paragraph = text_frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.CENTER
            paragraph.font.size = Pt(10)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.font.bold = True
            text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            
            # Add arrow (except for last step)
            if i < min(len(steps), max_steps_per_row) - 1:
                arrow_left = left + step_width
                arrow_shape = slide.shapes.add_shape(
                    MSO_SHAPE.RIGHT_ARROW, arrow_left, top + Inches(0.2), 
                    arrow_width, Inches(0.3)
                )
                arrow_shape.fill.solid()
                arrow_shape.fill.fore_color.rgb = self.colors['accent']
                arrow_shape.line.color.rgb = self.colors['accent']
        
        # Add "..." if there are more steps
        if len(steps) > max_steps_per_row:
            dots_left = start_left + max_steps_per_row * (step_width + arrow_width)
            dots_shape = slide.shapes.add_textbox(
                dots_left, top + Inches(0.25), Inches(0.5), Inches(0.2)
            )
            dots_frame = dots_shape.text_frame
            dots_frame.text = "..."
            dots_frame.paragraphs[0].font.size = Pt(14)
            dots_frame.paragraphs[0].font.bold = True
            dots_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    def _add_compact_diagram_to_slide(self, slide, slide_data: Slide):
        """Add compact diagram for mixed layouts"""
        diagram_type = slide_data.diagram_type
        diagram_data = slide_data.diagram_data or []
        
        if diagram_type == 'process':
            self._create_compact_process_diagram(slide, diagram_data)
        elif diagram_type == 'comparison':
            self._create_compact_comparison_diagram(slide, diagram_data)
    
    def _create_compact_process_diagram(self, slide, steps):
        """Create compact process diagram for mixed layouts"""
        if not steps:
            return
        
        max_steps = min(len(steps), 3)  # Max 3 steps for compact version
        step_width = Inches(1.2)
        step_height = Inches(0.5)
        arrow_width = Inches(0.3)
        
        start_left = Inches(0.5)
        top = Inches(4.2)
        
        for i, step in enumerate(steps[:max_steps]):
            left = start_left + i * (step_width + arrow_width)
            
            # Add step box
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, left, top, step_width, step_height
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.colors['secondary']
            shape.line.color.rgb = self.colors['primary']
            
            # Add step text
            text_frame = shape.text_frame
            step_text = step.get('step', str(step)) if isinstance(step, dict) else str(step)
            if len(step_text) > 10:
                step_text = step_text[:8] + ".."
            
            text_frame.text = step_text
            paragraph = text_frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.CENTER
            paragraph.font.size = Pt(8)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.font.bold = True
            text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            
            # Add arrow
            if i < max_steps - 1:
                arrow_left = left + step_width
                arrow_shape = slide.shapes.add_shape(
                    MSO_SHAPE.RIGHT_ARROW, arrow_left, top + Inches(0.15), 
                    arrow_width, Inches(0.2)
                )
                arrow_shape.fill.solid()
                arrow_shape.fill.fore_color.rgb = self.colors['accent']
    
    def _create_comparison_diagram(self, slide, comparison_data):
        """Create comparison diagram (two columns) with proper sizing"""
        if len(comparison_data) < 2:
            return
        
        # Box dimensions that fit within slide bounds
        box_width = Inches(3.5)
        box_height = Inches(2.5)
        gap = Inches(0.5)
        
        # Center the comparison boxes
        total_width = 2 * box_width + gap
        start_left = (Inches(10) - total_width) / 2
        top = Inches(4)
        
        # Left column
        left_box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, start_left, top, box_width, box_height
        )
        left_box.fill.solid()
        left_box.fill.fore_color.rgb = RGBColor(230, 240, 250)
        left_box.line.color.rgb = self.colors['secondary']
        left_box.line.width = Pt(2)
        
        left_text = left_box.text_frame
        left_text.margin_left = Pt(12)
        left_text.margin_right = Pt(12)
        left_text.margin_top = Pt(12)
        left_text.margin_bottom = Pt(12)
        
        left_title = comparison_data[0].get('title', 'Option A') if isinstance(comparison_data[0], dict) else str(comparison_data[0])
        # Truncate long titles
        if len(left_title) > 50:
            left_title = left_title[:47] + "..."
        
        left_text.text = left_title
        self._format_comparison_text(left_text)
        
        # Right column
        right_box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, start_left + box_width + gap, top, box_width, box_height
        )
        right_box.fill.solid()
        right_box.fill.fore_color.rgb = RGBColor(250, 240, 230)
        right_box.line.color.rgb = self.colors['accent']
        right_box.line.width = Pt(2)
        
        right_text = right_box.text_frame
        right_text.margin_left = Pt(12)
        right_text.margin_right = Pt(12)
        right_text.margin_top = Pt(12)
        right_text.margin_bottom = Pt(12)
        
        right_title = comparison_data[1].get('title', 'Option B') if isinstance(comparison_data[1], dict) else str(comparison_data[1])
        # Truncate long titles
        if len(right_title) > 50:
            right_title = right_title[:47] + "..."
        
        right_text.text = right_title
        self._format_comparison_text(right_text)
    
    def _create_compact_comparison_diagram(self, slide, comparison_data):
        """Create compact comparison diagram for mixed layouts"""
        if len(comparison_data) < 2:
            return
        
        # Smaller boxes for compact layout
        box_width = Inches(2.5)
        box_height = Inches(1.8)
        gap = Inches(0.3)
        
        start_left = Inches(1)
        top = Inches(4.5)
        
        # Left column
        left_box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, start_left, top, box_width, box_height
        )
        left_box.fill.solid()
        left_box.fill.fore_color.rgb = RGBColor(230, 240, 250)
        left_box.line.color.rgb = self.colors['secondary']
        
        left_text = left_box.text_frame
        left_title = comparison_data[0].get('title', 'Option A') if isinstance(comparison_data[0], dict) else str(comparison_data[0])
        if len(left_title) > 30:
            left_title = left_title[:27] + "..."
        left_text.text = left_title
        
        paragraph = left_text.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.font.size = Pt(12)
        paragraph.font.bold = True
        paragraph.font.color.rgb = self.colors['primary']
        left_text.vertical_anchor = MSO_ANCHOR.MIDDLE
        
        # Right column
        right_box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, start_left + box_width + gap, top, box_width, box_height
        )
        right_box.fill.solid()
        right_box.fill.fore_color.rgb = RGBColor(250, 240, 230)
        right_box.line.color.rgb = self.colors['accent']
        
        right_text = right_box.text_frame
        right_title = comparison_data[1].get('title', 'Option B') if isinstance(comparison_data[1], dict) else str(comparison_data[1])
        if len(right_title) > 30:
            right_title = right_title[:27] + "..."
        right_text.text = right_title
        
        paragraph = right_text.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.font.size = Pt(12)
        paragraph.font.bold = True
        paragraph.font.color.rgb = self.colors['primary']
        right_text.vertical_anchor = MSO_ANCHOR.MIDDLE
    
    def _create_hierarchy_diagram(self, slide, hierarchy_data):
        """Create hierarchy diagram with proper sizing"""
        if not hierarchy_data:
            return
        
        # Top level box
        top_item = hierarchy_data[0] if hierarchy_data else {}
        top_text = top_item.get('title', 'Root') if isinstance(top_item, dict) else str(top_item)
        
        # Ensure text fits in box
        if len(top_text) > 20:
            top_text = top_text[:17] + "..."
        
        # Center the top box
        box_width = Inches(3)
        box_height = Inches(0.8)
        top_left = (Inches(10) - box_width) / 2
        top_top = Inches(4)
        
        top_box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, top_left, top_top, box_width, box_height
        )
        top_box.fill.solid()
        top_box.fill.fore_color.rgb = self.colors['primary']
        top_box.line.color.rgb = self.colors['primary']
        top_box.line.width = Pt(2)
        
        text_frame = top_box.text_frame
        text_frame.margin_left = Pt(8)
        text_frame.margin_right = Pt(8)
        text_frame.margin_top = Pt(8)
        text_frame.margin_bottom = Pt(8)
        
        text_frame.text = top_text
        paragraph = text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.font.size = Pt(14)
        paragraph.font.color.rgb = RGBColor(255, 255, 255)
        paragraph.font.bold = True
        text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        
        # Add sub-items if available
        if len(hierarchy_data) > 1:
            sub_items = hierarchy_data[1:4]  # Max 3 sub-items
            sub_box_width = Inches(2.2)
            sub_box_height = Inches(0.6)
            sub_gap = Inches(0.4)
            
            total_sub_width = len(sub_items) * sub_box_width + (len(sub_items) - 1) * sub_gap
            sub_start_left = (Inches(10) - total_sub_width) / 2
            sub_top = top_top + box_height + Inches(0.5)
            
            for i, sub_item in enumerate(sub_items):
                sub_text = sub_item.get('title', f'Item {i+1}') if isinstance(sub_item, dict) else str(sub_item)
                if len(sub_text) > 15:
                    sub_text = sub_text[:12] + "..."
                
                sub_left = sub_start_left + i * (sub_box_width + sub_gap)
                
                sub_box = slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE, sub_left, sub_top, sub_box_width, sub_box_height
                )
                sub_box.fill.solid()
                sub_box.fill.fore_color.rgb = self.colors['secondary']
                sub_box.line.color.rgb = self.colors['primary']
                
                sub_text_frame = sub_box.text_frame
                sub_text_frame.text = sub_text
                sub_paragraph = sub_text_frame.paragraphs[0]
                sub_paragraph.alignment = PP_ALIGN.CENTER
                sub_paragraph.font.size = Pt(11)
                sub_paragraph.font.color.rgb = RGBColor(255, 255, 255)
                sub_paragraph.font.bold = True
                sub_text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
                
                # Add connecting line
                line_start_x = top_left + box_width / 2
                line_start_y = top_top + box_height
                line_end_x = sub_left + sub_box_width / 2
                line_end_y = sub_top
                
                connector = slide.shapes.add_connector(
                    1, line_start_x, line_start_y, line_end_x, line_end_y
                )
                connector.line.color.rgb = self.colors['primary']
                connector.line.width = Pt(2)
    
    def _format_comparison_text(self, text_frame):
        """Format comparison diagram text with proper sizing"""
        paragraph = text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER
        paragraph.font.size = Pt(14)
        paragraph.font.bold = True
        paragraph.font.color.rgb = self.colors['primary']
        text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        text_frame.word_wrap = True
    
    def _add_legacy_diagram(self, slide, diagram_description):
        """Add legacy diagram support"""
        try:
            diagram_img = generate_diagram_image(diagram_description)
            slide.shapes.add_picture(diagram_img, Inches(2), Inches(2), width=Inches(4))
        except Exception as e:
            logger.error(f"Failed to embed legacy diagram: {diagram_description} - {e}")
