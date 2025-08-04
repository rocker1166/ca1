import os
import requests
import logging
from typing import Optional, Dict, Any
from core.config import settings
from core.logger import get_logger

logger = get_logger("gofile_service")

class GoFileService:
    """Service for interacting with GoFile.io API to store files online"""
    
    def __init__(self):
        self.base_url = "https://api.gofile.io"
        self.api_token = settings.gofile_api_token
        self.folder_id = settings.gofile_folder_id  # Optional: default folder to upload to
    
    def get_best_server(self) -> Dict[str, Any]:
        """Get the best server for uploading files"""
        try:
            response = requests.get(f"{self.base_url}/getServer")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok":
                    server = result.get("data", {}).get("server")
                    logger.debug(f"Got best server: {server}")
                    return {"success": True, "server": server}
                else:
                    logger.error(f"Failed to get server: {result}")
                    return {"success": False, "error": result.get("status", "Unknown error")}
            else:
                logger.error(f"Server API returned status code: {response.status_code}")
                return {"success": False, "error": f"Server API Error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting server: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None, custom_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to GoFile.io
        
        Args:
            file_path: Path to the file to upload
            folder_id: Optional folder ID to upload to (if None, uses default or creates new)
            custom_filename: Optional custom filename to use instead of the original filename
            
        Returns:
            Dict with upload result details including download URL
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {"success": False, "error": "File not found"}

            # Use custom filename if provided, otherwise use original filename
            upload_filename = custom_filename if custom_filename else os.path.basename(file_path)
            logger.info(f"Uploading file to GoFile: {file_path} as '{upload_filename}'")
            
            # Use the correct upload endpoint
            upload_url = "https://upload.gofile.io/uploadfile"
            
            # Prepare headers with token if available
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
                logger.debug("Using API token for authentication")
            else:
                logger.warning("No API token configured - using guest upload")
            
            # Prepare files and data
            with open(file_path, 'rb') as f:
                files = {'file': (upload_filename, f)}
                data = {}
                
                # Add folder ID if specified and we have API token
                if (folder_id or self.folder_id) and self.api_token:
                    target_folder = folder_id or self.folder_id
                    data['folderId'] = target_folder  # Correct parameter name
                    logger.debug(f"Uploading to folder: {target_folder}")
                elif (folder_id or self.folder_id) and not self.api_token:
                    logger.warning("Cannot upload to specific folder without API token - creating new folder")
                else:
                    logger.debug("No folder specified - uploading to new folder")
                
                logger.debug(f"Upload URL: {upload_url}")
                logger.debug(f"Data parameters: {data}")
                
                # Upload the file
                response = requests.post(
                    upload_url,
                    headers=headers if headers else None,
                    files=files,
                    data=data if data else None
                )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "ok":
                    file_data = result.get("data", {})
                    download_url = file_data.get("downloadPage", "")
                    file_id = file_data.get("fileId", "")
                    
                    logger.info(f"File uploaded successfully. ID: {file_id}, Custom name: {upload_filename}")
                    return {
                        "success": True,
                        "file_id": file_id,
                        "download_url": download_url,
                        "file_name": upload_filename,
                        "original_file_name": os.path.basename(file_path),
                        "raw_response": file_data
                    }
                else:
                    error = result.get("status", "Unknown error")
                    logger.error(f"GoFile upload failed: {error}")
                    return {"success": False, "error": error}
            else:
                logger.error(f"GoFile API returned status code: {response.status_code}")
                logger.error(f"Response headers: {dict(response.headers)}")
                logger.error(f"Response text: {response.text}")
                return {
                    "success": False, 
                    "error": f"API Error: {response.status_code}",
                    "response_text": response.text[:500],
                    "response_headers": dict(response.headers)
                }
                
        except Exception as e:
            logger.error(f"Error uploading file to GoFile: {e}")
            return {"success": False, "error": str(e)}
    
    def create_folder(self, parent_folder_id: str, folder_name: str) -> Dict[str, Any]:
        """
        Create a new folder within a parent folder
        
        Args:
            parent_folder_id: ID of the parent folder
            folder_name: Name for the new folder
            
        Returns:
            Dict with folder creation result details
        """
        if not self.api_token:
            logger.error("GoFile API token is required for folder creation")
            return {"success": False, "error": "API token required"}
            
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}"
            }
            
            data = {
                "parentFolderId": parent_folder_id,
                "folderName": folder_name
            }
            
            response = requests.post(
                f"{self.base_url}/contents/createFolder",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "ok":
                    folder_data = result.get("data", {})
                    folder_id = folder_data.get("id", "")
                    
                    logger.info(f"Folder created successfully. ID: {folder_id}")
                    return {
                        "success": True,
                        "folder_id": folder_id,
                        "folder_name": folder_name,
                        "raw_response": folder_data
                    }
                else:
                    error = result.get("status", "Unknown error")
                    logger.error(f"GoFile folder creation failed: {error}")
                    return {"success": False, "error": error}
            else:
                logger.error(f"GoFile API returned status code: {response.status_code}")
                return {"success": False, "error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error creating folder on GoFile: {e}")
            return {"success": False, "error": str(e)}
    
    def get_account_id(self) -> Dict[str, Any]:
        """
        Get the account ID associated with the API token
        
        Returns:
            Dict with account ID information
        """
        if not self.api_token:
            logger.error("GoFile API token is required to get account ID")
            return {"success": False, "error": "API token required"}
            
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            
            response = requests.get(
                f"{self.base_url}/accounts/getid",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "ok":
                    account_data = result.get("data", {})
                    account_id = account_data.get("id", "")
                    
                    logger.info(f"Retrieved account ID: {account_id}")
                    return {
                        "success": True,
                        "account_id": account_id,
                        "raw_response": account_data
                    }
                else:
                    error = result.get("status", "Unknown error")
                    logger.error(f"GoFile get account ID failed: {error}")
                    return {"success": False, "error": error}
            else:
                logger.error(f"GoFile API returned status code: {response.status_code}")
                return {"success": False, "error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting GoFile account ID: {e}")
            return {"success": False, "error": str(e)}
            
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to GoFile API
        
        Returns:
            Dict with connection test results
        """
        if not self.api_token:
            logger.warning("No GoFile API token configured. Will use guest upload.")
            # Test guest upload capability
            try:
                response = requests.get(self.upload_url)
                if response.status_code in (200, 405):  # 405 is expected for GET on POST endpoint
                    return {"success": True, "message": "Guest upload should be available"}
                else:
                    return {"success": False, "error": f"API endpoint not available: {response.status_code}"}
            except Exception as e:
                return {"success": False, "error": f"Connection error: {str(e)}"}
        else:
            # Test with account ID endpoint
            return self.get_account_id()

# Global instance
gofile_service = GoFileService()
