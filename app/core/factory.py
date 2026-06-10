from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import users, health


def create_app() -> FastAPI:
    tags_metadata = [
        {"name": "coach", "description": "Opérations liées à la génération d'entraînements IA."},
        {"name": "health", "description": "Endpoints de surveillance et statut."},
    ]

    app = FastAPI(
        title="Coach Sportif IA API",
        debug=settings.debug,
        version="1.0.0",
        description="API FastAPI + Ollama pour la génération de programmes sportifs sur mesure",
        openapi_tags=tags_metadata,
        swagger_ui_parameters={"displayRequestDuration": True, "defaultModelsExpandDepth": -1},
    )

    # CORS - Configuration de développement (identique au cours)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:63342" , "http://127.0.0.1:3000", "http://127.0.0.1:8000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Personnalisation OpenAPI (Swagger)
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        schema.setdefault("info", {})
        schema["servers"] = [{"url": "http://localhost:8000", "description": "Local"}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Inclusion des routeurs
    app.include_router(health.router)
    app.include_router(users.router)  # On inclut le routeur du coach ici

    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

    return app