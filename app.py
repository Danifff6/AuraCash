from flask import Flask, render_template, request, redirect, session, jsonify
import os
import sqlite3

# Obter o diretório atual
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(current_dir, 'static')

print(f"📁 Diretório atual: {current_dir}")
print(f"📄 Pasta de templates: {template_dir}")
print(f"🎨 Pasta static: {static_dir}")

# Verificar se a pasta templates existe
if os.path.exists(template_dir):
    print("✅ Pasta templates encontrada!")
    print("📄 Arquivos na pasta templates:")
    for file in os.listdir(template_dir):
        print(f"   - {file}")
else:
    print("❌ Pasta templates NÃO encontrada!")

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
app.secret_key = os.environ.get("SECRET_KEY", "auracash_secret_2025_dev")

# ------------------------------------------
# BANCO DE DADOS
# ------------------------------------------

def get_db():
    conn = sqlite3.connect('auracash.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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
    
    # Inserir usuário de teste se a tabela estiver vazia
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    
    if count == 0:
        c.execute(
            "INSERT INTO users (name, email, password, income) VALUES (?, ?, ?, ?)",
            ("Usuário Teste", "teste@teste.com", "1234", 2000.0)
        )
        print("✅ Usuário de teste criado")
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")

# ------------------------------------------
# ROTAS DE AUTENTICAÇÃO
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
        print(f"❌ Erro em login: {str(e)}")
        return render_template("tlogin.html", error="Erro interno do servidor")

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
            c = conn.cursor()

            try:
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
        print(f"❌ Erro em cadastro: {str(e)}")
        return render_template("tcadastro.html", error="Erro interno do servidor")

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
        # Calcular totais básicos
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'", (session["user_id"],))
        total_income = c.fetchone()[0] or 0
        
        c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'", (session["user_id"],))
        total_expense = c.fetchone()[0] or 0
        
        balance = total_income - total_expense
        conn.close()
        
        return render_template("tdashboard.html", 
                             user=session.get("user_name", "Usuário"),
                             total_income=total_income,
                             total_expense=total_expense,
                             balance=balance)
    except Exception as e:
        print(f"❌ Erro em dashboard: {str(e)}")
        return render_template("tdashboard.html", 
                             user=session.get("user_name", "Usuário"),
                             total_income=0,
                             total_expense=0,
                             balance=0)

@app.route("/configuracoes")
@login_required
def configuracoes():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        user = c.fetchone()
        conn.close()
        
        return render_template("tConfiguracoes.html", user=user)
    except Exception as e:
        print(f"❌ Erro em configuracoes: {str(e)}")
        return render_template("tConfiguracoes.html")

# ------------------------------------------
# ROTAS PARA PÁGINAS BÁSICAS
# ------------------------------------------

@app.route("/transacoes")
@login_required
def transacoes():
    return "Página de transações - Em desenvolvimento"

@app.route("/categorias")
@login_required
def categorias():
    return "Página de categorias - Em desenvolvimento"

@app.route("/metas")
@login_required
def metas():
    return "Página de metas - Em desenvolvimento"

@app.route("/relatorios")
@login_required
def relatorios():
    return "Página de relatórios - Em desenvolvimento"

@app.route("/dicas")
@login_required
def dicas():
    return "Página de dicas - Em desenvolvimento"

@app.route("/empreendedor")
@login_required
def empreendedor():
    return "Página empreendedor - Em desenvolvimento"

@app.route("/compartilhada")
@login_required
def compartilhada():
    return "Página compartilhada - Em desenvolvimento"

# ------------------------------------------
# ROTAS DE API E UTILITÁRIOS
# ------------------------------------------

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "templates_folder": app.template_folder,
        "static_folder": app.static_folder,
        "templates_exists": os.path.exists(template_dir),
        "templates_files": os.listdir(template_dir) if os.path.exists(template_dir) else []
    })

@app.route("/debug")
def debug():
    import os
    info = {
        "current_directory": os.getcwd(),
        "files_in_root": os.listdir('.'),
        "templates_directory": template_dir,
        "templates_exists": os.path.exists(template_dir),
        "templates_files": os.listdir(template_dir) if os.path.exists(template_dir) else "NOT FOUND",
        "session_keys": list(session.keys())
    }
    return jsonify(info)

# ------------------------------------------
# INICIALIZAÇÃO
# ------------------------------------------

if __name__ == "__main__":
    print("🚀 Iniciando AuraCash...")
    
    # Inicializar banco de dados
    init_db()
    
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    print(f"🌐 Servidor iniciando na porta: {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
