from flask import Flask, render_template, request, redirect, session, jsonify, g
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "auracash_secret_2025"
app.config['DATABASE'] = 'auracash.db'

# ------------------------------------------
# CONEXÃO COM BANCO DE DADOS
# ------------------------------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    with app.app_context():
        db = get_db()
        create_tables(db)

def create_tables(db):
    cursor = db.cursor()

    # Tabela de usuários
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

    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Tabela de transações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            category_id INTEGER,
            amount REAL NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)

    # Tabela de metas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)

    # Tabela de materiais (empreendedor)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            total_value REAL NOT NULL,
            quantity REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Tabela de contas compartilhadas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shared_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            share_id TEXT UNIQUE NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    """)

    # Tabela de membros das contas compartilhadas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shared_account_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES shared_accounts (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(account_id, user_id)
        )
    """)

    db.commit()

# Fechar conexão com o banco
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# ------------------------------------------
# ROTAS DE AUTENTICAÇÃO
# ------------------------------------------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect("/dashboard")
        else:
            return render_template("tlogin.html", error="E-mail ou senha incorretos")

    return render_template("tlogin.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        income = request.form.get("income", 0)

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("INSERT INTO users (name, email, password, income) VALUES (?, ?, ?, ?)",
                          (name, email, password, income))
            db.commit()
            return redirect("/login")
        except sqlite3.IntegrityError:
            return render_template("tcadastro.html", error="E-mail já cadastrado")

    return render_template("tcadastro.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ------------------------------------------
# ROTAS PRINCIPAIS
# ------------------------------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    # Calcular totais
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'", (user_id,))
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'", (user_id,))
    total_expense = cursor.fetchone()[0] or 0

    balance = total_income - total_expense

    # Últimas transações
    cursor.execute("""
        SELECT t.*, c.name as category_name 
        FROM transactions t 
        LEFT JOIN categories c ON t.category_id = c.id 
        WHERE t.user_id = ? 
        ORDER BY t.date DESC 
        LIMIT 5
    """, (user_id,))
    transactions = cursor.fetchall()

    return render_template("tdashboard.html", 
                         user=session.get("user_name"),
                         total_income=total_income,
                         total_expense=total_expense,
                         balance=balance,
                         transactions=transactions)

@app.route("/transacoes")
def transacoes():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    # Buscar categorias do usuário
    cursor.execute("SELECT * FROM categories WHERE user_id = ?", (user_id,))
    categories = cursor.fetchall()

    # Buscar transações
    cursor.execute("""
        SELECT t.*, c.name as category_name 
        FROM transactions t 
        LEFT JOIN categories c ON t.category_id = c.id 
        WHERE t.user_id = ? 
        ORDER BY t.date DESC
    """, (user_id,))
    transactions = cursor.fetchall()

    return render_template("transacoes.html", 
                         categories=categories, 
                         transactions=transactions)

@app.route("/api/transacao", methods=["POST"])
def criar_transacao():
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401

    user_id = session["user_id"]
    data = request.json

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO transactions (user_id, type, category_id, amount, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, data['type'], data.get('category_id'), data['amount'], 
              data.get('description'), data['date']))
        db.commit()
        return jsonify({"success": True, "message": "Transação criada com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/categorias")
def categorias():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM categories WHERE user_id = ?", (user_id,))
    categories = cursor.fetchall()

    return render_template("tcategorias.html", categories=categories)

@app.route("/api/categoria", methods=["POST"])
def criar_categoria():
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401

    user_id = session["user_id"]
    data = request.json

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO categories (user_id, name, type) VALUES (?, ?, ?)",
                      (user_id, data['name'], data['type']))
        db.commit()
        return jsonify({"success": True, "message": "Categoria criada com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/metas")
def metas():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM categories WHERE user_id = ?", (user_id,))
    categories = cursor.fetchall()

    cursor.execute("""
        SELECT g.*, c.name as category_name 
        FROM goals g 
        LEFT JOIN categories c ON g.category_id = c.id 
        WHERE g.user_id = ?
    """, (user_id,))
    goals = cursor.fetchall()

    return render_template("tmetas.html", categories=categories, goals=goals)

@app.route("/api/meta", methods=["POST"])
def criar_meta():
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401

    user_id = session["user_id"]
    data = request.json

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO goals (user_id, category_id, target_amount, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, data.get('category_id'), data['amount'], data['from'], data['to']))
        db.commit()
        return jsonify({"success": True, "message": "Meta criada com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/relatorios")
def relatorios():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("trelatorio.html")

@app.route("/dicas")
def dicas():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("tDicas.html")

@app.route("/empreendedor")
def empreendedor():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM materials WHERE user_id = ?", (user_id,))
    materials = cursor.fetchall()

    return render_template("empreendedor.html", materials=materials)

@app.route("/api/material", methods=["POST"])
def criar_material():
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401

    user_id = session["user_id"]
    data = request.json

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO materials (user_id, name, total_value, quantity)
            VALUES (?, ?, ?, ?)
        """, (user_id, data['name'], data['totalValue'], data['qty']))
        db.commit()
        return jsonify({"success": True, "message": "Material criado com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/compartilhada")
def compartilhada():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT sa.* FROM shared_accounts sa
        JOIN shared_account_members sam ON sa.id = sam.account_id
        WHERE sam.user_id = ?
    """, (user_id,))
    shared_accounts = cursor.fetchall()

    return render_template("tcompartilhada.html", shared_accounts=shared_accounts)

@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        income = request.form.get("income", 0)

        try:
            cursor.execute("UPDATE users SET name=?, email=?, income=? WHERE id=?",
                          (name, email, income, user_id))
            db.commit()

            session["user_name"] = name
            session["user_email"] = email

            cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
            user = cursor.fetchone()
            return render_template("tConfiguracoes.html", user=user, success="Alterações salvas!")
        except sqlite3.IntegrityError:
            cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
            user = cursor.fetchone()
            return render_template("tConfiguracoes.html", user=user, error="E-mail já está em uso")

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    return render_template("tConfiguracoes.html", user=user)

# ------------------------------------------
# INICIALIZAÇÃO
# ------------------------------------------

if __name__ == "__main__":
    # Criar banco de dados e tabelas
    with app.app_context():
        init_db()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
