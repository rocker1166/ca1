import os
import uuid
import requests
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.enum.text import PP_ALIGN
from services.slide_schema import Deck, Slide
from core.logger import get_logger
from io import BytesIO

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'template.pptx')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp')
os.makedirs(OUTPUT_DIR, exist_ok=True)
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
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

# Layout registry
LAYOUT_REGISTRY = {
    "title_bullets": TitleBulletsLayout(),
    "image": ImageLayout(),
    "diagram": DiagramLayout(),
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
    def __init__(self, template_path: str = TEMPLATE_PATH):
        self.template_path = template_path

    def build(self, deck: Deck, use_template: bool = True) -> str:
        try:
            logger.info(f"Building PPTX. use_template={use_template}, slides={len(deck.slides)}")
            if use_template:
                if not os.path.exists(self.template_path):
                    raise FileNotFoundError(f"PPTX template not found: {self.template_path}")
                prs = Presentation(self.template_path)
            else:
                prs = Presentation()
            default_layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
            for i, slide_data in enumerate(deck.slides):
                logger.info(f"Processing slide {i+1}: {slide_data.title}")
                layout = default_layout
                pptx_slide = prs.slides.add_slide(layout)
                # Defensive: fallback if title placeholder is missing
                title_shape = pptx_slide.shapes.title
                if title_shape is not None:
                    title_shape.text = slide_data.title
                    title_shape.text_frame.paragraphs[0].font.size = Pt(32)
                    title_shape.text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT
                else:
                    textbox = pptx_slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(1))
                    tf = textbox.text_frame
                    tf.text = slide_data.title
                    tf.paragraphs[0].font.size = Pt(32)
                    tf.paragraphs[0].alignment = PP_ALIGN.LEFT
                plugin = get_layout(slide_data)
                plugin.render(slide_data, pptx_slide)
                # Embed additional images (if any)
                if slide_data.images and len(slide_data.images) > 1:
                    for img_url in slide_data.images[1:]:
                        try:
                            img_bytes = requests.get(img_url, timeout=5).content
                            image_stream = BytesIO(img_bytes)
                            pptx_slide.shapes.add_picture(image_stream, Inches(1), Inches(1), width=Inches(2))
                        except Exception as e:
                            logger.error(f"Failed to embed extra image: {img_url} - {e}")
                # Embed additional diagrams (if any)
                if slide_data.diagrams and len(slide_data.diagrams) > 1:
                    for desc in slide_data.diagrams[1:]:
                        try:
                            diagram_img = generate_diagram_image(desc)
                            pptx_slide.shapes.add_picture(diagram_img, Inches(1), Inches(1), width=Inches(2))
                        except Exception as e:
                            logger.error(f"Failed to embed extra diagram: {desc} - {e}")
            file_path = os.path.join(RESULTS_DIR, f"{uuid.uuid4()}.pptx")
            prs.save(file_path)
            logger.info(f"PPTX generated: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to build PPTX: {e}")
            raise
