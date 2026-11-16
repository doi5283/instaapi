from fastapi import APIRouter
from deps import SessionDep
from sqlalchemy import select
from models import Post
from schemas import PostOut

router = APIRouter(prefix='/api/posts')


@router.get('', response_model=list[PostOut]) # prefix
def post_list(db: SessionDep):
    # db.scalars(select(Post))# 테이블(Post)에서 전체데이터 가져오기
    posts = db.scalars(select(Post).order_by(Post.created_at.desc())).all()
    
    # for post in posts: # postman 확인용
    #     print(post.user.username)
        
    return posts




