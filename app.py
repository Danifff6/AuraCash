from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "auracash_secret_2025"


# ------------------------------------------
# BANCO DE DADOS
# ------------------------------------------

def get_db():
    conn = sqlite3.connect("auracash.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    c = conn.cursor()

    # Usuários
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            income REAL DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()

create_tables()


# ------------------------------------------
# ROTA PRINCIPAL
# ------------------------------------------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


# ------------------------------------------
# LOGIN
# ------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="E-mail ou senha incorretos")

    return render_template("login.html")


# ------------------------------------------
# CADASTRO
# ------------------------------------------

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                      (name, email, password))
            conn.commit()
            return redirect("/login")
        except:
            return render_template("registrar.html", error="E-mail já cadastrado")

    return render_template("registrar.html")


# ------------------------------------------
# LOGOUT
# ------------------------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ------------------------------------------
# DASHBOARD
# ------------------------------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("tdashboard.html", user=session.get("user_name"))


# ------------------------------------------
# CONFIGURAÇÕES
# ------------------------------------------

@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        income = request.form.get("income")

        c.execute("UPDATE users SET name=?, email=?, income=? WHERE id=?",
                  (name, email, income, user_id))
        conn.commit()

        session["user_name"] = name
        session["user_email"] = email

        return render_template("tConfiguracoes.html", success="Alterações salvas!")

    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    return render_template("tConfiguracoes.html", user=user)


# ------------------------------------------
# ARQUIVOS ESTÁTICOS
# (Railway precisa disso)
# ------------------------------------------

@app.route("/static/<path:filename>")
def static_files(filename):
    return app.send_static_file(filename)


# ------------------------------------------
# INICIAR SERVIDOR
# ------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
