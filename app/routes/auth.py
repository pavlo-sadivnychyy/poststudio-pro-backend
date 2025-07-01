from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import requests
import os
import jwt
import datetime
from urllib.parse import quote
from app.models.database import get_db
from app.services.user_service import create_or_update_user

router = APIRouter()

# Environment variables
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "your_client_secret")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey")

# Hardcoded redirect URI (since you don't have env variable)
REDIRECT_URI = "https://poststudio-pro-backend-production.up.railway.app/auth/linkedin/callback"

@router.get("/linkedin/login")
def linkedin_login():
    """
    Initiate LinkedIn OAuth login using Sign In with LinkedIn v2
    """
    # Use the new LinkedIn Sign In scopes
    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20email"  # Updated to use OpenID Connect scopes
        f"&state=linkedin_oauth"
    )
    
    print(f"Generated LinkedIn URL: {linkedin_auth_url}")
    return RedirectResponse(linkedin_auth_url)

@router.get("/linkedin/callback")
def linkedin_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    """
    Handle LinkedIn OAuth callback
    """
    try:
        # Verify state parameter (optional but recommended)
        if state != "linkedin_oauth":
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Exchange authorization code for access token
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
            raise HTTPException(
                status_code=400, 
                detail=f"Token request failed: {token_res.status_code} - {token_res.text}"
            )
        
        token_json = token_res.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to get access token: {token_json}"
            )
        
        # Get user profile using OpenID Connect
        profile_res = requests.get(
            "https://api.linkedin.com/v2/userinfo",  # Updated endpoint
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if profile_res.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get profile: {profile_res.status_code} - {profile_res.text}"
            )
        
        profile = profile_res.json()
        
        # With OpenID Connect, email is included in the userinfo response
        email = profile.get("email")
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Could not extract email from LinkedIn response"
            )
        
        # Create or update user in database
        user = create_or_update_user(
            db,
            linkedin_id=profile.get("sub"),  # Use 'sub' for OpenID Connect
            name=profile.get("name", ""),
            email=email,
            access_token=access_token
        )
        
        # Generate JWT token for frontend
        jwt_payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")
        
        # Return success response with token and user data
        return JSONResponse({
            "message": "Login successful",
            "token": jwt_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"LinkedIn callback error: {str(e)}")  # Debug
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/linkedin/test")
def test_linkedin_config():
    """
    Test endpoint to verify LinkedIn configuration
    """
    return JSONResponse({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "has_client_secret": bool(CLIENT_SECRET and CLIENT_SECRET != "your_client_secret"),
        "has_jwt_secret": bool(JWT_SECRET and JWT_SECRET != "supersecretjwtkey"),
        "client_id_length": len(CLIENT_ID) if CLIENT_ID else 0,
        "client_secret_length": len(CLIENT_SECRET) if CLIENT_SECRET else 0
    })

@router.get("/linkedin/debug")
def debug_linkedin_auth():
    """
    Debug endpoint to check the authorization URL
    """
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=r_liteprofile%20r_emailaddress"
        f"&state=linkedin_oauth"
    )
    
    return JSONResponse({
        "auth_url": auth_url,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "r_liteprofile r_emailaddress"
    })