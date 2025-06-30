from fastapi import APIRouter

router = APIRouter()

@router.get("/schedule")
def get_schedule():
    return {"schedule": ["Monday 9 AM", "Thursday 1 PM"]}

@router.post("/save")
def save_schedule():
    return {"message": "Schedule saved"}