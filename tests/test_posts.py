from fastapi.testclient import TestClient # = 내부에서 postman or chrome 열어보겠다.
from main import app

client = TestClient(app) # app 코드 기반으로 하겠다.

# 함수명 규칙: test_~~~~ 시작해야함!!

def test_post_list():
    res = client.get('/api/posts') #get 요청 보내봐
    assert res.status_code == 200
    
    
# 없는 게시물
def test_post_detail_404():
    res = client.get('/api/posts/999999')
    assert res.status_code == 404
    assert res.json() == {'detail':'해당 게시물이 없습니다.'}
    
    
# 예외처리
def test_post_create_empty_422():
    res = client.post('/api/posts', json={'content': '', 'user_id': 1}) # 게시물 보낼땐 json 필드에 넣어서 / content 값이 비어있는 경우 확인용
    assert res.status_code == 422
    
    
#게시물 생성
def test_post_create():
    res = client.post('/api/posts', json={'content': 'hello', 'user_id': 1})
    assert res.status_code == 201
    post_id = res.json()['id'] # 방금 생성한 게시물의 id만 뽑기
    
    client.delete('/api/posts{post_id}') # 방금 생성한거 삭제
    assert res.status_code == 204
    assert client.get(f'/api/posts/{post_id}').status_code == 404
    