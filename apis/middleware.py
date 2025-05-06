import datetime
import logging
import logging.config

import pytz
import yaml
from config import settings
from opentelemetry import trace
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import Response

IGNORED_PATHS = ["/metrics", "/health"]


async def set_request_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive


def load_logging_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)


def log_request(status_code, message):
    if status_code >= 400:
        logging.error(message)
        span = trace.get_current_span()
        trace_id = trace.format_trace_id(span.get_span_context().trace_id)
        span_id = trace.format_span_id(span.get_span_context().span_id)
        now_kst = datetime.datetime.now(pytz.timezone("Asia/Seoul"))
        logging.error(
            f"[{settings.APP_NAME} error] [{now_kst.strftime('%Y-%m-%d %H:%M:%S')}] [trace id: {trace_id} span id: {span_id}]"
        )
    else:
        logging.info(message)


async def log_request_middleware(request: Request, call_next):
    request_body = await request.body()
    decoded_request_body = request_body.decode("utf-8")
    await set_request_body(request, request_body)

    response = await call_next(request)

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    background_task = None
    if request.url.path not in IGNORED_PATHS:
        decoded_response_body = response_body.decode("utf-8")
        message = f"\n Request url: {request.url} \
                    \n Status code: {response.status_code} \
                    \n Request: {decoded_request_body} \
                    \n Response: {decoded_response_body}"
        background_task = BackgroundTask(log_request, response.status_code, message)

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=background_task,
    )
