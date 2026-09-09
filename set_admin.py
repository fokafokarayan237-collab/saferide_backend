import pg8000.native

conn = pg8000.native.Connection(
    user="saferide_6l1x_user",
    password="iEsN2xZEDVLPWmmiI81q9wBXaT0zw37B",
    host="dpg-da7dcu67bikc73ac4di0-a.ohio-postgres.render.com",
    port=5432,
    database="saferide_6l1x",
)

phone = input("Numéro de téléphone du compte à promouvoir admin : ").strip()

rows = conn.run(
    "UPDATE users SET is_admin = TRUE WHERE phone = :phone RETURNING id, phone, is_admin",
    phone=phone,
)

if not rows:
    print(f"Aucun compte trouvé avec le numéro {phone}.")
else:
    user_id, user_phone, is_admin = rows[0]
    print(f"Compte {user_phone} (id={user_id}) est maintenant admin={is_admin}.")

conn.close()
