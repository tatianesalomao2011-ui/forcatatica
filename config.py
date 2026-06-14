import os

class Config:
    # Em produção, o Railway vai ler a variável real. Se não existir, usa o fallback seguro.
    SECRET_KEY = os.environ.get("SECRET_KEY", "uma-chave-ultra-secreta-e-longa-aqui-123")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "database", "database.db")

PATENTES = [
    "Aluno Força Tática",
    "Soldado 2ª Classe",
    "Soldado 1ª Classe",
    "Cabo",
    "3º Sargento",
    "2º Sargento",
    "1º Sargento",
    "Subtenente",
    "Administrador",
    "Aspirante",
    "2º Tenente",
    "1º Tenente",
    "Capitão",
    "Major",
    "Tenente Coronel",
    "Coronel"
]

PATENTES_ADMIN = ["Administrador", "Tenente Coronel", "Coronel"]