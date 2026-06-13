import json
import random
import urllib.parse
from fastapi import HTTPException, status
from app.services.ollama_service import OllamaService
from app.schemas.coach import UserOnboarding, DailyWorkoutRequest, WorkoutResponse

class CoachService:
    def __init__(self, ollama_service: OllamaService, exercises_path: str):
        self.ollama_service = ollama_service

        with open(exercises_path, "r", encoding="utf-8") as f:
            self.exercises_catalog = json.load(f)

    def _build_system_prompt(self, user: UserOnboarding, daily_state: DailyWorkoutRequest) -> str:
        # 1. On filtre d'abord le catalogue par Zone !
        filtered_exercises = []
        for exo in self.exercises_catalog:
            if daily_state.target_zone == "Tout le corps" or exo.get("zone") == daily_state.target_zone:
                filtered_exercises.append(exo)

        # 2. Si la liste est trop longue, on tire au sort 10 exercices.
        # L'IA aura un petit menu parfait dans lequel piocher, sans jamais saturer sa mémoire.
        if len(filtered_exercises) > 10:
            filtered_exercises = random.sample(filtered_exercises, 10)

        catalog_str = json.dumps(filtered_exercises, ensure_ascii=False, indent=2)

        # A. Calcul du nombre d'exercices (1 exercice = ~5-7 minutes)
        if daily_state.available_time_min <= 20:
            exo_count = 2
        elif daily_state.available_time_min <= 30:
            exo_count = 3
        elif daily_state.available_time_min <= 45:
            exo_count = 4
        elif daily_state.available_time_min <= 60:
            exo_count = 5
        else:
            exo_count = 6

        # B. Traduction de l'énergie en consignes claires
        if daily_state.energy_level <= 3:
            energy_rules = "ÉNERGIE TRÈS BASSE : 1 à 2 séries MAX par exercice. Repos long (60 à 90 secondes). Répétitions faibles (5 à 8)."
            vibe = "Récupération douce"
        elif daily_state.energy_level <= 7:
            energy_rules = "ÉNERGIE MOYENNE : 3 séries par exercice. Repos modéré (45 à 60 secondes). 8 à 12 répétitions."
            vibe = "Séance équilibrée"
        else:
            energy_rules = "ÉNERGIE MAXIMALE : 4 séries. Repos court (30 secondes). 12 à 15 répétitions."
            vibe = "Séance très intense"

        notes_section = f"\n- Demande spécifique : {daily_state.additional_notes}" if daily_state.additional_notes else ""

        return f"""Tu es un coach sportif d'élite. Ton but est de créer une {vibe}.

PROFIL ATHLÈTE : Niveau: {user.fitness_level} | Sport: {', '.join(user.favorite_sports)}
CONTRAINTES : Temps : {daily_state.available_time_min} min | Matériel : {daily_state.equipment}{notes_section}

CATALOGUE D'EXERCISES :
{catalog_str}

RÈGLES ABSOLUES :
1. NOMBRE : TU DOIS sélectionner EXACTEMENT {exo_count} exercices issus UNIQUEMENT du catalogue ci-dessus. Pas un de plus.
2. INTENSITÉ : {energy_rules}
3. PÉDAGOGIE : Dans la "description", justifie brièvement pourquoi l'exercice aide pour ({user.favorite_sports[0] if user.favorite_sports else ''}).
"""

    async def generate_session(self, user: UserOnboarding, daily_state: DailyWorkoutRequest) -> WorkoutResponse:
        system_prompt = self._build_system_prompt(user, daily_state)
        user_prompt = "Génère mon entraînement."

        raw_response = await self.ollama_service.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=WorkoutResponse.model_json_schema()
        )

        try:
            parsed_data = json.loads(raw_response.strip())

            # Vérifier que "exercises" existe
            if "exercises" not in parsed_data or not isinstance(parsed_data["exercises"], list):
                raise ValueError("Liste d'exercices manquante")

            for exo in parsed_data["exercises"]:
                # Au cas où l'IA oublierait le name
                name = exo.get("name", "Exercice")
                safe_name = urllib.parse.quote(f"tutoriel {name}")
                exo["youtube_search_url"] = f"https://www.youtube.com/results?search_query={safe_name}"

            return WorkoutResponse(**parsed_data)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"🚨 ERREUR DE VALIDATION : {e}")
            print(f"🤖 RÉPONSE BRUTE D'OLLAMA : {raw_response}")
            # Si l'IA plante quand même, on renvoie une erreur 500
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Le coach IA a eu un moment d'égarement. Veuillez relancer la génération."
            )