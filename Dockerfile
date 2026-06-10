# 1. On part d'une image Python officielle, version légère (slim)
FROM python:3.11-slim

# 2. On définit le dossier de travail dans le conteneur
WORKDIR /app

# 3. On copie d'abord le fichier des dépendances
COPY requirements.txt .

# 4. On installe les librairies Python
RUN pip install --no-cache-dir -r requirements.txt

# 5. On copie tout le reste de notre projet dans le conteneur
# (Les dossiers app, data et frontend)
COPY . .

# 6. On expose le port 8000 (celui qu'utilise FastAPI)
EXPOSE 8000

# 7. La commande pour démarrer l'application quand le conteneur se lance
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]