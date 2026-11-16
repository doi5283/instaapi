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
    user_id: int
    
    
class PostUpdate(BaseModel):
    content: str = Field(min_length=1, max_lenght=500)
    
    
    
