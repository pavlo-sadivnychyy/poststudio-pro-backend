import requests
import logging

def post_linkedin_content(access_token: str, content: str) -> bool:
    """Post the given content to LinkedIn using the user’s access token"""

    url = "https://api.linkedin.com/v2/ugcPosts"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # Build the body per LinkedIn API requirements (you will need to adapt this)
    payload = {
        "author": "urn:li:person:YOUR_PERSON_URN",  # You need to store/get the correct URN
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "CONNECTIONS"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            return True
        else:
            logging.error(f"LinkedIn post failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logging.error(f"Exception posting to LinkedIn: {e}")
        return False
