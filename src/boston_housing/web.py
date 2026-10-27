from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from boston_housing.contracts import Scenario
from boston_housing.runtime import Predictor

SITE = Path(__file__).parent / "site"


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = 4097
        if declared < 0 or declared > 4096:
            return await JSONResponse({"detail": "Request body too large"}, status_code=413)(
                scope, receive, send
            )
        messages, length = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            length += len(message.get("body", b""))
            if length > 4096:
                return await JSONResponse({"detail": "Request body too large"}, status_code=413)(
                    scope, receive, send
                )
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            if messages:
                return messages.pop(0)
            return {"type": "http.disconnect"}

        await self.app(scope, replay, send)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(application):
        application.state.predictor = Predictor()
        yield

    application = FastAPI(title="Boston Housing Historical Research", lifespan=lifespan)
    application.add_middleware(BodyLimit)

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            }
        )
        return response

    @application.get("/api/health")
    def health():
        return {
            "status": "ok",
            "scope": "historical-research",
            "model_sha256": application.state.predictor.report["model_sha256"],
        }

    @application.get("/api/report")
    def report():
        return application.state.predictor.report

    @application.post("/api/predict")
    def predict(scenario: Scenario):
        return application.state.predictor.predict(scenario)

    if SITE.is_dir():
        application.mount("/", StaticFiles(directory=SITE, html=True), name="site")
    return application


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("boston_housing.web:app", host="127.0.0.1", port=8897)
