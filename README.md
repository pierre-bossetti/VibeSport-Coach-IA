# 🏋️‍♂️ VibeSport - Coach Sportif Intelligent (IA Générative & RAG Local)

**VibeSport** est une application web moderne intégrant une architecture client/serveur, une API RESTful **FastAPI**, et un moteur d'intelligence artificielle locale via **Ollama (Llama 3.2)**.

Cette application permet à un utilisateur de s'inscrire, de définir ses préférences sportives et de générer à la demande des séances d'entraînement personnalisées et adaptées à sa forme du jour, tout en conservant un historique de ses entrainements.

---

## 🚀 Démarrage Rapide

Si vous avez **Docker Desktop** d'installé, lancez le projet en une seule commande depuis la racine du dossier :

```bash
docker compose up -d --build
```

*💡 L'IA Llama 3.2 (2 Go) se téléchargera automatiquement en arrière-plan.
Patientez 1 à 2 minutes, puis ouvrez [http://localhost:8000](http://localhost:8000).*

---

## 🛠️ 1. Fonctionnement Général

L'application repose sur un écosystème découplé et conteneurisé composé de trois briques majeures :

1. **Le Frontend (Client d'interface) :** Une application monopage (SPA) conçue en HTML5, CSS3 (Bootstrap 5) et JavaScript Vanilla. Elle gère dynamiquement l'état local, le stockage persistant de la session et la restitution visuelle des séances générées avec des liens vers des tutoriels vidéos.
2. **Le Backend (Serveur API REST) :** Une API développée avec **FastAPI (Python 3.11)**. Elle valide les payloads via **Pydantic**, expose la documentation Swagger et orchestre la logique métier de l'application.
3. **Le Moteur LLM Local & RAG :** Le backend extrait un catalogue local d'exercices physiques (`exercises.json`), filtre les mouvements pertinents selon la zone ciblée par l'athlète, puis injecte ce menu ultra-ciblé dans un *System Prompt* transmis à **Ollama**. C'est le principe du **RAG (Retrieval-Augmented Generation)**, qui empêche l'IA d'inventer des mouvements inexistants.

---

## 📂 2. Structure du Projet

Conformément aux bonnes pratiques de développement logiciel et de séparation des responsabilités transmises durant les workshops, le projet applique une structure modulaire stricte :


```
vibesport/
│
├── app/
│   ├── main.py                  # Point d'entrée de l'application FastAPI
│   │
│   ├── core/
│   │   ├── config.py            # Centralisation des variables d'environnement
│   │   └── dependencies.py      # Dépendances globales (Sécurité Simple Auth)
│   │
│   ├── routers/
│   │   ├── health.py            # Vérifie si L'API et Ollama sont fonctionnelles
│   │   └── users.py             # Routeur HTTP RESTful orienté ressource (Users)
│   │
│   ├── schemas/
│   │   └── coach.py             # Modèles et schémas de données Pydantic
│   │
│   └── services/
│       ├── coach_service.py     # Logique métier, Prompt Engineering et RAG local
│       └── ollama_service.py    # Client HTTP asynchrone pour la communication avec Ollama
│
├── data/
│   └── exercises.json           # Catalogue local de référence (50+ exercices de musculation/cardio)
│
├── frontend/
│   ├── index.html               # Interface utilisateur structurée
│   └── app.js                   # Logique client, requêtes asynchrones et gestion du State
│
├── .dockerignore                # Fichiers exclus du build Docker (légèreté et isolation)
├── Dockerfile                   # Recette de construction de l'image de l'API FastAPI
├── compose.yaml                 # Orchestration multi-conteneurs (App + Moteur Ollama)
└── requirements.txt             # Gestion rigoureuse des dépendances et de leurs versions
```

---

## 🎯 3. Spécifications Techniques & Endpoints RESTful

L'API respecte scrupuleusement les contraintes de l'architecture **REST** (représentation par ressources au pluriel, verbes HTTP explicites). Toutes les opérations gravitent autour de la ressource principale `/users`.

### 🔐 Sécurité des accès (Simple Auth)

À l'exception de la route de création de profil (`POST /users`), tous les points d'accès sont verrouillés par un intercepteur FastAPI (`Depends(require_simple_api_token)`). Le client doit obligatoirement transmettre le jeton secret dans les en-têtes HTTP de sa requête : `X-API-Token: vibe-sport-secret-key-123`.

### Table des Endpoints

| Méthode | URL | Description | Statut HTTP | Accès |
| --- | --- | --- | --- | --- |
| **GET** | `/health` | Vérifie la santé de l'API et le statut de connexion au moteur Ollama | `200 OK` | Ouvert |
| **GET** | `/ping` | Route de ping basique | `200 OK` | Ouvert |
| **POST** | `/users` | Crée un nouveau profil utilisateur (Onboarding) | `201 Created` ou `400` | Ouvert |
| **GET** | `/users/{username}` | Récupère les données de profil (Vérification existence) | `200 OK` ou `404` | Protégé |
| **GET** | `/users/{username}/workouts` | Récupère l'historique des 10 dernières séances générées | `200 OK` ou `404` | Protégé |
| **POST** | `/users/{username}/workouts/generate` | Déclenche l'orchestration IA pour concevoir un workout | `200 OK`, `404` ou `500` | Protégé |

### 🖥️ Distribution du Frontend (Bonus)
Afin de livrer une application complète et autonome (*Full-Stack*) sans nécessiter un second conteneur (comme Nginx), FastAPI est configuré pour servir lui-même l'interface utilisateur.
* L'application utilise `StaticFiles` pour exposer le dossier `/frontend`.
* Lorsque l'utilisateur navigue sur la racine `GET /`, FastAPI renvoie directement le fichier `index.html`. L'API fait donc office à la fois de serveur de données (JSON) et de serveur web statique (HTML/JS/CSS).

---

## 🧠 4. Prompt Engineering & Intégration LLM (RAG Local)

La génération de l'entraînement ne délègue pas toute la logique métier au hasard du LLM. Elle utilise une communication déterministe stricte :

1. **Le filtrage RAG :** Le backend parcourt le fichier `data/exercises.json`. Si l'utilisateur demande à cibler le "Haut du corps", le script Python ne sélectionne que les exercices correspondants. Si la liste dépasse 10 exercices, un tirage aléatoire (`random.sample`) extrait un sous-ensemble. Ce catalogue restreint sous forme de chaîne JSON est directement injecté dans les consignes de l'IA.
2. **Le System Prompt :** Un prompt système ultra-directif contraint le modèle à se comporter en entraîneur strict. Il lui est interdit d'inventer un exercice en dehors du menu fourni, et il lui est imposé d'adapter les répétitions au niveau d'énergie saisi par l'athlète.
3. **Le formatage JSON Contraint :** Grâce au paramètre `"format": "json"` envoyé à l'API d'Ollama, le modèle est structurellement forcé de renvoyer une chaîne JSON valide, mappée sur le schéma Pydantic `WorkoutResponse`.
4. **Le nettoyage post-génération :** Le service intègre une routine de nettoyage (`strip()`, élimination des blocs markdown ```json) pour parer aux éventuels résidus textuels du modèle.

---

## 📜 5. Gestion de l'Historique & Robustesse Globale

### Historique glissant en mémoire

Le serveur maintient un dictionnaire en mémoire globale `fake_history_db`. À chaque génération de séance réussie, l'objet structuré `WorkoutResponse` est ajouté à l'historique de l'utilisateur. Une opération de découpage (`slice`) garantit la sauvegarde stricte des **10 derniers entraînements**, évitant ainsi toute saturation de la mémoire volatile.

### Gestion du State & Mécanisme de "Self-Healing" du Frontend

L'application frontend utilise le `localStorage` pour maintenir l'utilisateur connecté d'une session à l'autre. Afin de résoudre le problème des désynchronisations d'état lors du redémarrage du serveur Docker (qui vide la mémoire globale alors que le navigateur se souvient du pseudo), le fichier `app.js` intègre un système d'auto-guérison (*Self-Healing*) :

* Au chargement, le script interroge directement `GET /users/{username}`.
* Si le serveur répond `200`, le Dashboard s'affiche normalement.
* Si le serveur répond `404` (suite à un redémarrage ou une perte de mémoire), le frontend intercepte l'erreur, nettoie proprement le `localStorage` et réaffiche instantanément l'écran d'Onboarding de manière transparente.

---

## 🛡️ 6. Gestion des Erreurs & Robustesse API

Conformément aux exigences du critère 6, l'application est blindée contre les anomalies réseaux et les entrées utilisateur invalides :

* **Erreur Utilisateur (400 Bad Request) :** Déclenchée si un utilisateur tente de s'inscrire avec un pseudonyme déjà présent dans `fake_users_db`.
* **Ressource Introuvable (404 Not Found) :** Renvoyée si une action est demandée sur un utilisateur inexistant.
* **Panne de l'IA (500 Internal Server Error) :** Si le LLM omet une clé obligatoire requise par le schéma Pydantic (ex: la clé `reps_or_time`), le bloc `try...except (json.JSONDecodeError, ValueError)` de `coach_service.py` intercepte l'exception, imprime la réponse brute dans les logs du serveur pour le débogage, et renvoie un message d'erreur clair et sécurisé à l'utilisateur.
* **Exceptions Réseau Ollama (502 / 503 / 504) :** Le service `ollama_service.py` capture explicitement les exceptions d'**HTTPX** (`TimeoutException`, `RequestError`, `HTTPStatusError`) pour renvoyer des statuts HTTP explicites (*"Ollama a mis trop de temps à répondre"*, *"Service indisponible"*) plutôt que de laisser l'API crasher de manière silencieuse.
* **Healthcheck Intelligent (Monitoring) :** La route `/health` effectue un ping asynchrone (avec un délai d'expiration de 2 secondes) directement vers le conteneur du LLM. Cela permet à l'infrastructure (et à Docker) de savoir si l'API est simplement allumée, ou si elle est **pleinement opérationnelle** et capable de générer des séances.

---

## 🐳 7. Guide de Déploiement & Conteneurisation Docker

Grâce à la conteneurisation complète du projet, aucune installation locale de Python ou de librairies tierces n'est requise.

### 1. Prérequis

Disposer de **Docker Desktop** démarré sur votre machine.

### 2. Lancement de la stack applicative

Placez-vous à la racine du projet et exécutez l'unique commande d'assemblage :

```bash
docker compose up -d --build
```
C'est tout ! L'orchestration est entièrement automatisée. Grâce à un Bilan de santé (Healthcheck) sur le moteur IA et à un Conteneur d'initialisation (Init Container), le modèle llama3.2 se téléchargera tout seul en tâche de fond dès que le serveur sera prêt.

Patientez simplement 1 à 2 minutes (selon votre connexion) jusqu'à ce que le conteneur vibesport-ollama-pull affiche "Exited (0)", puis accédez aux interfaces ci-dessous :

### 3. Accès aux interfaces

* **Interface Frontend de VibeSport :** `http://localhost:8000`
* **Documentation Interactive Swagger :** `http://localhost:8000/docs`

### 4. Commandes de maintenance utiles

* **Consulter les logs de l'API en temps réel :** `docker compose logs -f web`
* **Vérifier le statut de santé des conteneurs :** `docker compose ps`
* **Arrêter proprement l'application :** `docker compose down`

---

## 🧪 8. Résultats de Tests

Le bon fonctionnement de l'application a fait l'objet de tests, validés à travers les logs d'exécution de la stack Docker :

1. **Validation du Self-Healing (404 contrôlé) :** Au démarrage, le frontend a cherché un ancien utilisateur résiduel. Le serveur a répondu `404 Not Found`. Le client a effacé son stockage local et a affiché proprement la création de profil.
2. **Validation de l'Onboarding (201 Created) :** Soumission d'un nouvel utilisateur `pierre`. Le backend a traité et renvoyé le statut de succès attendu :

```text
vibesport-web  | INFO: 192.168.65.1:22857 - "POST /users HTTP/1.1" 201 Created
```

3. **Validation de la Génération IA & RAG (200 OK) :** Lors de la requête de génération d'exercices, le catalogue a été correctement filtré par la logique métier, envoyé au modèle, validé par Pydantic, enrichi par des URLs dynamiques de recherche YouTube pour chaque exercice, et retourné avec succès au client :

```text
vibesport-web  | INFO: 192.168.65.1:22857 - "POST /users/pierre/workouts/generate HTTP/1.1" 200 OK
```

### 🎯 Validation du Prompt Engineering et du RAG local
Pour prouver l'efficacité du "System Prompt" et du RAG, j'ai mené des tests de comportement sur l'IA générative avec différents scénarios :

* **Test A : Respect de la zone ciblée (RAG effectif)**
    * *Entrée :* `target_zone: "Haut du corps"`
    * *Résultat attendu et validé :* Le système a parfaitement filtré le catalogue local. Le JSON renvoyé par l'IA ne contient **que** des exercices du haut du corps (ex: *Pompes diamant, Dips*). L'IA n'a pas halluciné de squats.
* **Test B : Adaptation au temps et à l'énergie**
    * *Entrée :* `available_time_min: 15` et `energy_level: 4` (Fatigué).
    * *Résultat attendu et validé :* L'IA a réduit le volume. Au lieu des 5 exercices habituels avec 4 séries, elle a généré une réponse JSON avec seulement **3 exercices, 2 séries par exercice, et des temps de repos allongés (1 minute au lieu de 30s)**.
* **Extrait d'un payload JSON généré par l'IA (Format strictement respecté) :**
  ```json
  {
    "title": "Haut du corps Express (Récupération)",
    "intro_message": "On y va en douceur aujourd'hui pour respecter ton niveau d'énergie.",
    "exercises": [
      {
        "name": "Pompes sur les genoux",
        "sets": 2,
        "reps": "10 reps",
        "rest_time": "60 secondes",
        "description": "Idéal pour engager les pectoraux sans surcharger le système nerveux.",
        "youtube_search_url": "https://www.youtube.com/results?search_query=tutoriel+Pompes+sur+les+genoux"
      }
    ]
  }
  ```

### 📈 Analyse Critique et Évolution de la Sécurité

Pour ce prototype (MVP), j'ai implémenté une sécurité de type **"Simple Auth"** (un jeton secret transmis dans les en-têtes HTTP) afin de protéger la route de génération d'exercices. C'est une première étape pour ne pas laisser l'API totalement ouverte, mais dans une vraie application, exposer une clé statique unique côté client reste limité.

Conformément aux bonnes pratiques abordées dans le support de cours, l'évolution naturelle de ce projet vers une version de production inclurait le passage à une authentification **JWT (JSON Web Token)**. Cela permettrait :

1. **Un vrai système de connexion :** Remplacer le dictionnaire Python en mémoire (`fake_users_db`) par une véritable base de données où les mots de passe seraient hashés (par exemple avec `passlib`).
2. **Des jetons éphémères et sécurisés :** Délivrer un `access_token` avec une date d'expiration courte (ex: 60 minutes), complété par un `refresh_token` pour maintenir la session de l'athlète de manière transparente.
3. **Le transport de l'identité :** Stocker le nom de l'utilisateur de manière chiffrée directement dans le *payload* du token JWT, rendant les échanges plus sûrs.
4. **La protection absolue des secrets :** Garantir que la `JWT_SECRET_KEY` reste exclusivement dans les variables d'environnement (`.env`) du backend FastAPI, sans jamais transiter vers le frontend.