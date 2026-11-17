from fastapi import APIRouter
from deps import PostDep, CurrentUserDep, SessionDep
from schemas import CommentCreate, CommentOut
from models import Comment


router = APIRouter(prefix='/api')


@router.get('/posts/{post_id}/comments', response_model=list[CommentOut]) # 여러개 commentout
def comment_list(post: PostDep):
    return post.comments


@router.post('/posts/{post_id}/comments', response_model=CommentOut) # 한개 commentout
def comment_create(post: PostDep, db: SessionDep, user: CurrentUserDep, data: CommentCreate):
    comment = Comment(content=data.content, post_id=post.id, user_id=user.id)
    db.add(comment)
    db.commit()
    return comment


@router.patch('/comments/{comment_id}')
def comment_update():
    pass


@router.delete('/comments/{comment_id}')
def comment_delete():
    pass


