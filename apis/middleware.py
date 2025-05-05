import sys

from loguru import logger
from config import settings
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import Response

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | {level} | <level>{message}</level>",
)


async def set_request_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive


def log_response_body(response_body):
    logger.info(response_body)


async def log_request_middleware(request, call_next):
    # skip logging for health check by probe call
    user_agent = request.headers.get("user-agent", "")
    health_check_paths = ["/health"]
    if request.url.path in health_check_paths and "kube-probe" in user_agent:
        return await call_next(request)

    trace_id = request.headers.get("trace_id", "")

    if request.headers.get("accept") == "text/event-stream":
        logger.info(f"[{trace_id}] {request.method} {request.url} - SSE request (Stream)")
        return await call_next(request)

    request_body = await request.body()
    decoded_request_body = request_body.decode("utf-8")

    request_log_message = f"[{trace_id}] {request.method} {request.url} {decoded_request_body}"
    logger.info(request_log_message)
    await set_request_body(request, request_body)

    response = await call_next(request)

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    decoded_response_body = ""
    if not request.url.path.startswith("/static"):
        decoded_response_body = response_body.decode("utf-8")
    response_log_message = f"[{trace_id}] {response.status_code} {request.method} {request.url} {decoded_response_body}"

    task = BackgroundTask(log_response_body, response_log_message)
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=task,
    )
