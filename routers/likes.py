from fastapi import APIRouter, HTTPException
from deps import PostDep, CurrentUserDep, SessionDep
from models import Like
from schemas import PostOut

router = APIRouter(prefix='/api/posts/{post_id}/likes', tags=['likes'])


# 좋아요
@router.post('', response_model=PostOut)
def like_create(post: PostDep, db: SessionDep, user: CurrentUserDep):
    if db.get(Like, (user.id, post.id)): # Like: user_id + post_id
        raise HTTPException(status_code=409, detail='이미 좋아요를 눌렀습니다.')
    # 좋아요 x면?
    db.add(Like(user_id=user.id, post_id=post.id))
    db.commit() 
    return post # 게시물 정보 return(가장 최신화 좋아요 수) - 화면 반환(front)


# 좋아요 삭제
@router.delete('', response_model=PostOut) 
def like_delete(post: PostDep, db: SessionDep, user: CurrentUserDep):
    
    like = db.get(Like, (user.id, post.id)) # 좋아요 찾기
    
    if like is None:
        raise HTTPException(status_code=404, detail='좋아요를 누르지 않았습니다.')
    
    db.delete(like)
    db.commit()
    return post