from pydantic import BaseModel, Field

# 1. Données récoltées à l'inscription (Onboarding)
class UserOnboarding(BaseModel):
    username: str = Field(..., description="Nom de l'utilisateur")
    favorite_sports: list[str] = Field(..., description="Ex: ['Course', 'Fitness', 'Yoga']")
    fitness_level: str = Field(..., description="Débutant, Intermédiaire, ou Avancé")

# 2. Données récoltées le jour même pour générer la séance
class DailyWorkoutRequest(BaseModel):
    energy_level: int = Field(..., ge=1, le=10, description="Niveau d'énergie de 1 (épuisé) à 10 (en pleine forme)")
    available_time_min: int = Field(..., ge=10, le=120, description="Temps disponible en minutes")
    target_zone: str | None = Field("Tout le corps", description="Zone ciblée : Haut du corps, Bas du corps, Gainage, Tout le corps")
    equipment: str = Field("Aucun", description="Ex: Aucun, Haltères, Barre de traction")
    additional_notes: str | None = Field(None, min_length=0, max_length=500, description="Texte libre optionnel sur les envies spécifiques")

# 3. La structure de la réponse de l'IA (Ce que le front-end affichera)
class Exercise(BaseModel):
    name: str
    sets: int = Field(..., description="Nombre de séries")
    reps: str = Field(..., description="Ex: '12 répétitions' ou '30 secondes'")
    rest_time: str = Field(..., description="Temps de repos, ex: '45 secondes'")
    description: str
    youtube_search_url: str = Field(..., description="Lien de recherche YouTube pour l'exercice")

class WorkoutResponse(BaseModel):
    title: str = Field(..., description="Titre motivant de la séance")
    intro_message: str = Field(..., description="Petit mot d'encouragement du coach")
    exercises: list[Exercise]