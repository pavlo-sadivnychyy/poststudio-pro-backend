import requests
import logging

def get_linkedin_profile_info(access_token: str) -> dict:
    """Get LinkedIn profile information to retrieve the person URN"""
    url = "https://api.linkedin.com/v2/people/~"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to get LinkedIn profile: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        logging.error(f"Exception getting LinkedIn profile: {e}")
        return {}

def post_linkedin_content(access_token: str, content: str) -> bool:
    """Post the given content to LinkedIn using the user's access token"""
    
    # First, get the user's profile to get their person URN
    profile_info = get_linkedin_profile_info(access_token)
    if not profile_info or 'id' not in profile_info:
        logging.error("Failed to get LinkedIn profile information")
        return False
    
    person_urn = f"urn:li:person:{profile_info['id']}"
    
    url = "https://api.linkedin.com/v2/ugcPosts"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # Build the payload with correct LinkedIn API format
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
        logging.info(f"Attempting to post to LinkedIn for user {person_urn}")
        logging.info(f"Payload: {payload}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        logging.info(f"LinkedIn API Response: {response.status_code}")
        logging.info(f"Response text: {response.text}")
        
        if response.status_code == 201:
            logging.info("LinkedIn post created successfully!")
            return True
        else:
            logging.error(f"LinkedIn post failed: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Exception posting to LinkedIn: {e}")
        return False