from typing import List, Optional
from pydantic import BaseModel

class Slide(BaseModel):
    title: str
    bullets: List[str]
    notes: Optional[str] = None
    images: Optional[List[str]] = None  # URLs or base64
    diagrams: Optional[List[str]] = None  # Diagram descriptions or URLs
    type: Optional[str] = "title_bullets"  # For plugin-style layouts

class Deck(BaseModel):
    slides: List[Slide]
