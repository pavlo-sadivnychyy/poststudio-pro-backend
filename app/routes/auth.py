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
FRONTEND_URL = "http://localhost:3000"  # заміни на URL фронтенду

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

        # Отримуємо профіль користувача LinkedIn (r_liteprofile)
        profile_res = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if profile_res.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get profile: {profile_res.status_code} - {profile_res.text}"
            )

        profile = profile_res.json()

        # Отримуємо email користувача
        email_res = requests.get(
            "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if email_res.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get email: {email_res.status_code} - {email_res.text}"
            )

        email_data = email_res.json()
        email = email_data["elements"][0]["handle~"]["emailAddress"]

        # Формуємо посилання на LinkedIn профіль (можна кастомізувати)
        linkedin_profile_url = f"https://www.linkedin.com/in/{profile.get('id')}"

        user = create_or_update_user(
            db,
            linkedin_id=profile.get("id"),
            name=profile.get("localizedFirstName") + " " + profile.get("localizedLastName"),
            email=email,
            access_token=access_token,
            linkedin_profile=linkedin_profile_url  # Додаємо нове поле
        )

        jwt_payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")

        params = urlencode({"token": jwt_token})
        redirect_url = f"{FRONTEND_URL}?{params}"

        return RedirectResponse(redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        print(f"LinkedIn callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
