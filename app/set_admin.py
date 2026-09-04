from pg8000.native import Connection

PHONE_A_PROMOUVOIR = "658553596"

conn = Connection(
    user="saferide_6l1x_user",
    password="iEsN2xZEDVLPWmmiI81q9wBXaT0zw37B",
    host="dpg-da7dcu67bikc73ac4di0-a.ohio-postgres.render.com",
    database="saferide_6l1x",
    port=5432,
    ssl_context=True,
)

result = conn.run(
    "UPDATE users SET is_admin = TRUE WHERE phone = :phone RETURNING id, phone, is_admin",
    phone=PHONE_A_PROMOUVOIR,
)

if result:
    print(f"Utilisateur promu administrateur : id={result[0][0]}, phone={result[0][1]}, is_admin={result[0][2]}")
else:
    print("Aucun utilisateur trouvé avec ce numéro. Vérifie PHONE_A_PROMOUVOIR.")

conn.close()