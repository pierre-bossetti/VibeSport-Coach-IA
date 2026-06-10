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

        notes_section = f"\n- Demande spécifique : {daily_state.additional_notes}" if daily_state.additional_notes else ""

        return f"""Tu es un coach sportif d'élite.
Tu dois concevoir la meilleure séance possible pour cet athlète en piochant STRICTEMENT dans la liste d'exercices fournie.

PROFIL : {user.username}, Niveau: {user.fitness_level}, Sport: {', '.join(user.favorite_sports)}
SÉANCE À CRÉER : 
- Énergie: {daily_state.energy_level}/10 
- Temps dispo: {daily_state.available_time_min} min
- Matériel: {daily_state.equipment}{notes_section}

MENU D'EXERCICES PRÉ-SÉLECTIONNÉS (Choisis-en 3 à 5 là-dedans) :
{catalog_str}

RÈGLES ABSOLUES :
1. N'utilise QUE le "name" exact des exercices du menu ci-dessus. N'invente AUCUN exercice.
2. Définis des "sets", "reps" (répétitions logiques) et "rest_time" adaptés à l'énergie ({daily_state.energy_level}/10).
3. Adapte la "description" pour expliquer l'intérêt de l'exercise par rapport à son sport favori ({user.favorite_sports[0]}).
4. Renvoie le tout dans un format JSON valide.

FORMAT JSON ATTENDU :
{{
    "title": "Un titre dynamique",
    "intro_message": "Une phrase d'encouragement.",
    "exercises": [
        {{
            "name": "Nom exact",
            "sets": 3,
            "reps": "12 reps",
            "rest_time": "45 secondes",
            "description": "Explication pertinente."
        }}
    ]
}}
"""

    async def generate_session(self, user: UserOnboarding, daily_state: DailyWorkoutRequest) -> WorkoutResponse:
        system_prompt = self._build_system_prompt(user, daily_state)
        user_prompt = "Génère mon entraînement au format JSON."

        raw_response = await self.ollama_service.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # Nettoyage de la réponse au cas où Ollama ne respecte pas le format JSON
        cleaned_response = raw_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        try:
            parsed_data = json.loads(cleaned_response.strip())

            # Sécurité : vérifier que "exercises" existe
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