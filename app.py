# app.py

from fastapi import FastAPI, Request, Header, HTTPException, Response
import httpx
from database import (
    init_db, is_api_key_valid, get_calls_today,
    increment_call, get_user_type
)

FREE_LIMIT = 100
REAL_URL = "https://esp-api.com/real-endpoint"

app = FastAPI()

# 初始化数据库
init_db()

@app.api_route("/v1/endpoint", methods=["GET", "POST"])
async def proxy_endpoint(
    request: Request,
    x_api_key: str = Header(None)
):
    # 验证API KEY
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header missing")

    valid, expired_at = is_api_key_valid(x_api_key)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid or expired API Key")
    user_type = get_user_type(x_api_key)
    is_free = (user_type == "free")

    # 免费用户计数
    if is_free:
        count = get_calls_today(x_api_key)
        if count >= FREE_LIMIT:
            raise HTTPException(status_code=429, detail="Free usage limit exceeded today")
        increment_call(x_api_key)

    # 构建请求
    params = str(request.query_params)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers.pop("x-api-key", None)  # 不要转发内部KEY

    # GET && POST
    async with httpx.AsyncClient(timeout=30.0) as client:
        if request.method == "GET":
            real_resp = await client.get(
                REAL_URL,
                headers=headers,
                params=request.query_params
            )
        elif request.method == "POST":
            body = await request.body()
            real_resp = await client.post(
                REAL_URL,
                content=body,
                headers=headers,
                params=request.query_params
            )
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")

    # 构造响应
    return Response(
        content=real_resp.content,
        status_code=real_resp.status_code,
        headers={
            # 可选择加上其它headers
            k: v for k, v in real_resp.headers.items() if k.lower() in ["content-type"]
        }
    )
