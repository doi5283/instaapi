from fastapi import FastAPI
from routers import posts, auth

app = FastAPI()

# 라우터는 여기에 붙인다
app.include_router(posts.router)
app.include_router(auth.router)

