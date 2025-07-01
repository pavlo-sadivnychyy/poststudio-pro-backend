from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import requests
import os
import jwt
import datetime
from urllib.parse import urlencode
from app.models.database import get_db
from app.services.user_service import create_or_update_user

router = APIRouter()

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "your_client_secret")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey")

REDIRECT_URI = "https://poststudio-pro-backend-production.up.railway.app/auth/linkedin/callback"

# Use environment variable for frontend URL with fallback
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.get("/linkedin/login")
def linkedin_login():
    # Use modern OpenID Connect scopes
    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20email"
        f"&state=linkedin_oauth"
    )
    print(f"Generated LinkedIn auth URL: {linkedin_auth_url}")  # Debug log
    return RedirectResponse(linkedin_auth_url)

@router.get("/linkedin/callback")
def linkedin_callback(request: Request, db: Session = Depends(get_db), code: str = None, state: str = None, error: str = None, error_description: str = None):
    """
    Handle LinkedIn OAuth callback with comprehensive error handling
    """
    try:
        # Log all query parameters for debugging
        print(f"LinkedIn callback received:")
        print(f"  code: {code}")
        print(f"  state: {state}")
        print(f"  error: {error}")
        print(f"  error_description: {error_description}")
        print(f"  all params: {dict(request.query_params)}")
        
        # Check for LinkedIn OAuth errors first
        if error:
            error_msg = f"LinkedIn OAuth error: {error}"
            if error_description:
                error_msg += f" - {error_description}"
            
            print(f"LinkedIn OAuth error: {error_msg}")
            error_params = urlencode({
                "error": "linkedin_oauth_error", 
                "message": error_msg
            })
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        # Check if code parameter is missing
        if not code:
            print("Missing code parameter in LinkedIn callback")
            error_params = urlencode({
                "error": "missing_code", 
                "message": "Authorization code not received from LinkedIn"
            })
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        # Validate state parameter
        if state != "linkedin_oauth":
            print(f"Invalid state parameter: {state}")
            error_params = urlencode({
                "error": "invalid_state", 
                "message": "Invalid state parameter - possible CSRF attack"
            })
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        print(f"Processing LinkedIn OAuth with code: {code[:10]}...")

        # Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        print("Requesting access token from LinkedIn...")
        token_res = requests.post(token_url, data=token_data, headers=headers)
        
        print(f"Token response status: {token_res.status_code}")
        print(f"Token response: {token_res.text}")

        if token_res.status_code != 200:
            error_params = urlencode({
                "error": "token_request_failed",
                "message": f"LinkedIn token request failed: {token_res.status_code}"
            })
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        token_json = token_res.json()
        access_token = token_json.get("access_token")

        if not access_token:
            print(f"No access token in response: {token_json}")
            error_params = urlencode({
                "error": "no_access_token",
                "message": "No access token received from LinkedIn"
            })
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        print("Successfully obtained access token, fetching profile...")

        # Get user profile using OpenID Connect
        profile_res = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        print(f"Profile response status: {profile_res.status_code}")

        if profile_res.status_code != 200:
            print(f"Profile request failed: {profile_res.text}")
            error_params = urlencode({
                "error": "profile_request_failed",
                "message": f"Failed to get LinkedIn profile: {profile_res.status_code}"
            })
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        profile = profile_res.json()
        print(f"Profile data: {profile}")

        # With OpenID Connect, email is included in the userinfo response
        email = profile.get("email")
        if not email:
            print("No email in OpenID Connect response")
            error_params = urlencode({
                "error": "email_not_found",
                "message": "Email not found in LinkedIn profile"
            })
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        print(f"Extracted email: {email}")

        # Get name from OpenID Connect response
        full_name = profile.get("name", "")
        
        # If no name, use email prefix
        if not full_name:
            full_name = email.split("@")[0]

        print(f"User name: {full_name}")

        # Create LinkedIn profile URL using 'sub' (subject) from OpenID Connect
        linkedin_id = profile.get("sub", "")
        linkedin_profile_url = f"https://www.linkedin.com/in/{linkedin_id}" if linkedin_id else None

        print(f"Creating/updating user with LinkedIn ID: {linkedin_id}")

        # Create or update user in database
        user = create_or_update_user(
            db,
            linkedin_id=linkedin_id,
            name=full_name,
            email=email,
            access_token=access_token,
            linkedin_profile=linkedin_profile_url
        )

        print(f"User created/updated with ID: {user.id}")

        # Generate JWT token
        jwt_payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")

        print(f"Generated JWT token for user {user.id}")

        # Redirect to frontend with token
        params = urlencode({"token": jwt_token})
        redirect_url = f"{FRONTEND_URL}?{params}"

        print(f"Redirecting to: {redirect_url}")
        return RedirectResponse(redirect_url)

    except Exception as e:
        print(f"LinkedIn callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Redirect to frontend with generic error
        error_params = urlencode({
            "error": "internal_server_error", 
            "message": str(e)
        })
        return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

# Add debug endpoint to check configuration
@router.get("/linkedin/config")
def linkedin_config():
    return JSONResponse({
        "client_id": CLIENT_ID[:10] + "..." if CLIENT_ID else "Not set",
        "redirect_uri": REDIRECT_URI,
        "frontend_url": FRONTEND_URL,
        "has_client_secret": bool(CLIENT_SECRET and CLIENT_SECRET != "your_client_secret"),
        "has_jwt_secret": bool(JWT_SECRET and JWT_SECRET != "supersecretjwtkey")
    })

# Add test endpoint to check if the callback URL is working
@router.get("/linkedin/test")
def test_callback():
    return JSONResponse({
        "message": "LinkedIn OAuth router is working",
        "redirect_uri": REDIRECT_URI,
        "frontend_url": FRONTEND_URL
    })