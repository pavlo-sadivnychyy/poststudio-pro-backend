from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import requests
import os
import jwt
import datetime
from app.models.database import get_db
from app.services.user_service import create_or_update_user

router = APIRouter()

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "your_client_secret")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "https://poststudio-pro-backend-production.up.railway.app/auth/linkedin/callback")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey")  # Візьми з env

@router.get("/linkedin/login")
def linkedin_login():
    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=r_liteprofile%20r_emailaddress%20w_member_social"
    )
    return RedirectResponse(linkedin_auth_url)

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
        raise HTTPException(status_code=400, detail=f"Failed to get access token: {token_json}")

    profile_res = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    profile_res.raise_for_status()
    profile = profile_res.json()

    email_res = requests.get(
        "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    email_res.raise_for_status()
    email_data = email_res.json()
    email = email_data["elements"][0]["handle~"]["emailAddress"]

    user = create_or_update_user(
        db,
        linkedin_id=profile["id"],
        name=profile.get("localizedFirstName"),
        email=email,
        access_token=access_token
    )

    # Генеруємо JWT токен для фронтенду
    jwt_payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")

    # Можна редіректити на фронтенд і передавати токен як параметр
    frontend_url = f"https://your-frontend-url.com/dashboard?token={jwt_token}"

    # Або просто повернути json з токеном
    return JSONResponse({
        "message": "Login successful",
        "token": jwt_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    })
