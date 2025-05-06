from config import settings
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from middleware import log_request_middleware
from mlmodels.router import router
from starlette.requests import Request
from starlette_context.middleware import ContextMiddleware
from tracing import PrometheusMiddleware, metrics, setting_otlp

__version__ = "0.0.1"

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url="/openapi.json",
    docs_url=None,
    redoc_url=None,
    version=__version__,
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "deepLinking": True},
)
app.include_router(router)
app.middleware("http")(log_request_middleware)
app.add_middleware(PrometheusMiddleware, app_name=settings.APP_NAME)
app.add_middleware(ContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_route("/metrics", metrics)
app.mount("/static", StaticFiles(directory="static"), name="static")

setting_otlp(app, settings.APP_NAME)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  # pylint: disable=W0613
    """request body validation, return json format"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/health")
async def health():
    return {"message": "Healthy"}
