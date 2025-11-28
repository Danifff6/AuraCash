from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'auracash-key-2024'

# Banco de dados simples
def init_db():
    conn = sqlite3.connect('auracash.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            nome TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description TEXT,
            amount REAL,
            type TEXT,
            category TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Servir arquivos
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/style.css')
def css_file():
    return send_from_directory('templates/public', 'style.css')

# Rotas principais
@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('auracash.db')
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['user_email'] = user[1]
            session['user_nome'] = user[3]
            flash('Login feito!')
            return redirect('/dashboard')
        else:
            flash('Email ou senha errados')
    
    return render_template('public/tlogin.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nome = request.form.get('name')
        
        try:
            conn = sqlite3.connect('auracash.db')
            conn.execute(
                'INSERT INTO users (email, password, nome) VALUES (?, ?, ?)',
                (email, generate_password_hash(password), nome)
            )
            conn.commit()
            conn.close()
            flash('Cadastro feito!')
            return redirect('/login')
        except:
            flash('Email já existe')
    
    return render_template('templates/public/tcadastro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('auracash.db')
    
    # Calcular totais
    income = conn.execute(
        'SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = "income"',
        (session['user_id'],)
    ).fetchone()[0] or 0
    
    expenses = conn.execute(
        'SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = "expense"',
        (session['user_id'],)
    ).fetchone()[0] or 0
    
    balance = income - expenses
    
    # Transações
    transactions = conn.execute(
        'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    
    return render_template('public/tdashboard.html',
                         username=session['user_nome'],
                         income=income,
                         expenses=expenses,
                         balance=balance,
                         transactions=transactions)

@app.route('/transacoes', methods=['GET', 'POST'])
def transacoes():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('auracash.db')
    
    if request.method == 'POST':
        description = request.form.get('desc')
        amount = request.form.get('amount')
        type = request.form.get('type')
        date = request.form.get('date')
        
        conn.execute(
            'INSERT INTO transactions (user_id, description, amount, type, date) VALUES (?, ?, ?, ?, ?)',
            (session['user_id'], description, amount, type, date)
        )
        conn.commit()
        flash('Transação salva!')
        return redirect('/transacoes')
    
    transactions = conn.execute(
        'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    
    return render_template('public/transacoes.html', transactions=transactions)

@app.route('/categorias')
def categorias():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('public/tcategorias.html')

@app.route('/metas')
def metas():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('public/tmetas.html')

@app.route('/compartilhada')
def compartilhada():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('public/tcompartilhada.html')

@app.route('/empreendedor')
def empreendedor():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('public/empreendedor.html')

@app.route('/relatorios')
def relatorios():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('public/trelatorio.html')

@app.route('/dicas')
def dicas():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('public/tDicas.html')

@app.route('/configuracoes')
def configuracoes():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('public/tConfiguracoes.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Saiu!')
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    print("🚀 AuraCash rodando: http://localhost:5000")
    app.run(debug=True, port=5000)
