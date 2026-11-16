from fastapi import APIRouter
from deps import SessionDep, postDep
from sqlalchemy import select
from models import Post
from schemas import PostOut, PostCreate, PostUpdate # 데이터리턴, 데이터 생성, 데이터 수정

router = APIRouter(prefix='/api/posts')


@router.get('', response_model=list[PostOut]) # prefix / 게시물 여러개
def post_list(db: SessionDep): # 전체 테이블
    # db.scalars(select(Post))# 테이블(Post)에서 전체데이터 가져오기
    posts = db.scalars(select(Post).order_by(Post.created_at.desc())).all()
    
    # for post in posts: # postman 확인용
    #     print(post.user.username)
        
    return posts


@router.get('/{post_id}', response_model=PostOut)# 게시물 1개
# def post_detail(post_id: int, db: SessionDep):
def post_detail(post: postDep):
    
    # post = db.get(Post, post_id)# 데이터베이스 조회 # postDep 사용으로 생략가능
    return post




@router.post('', response_model=PostOut, status_code=201) # status_code= 201 : post / get은 200
def post_create(data: PostCreate, db: SessionDep):
    post = Post(content=data.content, user_id=data.user_id) # 딕셔너리로 들어올 것
    db.add(post)
    db.commit()
    return post


## PATCH
## 지난시간방법
# /posts/create
# /posts/100
# /posts/delete
# /posts/update

## 오늘 방법 (RESTful API)
# n형태의 리소스만 작성(v형태는 crud로만 작성)
# GET /posts
# POST /posts
# PATCH /posts/10


@router.patch('/{post_id}', response_model=PostOut)
def post_update(post: postDep, data: PostUpdate, db: SessionDep): # data: 수정용
    post.content= data.content # 기존 컨텐츠 = 새로 들어온 컨텐츠 (덮어씌우기)
    db.commit()
    return post







