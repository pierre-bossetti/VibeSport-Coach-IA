from pydantic import BaseModel, Field

# 1. Données récoltées à l'inscription (Onboarding)
class UserOnboarding(BaseModel):
    username: str = Field("pierre", description="Nom de l'utilisateur")
    favorite_sports: list[str] = Field(["Trail"], description="Ex: ['Course', 'Fitness', 'Yoga']")
    fitness_level: str = Field("Intermédiaire", description="Débutant, Intermédiaire, ou Avancé")

# 2. Données récoltées pour générer la séance
class WorkoutRequest(BaseModel):
    energy_level: int = Field(5, ge=1, le=10, description="Niveau d'énergie de 1 (épuisé) à 10 (en pleine forme)")
    available_time_min: int = Field(30, ge=10, le=120, description="Temps disponible en minutes")
    target_zone: str | None = Field("Tout le corps", description="Zone ciblée : Haut du corps, Bas du corps, Gainage, Tout le corps")
    equipment: str = Field("Aucun", description="Ex: Aucun, Haltères, Barre de traction")
    additional_notes: str | None = Field("", min_length=0, max_length=500, description="Texte libre optionnel sur les envies spécifiques")

# 3. La structure de la réponse de l'IA
# Un exercise individuel
class Exercise(BaseModel):
    name: str = Field(..., description="Nom exact de l'exercice (DOIT correspondre à un exercice du catalogue fourni).")
    sets: int = Field(..., description="Nombre de séries (ex: 3, 4, 5)")
    reps: int = Field(..., description="Nombre de répétitions exactes (ex: 10, 12, 15)")
    rest_time: int = Field(..., description="Temps de repos entre chaque série, STRICTEMENT en secondes (ex: 45, 60, 90)")
    description: str = Field(..., description="Explication de l'exercice et comment il aide l'utilisateur dans son sport favori.")
    youtube_search_url: str = Field("", description="Lien de recherche YouTube pour l'exercice")

# Le JSON renvoyé au Frontend
class WorkoutResponse(BaseModel):
    title: str = Field(..., description="Titre motivant de la séance")
    exercises: list[Exercise] = Field(
        ...,
        min_length=2,
        max_length=6,
        description="Liste stricte contenant entre 2 et 6 exercices maximum."
    )