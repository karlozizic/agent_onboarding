import os

from fastapi import Depends, FastAPI, Header, HTTPException

TOKEN = os.environ.get("CORE_TOKEN", "dev-token")


def check_token(authorization: str = Header(default="")):
    if authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401)


app = FastAPI(dependencies=[Depends(check_token)])


@app.get("/health")
def health():
    return {"status": "ok"}