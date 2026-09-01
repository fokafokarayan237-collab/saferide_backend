import pg8000.native

conn = pg8000.native.Connection(
    user="saferide_6l1x_user",
    password="iEsN2xZEDVLPWmmiI81q9wBXaT0zw37B",
    host="dpg-da7dcu67bikc73ac4di0-a.ohio-postgres.render.com",
    port=5432,
    database="saferide_6l1x"
)

rows = conn.run("SELECT id, latitude, longitude FROM evaluations ORDER BY id DESC LIMIT 5;")
print("Dernières évaluations :", rows)

conn.close()