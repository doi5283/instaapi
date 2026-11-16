from fastapi import APIRouter, HTTPException
from schemas import UserCreate, UserOut
from deps import SessionDep, password_hash
from models import User
from sqlalchemy import select

router = APIRouter(prefix='/api/auth', tags=['auth'])

@router.post('/signup', response_model=UserOut)
def signup(data: UserCreate, db: SessionDep):
    user = db.scalar(select(User).where(User.username == data.username)) # User 테이블 안 User컬럼

    if user:
        raise HTTPException(status_code=409, detail='이미 사용중인 아이디입니다.')
    
    hashed_pw = password_hash.hash(data.password)
    user = User(username=data.username, password_hash=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)  # 저장 후 id 등 DB가 정한 값을 다시 읽어옴
    
    return user
