# SafeRide Cameroun — Backend API

## Lancer en local

```bash
python -m venv venv
source venv/bin/activate       # Windows : venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

L'API est alors disponible sur `http://127.0.0.1:8000`, avec la doc
interactive sur `http://127.0.0.1:8000/docs`.

## Base de données

Créer une base MySQL vide nommée `saferide` (ou adapter `DATABASE_URL`) :

```sql
CREATE DATABASE saferide CHARACTER SET utf8mb4;
```

Puis définir la variable d'environnement avant de lancer l'API :

```bash
export DATABASE_URL="mysql+pymysql://<user>:<password>@localhost:3306/saferide"
export SECRET_KEY="change-moi-en-production"
```

Les tables `users` et `evaluations` sont créées automatiquement au démarrage
(`Base.metadata.create_all` dans `main.py`). Pour un projet amené à évoluer,
il vaudra mieux migrer vers **Alembic** plutôt que de garder cette approche.

## Endpoints actuels

| Méthode | Route            | Statut                                          |
|---------|------------------|---------------------------------------------------|
| POST    | `/auth/register` | Fonctionnel — crée un compte (MySQL + JWT)         |
| POST    | `/auth/login`    | Fonctionnel — vérifie le mot de passe (bcrypt)     |
| POST    | `/predict`       | Fonctionnel — modèle ML si présent, sinon règles ; enregistre l'évaluation |
| GET     | `/history`       | Fonctionnel — nécessite d'être connecté            |
| GET     | `/health`        | Fonctionnel                                        |

## Modèle ML

Un modèle Random Forest entraîné se trouve dans `ml_model/risk_model.joblib`.
`app/services/risk_model.py` le charge automatiquement au démarrage ; s'il
est absent ou introuvable, l'API bascule sur un scoring à base de règles
(comportement identique à avant, aucune erreur).

⚠️ **Ce modèle a été entraîné sur des données synthétiques** (voir le
projet `saferide_ml/` fourni séparément), uniquement pour valider le
pipeline de bout en bout. Il faut le ré-entraîner sur les vrais datasets
(Kaggle + données locales, Phase 1/3 du projet) avant toute mise en
production — il suffit de relancer `train_model.py` sur les vraies
données et de remplacer `ml_model/risk_model.joblib` par le nouveau
fichier généré.

`/predict` et `/history` attendent un header `Authorization: Bearer <token>`
(le token renvoyé par `/auth/login` ou `/auth/register`).

## Prochaines étapes

1. **Modèle ML** : une fois le dataset nettoyé (Phase 1) et le modèle
   Random Forest entraîné (Phase 3), remplacer le contenu de
   `app/services/risk_model.py::compute_risk` par un appel au modèle
   sauvegardé (`joblib.load(...)`), en gardant la même signature.
2. **Migrations** : remplacer `create_all` par Alembic si le schéma évolue.
3. **Tests automatisés** : ajouter `pytest` + une base SQLite en mémoire
   pour les tests, sans dépendre d'un vrai serveur MySQL.

## Connexion depuis l'app Flutter

Le service `lib/services/api_service.dart` de l'app mobile appelle déjà
`/auth/login` et stocke le token reçu (`setAuthToken`). Il faudra ajouter
un appel à `/auth/register` côté app pour le bouton "Créer un compte"
(actuellement sans action) et propager le token aux appels `/predict` et
`/history`, qui exigent maintenant d'être authentifiés.
