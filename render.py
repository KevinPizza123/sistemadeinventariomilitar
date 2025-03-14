import psycopg2

DATABASE_URL = "postgresql://gestion_locales_user:SBt1IjWBA09qqXuiGNJyXFJtukOw6MRb@dpg-cv9od4lumphs73a9jksg-a/gestion_locales"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Ejecuta tus consultas SQL aquí
    cur.execute("SELECT * FROM Vendedores;")
    rows = cur.fetchall()
    for row in rows:
        print(row)

    cur.close()
    conn.close()
except psycopg2.Error as e:
    print(f"Error connecting to database: {e}")
    #paella
    