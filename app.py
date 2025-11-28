from flask import Flask, render_template, request, redirect, session, jsonify
import os
import sqlite3
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurações de caminho
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
app.secret_key = os.environ.get("SECRET_KEY", "auracash_secret_key_2025")

# ------------------------------------------
# BANCO DE DADOS
# ------------------------------------------

def get_db():
    try:
        conn = sqlite3.connect('auracash.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro no banco: {e}")
        return None

def init_db():
    try:
        conn = get_db()
        if not conn:
            return
            
        c = conn.cursor()
        
        # Tabela de usuários
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                income REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Verificar se existe algum usuário
        c.execute("SELECT COUNT(*) FROM users")
        count = c.fetchone()[0]
        
        if count == 0:
            c.execute(
                "INSERT INTO users (name, email, password, income) VALUES (?, ?, ?, ?)",
                ("Usuário Teste", "teste@teste.com", "1234", 2000.0)
            )
            logger.info("Usuário de teste criado")
        
        conn.commit()
        conn.close()
        logger.info("Banco inicializado")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")

# ------------------------------------------
# MIDDLEWARE
# ------------------------------------------

@app.before_request
def before_request():
    logger.info(f"Request: {request.method} {request.path}")

# ------------------------------------------
# ROTAS PÚBLICAS
# ------------------------------------------

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()

            if not email or not password:
                return render_template("tlogin.html", error="E-mail e senha são obrigatórios")

            conn = get_db()
            if not conn:
                return render_template("tlogin.html", error="Erro de conexão com o banco")

            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
            user = c.fetchone()
            conn.close()

            if user:
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]
                return redirect("/dashboard")
            else:
                return render_template("tlogin.html", error="E-mail ou senha incorretos")

        return render_template("tlogin.html")
        
    except Exception as e:
        logger.error(f"Erro em login: {e}")
        return render_template("tlogin.html", error="Erro interno")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            income = request.form.get("income", 0) or 0

            if not name or not email or not password:
                return render_template("tcadastro.html", error="Todos os campos são obrigatórios")

            conn = get_db()
            if not conn:
                return render_template("tcadastro.html", error="Erro de conexão com o banco")

            try:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO users (name, email, password, income) VALUES (?, ?, ?, ?)",
                    (name, email, password, float(income))
                )
                conn.commit()
                conn.close()
                return redirect("/login")
            except sqlite3.IntegrityError:
                conn.close()
                return render_template("tcadastro.html", error="E-mail já cadastrado")
            except Exception as e:
                conn.close()
                return render_template("tcadastro.html", error="Erro no cadastro")

        return render_template("tcadastro.html")
    except Exception as e:
        logger.error(f"Erro em cadastro: {e}")
        return render_template("tcadastro.html", error="Erro interno")

# ------------------------------------------
# ROTAS PROTEGIDAS
# ------------------------------------------

def login_required(f):
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route("/dashboard")
@login_required
def dashboard():
    try:
        return render_template("tdashboard.html", user=session.get("user_name", "Usuário"))
    except Exception as e:
        logger.error(f"Erro em dashboard: {e}")
        return redirect("/login")

@app.route("/transacoes")
@login_required
def transacoes():
    try:
        return render_template("transacoes.html")
    except Exception as e:
        logger.error(f"Erro em transacoes: {e}")
        return "Página de transações"

@app.route("/categorias")
@login_required
def categorias():
    try:
        return render_template("tcategorias.html")
    except Exception as e:
        logger.error(f"Erro em categorias: {e}")
        return "Página de categorias"

@app.route("/metas")
@login_required
def metas():
    try:
        return render_template("tmetas.html")
    except Exception as e:
        logger.error(f"Erro em metas: {e}")
        return "Página de metas"

@app.route("/relatorios")
@login_required
def relatorios():
    try:
        return render_template("trelatorio.html")
    except Exception as e:
        logger.error(f"Erro em relatorios: {e}")
        return "Página de relatórios"

@app.route("/dicas")
@login_required
def dicas():
    try:
        return render_template("tDicas.html")
    except Exception as e:
        logger.error(f"Erro em dicas: {e}")
        return "Página de dicas"

@app.route("/empreendedor")
@login_required
def empreendedor():
    try:
        return render_template("empreendedor.html")
    except Exception as e:
        logger.error(f"Erro em empreendedor: {e}")
        return "Página empreendedor"

@app.route("/compartilhada")
@login_required
def compartilhada():
    try:
        return render_template("tcompartilhada.html")
    except Exception as e:
        logger.error(f"Erro em compartilhada: {e}")
        return "Página compartilhada"

@app.route("/configuracoes")
@login_required
def configuracoes():
    try:
        conn = get_db()
        if conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
            user = c.fetchone()
            conn.close()
            return render_template("tConfiguracoes.html", user=user)
        return render_template("tConfiguracoes.html")
    except Exception as e:
        logger.error(f"Erro em configuracoes: {e}")
        return render_template("tConfiguracoes.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ------------------------------------------
# ROTAS DA API
# ------------------------------------------

@app.route("/api/transacao", methods=["POST"])
@login_required
def api_transacao():
    try:
        data = request.json
        # Implementar criação de transação
        return jsonify({"success": True, "message": "Transação criada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/categoria", methods=["POST"])
@login_required
def api_categoria():
    try:
        data = request.json
        # Implementar criação de categoria
        return jsonify({"success": True, "message": "Categoria criada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------------------------
# ROTAS DE UTILIDADE
# ------------------------------------------

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "database": "connected" if get_db() else "disconnected"
    })

@app.route("/debug")
def debug():
    import os
    return jsonify({
        "python_version": os.sys.version,
        "templates_folder": app.template_folder,
        "static_folder": app.static_folder,
        "templates": os.listdir('templates') if os.path.exists('templates') else [],
        "session_keys": list(session.keys())
    })

# ------------------------------------------
# INICIALIZAÇÃO
# ------------------------------------------

if __name__ == "__main__":
    print("Iniciando AuraCash...")
    
    # Log da estrutura
    print("Estrutura de arquivos:")
    for item in os.listdir('.'):
        print(f"  {item}")
    if os.path.exists('templates'):
        print("Templates:", os.listdir('templates'))
    
    # Inicializar banco
    init_db()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
