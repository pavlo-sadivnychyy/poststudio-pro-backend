import requests
import logging
import json

def get_linkedin_profile_info(access_token: str) -> dict:
    """Get LinkedIn profile information to retrieve the person URN"""
    url = "https://api.linkedin.com/v2/people/~"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        logging.info("🔍 Getting LinkedIn profile info...")
        response = requests.get(url, headers=headers)
        
        logging.info(f"Profile API response: {response.status_code}")
        logging.info(f"Profile API response text: {response.text}")
        
        if response.status_code == 200:
            profile_data = response.json()
            logging.info(f"✅ LinkedIn profile retrieved: {profile_data}")
            return profile_data
        elif response.status_code == 401:
            logging.error("❌ LinkedIn API returned 401 - Access token is invalid or expired")
            return {}
        elif response.status_code == 403:
            logging.error("❌ LinkedIn API returned 403 - Missing required permissions")
            return {}
        else:
            logging.error(f"❌ Failed to get LinkedIn profile: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        logging.error(f"❌ Exception getting LinkedIn profile: {e}")
        return {}

def check_linkedin_permissions(access_token: str) -> dict:
    """Check what permissions the current token has"""
    url = "https://api.linkedin.com/v2/me"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        logging.info(f"Permissions check: {response.status_code}")
        
        if response.status_code == 200:
            return {"status": "valid", "data": response.json()}
        else:
            return {"status": "invalid", "error": response.text}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def try_simple_text_post(access_token: str, content: str) -> dict:
    """Try the simplest possible LinkedIn post to test permissions"""
    
    # First get profile
    profile_info = get_linkedin_profile_info(access_token)
    if not profile_info or 'id' not in profile_info:
        return {"success": False, "error": "Could not get LinkedIn profile"}
    
    person_urn = f"urn:li:person:{profile_info['id']}"
    
    # Try the v2/shares API (simpler format)
    url = "https://api.linkedin.com/v2/shares"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    # Simplest possible payload
    payload = {
        "owner": person_urn,
        "text": {
            "text": content
        },
        "distribution": {
            "linkedInDistributionTarget": {}
        }
    }
    
    try:
        logging.info("📤 Trying simple text post...")
        logging.info(f"URL: {url}")
        logging.info(f"Headers: {headers}")
        logging.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        logging.info(f"Simple post response: {response.status_code}")
        logging.info(f"Simple post response text: {response.text}")
        
        result = {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "response_text": response.text,
            "url_used": url,
            "payload_used": payload
        }
        
        if response.status_code in [200, 201]:
            logging.info("✅ Simple LinkedIn post SUCCESS!")
        elif response.status_code == 401:
            result["error"] = "Access token invalid or expired"
        elif response.status_code == 403:
            result["error"] = "Missing permissions - need w_member_social scope"
        elif response.status_code == 422:
            result["error"] = "Invalid request format"
        else:
            result["error"] = f"Unexpected error: {response.status_code}"
        
        return result
        
    except Exception as e:
        logging.error(f"❌ Exception in simple post: {e}")
        return {"success": False, "error": str(e)}

def post_linkedin_content(access_token: str, content: str) -> bool:
    """Main posting function with enhanced debugging"""
    
    logging.info("🚀 Starting LinkedIn post with enhanced debugging...")
    
    # Step 1: Check permissions
    permissions = check_linkedin_permissions(access_token)
    logging.info(f"Permission check result: {permissions}")
    
    # Step 2: Try simple post
    result = try_simple_text_post(access_token, content)
    
    # Log full debugging info
    logging.info("=== LINKEDIN POST DEBUG INFO ===")
    logging.info(f"Success: {result.get('success', False)}")
    logging.info(f"Status Code: {result.get('status_code')}")
    logging.info(f"Error: {result.get('error', 'None')}")
    logging.info(f"Response: {result.get('response_text', 'None')}")
    logging.info("===============================")
    
    return result.get('success', False)