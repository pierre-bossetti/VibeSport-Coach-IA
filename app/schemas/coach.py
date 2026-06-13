from pydantic import BaseModel, Field

# 1. Données récoltées à l'inscription (Onboarding)
class UserOnboarding(BaseModel):
    username: str = Field("pierre", description="Nom de l'utilisateur")
    favorite_sports: list[str] = Field(["Trail"], description="Ex: ['Course', 'Fitness', 'Yoga']")
    fitness_level: str = Field("Intermédiaire", description="Débutant, Intermédiaire, ou Avancé")

# 2. Données récoltées le jour même pour générer la séance
class DailyWorkoutRequest(BaseModel):
    energy_level: int = Field(5, ge=1, le=10, description="Niveau d'énergie de 1 (épuisé) à 10 (en pleine forme)")
    available_time_min: int = Field(30, ge=10, le=120, description="Temps disponible en minutes")
    target_zone: str | None = Field("Tout le corps", description="Zone ciblée : Haut du corps, Bas du corps, Gainage, Tout le corps")
    equipment: str = Field("Aucun", description="Ex: Aucun, Haltères, Barre de traction")
    additional_notes: str | None = Field(None, min_length=0, max_length=500, description="Texte libre optionnel sur les envies spécifiques")

# 3. La structure de la réponse de l'IA (Ce que le front-end affichera)
class Exercise(BaseModel):
    name: str
    sets: int = Field(..., description="Nombre de séries")
    reps: int = Field(..., description="Ex: 'Nombre de répétitions'")
    rest_time: int = Field(..., description="Le temps de repos STRICTEMENT en secondes (ex: 45, 60, 90)")
    description: str
    youtube_search_url: str = Field(..., description="Lien de recherche YouTube pour l'exercice")

class WorkoutResponse(BaseModel):
    title: str = Field(..., description="Titre motivant de la séance")
    exercises: list[Exercise] = Field(
        ...,
        min_length=2,
        max_length=6,
        description="Liste stricte contenant entre 2 et 6 exercices maximum."
    )