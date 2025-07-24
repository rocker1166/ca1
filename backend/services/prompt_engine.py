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

    def generate_slides(self, topic: str) -> Deck:
        print("DEBUG: generate_slides called", flush=True)
        prompt = self.prompt_template.format(topic=topic)
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Calling Gemini for topic: {topic} (attempt {attempt})")
                print("DEBUG: About to call LLM", flush=True)
                try:
                    response = self.llm.invoke(prompt)
                    print("DEBUG: LLM call returned", flush=True)
                    print("DEBUG: LLM response object:", response, flush=True)
                    print("RAW LLM OUTPUT:", getattr(response, 'content', response), flush=True)
                except Exception as e:
                    print("EXCEPTION DURING LLM CALL:", e, flush=True)
                    raise
                # Use the structured output parser
                deck = self.parser.parse(getattr(response, 'content', response))
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
