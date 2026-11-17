import uuid
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ---------- 도우미 ----------
def login(username, password='pw1234'):
    res = client.post('/api/auth/login', data={'username': username, 'password': password})
    token = res.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def unique_name():
    # username은 3~20자 규칙이 있어서 uuid를 8자리만 잘라 씀 (u_ + 8자 = 10자)
    return 'u_' + uuid.uuid4().hex[:8]


@pytest.fixture
def make_post():
    """게시물을 만들어주고, 테스트가 끝나면 만든 게시물을 전부 지워줌."""
    created = []  # (post_id, 작성자 이름)

    def _make(username='alice', content='규칙 테스트용 글'):
        res = client.post('/api/posts', json={'content': content}, headers=login(username))
        assert res.status_code == 201
        post_id = res.json()['id']
        created.append((post_id, username))
        return post_id

    yield _make

    # yield 아래는 테스트가 끝난 뒤에 실행됨 (정리 단계)
    for post_id, username in created:
        client.delete(f'/api/posts/{post_id}', headers=login(username))  # 이미 지워졌으면 404라 무시


# ---------- 가입 규칙 ----------
def test_signup_success():
    res = client.post('/api/auth/signup', json={'username': unique_name(), 'password': 'pw1234'})
    assert res.status_code == 201
    assert 'password' not in res.json()  # 비밀번호는 응답에 나오면 안 됨


def test_signup_duplicate_409():
    name = unique_name()
    first = client.post('/api/auth/signup', json={'username': name, 'password': 'pw1234'})
    assert first.status_code == 201

    second = client.post('/api/auth/signup', json={'username': name, 'password': 'pw1234'})
    assert second.status_code == 409


def test_signup_existing_seed_user_409():
    res = client.post('/api/auth/signup', json={'username': 'alice', 'password': 'pw1234'})
    assert res.status_code == 409


def test_signup_username_too_short_422():
    res = client.post('/api/auth/signup', json={'username': 'ab', 'password': 'pw1234'})
    assert res.status_code == 422


def test_signup_username_too_long_422():
    res = client.post('/api/auth/signup', json={'username': 'a' * 21, 'password': 'pw1234'})
    assert res.status_code == 422


def test_signup_password_too_short_422():
    res = client.post('/api/auth/signup', json={'username': unique_name(), 'password': '123'})
    assert res.status_code == 422


# ---------- 로그인 규칙 ----------
def test_login_wrong_password_401():
    res = client.post('/api/auth/login', data={'username': 'alice', 'password': 'wrong'})
    assert res.status_code == 401


def test_login_unknown_user_401():
    res = client.post('/api/auth/login', data={'username': unique_name(), 'password': 'pw1234'})
    assert res.status_code == 401


def test_me_returns_logged_in_user():
    res = client.get('/api/auth/me', headers=login('bob'))
    assert res.status_code == 200
    assert res.json()['username'] == 'bob'


def test_me_without_token_401():
    assert client.get('/api/auth/me').status_code == 401


# ---------- 게시물 작성 규칙 ----------
def test_create_without_login_401():
    res = client.post('/api/posts', json={'content': 'hello'})
    assert res.status_code == 401


def test_create_with_bad_token_401():
    res = client.post('/api/posts', json={'content': 'hello'}, headers={'Authorization': 'Bearer abc.def.ghi'})
    assert res.status_code == 401


def test_create_empty_content_422():
    res = client.post('/api/posts', json={'content': ''}, headers=login('alice'))
    assert res.status_code == 422


def test_create_content_too_long_422():
    res = client.post('/api/posts', json={'content': 'a' * 501}, headers=login('alice'))
    assert res.status_code == 422


def test_create_author_is_logged_in_user(make_post):
    post_id = make_post('alice')
    res = client.get(f'/api/posts/{post_id}')
    assert res.json()['user']['username'] == 'alice'  # 작성자는 토큰으로 정해짐


# ---------- 수정 / 삭제 규칙 ----------
def test_update_my_post(make_post):
    post_id = make_post('alice')
    res = client.patch(f'/api/posts/{post_id}', json={'content': '수정됨'}, headers=login('alice'))
    assert res.status_code == 200
    assert res.json()['content'] == '수정됨'


def test_update_others_post_403(make_post):
    post_id = make_post('alice')
    res = client.patch(f'/api/posts/{post_id}', json={'content': '남의 글 수정'}, headers=login('bob'))
    assert res.status_code == 403
    # 실제로 안 바뀌었는지도 확인
    assert client.get(f'/api/posts/{post_id}').json()['content'] == '규칙 테스트용 글'


def test_update_empty_content_422(make_post):
    post_id = make_post('alice')
    res = client.patch(f'/api/posts/{post_id}', json={'content': ''}, headers=login('alice'))
    assert res.status_code == 422


def test_update_without_login_401(make_post):
    post_id = make_post('alice')
    res = client.patch(f'/api/posts/{post_id}', json={'content': '비로그인 수정'})
    assert res.status_code == 401


def test_update_missing_post_404():
    res = client.patch('/api/posts/999999', json={'content': 'x'}, headers=login('alice'))
    assert res.status_code == 404


def test_delete_others_post_403(make_post):
    post_id = make_post('alice')
    res = client.delete(f'/api/posts/{post_id}', headers=login('bob'))
    assert res.status_code == 403
    assert client.get(f'/api/posts/{post_id}').status_code == 200  # 아직 남아있어야 함


def test_delete_without_login_401(make_post):
    post_id = make_post('alice')
    res = client.delete(f'/api/posts/{post_id}')
    assert res.status_code == 401


def test_delete_my_post(make_post):
    post_id = make_post('bob')
    res = client.delete(f'/api/posts/{post_id}', headers=login('bob'))
    assert res.status_code == 204
    assert client.get(f'/api/posts/{post_id}').status_code == 404
