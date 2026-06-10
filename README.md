# 🏋️‍♂️ VibeSport - Coach Sportif Intelligent (IA Générative & RAG Local)

**VibeSport** est une application web moderne intégrant une architecture client/serveur, une API RESTful **FastAPI**, et un moteur d'intelligence artificielle locale via **Ollama (Llama 3.2)**.

Cette application permet à un utilisateur de s'inscrire, de définir ses préférences sportives et de générer à la demande des séances d'entraînement personnalisées et adaptées à sa forme du jour, tout en conservant un historique de ses entrainements.

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

---

## 🧠 4. Prompt Engineering & Intégration LLM (RAG Local)

La génération de l'entraînement ne délègue pas toute la logique métier au hasard du LLM. Elle utilise une communication déterministe stricte :

1. **Le filtrage RAG :** Le backend parcourt le fichier `data/exercises.json`. Si l'utilisateur demande à cibler le "Haut du corps", le script Python ne sélectionne que les exercices correspondants. Si la liste dépasse 10 exercices, un tirage aléatoire (`random.sample`) extrait un sous-ensemble. Ce catalogue restreint sous forme de chaîne JSON est directement injecté dans les consignes de l'IA.
2. **Le System Prompt :** Un prompt système ultra-directif contraint le modèle à se comporter en entraîneur strict. Il lui est interdit d'inventer un exercice en dehors du menu fourni, et il lui est imposé d'adapter les répétitions au niveau d'énergie saisi par l'athlète.
3. **Le formatage JSON Contraint :** Grâce au paramètre `"format": "json"` envoyé à l'API d'Ollama, le modèle est structurellement forcé de renvoyer une chaîne JSON valide, mappée sur notre schéma Pydantic `WorkoutResponse`.
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

Placez-vous à la racine du projet (là où se trouve le fichier `compose.yaml`) et exécutez la commande d'assemblage :

```bash
docker compose up -d --build

```

*Cette commande va télécharger l'image d'Ollama, construire l'image de l'API FastAPI à partir du `Dockerfile`, isoler le code en respectant le `.dockerignore`, lier les volumes de données et exposer les ports.*

### 3. Initialisation du modèle d'Intelligence Artificielle

Le conteneur Ollama démarre initialement "vide". Pour télécharger localement le modèle requis (`llama3.2`), exécutez la commande d'injection directe dans le conteneur actif :

```bash
docker compose exec ollama ollama pull llama3.2

```

Une fois le téléchargement complété à 100%, la stack est pleinement opérationnelle !

### 4. Accès aux interfaces

* **Interface Frontend de VibeSport :** `http://localhost:8000` (ou double-cliquez directement sur votre fichier `index.html`).
* **Documentation Interactive Swagger :** `http://localhost:8000/docs`

### 5. Commandes de maintenance utiles

* **Consulter les logs de l'API en temps réel :** `docker compose logs -f api`
* **Vérifier le statut de santé des conteneurs :** `docker compose ps`
* **Arrêter proprement l'application :** `docker compose down`

---

## 🧪 8. Résultats de Tests et Rapport de Validation

Le bon fonctionnement de l'application a fait l'objet de tests rigoureux, validés à travers les logs d'exécution de la stack Docker :

1. **Validation du Self-Healing (404 contrôlé) :** Au démarrage, le frontend a cherché un ancien utilisateur résiduel. Le serveur a répondu `404 Not Found`. Le client a effacé son stockage local et a affiché proprement la création de profil.
2. **Validation de l'Onboarding (201 Created) :** Soumission d'un nouvel utilisateur `pierre`. Le backend a traité et renvoyé le statut de succès attendu :
```text
vibesport-web  | INFO: 192.168.65.1:22857 - "POST /users HTTP/1.1" 201 Created

```


3. **Validation de la Génération IA & RAG (200 OK) :** Lors de la requête de génération d'exercices, le catalogue a été correctement filtré par la logique métier, envoyé au modèle, validé par Pydantic, enrichi par des URLs dynamiques de recherche YouTube pour chaque exercice, et retourné avec succès au client :
```text
vibesport-web  | INFO: 192.168.65.1:22857 - "POST /users/pierre/workouts/generate HTTP/1.1" 200 OK

```



### 📈 Analyse Critique de Sécurité (Livrable de Fin d'Étude)

Dans le cadre de ce prototype (MVP) réalisé en 2 semaines, la clé secrète `X-API-Token` est hébergée au sein du fichier de configuration global JavaScript (`app.js`). Nous soulignons que dans une infrastructure d'entreprise réelle, stocker une clé d'en-tête côté client constitue une vulnérabilité (détectable via l'onglet Réseau de l'inspecteur).
Pour une mise en production industrielle, ce système évoluerait vers :

* L'intégration d'une authentification **JWT (JSON Web Token)** dynamique avec paires de clés éphémères (*Access/Refresh Token*) conformément au support de cours avancé.
* La mise en place d'un **Reverse Proxy** (Nginx/Traefik) chargé d'encapsuler la stack dans un tunnel de chiffrement **HTTPS** afin d'empêcher l'interception des en-têtes sur le réseau local.