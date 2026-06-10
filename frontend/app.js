// Configuration
const API_BASE_URL = "http://127.0.0.1:8000";
const API_TOKEN = "vibe-sport-secret-key-123";

// Liste des sports proposés à l'utilisateur
const SPORTS_LIST = ["Trail", "Course sur route", "Natation", "Cyclisme", "Football", "Basketball", "Tennis", "Ski", "Escalade", "Arts Martiaux", "Yoga"];

// Variables d'état
let currentUser = localStorage.getItem("vibeSportUser");

// --- INITIALISATION DE LA PAGE ---
document.addEventListener("DOMContentLoaded", () => {
    // Générer les cases à cocher des sports
    const sportsContainer = document.getElementById("sportsContainer");
    SPORTS_LIST.forEach(sport => {
        sportsContainer.innerHTML += `
            <div class="form-check">
                <input class="form-check-input sport-checkbox" type="checkbox" value="${sport}" id="sport_${sport}">
                <label class="form-check-label" for="sport_${sport}">${sport}</label>
            </div>
        `;
    });

    // Vérifier si l'utilisateur est déjà connecté
    if (currentUser) {
        verifyUserSession();
    }
});

// --- GESTION DE L'ONBOARDING ---
document.getElementById("onboardingForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    // Récupérer les sports cochés
    const checkboxes = document.querySelectorAll('.sport-checkbox:checked');
    if (checkboxes.length === 0 || checkboxes.length > 3) {
        document.getElementById("sportsError").classList.remove("d-none");
        return;
    }
    document.getElementById("sportsError").classList.add("d-none");

    const sports = Array.from(checkboxes).map(cb => cb.value);
    const username = document.getElementById("username").value;

    const payload = {
        username: username,
        fitness_level: document.getElementById("fitnessLevel").value,
        favorite_sports: sports
    };

    try {
        // Appel API : POST /users
        const response = await fetch(`${API_BASE_URL}/users`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Token": API_TOKEN
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            currentUser = username;
            localStorage.setItem("vibeSportUser", username); // Sauvegarde dans le navigateur
            showDashboard();
        } else if (response.status === 400) {
            // L'API nous dit que le nom est déjà pris
            alert("Ce nom d'utilisateur est déjà pris. Choisis-en un autre !");
        } else {
            alert("Erreur lors de la création du profil.");
        }
    } catch (error) {
        alert("Erreur de connexion au serveur Backend.");
    }
});

// --- GESTION DE LA GÉNÉRATION DE SÉANCE ---
document.getElementById("workoutForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const displayZone = document.getElementById("displayZone");
    const loadingZone = document.getElementById("loadingZone");
    const btn = document.getElementById("generateBtn");

    displayZone.innerHTML = "";
    loadingZone.classList.remove("d-none");
    btn.disabled = true;

    const payload = {
        energy_level: parseInt(document.getElementById("energyLevel").value),
        equipment: document.getElementById("equipment").value,
        available_time_min: parseInt(document.getElementById("availableTime").value),
        target_zone: document.getElementById("targetZone").value,
        additional_notes: document.getElementById("additionalNotes").value || null
    };

    try {
        // Appel API : POST users/{username}/workouts/generate
        const response = await fetch(`${API_BASE_URL}/users/${currentUser}/workouts/generate`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Token": API_TOKEN
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error("Erreur IA");

        const data = await response.json();
        renderWorkout(data); // Affiche la séance générée

    } catch (error) {
        alert("Erreur lors de la génération. Ollama tourne-t-il bien ?");
    } finally {
        loadingZone.classList.add("d-none");
        btn.disabled = false;
    }
});

// --- GESTION DE L'HISTORIQUE ---
document.getElementById("btnHistory").addEventListener("click", async () => {
    const displayZone = document.getElementById("displayZone");
    displayZone.innerHTML = "<div class='text-center mt-4'>Chargement de l'historique...</div>";

    try {
        // Appel API : GET users/{username}/workouts
        const response = await fetch(`${API_BASE_URL}/users/${currentUser}/workouts`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-API-Token": API_TOKEN
            }
        });
        if (!response.ok) throw new Error();

        const history = await response.json();

        if (history.length === 0) {
            displayZone.innerHTML = "<div class='alert alert-info mt-4'>Vous n'avez pas encore généré de séance.</div>";
            return;
        }

        let html = "<h3 class='mt-4'>📜 Vos 10 dernières séances</h3>";
        // On inverse le tableau pour voir la plus récente en haut
        history.slice().reverse().forEach((workout, index) => {
            html += `<div class="card mb-3 shadow-sm border-secondary"><div class="card-body">`;
            html += `<h5>${workout.title}</h5><p class="text-muted small">${workout.intro_message}</p>`;
            html += `<ul>`;
            workout.exercises.forEach(exo => {
                html += `<li><b>${exo.name}</b> (${exo.sets} séries)</li>`;
            });
            html += `</ul></div></div>`;
        });
        displayZone.innerHTML = html;

    } catch (error) {
        alert("Impossible de récupérer l'historique.");
    }
});

// --- VÉRIFICATION DE SESSION (Self-Healing) ---
async function verifyUserSession() {
    try {
        // On demande le profil au serveur pour voir s'il s'en souvient
        const response = await fetch(`${API_BASE_URL}/users/${currentUser}`, {
            method: "GET",
            headers: {
                "X-API-Token": API_TOKEN
            }
        });

        if (response.ok) {
            // Le serveur s'en souvient, on affiche le tableau de bord
            showDashboard();
        } else if (response.status === 404) {
            // Le serveur a redémarré et a oublié l'utilisateur !
            // On nettoie le navigateur et on montre la page d'inscription.
            localStorage.removeItem("vibeSportUser");
            currentUser = null;
            document.getElementById("dashboardScreen").classList.add("d-none");
            document.getElementById("onboardingScreen").classList.remove("d-none");
        }
    } catch (error) {
        console.error("Le serveur est injoignable.");
    }
}

// --- FONCTIONS UTILITAIRES ---
function showDashboard() {
    document.getElementById("onboardingScreen").classList.add("d-none");
    document.getElementById("dashboardScreen").classList.remove("d-none");
    document.getElementById("welcomeMessage").textContent = `Bonjour ${currentUser} !`;
}

function renderWorkout(data) {
    let html = `
        <div class="card shadow mb-4 border-primary">
            <div class="card-body text-center bg-light rounded">
                <h2 class="text-primary fw-bold">${data.title}</h2>
                <p class="lead mb-0">${data.intro_message}</p>
            </div>
        </div>
        <div class="row">
    `;

    data.exercises.forEach(exo => {
        html += `
            <div class="col-md-6 mb-4">
                <div class="card h-100 shadow-sm exercise-card border-0 bg-white">
                    <div class="card-body">
                        <h5 class="card-title fw-bold text-dark">${exo.name}</h5>
                        <div class="mb-3">
                            <span class="badge bg-primary me-1">${exo.sets || 3} séries</span>
                            <span class="badge bg-info text-dark me-1">${exo.reps_or_time || '10 reps'}</span>
                            <span class="badge bg-secondary">Repos: ${exo.rest_time || '45s'}</span>
                        </div>
                        <p class="card-text text-muted">${exo.description}</p>
                    </div>
                    <div class="card-footer bg-transparent border-0 pb-3">
                        <a href="${exo.youtube_search_url}" target="_blank" class="btn btn-outline-danger w-100">
                            🎬 Voir le tutoriel
                        </a>
                    </div>
                </div>
            </div>
        `;
    });

    html += `</div>`;
    document.getElementById("displayZone").innerHTML = html;
}