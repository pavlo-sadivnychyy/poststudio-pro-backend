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
        else:
            logging.error(f"❌ Failed to get LinkedIn profile: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        logging.error(f"❌ Exception getting LinkedIn profile: {e}")
        return {}

def post_linkedin_content(access_token: str, content: str) -> bool:
    """Post the given content to LinkedIn using the user's access token"""
    
    # First, get the user's profile to get their person URN
    logging.info("📝 Starting LinkedIn post process...")
    
    profile_info = get_linkedin_profile_info(access_token)
    if not profile_info or 'id' not in profile_info:
        logging.error("❌ Failed to get LinkedIn profile information")
        return False
    
    person_urn = f"urn:li:person:{profile_info['id']}"
    logging.info(f"👤 Using person URN: {person_urn}")
    
    # Try the newer LinkedIn API first (v2/shares)
    success = try_shares_api(access_token, person_urn, content)
    if success:
        return True
    
    # Fallback to ugcPosts API
    logging.info("🔄 Trying ugcPosts API as fallback...")
    return try_ugc_posts_api(access_token, person_urn, content)

def try_shares_api(access_token: str, person_urn: str, content: str) -> bool:
    """Try posting using the v2/shares API"""
    url = "https://api.linkedin.com/v2/shares"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
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
        logging.info("📤 Attempting to post using shares API...")
        logging.info(f"Shares API payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        logging.info(f"Shares API response: {response.status_code}")
        logging.info(f"Shares API response text: {response.text}")
        
        if response.status_code in [200, 201]:
            logging.info("✅ LinkedIn post created successfully using shares API!")
            return True
        else:
            logging.error(f"❌ Shares API failed: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Exception with shares API: {e}")
        return False

def try_ugc_posts_api(access_token: str, person_urn: str, content: str) -> bool:
    """Try posting using the ugcPosts API"""
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
        logging.info("📤 Attempting to post using ugcPosts API...")
        logging.info(f"UGC API payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        logging.info(f"UGC API response: {response.status_code}")
        logging.info(f"UGC API response text: {response.text}")
        
        if response.status_code == 201:
            logging.info("✅ LinkedIn post created successfully using ugcPosts API!")
            return True
        else:
            logging.error(f"❌ UGC API failed: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Exception with ugcPosts API: {e}")
        return False

def verify_linkedin_permissions(access_token: str) -> dict:
    """Verify what permissions the access token has"""
    url = "https://api.linkedin.com/v2/introspection"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to verify permissions: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        logging.error(f"Exception verifying permissions: {e}")
        return {}