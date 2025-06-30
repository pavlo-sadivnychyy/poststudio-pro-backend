from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import requests, os
from app.models.database import get_db
from app.services.user_service import create_or_update_user

router = APIRouter()

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "your_client_secret")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/auth/linkedin/callback")

@router.get("/linkedin/login")
def linkedin_login():
    return RedirectResponse(
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=r_liteprofile%20r_emailaddress%20w_member_social"
    )

@router.get("/linkedin/callback")
def linkedin_callback(code: str, db: Session = Depends(get_db)):
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
    token_json = token_res.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return {"error": "Failed to get access token", "details": token_json}

    profile = requests.get("https://api.linkedin.com/v2/me", headers={
        "Authorization": f"Bearer {access_token}"
    }).json()
    email_data = requests.get(
        "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    email = email_data["elements"][0]["handle~"]["emailAddress"]

    user = create_or_update_user(
        db,
        linkedin_id=profile["id"],
        name=profile.get("localizedFirstName"),
        email=email,
        access_token=access_token
    )

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }