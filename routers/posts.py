from fastapi import APIRouter, HTTPException
from deps import SessionDep, postDep, CurrentUserDep, MyPostDep
from sqlalchemy import select
from models import Post
from schemas import PostOut, PostCreate, PostUpdate # 데이터리턴, 데이터 생성, 데이터 수정

router = APIRouter(prefix='/api/posts', tags=['posts'])


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
def post_create(data: PostCreate, db: SessionDep, user:CurrentUserDep): # user:currentUserDep = deps.py 작성/ token 값을 기반으로 가져옴
    post = Post(content=data.content, user_id=user.id) # 딕셔너리로 들어올 것
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
# def post_update(post: postDep, data: PostUpdate, db: SessionDep, user: CurrentUserDep): # data: 수정용
def post_update(post: MyPostDep, data: PostUpdate, db: SessionDep): # 코드 줄이기
        
    # if post.user_id != user.id: # 다르면 / => 권한없음
    #     raise HTTPException(status_code=403, detail='내 글만 수정 가능합니다.')
    # = MyPostDep 으로 대체
    
    post.content= data.content # 기존 컨텐츠 = 새로 들어온 컨텐츠 (덮어씌우기)
    db.commit()
    return post


@router.delete('/{post_id}', status_code=204) # 삭제후 보여줄 데이터x 상태코드 보여줌(204: 성공하긴 했지만 보여줄 데이터는 없다)/ 안넣어도 상관은 없음. 200으로 나가도 괜찮음
# def post_delete(post: postDep, db: SessionDep):
def post_delete(post: MyPostDep, db: SessionDep):
    db.delete(post)
    db.commit()
    
    #return None # 파이썬 기본 규칙(return 작성 안하면 none)








