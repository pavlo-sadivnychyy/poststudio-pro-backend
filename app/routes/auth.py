from fastapi import APIRouter, Depends, HTTPException
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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

@router.get("/linkedin/login")
def linkedin_login():
    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=r_liteprofile%20r_emailaddress"
        f"&state=linkedin_oauth"
    )
    return RedirectResponse(linkedin_auth_url)

@router.get("/linkedin/callback")
def linkedin_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    try:
        if state != "linkedin_oauth":
            raise HTTPException(status_code=400, detail="Invalid state parameter")

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
        token_res = requests.post(token_url, data=token_data, headers=headers)

        if token_res.status_code != 200:
            # Redirect to frontend with error
            error_params = urlencode({"error": "token_request_failed"})
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        token_json = token_res.json()
        access_token = token_json.get("access_token")

        if not access_token:
            # Redirect to frontend with error
            error_params = urlencode({"error": "no_access_token"})
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        # Get user profile from LinkedIn
        profile_res = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if profile_res.status_code != 200:
            # Redirect to frontend with error
            error_params = urlencode({"error": "profile_request_failed"})
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        profile = profile_res.json()

        # Get user email
        email_res = requests.get(
            "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if email_res.status_code != 200:
            # Redirect to frontend with error
            error_params = urlencode({"error": "email_request_failed"})
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        email_data = email_res.json()
        
        # Safely extract email
        try:
            email = email_data["elements"][0]["handle~"]["emailAddress"]
        except (KeyError, IndexError):
            error_params = urlencode({"error": "email_extraction_failed"})
            return RedirectResponse(f"{FRONTEND_URL}?{error_params}")

        # Create full name safely
        first_name = profile.get("localizedFirstName", "")
        last_name = profile.get("localizedLastName", "")
        full_name = f"{first_name} {last_name}".strip()
        
        # If no name, use email prefix
        if not full_name:
            full_name = email.split("@")[0]

        # Create LinkedIn profile URL
        linkedin_profile_url = f"https://www.linkedin.com/in/{profile.get('id', '')}"

        # Create or update user in database
        user = create_or_update_user(
            db,
            linkedin_id=profile.get("id"),
            name=full_name,
            email=email,
            access_token=access_token,
            linkedin_profile=linkedin_profile_url
        )

        # Generate JWT token
        jwt_payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")

        # Redirect to frontend with token
        params = urlencode({"token": jwt_token})
        redirect_url = f"{FRONTEND_URL}?{params}"

        return RedirectResponse(redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        print(f"LinkedIn callback error: {str(e)}")
        # Redirect to frontend with generic error
        error_params = urlencode({"error": "internal_server_error", "message": str(e)})
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