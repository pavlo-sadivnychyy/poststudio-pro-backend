from fastapi import APIRouter, Depends, HTTPException
from app.services.subscription_service import require_subscription
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests
from app.models.database import get_db
from app.models.user import User

router = APIRouter()

class PostData(BaseModel):
    user_id: int
    text: str

class CommentData(BaseModel):
    user_id: int
    text: str
    parent_post_urn: str

def get_user_token(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.access_token

@router.post("/post")
def post_to_linkedin(data: PostData, db: Session = Depends(get_db), ok: bool = Depends(lambda: require_subscription(data.user_id))):
    token = get_user_token(data.user_id, db)

    # Get LinkedIn URN (author ID)
    me = requests.get("https://api.linkedin.com/v2/me", headers={
        "Authorization": f"Bearer {token}"
    }).json()
    author_urn = f"urn:li:person:{me['id']}"

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": data.text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    res = requests.post("https://api.linkedin.com/v2/ugcPosts", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }, json=payload)

    if res.status_code != 201:
        raise HTTPException(status_code=500, detail=f"Failed to post: {res.text}")
    return {"status": "Posted", "url": res.headers.get("x-restli-id")}

@router.post("/comment")
def comment_on_linkedin(data: CommentData, db: Session = Depends(get_db), ok: bool = Depends(lambda: require_subscription(data.user_id))):
    token = get_user_token(data.user_id, db)

    payload = {
        "actor": f"urn:li:person:{requests.get('https://api.linkedin.com/v2/me', headers={ 'Authorization': f'Bearer {token}' }).json()['id']}",
        "object": data.parent_post_urn,
        "message": {"text": data.text}
    }

    res = requests.post("https://api.linkedin.com/v2/socialActions/{}/comments".format(data.parent_post_urn),
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        },
                        json=payload)

    if res.status_code not in [201, 200]:
        raise HTTPException(status_code=500, detail=f"Failed to comment: {res.text}")
    return {"status": "Commented"}