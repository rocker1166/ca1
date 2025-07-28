import requests
import logging
from typing import Optional, List
import os
from urllib.parse import quote
from core.config import settings

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        # Load Unsplash API credentials from settings
        self.unsplash_access_key = settings.unsplash_access_key
        self.unsplash_secret_key = settings.unsplash_secret_key
        self.unsplash_base_url = "https://api.unsplash.com"
        
        # Topic to color mapping for better placeholders
        self.topic_colors = {
            'machine learning': '2196F3',
            'artificial intelligence': '9C27B0', 
            'data science': '4CAF50',
            'programming': 'FF9800',
            'python': '3776AB',
            'web development': 'E91E63',
            'business': '607D8B',
            'technology': '795548',
            'education': '009688',
            'science': '8BC34A',
            'marketing': 'FF5722',
            'finance': '3F51B5',
            'healthcare': '4CAF50',
            'security': 'F44336',
            'software': '607D8B',
            'cloud': '03A9F4',
            'mobile': '8BC34A',
            'design': 'E91E63',
            'analytics': '673AB7',
            'automation': 'FF9800'
        }
        
        logger.info(f"ImageService initialized. Unsplash API available: {'Yes' if self.unsplash_access_key else 'No'}")
    
    def get_image_url(self, topic: str, slide_title: str = "", size: str = "800x600") -> str:
        """Get relevant image URL for a topic"""
        try:
            # Try Unsplash first if API key is available
            if self.unsplash_access_key:
                url = self._get_unsplash_image(topic, slide_title)
                if url:
                    logger.info(f"✅ Got Unsplash image for: {topic}")
                    return url
                else:
                    logger.info(f"❌ No Unsplash results for: {topic}, using placeholder")
            else:
                logger.info("⚠️ No Unsplash API key, using placeholder")
            
            # Fallback to themed placeholder
            return self._get_themed_placeholder(topic, size)
            
        except Exception as e:
            logger.error(f"❌ Failed to get image for topic '{topic}': {e}")
            return self._get_basic_placeholder(size)
    
    def _get_unsplash_image(self, topic: str, slide_title: str = "") -> Optional[str]:
        """Get image from Unsplash API"""
        try:
            # Create search terms prioritizing slide title
            search_terms = []
            
            # Clean and prepare search terms
            if slide_title.strip():
                # Remove common presentation words
                cleaned_title = slide_title.replace("Introduction to", "").replace("Overview of", "").strip()
                if cleaned_title:
                    search_terms.append(cleaned_title)
            
            # Add main topic
            search_terms.append(topic.strip())
            
            # Create search query
            query = " ".join(search_terms[:2])  # Limit to 2 terms for better results
            
            headers = {
                'Authorization': f'Client-ID {self.unsplash_access_key}',
                'Accept-Version': 'v1'
            }
            
            params = {
                'query': query,
                'per_page': 3,  # Get multiple options
                'orientation': 'landscape',
                'content_filter': 'high',
                'order_by': 'relevant'
            }
            
            logger.info(f"🔍 Searching Unsplash for: '{query}'")
            
            response = requests.get(
                f"{self.unsplash_base_url}/search/photos",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results and len(results) > 0:
                    # Get the best result (first one is most relevant)
                    best_image = results[0]
                    
                    # Safely extract image URL
                    urls = best_image.get('urls', {})
                    image_url = urls.get('regular') or urls.get('small') or urls.get('thumb')
                    
                    if image_url:
                        # Log image details
                        description = best_image.get('description') or 'No description'
                        logger.info(f"📸 Found image: {description[:50]}...")
                        logger.info(f"🔗 Image URL: {image_url}")
                        return image_url
                    else:
                        logger.error(f"🔍 No valid image URLs found in result: {best_image}")
                else:
                    logger.info(f"🔍 No Unsplash results for query: '{query}'")
                    
            elif response.status_code == 403:
                logger.error("🚫 Unsplash API: Access forbidden - check your API key")
            elif response.status_code == 401:
                logger.error("🔑 Unsplash API: Unauthorized - invalid API key")
            else:
                logger.error(f"🚨 Unsplash API error: {response.status_code} - {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            logger.error("⏰ Unsplash API timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Unsplash API request error: {e}")
        except Exception as e:
            logger.error(f"💥 Unexpected Unsplash API error: {e}")
        
        return None
    
    def _get_themed_placeholder(self, topic: str, size: str = "800x600") -> str:
        """Get themed placeholder image based on topic"""
        topic_lower = topic.lower()
        
        # Find matching color and create display text
        color = '6C757D'  # Default gray
        display_text = "Slide Image"
        
        for key, topic_color in self.topic_colors.items():
            if key in topic_lower:
                color = topic_color
                display_text = key.replace(' ', '+').title()
                break
        
        # If no specific match, use first word of topic
        if color == '6C757D' and topic:
            display_text = topic.split()[0][:12] if topic.split() else "Image"
        
        # Create themed placeholder URL
        placeholder_url = f"https://placehold.co/{size}/{color}/ffffff?text={quote(display_text)}"
        
        logger.info(f"🎨 Using themed placeholder: {display_text} (color: #{color})")
        return placeholder_url
    
    def _get_basic_placeholder(self, size: str = "800x600") -> str:
        """Get basic placeholder image using a reliable service"""
        return f"https://placehold.co/{size}/CCCCCC/666666?text=Image+Placeholder"
    
    def get_multiple_images(self, topics: List[str], max_images: int = 5) -> List[str]:
        """Get multiple images for different topics"""
        images = []
        for topic in topics[:max_images]:
            url = self.get_image_url(topic)
            if url:
                images.append(url)
        return images
    
    def test_connection(self) -> bool:
        """Test Unsplash API connection"""
        try:
            if not self.unsplash_access_key:
                logger.error("🚫 No Unsplash API key configured")
                return False
            
            headers = {
                'Authorization': f'Client-ID {self.unsplash_access_key}',
                'Accept-Version': 'v1'
            }
            
            # Test with a simple request
            response = requests.get(
                f"{self.unsplash_base_url}/photos/random?featured=true",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Unsplash API connection successful!")
                return True
            else:
                logger.error(f"❌ Unsplash API test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Unsplash API test error: {e}")
            return False

# Global instance
image_service = ImageService()
