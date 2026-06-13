from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "forca_tatica_13bpm"

# Ajuste para caminho absoluto (evita erros de diretório no Railway)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "database", "database.db")


# =========================
# BANCO DE DADOS
# =========================
def conectar():
    return sqlite3.connect(DB)


def criar_banco():
    # Garante que a pasta database existe no servidor
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    
    conn = conectar()
    cur = conn.cursor()

    # USUÁRIOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        rgpm TEXT UNIQUE,
        discord_id TEXT UNIQUE,
        patente TEXT,
        senha TEXT,
        status TEXT DEFAULT 'PENDENTE',
        observacao TEXT DEFAULT ''
    )
    """)

    # ADVERTÊNCIAS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS advertencias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        motivo TEXT,
        aplicador TEXT,
        data TEXT
    )
    """)

    # CERTIFICADOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS certificados(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        curso TEXT,
        assinatura TEXT,
        data TEXT
    )
    """)

    # CURSOS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cursos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        data_inicio TEXT,
        data_fim TEXT,
        criado_por TEXT
    )
    """)

    # INSCRIÇÕES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inscricoes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER,
        usuario_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

# ISSO GARANTE QUE O BANCO VAI SER CRIADO NO RAILWAY MESMO USANDO GUNICORN
with app.app_context():
    criar_banco()


# =========================
# PERMISSÕES E AUXILIARES
# =========================
def get_user():
    if "usuario" not in session:
        return None

    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE nome=?", (session["usuario"],))
    user = cur.fetchone()
    conn.close()
    return user


def is_admin():
    user = get_user()
    if not user or len(user) < 5:
        return False
    return user[4] in ["Coronel", "Tenente Coronel", "Major"]


def is_approved():
    user = get_user()
    if not user or len(user) < 7:
        return False
    return user[6] == "APROVADO"


# =========================
# LOGIN / REGISTRO
# =========================
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/registro")
def registro():
    try:
        from config import PATENTES
    except ImportError:
        PATENTES = ["Soldado", "Cabo", "Sargento", "Subtenente", "Tenente", "Capitão", "Major", "Tenente Coronel", "Coronel"]
    return render_template("registro.html", patentes=PATENTES)


@app.route("/registrar", methods=["POST"])
def registrar():
    nome = request.form["nome"]
    rgpm = request.form["rgpm"]
    discord = request.form["discord"]
    patente = request.form["patente"]
    senha = request.form["senha"]
    confirmar = request.form["confirmar"]

    if senha != confirmar:
        return "Erro: A senha e a confirmação de senha não são iguais!", 400

    senha_hash = generate_password_hash(senha)

    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("""
        INSERT INTO usuarios (nome, rgpm, discord_id, patente, senha)
        VALUES (?, ?, ?, ?, ?)
        """, (nome, rgpm, discord, patente, senha_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Erro: Este RGPM ou ID do Discord já está cadastrado no sistema!", 400
    finally:
        conn.close()

    return redirect(url_for("login"))


@app.route("/entrar", methods=["POST"])
def entrar():
    usuario = request.form["usuario"]
    senha = request.form["senha"]

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM usuarios
    WHERE nome=? OR rgpm=? OR discord_id=?
    """, (usuario, usuario, usuario))
    user = cur.fetchone()
    conn.close()

    if not user:
        flash("Usuário, RGPM ou Discord ID não encontrado.")
        return redirect(url_for("login"))

    if user[6] != "APROVADO":
        if user[6] == "RECUSADO":
            flash(f"Seu cadastro foi recusado. Motivo: {user[7]}")
        else:
            flash("Seu cadastro ainda está PENDENTE de aprovação pela administração.")
        return redirect(url_for("login"))

    if not check_password_hash(user[5], senha):
        flash("Senha incorreta.")
        return redirect(url_for("login"))

    session["usuario"] = user[1]
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM usuarios WHERE status='APROVADO'")
    membros = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM advertencias")
    advertencias = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM certificados")
    certificados = cur.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        membros=membros,
        advertencias=advertencias,
        certificados=certificados
    )


# =========================
# PENDENTES
# =========================
@app.route("/pendentes")
def pendentes():
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE status='PENDENTE'")
    usuarios = cur.fetchall()
    conn.close()

    return render_template("pendentes.html", usuarios=usuarios)


@app.route("/aprovar/<int:id>", methods=["POST"])
def aprovar(id):
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET status='APROVADO' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("pendentes"))


@app.route("/recusar/<int:id>", methods=["POST"])
def recusar(id):
    if not is_approved():
        return redirect(url_for("login"))

    obs = request.form["observacao"]

    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET status='RECUSADO', observacao=? WHERE id=?", (obs, id))
    conn.commit()
    conn.close()

    return redirect(url_for("pendentes"))


# =========================
# MEMBROS
# =========================
@app.route("/membros")
def membros():
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE status='APROVADO'")
    usuarios = cur.fetchall()
    conn.close()

    return render_template("membros.html", usuarios=usuarios)


@app.route("/perfil/<int:id>")
def perfil(id):
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios WHERE id=?", (id,))
    usuario = cur.fetchone()

    cur.execute("SELECT * FROM advertencias WHERE usuario_id=?", (id,))
    advertencias = cur.fetchall()

    cur.execute("SELECT * FROM certificados WHERE usuario_id=?", (id,))
    certificados = cur.fetchall()

    conn.close()

    return render_template(
        "perfil.html",
        usuario=usuario,
        advertencias=advertencias,
        certificados=certificados
    )


# =========================
# ADVERTÊNCIAS
# =========================
@app.route("/advertencias")
def advertencias():
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios WHERE status='APROVADO'")
    usuarios = cur.fetchall()

    cur.execute("""
    SELECT advertencias.*, usuarios.nome
    FROM advertencias
    INNER JOIN usuarios ON usuarios.id = advertencias.usuario_id
    ORDER BY advertencias.id DESC
    """)
    lista = cur.fetchall()
    conn.close()

    return render_template(
        "advertencias.html",
        usuarios=usuarios,
        advertencias=lista
    )


@app.route("/aplicar_advertencia", methods=["POST"])
def aplicar_advertencia():
    if not is_approved():
        return redirect(url_for("login"))

    usuario_id = request.form["usuario_id"]
    motivo = request.form["motivo"]
    aplicador = session.get("usuario", "Desconhecido")
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO advertencias (usuario_id, motivo, aplicador, data)
    VALUES (?, ?, ?, ?)
    """, (usuario_id, motivo, aplicador, data))
    conn.commit()
    conn.close()

    return redirect(url_for("advertencias"))


@app.route("/remover_advertencia/<int:id>", methods=["POST"])
def remover_advertencia(id):
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM advertencias WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("advertencias"))


# =========================
# CERTIFICADOS
# =========================
@app.route("/certificados")
def certificados():
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios WHERE status='APROVADO'")
    usuarios = cur.fetchall()

    cur.execute("""
    SELECT certificados.*, usuarios.nome
    FROM certificados
    INNER JOIN usuarios ON usuarios.id = certificados.usuario_id
    ORDER BY certificados.id DESC
    """)
    lista = cur.fetchall()
    conn.close()

    return render_template(
        "certificados.html",
        usuarios=usuarios,
        certificados=lista
    )


@app.route("/emitir_certificado", methods=["POST"])
def emitir_certificado():
    if not is_approved():
        return redirect(url_for("login"))

    usuario_id = request.form["usuario_id"]
    curso = request.form["curso"]
    assinatura = request.form["assinatura"]
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO certificados (usuario_id, curso, assinatura, data)
    VALUES (?, ?, ?, ?)
    """, (usuario_id, curso, assinatura, data))
    conn.commit()
    conn.close()

    return redirect(url_for("certificados"))


@app.route("/remover_certificado/<int:id>", methods=["POST"])
def remover_certificado(id):
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM certificados WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("certificados"))


# =========================
# CURSOS
# =========================
@app.route("/cursos")
def cursos():
    if not is_approved():
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT * FROM cursos")
    cursos_lista = cur.fetchall()

    cur.execute("""
    SELECT inscricoes.curso_id, usuarios.nome
    FROM inscricoes
    INNER JOIN usuarios ON usuarios.id = inscricoes.usuario_id
    """)
    inscritos = cur.fetchall()
    conn.close()

    return render_template(
        "cursos.html",
        cursos=cursos_lista,
        inscritos=inscritos
    )


@app.route("/novo_curso")
def novo_curso():
    if not is_admin():
        return "Acesso negado", 403
    return render_template("criar_curso.html")


@app.route("/criar_curso", methods=["POST"])
def criar_curso():
    if not is_admin():
        return "Acesso negado", 403

    nome = request.form["nome"]
    descricao = request.form["descricao"]
    inicio = request.form["inicio"]
    fim = request.form["fim"]
    criador = session.get("usuario", "Admin")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO cursos (nome, descricao, data_inicio, data_fim, criado_por)
    VALUES (?, ?, ?, ?, ?)
    """, (nome, descricao, inicio, fim, criador))
    conn.commit()
    conn.close()

    return redirect(url_for("cursos"))


@app.route("/inscrever_curso/<int:id>", methods=["POST"])
def inscrever_curso(id):
    if not is_approved():
        return redirect(url_for("login"))

    user = get_user()
    if not user:
        flash("Sessão expirada. Faça login novamente.")
        return redirect(url_for("login"))

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO inscricoes (curso_id, usuario_id)
    VALUES (?, ?)
    """, (id, user[0]))
    conn.commit()
    conn.close()

    return redirect(url_for("cursos"))


@app.route("/encerrar_curso/<int:id>", methods=["POST"])
def encerrar_curso(id):
    if not is_admin():
        return "Acesso negado", 403

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT nome FROM cursos WHERE id=?", (id,))
    curso = cur.fetchone()

    cur.execute("SELECT usuario_id FROM inscricoes WHERE curso_id=?", (id,))
    alunos = cur.fetchall()

    if not curso:
        conn.close()
        return "Curso não encontrado", 404

    assinatura = "Tenente Coronel Oswaldo Santos - RGPM64832"
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    for a in alunos:
        cur.execute("""
        INSERT INTO certificados (usuario_id, curso, assinatura, data)
        VALUES (?, ?, ?, ?)
        """, (a[0], curso[0], assinatura, data))

    conn.commit()
    conn.close()

    return redirect(url_for("cursos"))


if __name__ == "__main__":
    app.run(debug=True)