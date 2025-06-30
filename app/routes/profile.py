from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_profile():
    return {"name": "John Doe", "email": "john@example.com"}

@router.put("/")
def update_profile():
    return {"message": "Profile updated"}