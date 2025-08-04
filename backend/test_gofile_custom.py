import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.gofile_service import gofile_service
from core.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("test_gofile_custom")

def test_custom_filename():
    """Test the GoFile service with custom filename functionality"""
    
    print("=" * 60)
    print("🧪 TESTING GOFILE.IO SERVICE - CUSTOM FILENAME")
    print("=" * 60)
    
    # Test API connection first
    print("\n1️⃣ Testing API Connection...")
    connection_result = gofile_service.test_connection()
    
    if not connection_result["success"]:
        print(f"❌ API connection failed: {connection_result.get('error', 'Unknown error')}")
        print("Check your API token in .env file (GOFILE_API_TOKEN)")
        return
    else:
        print("✅ GoFile API connection successful!")
        if "account_id" in connection_result:
            print(f"📝 Account ID: {connection_result['account_id']}")
        else:
            print("⚠️ Using guest upload mode (no API token)")
    
    # Test file upload with custom filename
    print("\n2️⃣ Testing File Upload with Custom Filename...")
    
    # Create a sample file to upload
    test_file_path = os.path.join(os.path.dirname(__file__), "tmp", "gofile_test.txt")
    try:
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, "w") as f:
            f.write("This is a test file for GoFile.io API integration with custom filename.")
        
        print(f"📄 Created test file: {test_file_path}")
        
        # Test upload with custom filename
        custom_filename = "john_doe_machine_learning.txt"
        upload_result = gofile_service.upload_file(test_file_path, custom_filename=custom_filename)
        
        if upload_result["success"]:
            print("✅ File upload with custom filename successful!")
            print(f"📎 File ID: {upload_result.get('file_id')}")
            print(f"📝 Custom Filename: {upload_result.get('file_name')}")
            print(f"📝 Original Filename: {upload_result.get('original_file_name')}")
            print(f"🔗 Download URL: {upload_result.get('download_url')}")
        else:
            print(f"❌ File upload failed: {upload_result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        # Clean up test file
        try:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                print(f"🧹 Cleaned up test file")
        except Exception:
            pass

def create_custom_filename(username: str, topic: str) -> str:
    """Test the custom filename creation function"""
    import re
    
    # Clean username - remove special characters and spaces
    clean_username = re.sub(r'[^\w\-_]', '', username.replace(' ', '_'))
    
    # Clean topic - remove special characters, replace spaces with underscores
    clean_topic = re.sub(r'[^\w\-_\s]', '', topic).replace(' ', '_')
    
    # Limit length to avoid very long filenames
    clean_username = clean_username[:20] if clean_username else "anonymous"
    clean_topic = clean_topic[:50] if clean_topic else "presentation"
    
    return f"{clean_username}_{clean_topic}.pptx"

def test_filename_creation():
    """Test the filename creation function"""
    print("\n3️⃣ Testing Custom Filename Creation...")
    
    test_cases = [
        ("John Doe", "Machine Learning Basics"),
        ("user@email.com", "Data Science & Analytics!"),
        ("", "Empty Username Test"),
        ("validuser", ""),
        ("Special!@#$%Characters", "Topic with Spaces and Numbers 123"),
        ("very_long_username_that_exceeds_limits", "very_long_topic_name_that_also_exceeds_the_character_limits_we_set"),
    ]
    
    for username, topic in test_cases:
        custom_filename = create_custom_filename(username, topic)
        print(f"📝 '{username}' + '{topic}' → '{custom_filename}'")

if __name__ == "__main__":
    test_custom_filename()
    test_filename_creation()
