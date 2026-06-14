from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.coach import UserOnboarding, WorkoutRequest, WorkoutResponse
from app.core.dependencies import get_coach_service, require_simple_api_token

# 🌟 On change le préfixe principal pour /users
router = APIRouter(prefix="/users", tags=["Users"])

fake_users_db = {}
fake_history_db = {}

# 1. POST /users (Créer un utilisateur)
@router.post("", summary="Créer un nouveau profil utilisateur", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserOnboarding):
    if payload.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà pris."
        )
    fake_users_db[payload.username] = payload
    fake_history_db[payload.username] = []
    return {"message": f"Bienvenue {payload.username} ! Profil enregistré."}

# 2. GET /users/{username} (Voir un utilisateur)
@router.get("/{username}", summary="Récupérer le profil utilisateur")
async def get_user_profile(
        username: str,
        _: None = Depends(require_simple_api_token)
):
    if username not in fake_users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé.")
    return fake_users_db[username]

# 3. GET /users/{username}/workouts (Voir l'historique des séances)
@router.get("/{username}/workouts", response_model=list[WorkoutResponse], summary="Voir l'historique des séances")
async def get_user_history(
        username: str,
        _: None = Depends(require_simple_api_token)
) -> list[WorkoutResponse]:
    if username not in fake_users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé.")
    return fake_history_db.get(username, [])

# 4. POST /users/{username}/workouts/generate (L'IA crée une séance)
@router.post("/{username}/workouts/generate", response_model=WorkoutResponse, summary="Générer l'entraînement du jour par l'IA")
async def generate_workout(
        username: str,
        payload: WorkoutRequest,
        _: None = Depends(require_simple_api_token)
) -> WorkoutResponse:
    if username not in fake_users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé.")

    user_profile = fake_users_db[username]
    workout = await get_coach_service().generate_session(user=user_profile, workout_request=payload)

    if username not in fake_history_db:
        fake_history_db[username] = []

    fake_history_db[username].append(workout)
    if len(fake_history_db[username]) > 10:
        fake_history_db[username] = fake_history_db[username][-10:]

    return workout