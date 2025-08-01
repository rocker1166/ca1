#!/usr/bin/env python
"""
NLTK Resource Setup Script

This script ensures all required NLTK resources are downloaded
for the Layout Intelligence system.
"""

import nltk
import sys
import os
from pathlib import Path

def setup_nltk_resources():
    """Download required NLTK resources."""
    print("Setting up NLTK resources...")
    
    # Create a data directory in the project if it doesn't exist
    project_nltk_data = Path(__file__).parent / "nltk_data"
    os.environ["NLTK_DATA"] = str(project_nltk_data)
    project_nltk_data.mkdir(exist_ok=True)
    
    # List of resources to download
    resources = [
        'punkt',
        'stopwords'
    ]
    
    # Download each resource
    for resource in resources:
        print(f"Downloading {resource}...")
        try:
            nltk.download(resource, download_dir=project_nltk_data)
            print(f"Successfully downloaded {resource}")
        except Exception as e:
            print(f"Error downloading {resource}: {e}")
    
    print("\nAll NLTK resources have been processed.")
    print(f"Resources stored in: {project_nltk_data}\n")
    
    # Verify the downloads
    print("Verifying downloads...")
    try:
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        
        # Test the tokenizer
        sample = "This is a test sentence."
        tokens = word_tokenize(sample)
        print(f"Tokenization test: '{sample}' → {tokens}")
        
        # Test the stopwords
        stop_words = stopwords.words('english')
        print(f"Stopwords test: First 5 stopwords: {stop_words[:5]}")
        
        print("\nAll tests passed. NLTK resources are ready to use.")
    except Exception as e:
        print(f"Verification failed: {e}")
        print("\nThere may be issues with NLTK resource setup.")

if __name__ == "__main__":
    setup_nltk_resources()
