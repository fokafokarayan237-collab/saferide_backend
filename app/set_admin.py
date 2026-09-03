"""
Script à usage unique : promeut un utilisateur existant au rôle
administrateur, en le désignant par son numéro de téléphone.

Utilisation :
    python set_admin.py

Modifie simplement PHONE_A_PROMOUVOIR ci-dessous avant de lancer.
"""

from pg8000.native import Connection

# ⚠️ Remplace par le numéro de téléphone du compte que tu as déjà créé
# dans l'application (celui que tu veux transformer en administrateur).
PHONE_A_PROMOUVOIR = "6XXXXXXXX"

conn = Connection(
    user="saferide_6l1x_user",
    password="iEsN2xZEDVLPWmmiI81q9wBXaT0zw37B",
    host="dpg-da7dcu67bikc73ac4di0-a.ohio-postgres.render.com",
    database="saferide_6l1x",
    port=5432,
    ssl_context=True,
)

result = conn.run(
    "UPDATE users SET is_admin = true WHERE phone = :phone RETURNING id, phone",
    phone=PHONE_A_PROMOUVOIR,
)

if result:
    print(f"Utilisateur promu administrateur : id={result[0][0]}, phone={result[0][1]}")
else:
    print("Aucun utilisateur trouvé avec ce numéro. Vérifie PHONE_A_PROMOUVOIR.")

conn.close()
