from pydantic import BaseModel, Field
from datetime import datetime


#user 구조
class UserOut(BaseModel):
    id: int
    username: str
    
#user 생성
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=4)


class PostOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    user: UserOut #PostOut 데이터 안 user 컬럼 안에 UserOut 데이터를 중첩
    

class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    # user_id: int # 현재 로그인한 user id
    # 주석처리 이유: 처음에는 작성자 id를 직접 보냈는데 마지막 커밋(로그인한 사람만 글쓰기)부터는 토큰을 보고 서버가 알아내도록 바꿔서 받을 필요가 없어진 것
    
    
class PostUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class Token(BaseModel):
    access_token : str #우리가 만들 jwt 토큰
    token_type: str #발행된 토큰 형태
    
    
