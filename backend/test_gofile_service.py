import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.gofile_service import gofile_service
from core.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("test_gofile")

def test_gofile_service():
    """Test the GoFile service with your API token"""
    
    print("=" * 60)
    print("🧪 TESTING GOFILE.IO SERVICE")
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
    
    # Test file upload
    print("\n2️⃣ Testing File Upload...")
    
    # Create a sample file to upload
    test_file_path = os.path.join(os.path.dirname(__file__), "tmp", "gofile_test.txt")
    try:
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, "w") as f:
            f.write("This is a test file for GoFile.io API integration.")
        
        print(f"📄 Created test file: {test_file_path}")
        
        # Upload the file
        upload_result = gofile_service.upload_file(test_file_path)
        
        if upload_result["success"]:
            print("✅ File upload successful!")
            print(f"📎 File ID: {upload_result.get('file_id')}")
            print(f"🔗 Download URL: {upload_result.get('download_url')}")
            
            # Test folder creation if API token is available
            if gofile_service.api_token:
                print("\n3️⃣ Testing Folder Creation...")
                # Get the parent folder ID from the upload result
                raw_response = upload_result.get('raw_response', {})
                parent_id = raw_response.get('parentFolder', None)
                
                if parent_id:
                    folder_result = gofile_service.create_folder(parent_id, "test_folder")
                    
                    if folder_result["success"]:
                        print("✅ Folder creation successful!")
                        print(f"📁 Folder ID: {folder_result.get('folder_id')}")
                    else:
                        print(f"❌ Folder creation failed: {folder_result.get('error')}")
                else:
                    print("⚠️ Cannot test folder creation - no parent folder ID available")
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

if __name__ == "__main__":
    test_gofile_service()
