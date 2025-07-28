from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

class BulletPoint(BaseModel):
    text: str
    level: int = 0
    sub_points: Optional[List[str]] = []

class DiagramData(BaseModel):
    type: str  # 'process', 'comparison', 'hierarchy'
    data: List[Dict[str, Any]]

class Slide(BaseModel):
    title: str
    bullets: List[str] = []  # Keep for backward compatibility
    notes: Optional[str] = None
    images: Optional[List[str]] = None  # URLs or base64
    diagrams: Optional[List[str]] = None  # Diagram descriptions or URLs
    type: Optional[str] = "content"  # 'title', 'content', 'image', 'conclusion'
    
    # Enhanced features
    content: Optional[List[Union[str, BulletPoint]]] = []
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    image_position: str = 'right'  # 'right', 'center', 'left'
    diagram_type: Optional[str] = None  # 'process', 'comparison', 'hierarchy'
    diagram_data: Optional[List[Dict[str, Any]]] = []

class Deck(BaseModel):
    slides: List[Slide]
    title: Optional[str] = "Presentation"
    theme: Optional[str] = 'professional'
    total_slides: Optional[int] = None
