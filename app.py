from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'auracash-secret-key-2024'

# Configuração do banco
def get_db_connection():
    conn = sqlite3.connect('auracash.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_categorias():
    """Cria categorias padrão se não existirem"""
    categorias_padrao = [
        ('Alimentação', 'padrao', 'expense'),
        ('Transporte', 'padrao', 'expense'),
        ('Moradia', 'padrao', 'expense'),
        ('Lazer', 'padrao', 'expense'),
        ('Saúde', 'padrao', 'expense'),
        ('Educação', 'padrao', 'expense'),
        ('Salário', 'padrao', 'income'),
        ('Freelance', 'padrao', 'income'),
        ('Investimentos', 'padrao', 'income'),
        ('Outros', 'padrao', 'income')
    ]
    
    conn = get_db_connection()
    
    # Verificar se já existem categorias
    existing = conn.execute('SELECT COUNT(*) as count FROM categorias').fetchone()['count']
    
    if existing == 0:
        for nome, padrao, tipo in categorias_padrao:
            conn.execute(
                'INSERT INTO categorias (nome, padrao, tipo) VALUES (?, ?, ?)',
                (nome, padrao, tipo)
            )
        conn.commit()
        print("✅ Categorias padrão criadas!")
    
    conn.close()

def init_db():
    conn = get_db_connection()
    
    # Criar tabela de usuários
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            nome TEXT,
            cpf TEXT,
            renda_mensal REAL,
            auxilio BOOLEAN
        )
    ''')
    
    # Criar tabela de transações
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Criar tabela de categorias
    conn.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            padrao TEXT DEFAULT 'personalizada',
            tipo TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Inicializar categorias padrão
    init_categorias()

# Servir arquivos estáticos
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ROTAS PRINCIPAIS
@app.route('/')
def index():
    return render_template('public/tlogin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Aceita tanto 'username' quanto 'email' como campo de login
        login_input = request.form.get('username') or request.form.get('email')
        password = request.form.get('password')
        
        if not login_input or not password:
            flash('❌ Preencha todos os campos')
            return render_template('public/tlogin.html')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?', 
            (login_input, login_input)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('✅ Login realizado com sucesso!')
            return redirect('/dashboard')
        else:
            flash('❌ Usuário/E-mail ou senha incorretos')
    
    return render_template('public/tlogin.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        # Usar o email como username também
        username = request.form.get('email') or request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email', '')
        nome = request.form.get('name', '')
        cpf = request.form.get('cpf', '')
        renda = request.form.get('income', 0)
        auxilio = 'aid' in request.form
        
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO users (username, email, password, nome, cpf, renda_mensal, auxilio) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (username, email, generate_password_hash(password), nome, cpf, float(renda), auxilio)
            )
            conn.commit()
            conn.close()
            flash('✅ Cadastro realizado com sucesso!')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('❌ Email já cadastrado.')
    
    return render_template('public/tcadastro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    transactions = conn.execute(
        'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()
    
    income = conn.execute(
        'SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND type = "income"',
        (session['user_id'],)
    ).fetchone()['total'] or 0
    
    expenses = conn.execute(
        'SELECT SUM(amount) as total FROM transactions WHERE user_id = ? AND type = "expense"',
        (session['user_id'],)
    ).fetchone()['total'] or 0
    
    balance = income - expenses
    conn.close()
    
    return render_template('public/tdashboard.html',
                         username=session['username'],
                         income=income,
                         expenses=expenses,
                         balance=balance,
                         transactions=transactions)

@app.route('/transacoes')
def transacoes():
    if 'user_id' not in session:
        return redirect('/login')
    
    # Buscar categorias para o formulário
    conn = get_db_connection()
    categorias = conn.execute('SELECT * FROM categorias').fetchall()
    transactions = conn.execute(
        'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    return render_template('public/transacoes.html',
                         categorias=categorias,
                         transactions=transactions)

@app.route('/categorias', methods=['GET', 'POST'])
def categorias():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    
    # Se for POST, adicionar nova categoria
    if request.method == 'POST':
        nome = request.form.get('name')
        tipo = request.form.get('type', 'expense')
        
        if nome:
            try:
                conn.execute(
                    'INSERT INTO categorias (nome, tipo) VALUES (?, ?)',
                    (nome, tipo)
                )
                conn.commit()
                flash('✅ Categoria adicionada com sucesso!')
            except sqlite3.IntegrityError:
                flash('❌ Categoria já existe.')
    
    # Buscar categorias do banco (tanto para GET quanto POST)
    categorias = conn.execute('SELECT * FROM categorias ORDER BY tipo, nome').fetchall()
    conn.close()
    
    return render_template('public/tcategorias.html', categorias=categorias)

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
    flash('✅ Logout realizado!')
    return redirect('/login')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    print("🚀 AuraCash rodando em: http://localhost:5000")
    print("👤 Usuário teste: admin / senha: 123")
    print("📊 Categorias padrão criadas automaticamente!")
    app.run(debug=True, port=5000)