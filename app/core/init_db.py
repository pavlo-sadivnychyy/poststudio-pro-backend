from app.models.database import Base, engine
from app.models.user import User
from app.models.subscription import Subscription

def init_db():
    Base.metadata.create_all(bind=engine)