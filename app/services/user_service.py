from sqlalchemy.orm import Session
from app.models.user import User

def create_or_update_user(db: Session, linkedin_id: str, name: str, email: str, access_token: str):
    user = db.query(User).filter(User.linkedin_id == linkedin_id).first()
    if user:
        user.access_token = access_token
        user.name = name
        user.email = email
    else:
        user = User(
            linkedin_id=linkedin_id,
            name=name,
            email=email,
            access_token=access_token
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user