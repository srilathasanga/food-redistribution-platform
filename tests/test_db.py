import psycopg2

connection = psycopg2.connect(
    host="localhost",
    port=5432,
    database="food_redistribution",
    user="postgres",
    password="Jesus@26#"
)

print("Database connection successful!")

connection.close()