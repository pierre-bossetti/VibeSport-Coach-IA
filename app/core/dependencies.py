from app.core.config import settings
from app.services.ollama_service import OllamaService
from app.services.coach_service import CoachService
from fastapi import Header, HTTPException, status

# 1. On instancie le service Ollama avec les paramètres de configuration
ollama_service = OllamaService(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model,
    timeout=settings.ollama_timeout,
)

# 2. On instancie le CoachService en lui injectant le service Ollama
coach_service = CoachService(
    ollama_service=ollama_service,
    exercises_path=settings.exercises_data_path
)

# 3. Fonctions d'injection pour les routes FastAPI
def get_ollama_service() -> OllamaService:
    return ollama_service

def get_coach_service() -> CoachService:
    return coach_service

def require_simple_api_token(x_api_token: str | None = Header(default=None)) -> None:
    """Verifie que le Header X-API-Token correspond à la clé secrète du serveur."""
    if x_api_token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Accès refusé. Clé API invalide.",
        )