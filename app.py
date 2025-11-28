from flask import Flask, render_template, request, redirect, session, jsonify, g
import sqlite3
import os
import traceback
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "auracash_secret_2025_dev")

# Configuração do banco de dados
if os.environ.get("DATABASE_URL"):
    # PostgreSQL no Railway
    app.config['DATABASE'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    # SQLite local
    app.config['DATABASE'] = 'auracash.db'

# ------------------------------------------
# CONEXÃO COM BANCO DE DADOS
# ------------------------------------------

def get_db():
    if 'db' not in g:
        try:
            if app.config['DATABASE'].startswith('postgresql://'):
                # PostgreSQL
                import psycopg2
                g.db = psycopg2.connect(app.config['DATABASE'], sslmode='require')
                g.db.autocommit = True
            else:
                # SQLite
                g.db = sqlite3.connect(app.config['DATABASE'])
                g.db.row_factory = sqlite3.Row
        except Exception as e:
            print(f"❌ Erro ao conectar com o banco: {e}")
            return None
    return g.db

def init_db():
    with app.app_context():
        db = get_db()
        if db:
            create_tables(db)

def create_tables(db):
    try:
        cursor = db.cursor()
        
        # Verificar se estamos usando PostgreSQL ou SQLite
        is_postgres = app.config['DATABASE'].startswith('postgresql://')
        
        # Tabela de usuários
        if is_postgres:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    income REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    income REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        print("✅ Tabelas verificadas/criadas com sucesso!")
        
        # Inserir usuário de teste se a tabela estiver vazia
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute(
                "INSERT INTO users (name, email, password, income) VALUES (%s, %s, %s, %s)" if is_postgres 
                else "INSERT INTO users (name, email, password, income) VALUES (?, ?, ?, ?)",
                ("Usuário Teste", "teste@teste.com", "1234", 2000.0)
            )
            print("✅ Usuário de teste criado")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        if not is_postgres:
            db.rollback()

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# ------------------------------------------
# MIDDLEWARE PARA LOGS
# ------------------------------------------

@app.before_request
def log_request():
    print(f"📥 {request.method} {request.path}")

@app.after_request
def log_response(response):
    print(f"📤 {response.status_code} {request.path}")
    return response

# ------------------------------------------
# ROTAS DE AUTENTICAÇÃO (CORRIGIDAS)
# ------------------------------------------

@app.route("/")
def home():
    try:
        if "user_id" in session:
            return redirect("/dashboard")
        return redirect("/login")
    except Exception as e:
        print(f"❌ Erro em home: {e}")
        return "Erro interno do servidor", 500

@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()

            if not email or not password:
                return render_template("login.html", error="E-mail e senha são obrigatórios")

            db = get_db()
            if not db:
                return render_template("login.html", error="Erro de conexão com o banco de dados")

            cursor = db.cursor()
            
            # Verificar se é PostgreSQL ou SQLite
            is_postgres = app.config['DATABASE'].startswith('postgresql://')
            
            try:
                if is_postgres:
                    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
                else:
                    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
                
                user = cursor.fetchone()
                
                if user:
                    session["user_id"] = user[0]
                    session["user_name"] = user[1]
                    session["user_email"] = user[2]
                    return redirect("/dashboard")
                else:
                    return render_template("login.html", error="E-mail ou senha incorretos")
                    
            except Exception as e:
                print(f"❌ Erro na consulta: {e}")
                init_db()  # Tentar criar tabelas se não existirem
                return render_template("login.html", error="Sistema em inicialização. Tente novamente.")

        return render_template("login.html")
        
    except Exception as e:
        print(f"❌ Erro em login: {e}")
        return render_template("login.html", error="Erro interno do servidor")

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            income = request.form.get("income", 0) or 0

            if not name or not email or not password:
                return render_template("registrar.html", error="Todos os campos são obrigatórios")

            db = get_db()
            if not db:
                return render_template("registrar.html", error="Erro de conexão com o banco de dados")

            cursor = db.cursor()
            is_postgres = app.config['DATABASE'].startswith('postgresql://')

            try:
                if is_postgres:
                    cursor.execute(
                        "INSERT INTO users (name, email, password, income) VALUES (%s, %s, %s, %s)",
                        (name, email, password, float(income))
                    )
                else:
                    cursor.execute(
                        "INSERT INTO users (name, email, password, income) VALUES (?, ?, ?, ?)",
                        (name, email, password, float(income))
                    )
                
                return redirect("/login")
                
            except Exception as e:
                print(f"❌ Erro no cadastro: {e}")
                error_msg = "E-mail já cadastrado" if "unique" in str(e).lower() else "Erro no cadastro"
                return render_template("registrar.html", error=error_msg)

        return render_template("registrar.html")
        
    except Exception as e:
        print(f"❌ Erro em registrar: {e}")
        return render_template("registrar.html", error="Erro interno do servidor")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

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
        print(f"❌ Erro em dashboard: {e}")
        return redirect("/login")

@app.route("/transacoes")
@login_required
def transacoes():
    return render_template("transacoes.html")

@app.route("/categorias")
@login_required
def categorias():
    return render_template("tcategorias.html")

@app.route("/metas")
@login_required
def metas():
    return render_template("tmetas.html")

@app.route("/relatorios")
@login_required
def relatorios():
    return render_template("trelatorio.html")

@app.route("/dicas")
@login_required
def dicas():
    return render_template("tDicas.html")

@app.route("/empreendedor")
@login_required
def empreendedor():
    return render_template("empreendedor.html")

@app.route("/compartilhada")
@login_required
def compartilhada():
    return render_template("tcompartilhada.html")

@app.route("/configuracoes")
@login_required
def configuracoes():
    return render_template("tConfiguracoes.html")

# ------------------------------------------
# ROTAS DE API E UTILITÁRIOS
# ------------------------------------------

@app.route("/health")
def health_check():
    db_status = "connected" if get_db() else "disconnected"
    return jsonify({
        "status": "healthy", 
        "database": db_status,
        "templates": "ok"
    })

@app.route("/debug")
def debug():
    info = {
        "python_version": os.sys.version,
        "database_url": app.config['DATABASE'][:50] + "..." if len(app.config['DATABASE']) > 50 else app.config['DATABASE'],
        "session_keys": list(session.keys()),
        "templates_folder": app.template_folder,
        "static_folder": app.static_folder
    }
    return jsonify(info)

# ------------------------------------------
# INICIALIZAÇÃO
# ------------------------------------------

if __name__ == "__main__":
    print("🚀 Iniciando AuraCash...")
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"📊 Banco de dados: {app.config['DATABASE']}")
    
    # Listar arquivos para debug
    try:
        print("📁 Conteúdo do diretório:")
        for item in os.listdir('.'):
            print(f"   {item}")
        if os.path.exists('templates'):
            print("📄 Templates encontrados:")
            for template in os.listdir('templates'):
                print(f"   - {template}")
    except Exception as e:
        print(f"❌ Erro ao listar arquivos: {e}")
    
    # Inicializar banco
    with app.app_context():
        init_db()
    
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    print(f"🌐 Servidor iniciando na porta: {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
