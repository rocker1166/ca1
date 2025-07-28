import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.image_service import image_service
from core.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("test_images")

def test_image_service():
    """Test the image service with your Unsplash API keys"""
    
    print("=" * 60)
    print("🧪 TESTING UNSPLASH IMAGE SERVICE")
    print("=" * 60)
    
    # Test API connection first
    print("\n1️⃣ Testing API Connection...")
    connection_ok = image_service.test_connection()
    
    if not connection_ok:
        print("❌ API connection failed. Check your keys and internet connection.")
        return
    
    # Test with various topics
    test_topics = [
        ("machine learning", "Introduction to Neural Networks"),
        ("python programming", "Data Structures and Algorithms"), 
        ("web development", "Building Modern Web Applications"),
        ("data science", "Data Visualization Techniques"),
        ("artificial intelligence", "AI Ethics and Future"),
        ("cloud computing", "Serverless Architecture"),
        ("cybersecurity", "Network Security Fundamentals")
    ]
    
    print("\n2️⃣ Testing Image Retrieval...")
    print("-" * 60)
    
    successful_images = 0
    
    for main_topic, slide_title in test_topics:
        print(f"\n📋 Topic: {main_topic}")
        print(f"📑 Slide: {slide_title}")
        
        url = image_service.get_image_url(main_topic, slide_title)
        
        if "unsplash" in url.lower():
            print(f"✅ Got Unsplash image!")
            successful_images += 1
        elif "placehold" in url.lower():
            print(f"🎨 Using themed placeholder")
        else:
            print(f"⚠️ Using basic placeholder")
        
        print(f"🔗 URL: {url[:80]}...")
        print("-" * 60)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"✅ Unsplash images: {successful_images}/{len(test_topics)}")
    print(f"🎨 Placeholders: {len(test_topics) - successful_images}/{len(test_topics)}")
    
    if successful_images > 0:
        print("🎉 SUCCESS! Unsplash API is working correctly!")
    else:
        print("⚠️ No Unsplash images retrieved. Check API limits or try different topics.")

if __name__ == "__main__":
    test_image_service()
