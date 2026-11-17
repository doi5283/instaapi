import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from main import app

client = TestClient(app)


# ---------- 도우미 ----------
def login(username, password='pw1234'):
    res = client.post('/api/auth/login', data={'username': username, 'password': password})
    token = res.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def fake_image_bytes():
    """진짜 파일 없이 메모리에서 작은 빨간 사진을 만들어줌."""
    buf = io.BytesIO()
    Image.new('RGB', (50, 50), 'red').save(buf, format='PNG')
    return buf.getvalue()


@pytest.fixture
def upload_photo():
    """사진을 올려주고, 테스트가 끝나면 서버 media 폴더에 생긴 파일을 지워줌."""
    saved = []  # media 폴더에 생긴 파일 경로

    def _upload(username='alice'):
        res = client.post(
            '/api/uploads',
            files={'photo': ('test.png', fake_image_bytes(), 'image/png')},
            headers=login(username),
        )
        assert res.status_code == 201
        image_url = res.json()['image_url']
        saved.append(Path('media') / Path(image_url).name)  # '/media/abc.jpg' -> media/abc.jpg
        return image_url

    yield _upload

    for path in saved:
        path.unlink(missing_ok=True)  # 이미 없어도 에러 안 냄


@pytest.fixture
def make_post():
    """글을 만들어주고, 테스트가 끝나면 지워줌."""
    created = []  # (post_id, 작성자)

    def _make(image_url, username='alice'):
        res = client.post(
            '/api/posts',
            json={'content': '사진 테스트용 글', 'image_url': image_url},
            headers=login(username),
        )
        assert res.status_code == 201
        post_id = res.json()['id']
        created.append((post_id, username))
        return post_id

    yield _make

    for post_id, username in created:
        client.delete(f'/api/posts/{post_id}', headers=login(username))


# 1. 사진을 올리면(POST /api/uploads) 201이고, image_url이 /media/로 시작한다
def test_upload_photo_201_and_media_url(upload_photo):
    # 201 확인은 upload_photo 안에서 함 (정리도 같이 해줌)
    image_url = upload_photo()
    assert image_url.startswith('/media/')


def test_uploaded_photo_is_actually_served(upload_photo):
    image_url = upload_photo()
    res = client.get(image_url)  # 받은 주소로 실제 사진이 열리는지
    assert res.status_code == 200
    assert res.headers['content-type'].startswith('image/')


# 2. 사진이 아닌 파일을 올리면 400
def test_upload_non_image_400():
    res = client.post(
        '/api/uploads',
        files={'photo': ('memo.txt', b'hello, I am not a photo', 'text/plain')},
        headers=login('alice'),
    )
    assert res.status_code == 400


# 3. 토큰 없이 올리면 401
def test_upload_without_token_401():
    res = client.post(
        '/api/uploads',
        files={'photo': ('test.png', fake_image_bytes(), 'image/png')},
    )
    assert res.status_code == 401


# 4. 올려서 받은 image_url로 글을 쓰면 201이고, 그 글의 image_url이 같은 주소다
def test_post_with_uploaded_image_url(upload_photo, make_post):
    image_url = upload_photo()

    post_id = make_post(image_url)  # 201 확인은 make_post 안에서 함

    res = client.get(f'/api/posts/{post_id}')
    assert res.status_code == 200
    assert res.json()['image_url'] == image_url
