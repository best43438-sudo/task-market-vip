import os
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    phantom_balance = db.Column(db.Float, default=10.0)
    vip_tier = db.Column(db.Integer, default=0)
    daily_tasks_done = db.Column(db.Integer, default=0)
    last_task_date = db.Column(db.String(20), default='')
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

class SystemState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    system_liquidity = db.Column(db.Float, default=1000.0)
    is_rug_pulled = db.Column(db.Boolean, default=False)
    total_deposits = db.Column(db.Float, default=0)
    total_withdrawals = db.Column(db.Float, default=0)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0)
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(phone='076000000').first():
        admin = User(phone='076000000', password='admin123', is_admin=True, phantom_balance=1000)
        db.session.add(admin)
        db.session.commit()
    if not SystemState.query.first():
        db.session.add(SystemState(system_liquidity=1000))
        db.session.commit()

# FRONT PAGE WITH YOUR IMAGE (FIXED PATH)
FRONT_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Market VIP - Earn NLE Daily</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { max-width: 500px; margin: 0 auto; padding: 20px; }
        
        .hero {
            background: white;
            border-radius: 30px;
            padding: 40px 25px;
            margin-top: 40px;
            text-align: center;
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        }
        
        .image-container {
            margin: -70px auto 20px auto;
            width: 120px;
            height: 120px;
            border-radius: 60px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            background: white;
        }
        
        .image-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        h1 {
            font-size: 28px;
            color: #333;
            margin: 20px 0 10px;
        }
        
        .tagline {
            color: #667eea;
            font-weight: bold;
            margin-bottom: 20px;
        }
        
        .features {
            text-align: left;
            margin: 30px 0;
            padding: 0 15px;
        }
        
        .features li {
            margin: 15px 0;
            list-style: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .features li:before {
            content: "✓";
            color: #667eea;
            font-weight: bold;
            font-size: 20px;
        }
        
        .btn {
            display: block;
            padding: 15px;
            margin: 15px 0;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            transition: transform 0.3s;
        }
        
        .btn:hover { transform: scale(1.05); background: #764ba2; }
        
        .btn-outline {
            background: transparent;
            border: 2px solid #667eea;
            color: #667eea;
        }
        
        .stats {
            background: #f8f9fa;
            border-radius: 20px;
            padding: 20px;
            margin-top: 20px;
            font-size: 14px;
        }
        
        .badge {
            display: inline-block;
            background: #ff9800;
            color: white;
            padding: 5px 15px;
            border-radius: 50px;
            font-size: 12px;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <div class="image-container">
                <img src="/IMG_1615.jpeg" alt="Task Market VIP">
            </div>
            
            <span class="badge">🔥 LIMITED OFFER</span>
            <h1>Task Market VIP</h1>
            <p class="tagline">Earn up to 100 NLE per task!</p>
            
            <ul class="features">
                <li>Start with 10 NLE FREE bonus</li>
                <li>Complete daily tasks for commission</li>
                <li>Refer friends & earn 10% commission</li>
                <li>VIP tiers with higher earnings</li>
            </ul>
            
            <a href="/login" class="btn">🚀 Login Now</a>
            <a href="/register" class="btn btn-outline">📝 Create Free Account</a>
            
            <div class="stats">
                <strong>📊 Platform Stats:</strong><br>
                Active Users: {{ users }}<br>
                Total Paid: {{ "%.2f"|format(total_paid) }} NLE
            </div>
        </div>
    </div>
</body>
</html>
'''

# LOGS PAGE
LOGS_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activity Logs</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f0f2f5;
            padding: 20px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .log-card {
            background: white;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        .log-time {
            font-size: 11px;
            color: #999;
            margin-bottom: 5px;
        }
        .log-action {
            font-size: 14px;
            color: #333;
        }
        .log-amount {
            font-weight: bold;
            color: #667eea;
        }
        .nav-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .nav-btn {
            flex: 1;
            padding: 12px;
            background: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            color: #667eea;
            font-weight: bold;
        }
        .nav-btn.active {
            background: #667eea;
            color: white;
        }
        .stats-card {
            background: white;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📋 Activity Memory Logs</h2>
            <p>All platform activities are recorded here</p>
        </div>
        
        <div class="nav-buttons">
            <a href="/dashboard" class="nav-btn">🏠 Dashboard</a>
            <a href="/logs" class="nav-btn active">📋 Logs</a>
            <a href="/logout" class="nav-btn">🚪 Logout</a>
        </div>
        
        <div class="stats-card">
            <div class="stat-number">{{ total_logs }}</div>
            <div>Total Activities Recorded</div>
        </div>
        
        {% for log in logs %}
        <div class="log-card">
            <div class="log-time">🕐 {{ log.timestamp }}</div>
            <div class="log-action">
                {{ log.action }}
                {% if log.amount > 0 %}
                    <span class="log-amount">({{ "%.2f"|format(log.amount) }} NLE)</span>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
'''

# DASHBOARD PAGE
DASHBOARD_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: #f0f2f5; padding: 20px; margin: 0; }
        .container { max-width: 500px; margin: 0 auto; }
        .card { background: white; border-radius: 15px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .balance { font-size: 36px; font-weight: bold; color: #667eea; }
        button { width: 100%; padding: 15px; margin: 10px 0; background: #667eea; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 16px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; }
        .alert-success { background: #d4edda; color: #155724; padding: 10px; border-radius: 10px; margin-top: 10px; }
        .alert-error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 10px; margin-top: 10px; }
        .ticker { background: #333; color: #0f0; padding: 10px; border-radius: 10px; margin-bottom: 15px; font-family: monospace; text-align: center; font-size: 12px; }
        .nav-buttons { display: flex; gap: 10px; margin-bottom: 15px; }
        .nav-btn { flex: 1; padding: 10px; background: #667eea; color: white; text-align: center; text-decoration: none; border-radius: 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="ticker" id="ticker">Loading...</div>
        
        <div class="nav-buttons">
            <a href="/dashboard" class="nav-btn" style="background:#667eea">🏠 Home</a>
            <a href="/logs" class="nav-btn" style="background:#764ba2">📋 Logs</a>
            <a href="/logout" class="nav-btn" style="background:#c00">🚪 Exit</a>
        </div>
        
        <div class="card">
            <h3>Welcome, {{ user.phone }}</h3>
            <div class="balance">{{ "%.2f"|format(user.phantom_balance) }} NLE</div>
            <p>VIP Level: {{ vip_level }} | Tasks: {{ tasks_done }}/{{ tasks_max }}</p>
            <p>Commission per task: {{ "%.2f"|format(commission) }} NLE</p>
        </div>
        
        <div class="card">
            <h3>💰 Mock Deposit</h3>
            <input type="number" id="depositAmount" placeholder="Amount in NLE">
            <button onclick="deposit()">Add Funds</button>
        </div>
        
        <div class="card">
            <h3>✅ Complete Task</h3>
            <button onclick="doTask()">Perform Task (+{{ "%.2f"|format(commission) }} NLE)</button>
            <div id="taskMsg"></div>
        </div>
        
        <div class="card">
            <h3>💸 Withdraw</h3>
            <input type="number" id="withdrawAmount" placeholder="Amount in NLE">
            <button onclick="withdraw()">Request Withdrawal</button>
            <div id="withdrawMsg"></div>
            <small>Minimum: 100 NLE</small>
        </div>
        
        {% if user.is_admin %}
        <div class="card">
            <h3>🔧 Admin</h3>
            <a href="/admin"><button style="background:#f90;">Go to Admin Panel</button></a>
        </div>
        {% endif %}
    </div>
    
    <script>
        function updateTicker() {
            fetch('/api/social_proof')
                .then(r => r.json())
                .then(d => { document.getElementById('ticker').innerHTML = d.message; });
        }
        setInterval(updateTicker, 5000);
        updateTicker();
        
        async function deposit() {
            let amount = document.getElementById('depositAmount').value;
            let formData = new FormData();
            formData.append('amount', amount);
            let res = await fetch('/deposit', {method: 'POST', body: formData});
            if(res.redirected) location.href = res.url;
        }
        
        async function doTask() {
            let res = await fetch('/complete_task');
            let data = await res.json();
            if(data.success) {
                document.getElementById('taskMsg').innerHTML = '<div class="alert-success">+'+data.commission+' NLE earned!</div>';
                setTimeout(() => location.reload(), 1500);
            } else {
                document.getElementById('taskMsg').innerHTML = '<div class="alert-error">'+data.error+'</div>';
            }
        }
        
        async function withdraw() {
            let amount = document.getElementById('withdrawAmount').value;
            let formData = new FormData();
            formData.append('amount', amount);
            let res = await fetch('/withdraw', {method: 'POST', body: formData});
            let data = await res.json();
            if(data.success) {
                document.getElementById('withdrawMsg').innerHTML = '<div class="alert-success">Withdrawal submitted!</div>';
                setTimeout(() => location.reload(), 1500);
            } else if(data.tax_trap) {
                if(confirm(data.message + '\\nFee: ' + data.fee + ' NLE')) {
                    let fd = new FormData();
                    fd.append('amount', data.fee);
                    await fetch('/deposit', {method: 'POST', body: fd});
                    alert('Fee paid. Try withdrawal again.');
                    location.reload();
                }
            } else {
                document.getElementById('withdrawMsg').innerHTML = '<div class="alert-error">'+data.message+'</div>';
            }
        }
    </script>
</body>
</html>
'''

ADMIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: #f0f2f5; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; }
        .card { background: white; border-radius: 15px; padding: 20px; margin-bottom: 15px; }
        button { width: 100%; padding: 15px; margin: 10px 0; border: none; border-radius: 10px; cursor: pointer; }
        .danger { background: #c00; color: white; }
        .warning { background: #f90; color: white; }
        .success { background: #090; color: white; }
        .metric { font-size: 28px; font-weight: bold; margin: 10px 0; }
        .red { color: #c00; }
        .nav-buttons { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav-btn { flex: 1; padding: 12px; background: #667eea; color: white; text-align: center; text-decoration: none; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-buttons">
            <a href="/dashboard" class="nav-btn">👤 User View</a>
            <a href="/logs" class="nav-btn">📋 Logs</a>
            <a href="/logout" class="nav-btn">🚪 Logout</a>
        </div>
        
        <div class="card">
            <h2>🔐 Admin Control</h2>
        </div>
        
        <div class="card">
            <h3>📊 System Health</h3>
            <p>Total Phantom: {{ stats.total_phantom }} NLE</p>
            <p>System Liquidity: {{ stats.liquidity }} NLE</p>
            <p class="metric {% if stats.ratio > 2 %}red{% endif %}">Collapse Ratio: {{ "%.2f"|format(stats.ratio) }}x</p>
            <p>Total Users: {{ stats.users }}</p>
            <p>Total Logs: {{ stats.logs }}</p>
        </div>
        
        <div class="card">
            <h3>⚙️ Controls</h3>
            <button class="danger" onclick="rugPull()">🔴 RUG PULL (Lock System)</button>
            <button class="warning" onclick="injectBots()">🤖 Inject 20 Bots</button>
            <button class="success" onclick="resetSystem()">🔄 Complete Reset</button>
        </div>
    </div>
    
    <script>
        async function rugPull() {
            if(confirm('⚠️ WARNING: This will lock ALL users out!')) {
                await fetch('/admin/rug_pull', {method: 'POST'});
                alert('Rug pull executed! System locked.');
                location.reload();
            }
        }
        async function injectBots() {
            let res = await fetch('/admin/inject_bots', {method: 'POST'});
            let data = await res.json();
            alert('Added ' + data.bots_added + ' bot users');
            location.reload();
        }
        async function resetSystem() {
            if(confirm('⚠️ DELETE EVERYTHING? This cannot be undone!')) {
                await fetch('/admin/reset', {method: 'POST'});
                alert('System reset! Redirecting to login...');
                location.href = '/login';
            }
        }
    </script>
</body>
</html>
'''

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; }
        .container { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 10px; cursor: pointer; }
        .error { background: #fee; color: red; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
        h1 { text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Login</h1>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="phone" placeholder="Phone Number" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p style="text-align: center; margin-top: 20px;"><a href="/register">Create Account</a> | <a href="/">Home</a></p>
    </div>
</body>
</html>
'''

REGISTER_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 10px; cursor: pointer; }
        .error { background: #fee; color: red; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Register</h1>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="phone" placeholder="Phone (076XXXXXX)" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Register</button>
        </form>
        <p style="text-align: center; margin-top: 20px;"><a href="/login">Already have an account?</a></p>
    </div>
</body>
</html>
'''

RUG_PULL = '''
<!DOCTYPE html>
<html>
<head>
    <title>System Error</title>
    <style>
        body { text-align: center; padding: 50px; background: #c00; color: white; font-family: Arial; }
        button { padding: 15px 30px; background: white; color: #c00; border: none; border-radius: 10px; cursor: pointer; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>⚠️ Account Suspended</h1>
    <p>System maintenance in progress.</p>
    <button onclick="location.href='/login'">Return to Login</button>
</body>
</html>
'''

def add_log(user_id, action, amount=0):
    log = ActivityLog(user_id=user_id, action=action, amount=amount)
    db.session.add(log)
    db.session.commit()

@app.route('/')
def index():
    total_users = User.query.count()
    total_paid = db.session.query(db.func.sum(User.phantom_balance)).scalar() or 0
    return render_template_string(FRONT_PAGE, users=total_users, total_paid=total_paid)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        user = User.query.filter_by(phone=phone, password=password).first()
        if user:
            if SystemState.query.first().is_rug_pulled:
                return RUG_PULL
            session['user_id'] = user.id
            add_log(user.id, f"User {phone} logged in")
            return redirect(url_for('admin' if user.is_admin else 'dashboard'))
        return render_template_string(LOGIN_PAGE, error='Invalid credentials')
    return render_template_string(LOGIN_PAGE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        if User.query.filter_by(phone=phone).first():
            return render_template_string(REGISTER_PAGE, error='Phone already registered')
        user = User(phone=phone, password=password, phantom_balance=10.0)
        db.session.add(user)
        db.session.commit()
        add_log(user.id, f"New user registered: {phone}")
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    return render_template_string(REGISTER_PAGE)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    
    if user.phantom_balance >= 2000:
        vip_level, tasks_max, commission = "VIP 3 👑", 15, 100
    elif user.phantom_balance >= 500:
        vip_level, tasks_max, commission = "VIP 2 ⭐", 10, 20
    elif user.phantom_balance >= 100:
        vip_level, tasks_max, commission = "VIP 1 💎", 5, 4
    else:
        vip_level, tasks_max, commission = "VIP 0 🆓", 1, 0.5
    
    today = str(date.today())
    tasks_done = user.daily_tasks_done if user.last_task_date == today else 0
    
    return render_template_string(DASHBOARD_PAGE, user=user, vip_level=vip_level, 
                                   tasks_max=tasks_max, tasks_done=tasks_done, commission=commission)

@app.route('/logs')
def view_logs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    logs = ActivityLog.query.order_by(ActivityLog.id.desc()).limit(100).all()
    return render_template_string(LOGS_PAGE, logs=logs, total_logs=len(logs))

@app.route('/deposit', methods=['POST'])
def deposit():
    user = User.query.get(session['user_id'])
    amount = float(request.form.get('amount', 0))
    if amount > 0:
        user.phantom_balance += amount
        state = SystemState.query.first()
        state.system_liquidity += amount
        state.total_deposits += amount
        db.session.commit()
        add_log(user.id, f"Deposited {amount} NLE", amount)
    return redirect(url_for('dashboard'))

@app.route('/complete_task')
def complete_task():
    user = User.query.get(session['user_id'])
    
    if user.phantom_balance >= 2000:
        commission, max_tasks = 100, 15
    elif user.phantom_balance >= 500:
        commission, max_tasks = 20, 10
    elif user.phantom_balance >= 100:
        commission, max_tasks = 4, 5
    else:
        commission, max_tasks = 0.5, 1
    
    today = str(date.today())
    
    if user.last_task_date == today and user.daily_tasks_done >= max_tasks:
        return jsonify({'success': False, 'error': 'Daily limit reached'})
    
    user.phantom_balance += commission
    if user.last_task_date != today:
        user.daily_tasks_done = 1
        user.last_task_date = today
    else:
        user.daily_tasks_done += 1
    db.session.commit()
    
    add_log(user.id, f"Completed task - earned {commission} NLE", commission)
    return jsonify({'success': True, 'commission': commission})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    user = User.query.get(session['user_id'])
    amount = float(request.form.get('amount', 0))
    state = SystemState.query.first()
    total_phantom = db.session.query(db.func.sum(User.phantom_balance)).scalar() or 0
    
    if amount > 300:
        return jsonify({'success': False, 'tax_trap': True, 
                       'message': '⚠️ Security Alert: Deposit 20% network verification fee', 
                       'fee': amount * 0.2})
    
    if state.system_liquidity < (total_phantom * 0.3):
        return jsonify({'success': False, 
                       'message': 'System maintenance in progress. Try again in 72 hours.'})
    
    if amount < 100:
        return jsonify({'success': False, 'message': 'Minimum withdrawal is 100 NLE'})
    
    if amount > user.phantom_balance:
        return jsonify({'success': False, 'message': 'Insufficient balance'})
    
    user.phantom_balance -= amount
    state.system_liquidity -= amount
    state.total_withdrawals += amount
    db.session.commit()
    
    add_log(user.id, f"Withdrew {amount} NLE", amount)
    return jsonify({'success': True})

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('dashboard'))
    
    total_phantom = db.session.query(db.func.sum(User.phantom_balance)).scalar() or 0
    state = SystemState.query.first()
    users_count = User.query.count()
    logs_count = ActivityLog.query.count()
    ratio = total_phantom / state.system_liquidity if state.system_liquidity > 0 else 0
    
    stats = {
        'total_phantom': f'{total_phantom:.2f}',
        'liquidity': f'{state.system_liquidity:.2f}',
        'ratio': ratio,
        'users': users_count,
        'logs': logs_count
    }
    return render_template_string(ADMIN_PAGE, stats=stats)

@app.route('/admin/rug_pull', methods=['POST'])
def admin_rug_pull():
    state = SystemState.query.first()
    state.is_rug_pulled = True
    db.session.commit()
    add_log(0, "⚠️ RUG PULL EXECUTED - System locked", 0)
    return jsonify({'success': True})

@app.route('/admin/inject_bots', methods=['POST'])
def admin_inject_bots():
    for i in range(20):
        bot = User(phone=f'077{i:05d}', password='bot123', phantom_balance=50)
        db.session.add(bot)
        add_log(0, f"Bot user {f'077{i:05d}'} injected", 50)
    db.session.commit()
    return jsonify({'success': True, 'bots_added': 20})

@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    db.drop_all()
    db.create_all()
    admin = User(phone='076000000', password='admin123', is_admin=True, phantom_balance=1000)
    db.session.add(admin)
    db.session.add(SystemState(system_liquidity=1000))
    db.session.commit()
    session.clear()
    return jsonify({'success': True})

@app.route('/api/social_proof')
def social_proof():
    prefixes = ['076', '077', '031', '088']
    actions = [
        f'✨ User +232 {random.choice(prefixes)}****** upgraded to VIP {random.randint(1,3)}!',
        f'💰 User +232 {random.choice(prefixes)}****** withdrew {random.randint(100,2000)} NLE!',
        f'🎉 New milestone reached by +232 {random.choice(prefixes)}******!',
        f'📈 Daily earnings record: {random.randint(500,5000)} NLE!'
    ]
    return jsonify({'message': random.choice(actions)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
