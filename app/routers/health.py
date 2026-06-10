import httpx
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health", summary="Vérifier l'état de l'API et de l'IA")
async def health_check():
    ollama_status = "hors ligne 🔴"

    # On tente un ping très rapide (timeout de 2 secondes) sur Ollama
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(settings.ollama_base_url)
            if response.status_code == 200:
                ollama_status = "en ligne 🟢"
    except httpx.RequestError:
        # Si Ollama est éteint, la requête plantera et on atterrit ici
        pass

    return {
        "api_status": "ok",
        "ollama_status": ollama_status,
        "message": (
            "Système 100% opérationnel."
            if ollama_status == "en ligne 🟢"
            else "L'API fonctionne, mais le coach IA (Ollama) est injoignable."
        )
    }

@router.get("/ping", summary="Ping basique")
async def ping():
    return {"status": "pong"}