from fastapi import FastAPI
from routers import posts, auth, likes, comments, upload
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 라우터는 여기에 붙인다
app.include_router(posts.router)
app.include_router(auth.router)
app.include_router(likes.router)
app.include_router(comments.router)
app.include_router(upload.router)

# staticfiles
app.mount('/media', StaticFiles(directory='media'))
