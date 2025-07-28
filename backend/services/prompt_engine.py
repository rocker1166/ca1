from core.config import settings
from core.logger import get_logger
from services.slide_schema import Deck
from pydantic import ValidationError
import json
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

logger = get_logger("prompt_engine")

class PromptEngine:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.temperature = 0.3
        self.max_retries = 2
        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            temperature=self.temperature,
        )
        self.parser = PydanticOutputParser(pydantic_object=Deck)
        self.format_instructions = self.parser.get_format_instructions()
        self.prompt_template = PromptTemplate(
            template=(
                "You are an expert slide deck generator.\n"
                "Generate a slide deck for the topic: {topic}\n"
                "{format_instructions}\n"
            ),
            input_variables=["topic"],
            partial_variables={"format_instructions": self.format_instructions},
        )

    def generate_slides(self, topic: str, num_slides: int = 8, include_images: bool = True, include_diagrams: bool = True) -> Deck:
        """Generate enhanced slide content with formatting instructions"""
        print("DEBUG: generate_slides called", flush=True)
        
        # Enhanced prompt with formatting instructions
        enhanced_prompt = f"""
        You are an expert slide deck generator. Create a professional PowerPoint presentation about "{topic}" with {num_slides} slides.
        
        Structure the presentation as follows:
        
        Slide 1 (Title Slide):
        - type: "title"
        - title: Main presentation title
        - subtitle: Brief description or author info
        
        Slides 2-{num_slides-1} (Content Slides):
        - type: "content"
        - title: Clear, descriptive heading
        - bullets: Array of 3-5 bullet points (for backward compatibility)
        - content: Enhanced bullet points with sub-points where appropriate
        {"- image_url: Include relevant placeholder image URL (e.g., 'https://via.placeholder.com/400x300/0066cc/ffffff?text=Topic+Image')" if include_images else ""}
        {"- diagram_type: 'process', 'comparison', or 'hierarchy' where concepts need visual explanation" if include_diagrams else ""}
        {"- diagram_data: Relevant data for the diagram" if include_diagrams else ""}
        
        Final Slide (Conclusion):
        - type: "conclusion"
        - title: "Conclusion" or "Key Takeaways"
        - bullets: Summary points
        
        Guidelines for content:
        1. Use clear, engaging headings
        2. Keep bullet points concise but informative
        3. Include sub-points for complex topics
        4. Suggest relevant images for visual appeal
        5. Add diagrams for processes, comparisons, or hierarchies
        6. Ensure professional tone throughout
        
        For bullet points, you can use simple strings or structured format:
        - Simple: ["Point 1", "Point 2", "Point 3"]
        - Enhanced: [
            "Simple point",
            {{"text": "Complex point with details", "level": 0, "sub_points": ["Detail 1", "Detail 2"]}},
            "Another simple point"
        ]
        
        {self.format_instructions}
        """
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Calling Gemini for topic: {topic} (attempt {attempt})")
                print("DEBUG: About to call LLM", flush=True)
                try:
                    response = self.llm.invoke(enhanced_prompt)
                    print("DEBUG: LLM call returned", flush=True)
                    print("DEBUG: LLM response object:", response, flush=True)
                    print("RAW LLM OUTPUT:", getattr(response, 'content', response), flush=True)
                except Exception as e:
                    print("EXCEPTION DURING LLM CALL:", e, flush=True)
                    raise
                
                # Use the structured output parser
                deck = self.parser.parse(getattr(response, 'content', response))
                
                # Post-process slides to ensure backward compatibility
                deck = self._post_process_deck(deck, topic, include_images, include_diagrams)
                
                logger.info(f"Validated Deck: {deck}")
                return deck
            except (ValidationError, json.JSONDecodeError, ValueError) as e:
                logger.error(f"Validation/JSON error: {e}")
                last_error = e
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                last_error = e
            time.sleep(1)
        raise ValueError(f"Failed to generate valid slides after {self.max_retries} attempts: {last_error}")
    
    def _post_process_deck(self, deck: Deck, topic: str, include_images: bool, include_diagrams: bool) -> Deck:
        """Post-process the deck to add enhanced features"""
        processed_slides = []
        
        for i, slide in enumerate(deck.slides):
            # Ensure backward compatibility by copying bullets to content if content is empty
            if not slide.content and slide.bullets:
                slide.content = slide.bullets.copy()
            elif not slide.bullets and slide.content:
                # Extract simple text from content for bullets field
                slide.bullets = [
                    item.text if isinstance(item, dict) and 'text' in item else str(item) 
                    for item in slide.content
                ]
            
            # Add sample images for certain slide types if requested
            if include_images and i > 0 and i < len(deck.slides) - 1:  # Skip title and conclusion
                if not slide.image_url and not slide.images:
                    # Add placeholder image URL based on slide content
                    topic_words = topic.replace(' ', '+')
                    slide.image_url = f"https://via.placeholder.com/400x300/0066cc/ffffff?text={topic_words}"
            
            # Add sample diagrams for process-oriented slides
            if include_diagrams and i > 0 and any(word in slide.title.lower() for word in ['process', 'steps', 'workflow', 'method']):
                if not slide.diagram_type:
                    slide.diagram_type = 'process'
                    slide.diagram_data = [
                        {'step': f'Step {j+1}', 'description': f'Process step {j+1}'} 
                        for j in range(min(4, len(slide.bullets)))
                    ]
            
            processed_slides.append(slide)
        
        deck.slides = processed_slides
        return deck
