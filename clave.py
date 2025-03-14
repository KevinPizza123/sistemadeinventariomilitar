import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

print(f"Clave secreta: {app.secret_key}") # Añade esta linea temporalmente

# ... (resto del código)