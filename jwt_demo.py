import jwt
from datetime import datetime, timedelta, timezone


SECRET_KEY = 'dev-secret'

exp = datetime.now(timezone.utc) + timedelta(minutes=30) # timezone.utc 현재시간

token = jwt.encode({'sub':'1', 'exp': exp, 'test': 'hello'}, SECRET_KEY, algorithm='HS256')
# print(token)


# 토큰 유요한지 검사
decoded_data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
print(decoded_data)