import pg8000.native

conn = pg8000.native.Connection(
    user="saferide_6l1x_user",
    password="iEsN2xZEDVLPWmmiI81q9wBXaT0zw37B",
    host="dpg-da7dcu67bikc73ac4di0-a.ohio-postgres.render.com",
    port=5432,
    database="saferide_6l1x"
)

conn.run("DROP SCHEMA public CASCADE;")
conn.run("CREATE SCHEMA public;")

print("Schéma réinitialisé avec succès !")

conn.close()