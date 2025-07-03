import requests
import logging
import json

def get_linkedin_profile_info(access_token: str) -> dict:
    """Get LinkedIn profile information using the correct API"""
    # Try the OpenID Connect endpoint first (more reliable)
    url = "https://api.linkedin.com/v2/userinfo"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        logging.info("🔍 Getting LinkedIn profile info via userinfo endpoint...")
        response = requests.get(url, headers=headers)
        
        logging.info(f"Profile API response: {response.status_code}")
        logging.info(f"Profile API response text: {response.text}")
        
        if response.status_code == 200:
            profile_data = response.json()
            logging.info(f"✅ LinkedIn profile retrieved via userinfo: {profile_data}")
            return profile_data
        else:
            # Fallback to v2/people/~ endpoint
            logging.info("Trying fallback v2/people/~ endpoint...")
            return get_linkedin_profile_fallback(access_token)
            
    except Exception as e:
        logging.error(f"❌ Exception getting LinkedIn profile: {e}")
        return get_linkedin_profile_fallback(access_token)

def get_linkedin_profile_fallback(access_token: str) -> dict:
    """Fallback method to get LinkedIn profile"""
    url = "https://api.linkedin.com/v2/people/~"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        logging.info(f"Fallback profile API response: {response.status_code}")
        logging.info(f"Fallback profile API response text: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"❌ Fallback profile failed: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        logging.error(f"❌ Exception in fallback profile: {e}")
        return {}

def check_linkedin_permissions(access_token: str) -> dict:
    """Check LinkedIn permissions using userinfo endpoint"""
    url = "https://api.linkedin.com/v2/userinfo"
    
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

def create_linkedin_post_new_api(access_token: str, content: str) -> dict:
    """Create LinkedIn post using the new REST API endpoints"""
    
    # First get profile info
    profile_info = get_linkedin_profile_info(access_token)
    if not profile_info:
        return {"success": False, "error": "Could not get LinkedIn profile"}
    
    # Extract person ID from profile
    person_id = profile_info.get("sub") or profile_info.get("id")
    if not person_id:
        return {"success": False, "error": "Could not get person ID from profile"}
    
    person_urn = f"urn:li:person:{person_id}"
    logging.info(f"👤 Using person URN: {person_urn}")
    
    # Use the new REST API for posting
    url = "https://api.linkedin.com/rest/posts"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202507"  # Fixed: Use correct version from screenshot
    }
    
    # New API payload format
    payload = {
        "author": person_urn,
        "commentary": content,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED"
    }
    
    try:
        logging.info("📤 Attempting to post using new REST API...")
        logging.info(f"URL: {url}")
        logging.info(f"Headers being sent: {headers}")
        logging.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Log each header individually to debug
        for key, value in headers.items():
            logging.info(f"Header {key}: {value}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        logging.info(f"REST API response: {response.status_code}")
        logging.info(f"REST API response text: {response.text}")
        logging.info(f"Response headers: {dict(response.headers)}")
        
        result = {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "response_text": response.text,
            "url_used": url,
            "payload_used": payload,
            "headers_sent": headers
        }
        
        if response.status_code in [200, 201]:
            logging.info("✅ LinkedIn post SUCCESS with new REST API!")
            result["post_id"] = response.json().get("id") if response.text else None
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
        logging.error(f"❌ Exception in new REST API: {e}")
        return {"success": False, "error": str(e)}

def create_linkedin_post_legacy_api(access_token: str, content: str) -> dict:
    """Fallback to legacy ugcPosts API"""
    
    profile_info = get_linkedin_profile_info(access_token)
    if not profile_info:
        return {"success": False, "error": "Could not get LinkedIn profile"}
    
    person_id = profile_info.get("sub") or profile_info.get("id")
    if not person_id:
        return {"success": False, "error": "Could not get person ID"}
    
    person_urn = f"urn:li:person:{person_id}"
    
    url = "https://api.linkedin.com/v2/ugcPosts"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        logging.info("📤 Attempting legacy ugcPosts API...")
        response = requests.post(url, headers=headers, json=payload)
        
        logging.info(f"Legacy API response: {response.status_code}")
        logging.info(f"Legacy API response text: {response.text}")
        
        return {
            "success": response.status_code == 201,
            "status_code": response.status_code,
            "response_text": response.text,
            "url_used": url
        }
        
    except Exception as e:
        logging.error(f"❌ Exception in legacy API: {e}")
        return {"success": False, "error": str(e)}

def post_linkedin_content(access_token: str, content: str) -> bool:
    """Main posting function - tries new API first, then legacy"""
    
    logging.info("🚀 Starting LinkedIn post with updated API endpoints...")
    
    # Try new REST API first
    result = create_linkedin_post_new_api(access_token, content)
    
    if result.get("success"):
        logging.info("✅ SUCCESS with new REST API!")
        return True
    
    logging.info("❌ New REST API failed, trying legacy API...")
    
    # Fallback to legacy API
    legacy_result = create_linkedin_post_legacy_api(access_token, content)
    
    if legacy_result.get("success"):
        logging.info("✅ SUCCESS with legacy API!")
        return True
    
    # Both failed
    logging.error("❌ Both new and legacy APIs failed")
    logging.error(f"New API result: {result}")
    logging.error(f"Legacy API result: {legacy_result}")
    
    return False

def try_simple_text_post(access_token: str, content: str) -> dict:
    """Try simple text post for debugging"""
    return create_linkedin_post_new_api(access_token, content)