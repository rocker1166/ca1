import pytest
from services.slide_schema import Slide, Deck
from pydantic import ValidationError

def test_valid_slide():
    slide = Slide(title="Intro", bullets=["Point 1", "Point 2"])
    assert slide.title == "Intro"
    assert slide.bullets == ["Point 1", "Point 2"]
    assert slide.notes is None

def test_valid_deck():
    deck = Deck(slides=[Slide(title="A", bullets=["B"])])
    assert len(deck.slides) == 1

def test_invalid_slide_missing_title():
    with pytest.raises(ValidationError):
        Slide(bullets=["A"])  # Missing title

def test_invalid_slide_bullets_type():
    with pytest.raises(ValidationError):
        Slide(title="A", bullets="notalist")
