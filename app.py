from flask import Flask, render_template, request, redirect, session, flash, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'auracash-key-2024'

# Configurar pastas explicitamente
app.template_folder = 'templates'
app.static_folder = 'static'

# Banco de dados simples
def init_db():
    conn = sqlite3.connect('auracash.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            nome TEXT,
            income REAL DEFAULT 0
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
    
    # Inserir usuário de teste se não existir
    try:
        conn.execute(
            "INSERT INTO users (email, password, nome, income) VALUES (?, ?, ?, ?)",
            ('teste@teste.com', generate_password_hash('1234'), 'Usuário Teste', 2000.0)
        )
        conn.commit()
    except:
        pass  # Usuário já existe
    
    conn.close()

# Servir arquivos estáticos CORRETAMENTE
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Rota para CSS específico
@app.route('/style.css')
def serve_css():
    return send_from_directory('static', 'style.css')

# Rotas principais
@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Tentativa de login: {email}")  # Debug
        
        conn = sqlite3.connect('auracash.db')
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['user_email'] = user[1]
            session['user_nome'] = user[3]
            flash('Login realizado com sucesso!')
            print("Login bem-sucedido, redirecionando...")  # Debug
            return redirect('/dashboard')
        else:
            flash('Email ou senha incorretos')
            print("Falha no login")  # Debug
    
    return render_template('tlogin.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nome = request.form.get('name')
        income = request.form.get('income', 0)
        
        try:
            conn = sqlite3.connect('auracash.db')
            conn.execute(
                'INSERT INTO users (email, password, nome, income) VALUES (?, ?, ?, ?)',
                (email, generate_password_hash(password), nome, float(income) if income else 0)
            )
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso!')
            return redirect('/login')
        except Exception as e:
            print(f"Erro no cadastro: {e}")  # Debug
            flash('Email já existe ou erro no cadastro')
    
    return render_template('tcadastro.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Por favor, faça login primeiro')
        return redirect('/login')
    
    conn = sqlite3.connect('auracash.db')
    
    # Calcular totais
    income_result = conn.execute(
        'SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = "income"',
        (session['user_id'],)
    ).fetchone()[0]
    income = income_result if income_result else 0
    
    expenses_result = conn.execute(
        'SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = "expense"',
        (session['user_id'],)
    ).fetchone()[0]
    expenses = expenses_result if expenses_result else 0
    
    balance = income - expenses
    
    # Transações recentes
    transactions = conn.execute(
        'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    
    return render_template('tdashboard.html',
                         username=session['user_nome'],
                         income=income,
                         expenses=expenses,
                         balance=balance,
                         transactions=transactions)

# Adicione esta rota para processar transações
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' not in session:
        return redirect('/login')
    
    description = request.form.get('description')
    amount = request.form.get('amount')
    type = request.form.get('type')
    date = request.form.get('date')
    
    conn = sqlite3.connect('auracash.db')
    conn.execute(
        'INSERT INTO transactions (user_id, description, amount, type, date) VALUES (?, ?, ?, ?, ?)',
        (session['user_id'], description, amount, type, date)
    )
    conn.commit()
    conn.close()
    
    flash('Transação adicionada com sucesso!')
    return redirect('/transacoes')

@app.route('/transacoes')
def transacoes():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('auracash.db')
    transactions = conn.execute(
        'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    return render_template('transacoes.html', transactions=transactions)

@app.route('/categorias')
def categorias():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('tcategorias.html')

@app.route('/metas')
def metas():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('tmetas.html')

@app.route('/compartilhada')
def compartilhada():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('tcompartilhada.html')

@app.route('/empreendedor')
def empreendedor():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('empreendedor.html')

@app.route('/relatorios')
def relatorios():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('trelatorio.html')

@app.route('/dicas')
def dicas():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('tDicas.html')

@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        # Atualizar configurações do usuário
        nome = request.form.get('name')
        email = request.form.get('email')
        income = request.form.get('income')
        
        conn = sqlite3.connect('auracash.db')
        conn.execute(
            'UPDATE users SET nome = ?, email = ?, income = ? WHERE id = ?',
            (nome, email, float(income), session['user_id'])
        )
        conn.commit()
        
        # Atualizar sessão
        session['user_nome'] = nome
        session['user_email'] = email
        
        conn.close()
        flash('Configurações atualizadas!')
        return redirect('/configuracoes')
    
    # Buscar dados do usuário
    conn = sqlite3.connect('auracash.db')
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('tConfiguracoes.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!')
    return redirect('/login')

# Rota de saúde para verificar se está funcionando
@app.route('/health')
def health():
    return 'OK - Servidor funcionando'

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 AuraCash rodando: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
