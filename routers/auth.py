from fastapi import APIRouter, HTTPException, Depends
from schemas import UserCreate, UserOut, Token
from deps import SessionDep, password_hash, create_access_token
from models import User
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

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


@router.post('/login', response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep): # OAuth2PasswordRequestForm 는 form 데이터로 넣어야함
    user = db.scalar(select(User).where(User.username == form.username)) #form 데이터에서 username 찾기

    # 유저가 없거나 비밀번호가 일치하지 않으면
    if user is None or not password_hash.verify(form.password, user.password_hash): # 방금 입력한 pw(form) + user pw 같은지 확인
        raise HTTPException(status_code=401, detail='아이디 또는 비밀번호가 틀렸습니다.') # 401: 인증오류
    token = create_access_token(user.id)
    
    return {'access_token': token, 'token_type': 'bearer'}
