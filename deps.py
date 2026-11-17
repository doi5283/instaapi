from fastapi import Depends, HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from typing import Annotated
from database import engine
from models import Post, User
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer


password_hash = PasswordHash.recommended()

def get_db():
    with Session(engine) as db:
        yield db

SessionDep = Annotated[Session, Depends(get_db)]

# 여기서부터 작성
def get_post_or_404(post_id: int, db: SessionDep):
    post = db.get(Post, post_id) # 데이터조회
    
    if post is None:
        raise HTTPException(status_code=404, detail='해당 게시물이 없습니다.')
    return post
postDep = Annotated[Post, Depends(get_post_or_404)]


SECRET_KEY = 'dev-secret'
ALGORITHM = 'HS256'
# 토큰 발행 함수
def create_access_token(user_id: int):
    exp = datetime.now(timezone.utc) + timedelta(minutes=30)
    return jwt.encode({'sub': str(user_id), 'exp': exp}, SECRET_KEY, algorithm=ALGORITHM)



oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login') #token 발행 위치
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail='토큰이 올바르지 않습니다.', headers={'WWW-Authenticate': 'Bearer'})
    
    user = db.get(User, int(payload['sub']))
    
    if user is None:
        raise HTTPException(status_code=401, detail='없는 사용자 입니다.', headers={'WWW-Authenticate': 'Bearer'})
    
    return user
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_my_post(post: PostDep, user: CurrentUserDep): # 그 게시글이 내가 만든 게시글인지 확인/ postDep: 게시물 가져오기, CurrentUserDep: 토큰에서 유저 가져오기
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail='내 글만 바꿀 수 있습니다.')
    return post #작성자 맞으면 게시글 리턴

MyPostDep = Annotated[Post, Depends(get_my_post)]