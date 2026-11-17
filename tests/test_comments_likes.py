import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ======================================================================
# 사용하는 API 주소 (routers/comments.py, routers/likes.py 기준)
#   댓글 목록 / 작성 : GET, POST     /api/posts/{post_id}/comments
#   댓글 수정 / 삭제 : PATCH, DELETE /api/comments/{comment_id}
#   하트 누르기      : POST   /api/posts/{post_id}/likes   (이미 눌렀으면 409)
#   하트 취소        : DELETE /api/posts/{post_id}/likes
#   글 상세(GET /api/posts/{id}) 응답의 'likes'는 [{'user_id': ..}, ...] 모양
# ======================================================================
def comments_url(post_id):
    return f'/api/posts/{post_id}/comments'


def comment_url(comment_id):
    return f'/api/comments/{comment_id}'


def likes_url(post_id):
    return f'/api/posts/{post_id}/likes'


# ---------- 도우미 ----------
def login(username, password='pw1234'):
    res = client.post('/api/auth/login', data={'username': username, 'password': password})
    token = res.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def user_id_of(username):
    """로그인해서 /me로 그 사람의 id를 알아냄. (likes에는 user_id만 들어있어서 필요)"""
    return client.get('/api/auth/me', headers=login(username)).json()['id']


def like_user_ids(post_id):
    """글 상세에서 하트 누른 사람들의 user_id 목록을 뽑아줌."""
    likes = client.get(f'/api/posts/{post_id}').json()['likes']
    return [like['user_id'] for like in likes]


@pytest.fixture
def make_post():
    """글을 만들어주고, 테스트가 끝나면 지워줌. (글을 지우면 딸린 댓글·하트도 같이 지워짐)"""
    created = []  # (post_id, 작성자)

    def _make(username='alice'):
        res = client.post('/api/posts', json={'content': '댓글·하트 테스트용 글'}, headers=login(username))
        assert res.status_code == 201
        post_id = res.json()['id']
        created.append((post_id, username))
        return post_id

    yield _make

    for post_id, username in created:
        client.delete(f'/api/posts/{post_id}', headers=login(username))


@pytest.fixture
def make_comment():
    """댓글을 만들어주고, 테스트가 끝나면 지워줌."""
    created = []  # (comment_id, 작성자)

    def _make(post_id, username='bob', content='테스트 댓글'):
        res = client.post(comments_url(post_id), json={'content': content}, headers=login(username))
        assert res.status_code == 201
        comment_id = res.json()['id']
        created.append((comment_id, username))
        return comment_id

    yield _make

    # 이미 지워진 댓글이면 404가 나오지만 무시함 (글을 지울 때 댓글도 같이 지워지니 이중 안전장치)
    for comment_id, username in created:
        client.delete(comment_url(comment_id), headers=login(username))


@pytest.fixture
def make_like():
    """하트를 눌러주고, 테스트가 끝나면 취소해줌."""
    created = []  # (post_id, 누른 사람)

    def _make(post_id, username='bob'):
        res = client.post(likes_url(post_id), headers=login(username))
        assert res.status_code == 201
        created.append((post_id, username))

    yield _make

    for post_id, username in created:
        client.delete(likes_url(post_id), headers=login(username))  # 이미 취소했으면 에러가 나도 무시


# ---------- 댓글 ----------
# 1. 댓글을 쓰면 201이고, 그 글의 댓글 목록에 보인다
def test_comment_create_201_and_listed(make_post):
    post_id = make_post('alice')

    # 201 응답을 직접 확인해야 해서 make_comment 대신 직접 요청함
    res = client.post(comments_url(post_id), json={'content': '좋은 글이네요'}, headers=login('bob'))
    assert res.status_code == 201
    comment_id = res.json()['id']

    try:
        listed = client.get(comments_url(post_id))
        assert listed.status_code == 200
        assert comment_id in [c['id'] for c in listed.json()]
    finally:
        client.delete(comment_url(comment_id), headers=login('bob'))  # 끝나면 지움


# 2. 내 댓글을 고치면 200이고, 내용이 바뀐다
def test_comment_update_mine_200(make_post, make_comment):
    post_id = make_post('alice')
    comment_id = make_comment(post_id, 'bob', '원래 내용')

    res = client.patch(comment_url(comment_id), json={'content': '고친 내용'}, headers=login('bob'))
    assert res.status_code == 200
    assert res.json()['content'] == '고친 내용'

    # 목록에서도 바뀌었는지 확인
    listed = client.get(comments_url(post_id)).json()
    assert [c['content'] for c in listed if c['id'] == comment_id] == ['고친 내용']


# 3. 남의 댓글을 고치거나(PATCH) 지우면(DELETE) 403
def test_comment_update_others_403(make_post, make_comment):
    post_id = make_post('alice')
    comment_id = make_comment(post_id, 'bob', '밥의 댓글')

    res = client.patch(comment_url(comment_id), json={'content': '앨리스가 고침'}, headers=login('alice'))
    assert res.status_code == 403

    # 실제로 안 바뀌었는지 확인
    listed = client.get(comments_url(post_id)).json()
    assert [c['content'] for c in listed if c['id'] == comment_id] == ['밥의 댓글']


def test_comment_delete_others_403(make_post, make_comment):
    post_id = make_post('alice')
    comment_id = make_comment(post_id, 'bob')

    res = client.delete(comment_url(comment_id), headers=login('alice'))
    assert res.status_code == 403

    # 아직 남아있어야 함
    listed = client.get(comments_url(post_id)).json()
    assert comment_id in [c['id'] for c in listed]


# 4. 없는 댓글을 고치면 404
def test_comment_update_missing_404():
    res = client.patch(comment_url(999999), json={'content': 'x'}, headers=login('bob'))
    assert res.status_code == 404


# 5. 내 댓글을 지우면 204이고, 목록에서 사라진다
def test_comment_delete_mine_204(make_post, make_comment):
    post_id = make_post('alice')
    comment_id = make_comment(post_id, 'bob')

    res = client.delete(comment_url(comment_id), headers=login('bob'))
    assert res.status_code == 204

    listed = client.get(comments_url(post_id)).json()
    assert comment_id not in [c['id'] for c in listed]


# ---------- 하트 ----------
# 6. 하트를 누르면 201이고, 글의 likes에 내가 있다
def test_like_201_and_in_likes(make_post):
    post_id = make_post('alice')

    res = client.post(likes_url(post_id), headers=login('bob'))
    assert res.status_code == 201

    try:
        assert user_id_of('bob') in like_user_ids(post_id)
    finally:
        client.delete(likes_url(post_id), headers=login('bob'))


# 7. 이미 누른 하트를 또 누르면 409
def test_like_twice_409(make_post, make_like):
    post_id = make_post('alice')
    make_like(post_id, 'bob')  # 첫 번째 (201 확인 포함)

    res = client.post(likes_url(post_id), headers=login('bob'))
    assert res.status_code == 409

    # 두 번 들어가지 않고 한 번만 있어야 함
    assert like_user_ids(post_id).count(user_id_of('bob')) == 1


# 8. 하트를 취소하면 200이고, likes에서 내가 빠진다
def test_unlike_200_and_removed(make_post, make_like):
    post_id = make_post('alice')
    make_like(post_id, 'bob')
    make_like(post_id, 'carol')  # 다른 사람 하트는 남아있는지도 확인하려고

    res = client.delete(likes_url(post_id), headers=login('bob'))
    assert res.status_code == 200

    ids = like_user_ids(post_id)
    assert user_id_of('bob') not in ids
    assert user_id_of('carol') in ids
