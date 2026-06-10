import httpx
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health", summary="Vérifier l'état de l'API et du modèle IA")
async def health_check():
    ollama_status = "hors ligne 🔴"
    model_status = "non installé 🔴"

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            # 1. On interroge l'API d'Ollama pour voir ses modèles disponibles
            response = await client.get(f"{settings.ollama_base_url}/api/tags")

            if response.status_code == 200:
                ollama_status = "en ligne 🟢"

                # 2. On vérifie si notre modèle (llama3.2) est dans la liste
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]

                # Ollama ajoute souvent le tag ":latest", donc on vérifie l'inclusion
                if any(settings.ollama_model in model_name for model_name in models):
                    model_status = "prêt 🟢"
                else:
                    model_status = "en cours de téléchargement ⏳"

    except httpx.RequestError:
        # Si le conteneur Ollama est éteint
        pass

    # Détermination du message global
    if ollama_status == "en ligne 🟢" and model_status == "prêt 🟢":
        message = "Système 100% opérationnel."
    elif ollama_status == "en ligne 🟢":
        message = "Ollama est allumé. Le téléchargement de l'IA est en cours en arrière-plan..."
    else:
        message = "L'API fonctionne, mais le moteur IA (Ollama) est injoignable."

    return {
        "api_status": "ok",
        "ollama_status": ollama_status,
        "model_status": model_status,
        "message": message
    }

@router.get("/ping", summary="Ping basique")
async def ping():
    return {"status": "pong"}