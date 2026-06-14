from flask import Flask, render_template, request, redirect, session, flash, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3
import os

from config import Config, PATENTES, PATENTES_ADMIN

app = Flask(__name__)
app.config.from_object(Config)

# =========================
# GERENCIAMENTO DE BANCO DE DADOS
# =========================
def obter_conexao():
    """Abre uma conexão com o banco configurada para retornar dicionários (Row)."""
    conn = sqlite3.connect(app.config["DB_PATH"])
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_sistema():
    """Garante a criação da estrutura de diretórios e tabelas de forma segura."""
    os.makedirs(os.path.dirname(app.config["DB_PATH"]), exist_ok=True)
    
    with obter_conexao() as conn:
        cur = conn.cursor()
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            rgpm TEXT UNIQUE NOT NULL,
            discord_id TEXT UNIQUE NOT NULL,
            patente TEXT NOT NULL,
            senha TEXT NOT NULL,
            status TEXT DEFAULT 'PENDENTE',
            observacao TEXT DEFAULT ''
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS advertencias(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            aplicador TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS certificados(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            curso TEXT NOT NULL,
            assinatura TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS cursos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            data_inicio TEXT,
            data_fim TEXT,
            criado_por TEXT NOT NULL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS inscricoes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curso_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            UNIQUE(curso_id, usuario_id),
            FOREIGN KEY(curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )""")
        conn.commit()

with app.app_context():
    inicializar_sistema()

# =========================
# DECORADORES DE SEGURANÇA (MIDDLEWARES)
# =========================
def login_requerido(f):
    """Garante que o usuário está logado e foi aprovado pela administração."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Por favor, faça login para acessar esta página.")
            return redirect(url_for("login"))
        
        with obter_conexao() as conn:
            user = conn.execute("SELECT status FROM usuarios WHERE id = ?", (session["usuario_id"],)).fetchone()
            
        if not user or user["status"] != "APROVADO":
            session.clear()
            flash("Sua conta não possui permissão ou foi desativada.")
            return redirect(url_for("login"))
            
        return f(*args, **kwargs)
    return decorated_function

def admin_requerido(f):
    """Garante que o usuário possui patente de Oficial Superior (Admin)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
            
        with obter_conexao() as conn:
            user = conn.execute("SELECT patente, status FROM usuarios WHERE id = ?", (session["usuario_id"],)).fetchone()
            
        if not user or user["status"] != "APROVADO" or user["patente"] not in PATENTES_ADMIN:
            flash("Acesso restrito aos Oficiais Superiores da Força Tática.")
            return redirect(url_for("dashboard"))
            
        return f(*args, **kwargs)
    return decorated_function

# =========================
# ROTAS DE AUTENTICAÇÃO E SETUP
# =========================
@app.route("/")
def login():
    with obter_conexao() as conn:
        total = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    
    if total == 0:
        return redirect(url_for("setup"))
    return render_template("login.html")

@app.route("/setup", methods=["GET", "POST"])
def setup():
    with obter_conexao() as conn:
        total = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        
    if total > 0:
        return redirect(url_for("login"))
        
    if request.method == "POST":
        senha_hash = generate_password_hash("forcatatica123")
        with obter_conexao() as conn:
            conn.execute("""
                INSERT INTO usuarios (nome, rgpm, discord_id, patente, senha, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Osvaldo Santos", "1201", "osvaldo_discord", "Tenente Coronel", senha_hash, "APROVADO"))
            conn.commit()
        flash("Administrador Master criado! Conta: Osvaldo Santos | Senha padrão: forcatatica123")
        return redirect(url_for("login"))
        
    return render_template("setup.html")

@app.route("/registro")
def registro():
    return render_template("registro.html", patentes=PATENTES)

@app.route("/registrar", methods=["POST"])
def registrar():
    nome = request.form.get("nome", "").strip()
    rgpm = request.form.get("rgpm", "").strip()
    discord = request.form.get("discord", "").strip()
    patente = request.form.get("patente", "").strip()
    senha = request.form.get("senha")
    confirmar = request.form.get("confirmar")

    if not all([nome, rgpm, discord, patente, senha, confirmar]):
        return "Erro: Todos os campos são obrigatórios!", 400

    if patente not in PATENTES:
        return "Erro: Patente inválida corporativa!", 400

    if senha != confirmar:
        return "Erro: As senhas digitadas não coincidem!", 400

    senha_hash = generate_password_hash(senha)
    
    try:
        with obter_conexao() as conn:
            conn.execute("""
                INSERT INTO usuarios (nome, rgpm, discord_id, patente, senha)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, rgpm, discord, patente, senha_hash))
            conn.commit()
    except sqlite3.IntegrityError:
        return "Erro: Este RGPM ou ID do Discord já consta no sistema!", 400

    flash("Cadastro enviado com sucesso! Aguarde a aprovação de um Oficial.")
    return redirect(url_for("login"))

@app.route("/entrar", methods=["POST"])
def entrar():
    identificador = request.form.get("usuario", "").strip()
    senha = request.form.get("senha")

    with obter_conexao() as conn:
        user = conn.execute("""
            SELECT * FROM usuarios 
            WHERE nome = ? OR rgpm = ? OR discord_id = ?
        """, (identificador, identificador, identificador)).fetchone()

    if not user or not check_password_hash(user["senha"], senha):
        flash("Credenciais incorretas. Tente novamente.")
        return redirect(url_for("login"))

    if user["status"] != "APROVADO":
        if user["status"] == "RECUSADO":
            flash(f"Cadastro recusado. Motivo: {user['observacao']}")
        else:
            flash("Seu cadastro está em análise pela administração.")
        return redirect(url_for("login"))

    session["usuario_id"] = user["id"]
    session["usuario_nome"] = user["nome"]
    session["usuario_patente"] = user["patente"]
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# DASHBOARD & MEMBROS
# =========================
@app.route("/dashboard")
@login_required
def dashboard():
    with obter_conexao() as conn:
        membros = conn.execute("SELECT COUNT(*) FROM usuarios WHERE status='APROVADO'").fetchone()[0]
        advertencias = conn.execute("SELECT COUNT(*) FROM advertencias").fetchone()[0]
        certificados = conn.execute("SELECT COUNT(*) FROM certificados").fetchone()[0]

    return render_template("dashboard.html", membros=membros, advertencias=advertencias, certificados=certificados)

@app.route("/membros")
@login_required
def membros():
    with obter_conexao() as conn:
        usuarios = conn.execute("SELECT id, nome, rgpm, patente, discord_id FROM usuarios WHERE status='APROVADO'").fetchall()
    return render_template("membros.html", usuarios=usuarios)

@app.route("/perfil/<int:id>")
@login_required
def perfil(id):
    with obter_conexao() as conn:
        usuario = conn.execute("SELECT id, nome, rgpm, patente, status, observacao FROM usuarios WHERE id=?", (id,)).fetchone()
        if not usuario:
            abort(404)
        advertencias = conn.execute("SELECT * FROM advertencias WHERE usuario_id=?", (id,)).fetchall()
        certificados = conn.execute("SELECT * FROM certificados WHERE usuario_id=?", (id,)).fetchall()

    return render_template("perfil.html", usuario=usuario, advertencias=advertencias, certificados=certificados)

# =========================
# MODERAÇÃO DE SOLICITAÇÕES (SÓ ADMIN)
# =========================
@app.route("/pendentes")
@admin_required
def pendentes():
    with obter_conexao() as conn:
        usuarios = conn.execute("SELECT id, nome, rgpm, patente, discord_id FROM usuarios WHERE status='PENDENTE'").fetchall()
    return render_template("pendentes.html", usuarios=usuarios)

@app.route("/aprovar/<int:id>", methods=["POST"])
@admin_required
def aprovar(id):
    with obter_conexao() as conn:
        conn.execute("UPDATE usuarios SET status='APROVADO' WHERE id=?", (id,))
        conn.commit()
    flash("Policial aprovado com sucesso!")
    return redirect(url_for("pendentes"))

@app.route("/recusar/<int:id>", methods=["POST"])
@admin_required
def recusar(id):
    obs = request.form.get("observacao", "Não cumpre os requisitos").strip()
    with obter_conexao() as conn:
        conn.execute("UPDATE usuarios SET status='RECUSADO', observacao=? WHERE id=?", (obs, id))
        conn.commit()
    flash("Solicitação recusada.")
    return redirect(url_for("pendentes"))

# =========================
# SISTEMA DE ADVERTÊNCIAS
# =========================
@app.route("/advertencias")
@login_required
def advertencias():
    with obter_conexao() as conn:
        usuarios = conn.execute("SELECT id, nome FROM usuarios WHERE status='APROVADO'").fetchall()
        lista = conn.execute("""
            SELECT adv.*, u.nome AS nome_usuario, u.patente AS patente_usuario
            FROM advertencias adv
            INNER JOIN usuarios u ON u.id = adv.usuario_id
            ORDER BY adv.id DESC
        """).fetchall()
    return render_template("advertencias.html", usuarios=usuarios, advertencias=lista)

@app.route("/aplicar_advertencia", methods=["POST"])
@admin_required
def aplicar_advertencia():
    usuario_id = request.form.get("usuario_id")
    motivo = request.form.get("motivo", "").strip()
    aplicador = session.get("usuario_nome", "Oficial Superior")
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not usuario_id or not motivo:
        flash("Preencha todos os campos da advertência!")
        return redirect(url_for("advertencias"))

    with obter_conexao() as conn:
        conn.execute("INSERT INTO advertencias (usuario_id, motivo, aplicador, data) VALUES (?, ?, ?, ?)", 
                     (usuario_id, motivo, aplicador, data))
        conn.commit()
    flash("Advertência lavrada com sucesso!")
    return redirect(url_for("advertencias"))

@app.route("/remover_advertencia/<int:id>", methods=["POST"])
@admin_required
def remover_advertencia(id):
    with obter_conexao() as conn:
        conn.execute("DELETE FROM advertencias WHERE id=?", (id,))
        conn.commit()
    flash("Advertência retirada.")
    return redirect(url_for("advertencias"))

# =========================
# SISTEMA DE CERTIFICADOS
# =========================
@app.route("/certificados")
@login_required
def certificados():
    with obter_conexao() as conn:
        usuarios = conn.execute("SELECT id, nome FROM usuarios WHERE status='APROVADO'").fetchall()
        lista = conn.execute("""
            SELECT cert.*, u.nome AS nome_usuario
            FROM certificados cert
            INNER JOIN usuarios u ON u.id = cert.usuario_id
            ORDER BY cert.id DESC
        """).fetchall()
    return render_template("certificados.html", usuarios=usuarios, certificados=lista)

@app.route("/emitir_certificado", methods=["POST"])
@admin_required
def emitir_certificado():
    usuario_id = request.form.get("usuario_id")
    curso = request.form.get("curso", "").strip()
    assinatura = request.form.get("assinatura", "").strip()
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not all([usuario_id, curso, assinatura]):
        flash("Todos os campos de emissão são obrigatórios.")
        return redirect(url_for("certificados"))

    with obter_conexao() as conn:
        conn.execute("INSERT INTO certificados (usuario_id, curso, assinatura, data) VALUES (?, ?, ?, ?)", 
                     (usuario_id, curso, assinatura, data))
        conn.commit()
    return redirect(url_for("certificados"))

@app.route("/remover_certificado/<int:id>", methods=["POST"])
@admin_required
def remover_certificado(id):
    with obter_conexao() as conn:
        conn.execute("DELETE FROM certificados WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for("certificados"))

# =========================
# GESTÃO DE CURSOS E INSCRIÇÕES
# =========================
@app.route("/cursos")
@login_required
def cursos():
    with obter_conexao() as conn:
        cursos_lista = conn.execute("SELECT * FROM cursos").fetchall()
        inscritos = conn.execute("""
            SELECT i.curso_id, u.nome AS nome_usuario, u.patente
            FROM inscricoes i
            INNER JOIN usuarios u ON u.id = i.usuario_id
        """).fetchall()
    return render_template("cursos.html", cursos=cursos_lista, inscritos=inscritos)

@app.route("/novo_curso")
@admin_required
def novo_curso():
    return render_template("criar_curso.html")

@app.route("/criar_curso", methods=["POST"])
@admin_required
def criar_curso():
    nome = request.form.get("nome", "").strip()
    descricao = request.form.get("descricao", "").strip()
    inicio = request.form.get("inicio", "").strip()
    fim = request.form.get("fim", "").strip()
    criador = session.get("usuario_nome", "Admin")

    if not nome:
        flash("O nome do curso é estritamente obrigatório.")
        return redirect(url_for("novo_curso"))

    with obter_conexao() as conn:
        conn.execute("INSERT INTO cursos (nome, descricao, data_inicio, data_fim, criado_por) VALUES (?, ?, ?, ?, ?)", 
                     (nome, descricao, inicio, fim, criador))
        conn.commit()
    return redirect(url_for("cursos"))

@app.route("/inscrever_curso/<int:id>", methods=["POST"])
@login_required
def inscrever_curso(id):
    try:
        with obter_conexao() as conn:
            conn.execute("INSERT INTO inscricoes (curso_id, usuario_id) VALUES (?, ?)", (id, session["usuario_id"]))
            conn.commit()
        flash("Inscrição realizada com sucesso!")
    except sqlite3.IntegrityError:
        flash("Você já está inscrito neste curso.")
    return redirect(url_for("cursos"))

@app.route("/encerrar_curso/<int:id>", methods=["POST"])
@admin_required
def encerrar_curso(id):
    with obter_conexao() as conn:
        curso = conn.execute("SELECT nome FROM cursos WHERE id=?", (id,)).fetchone()
        if not curso:
            abort(404)
            
        alunos = conn.execute("SELECT usuario_id FROM inscricoes WHERE curso_id=?", (id,)).fetchall()
        
        assinatura = f"{session.get('usuario_patente')} {session.get('usuario_nome')} - Comando Geral"
        data = datetime.now().strftime("%d/%m/%Y %H:%M")

        for aluno in alunos:
            conn.execute("INSERT INTO certificados (usuario_id, curso, assinatura, data) VALUES (?, ?, ?, ?)", 
                         (aluno["usuario_id"], curso["nome"], assinatura, data))
            
        # Deleta as inscrições do curso encerrado automaticamente
        conn.execute("DELETE FROM inscricoes WHERE curso_id=?", (id,))
        conn.commit()

    flash(f"Curso '{curso['nome']}' finalizado. Certificados gerados aos formandos.")
    return redirect(url_for("cursos"))

if __name__ == "__main__":
    app.run(debug=True)