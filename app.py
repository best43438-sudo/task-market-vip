import os
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    phantom_balance = db.Column(db.Float, default=10.0)
    referred_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    vip_tier = db.Column(db.Integer, default=0)
    daily_tasks_done = db.Column(db.Integer, default=0)
    last_task_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    system_liquidity = db.Column(db.Float, default=1000.0)
    is_rug_pulled = db.Column(db.Boolean, default=False)

class WithdrawalRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# HTML Templates as strings (for easy copy-paste)
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Task Market VIP</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; }
        .content { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { margin-bottom: 20px; color: #333; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        .error { background: #fee; color: #c00; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
        .warning { background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin-top: 20px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h1>Task Market VIP</h1>
            <h2>Login</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <input type="tel" name="phone" placeholder="Phone Number (e.g., 076123456)" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p style="margin-top: 15px; text-align: center;">New user? <a href="/register">Register here</a></p>
            <div class="warning">
                <strong>⚠️ EDUCATIONAL SIMULATION</strong><br>
                No real money involved. Demonstrates scam prevention awareness.
            </div>
        </div>
    </div>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Register - Task Market VIP</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; }
        .content { background: white; padding: 30px; border-radius: 10px; }
        h1 { margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .error { background: #fee; color: #c00; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h1>Register</h1>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <input type="tel" name="phone" placeholder="Phone (076XXXXXX)" required>
                <input type="password" name="password" placeholder="Password" required>
                <input type="text" name="referrer_id" placeholder="Referrer ID (optional)">
                <button type="submit">Register</button>
            </form>
            <p style="margin-top: 15px; text-align: center;">Already registered? <a href="/login">Login</a></p>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Task Market VIP</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f0f2f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .balance { font-size: 32px; font-weight: bold; color: #667eea; }
        button { width: 100%; padding: 15px; margin: 10px 0; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .alert-success { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-top: 10px; }
        .alert-error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-top: 10px; }
        .ticker { background: #333; color: #0f0; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-family: monospace; font-size: 14px; overflow: hidden; }
    </style>
</head>
<body>
    <div class="container">
        <div class="ticker" id="ticker">Loading social proof...</div>
        
        <div class="card">
            <h3>Welcome, {{ user.phone }}</h3>
            <div class="balance">{{ "%.2f"|format(user.phantom_balance) }} NLE</div>
            <p>VIP Tier: {{ user.vip_tier }} | Tasks: {{ user.daily_tasks_done }}/{{ config.daily_tasks }}</p>
            <p>Commission per task: {{ "%.2f"|format(config.commission) }} NLE</p>
            <a href="/logout" style="color: #666; text-decoration: none; display: inline-block; margin-top: 10px;">Logout</a>
        </div>
        
        <div class="card">
            <h3>Mock Deposit</h3>
            <input type="number" id="depositAmount" placeholder="Amount in NLE">
            <button onclick="deposit()">Deposit Funds</button>
        </div>
        
        <div class="card">
            <h3>Complete Task</h3>
            <button onclick="completeTask()">Perform Task ({{ "%.2f"|format(config.commission) }} NLE)</button>
            <div id="taskMessage"></div>
        </div>
        
        <div class="card">
            <h3>Withdraw Funds</h3>
            <input type="number" id="withdrawAmount" placeholder="Amount in NLE">
            <button onclick="withdraw()">Request Withdrawal</button>
            <div id="withdrawMessage"></div>
            <small>Minimum: {{ config.min_withdrawal }} NLE</small>
        </div>
    </div>
    
    <script>
        function updateTicker() {
            fetch('/api/social_proof')
                .then(r => r.json())
                .then(d => {
                    document.getElementById('ticker').innerHTML = d.message;
                });
        }
        setInterval(updateTicker, 5000);
        updateTicker();
        
        async function deposit() {
            let amount = document.getElementById('depositAmount').value;
            let formData = new FormData();
            formData.append('amount', amount);
            let r = await fetch('/deposit', {method: 'POST', body: formData});
            if(r.redirected) location.href = r.url;
        }
        
        async function completeTask() {
            let r = await fetch('/complete_task');
            let d = await r.json();
            if(d.success) {
                document.getElementById('taskMessage').innerHTML = '<div class="alert-success">+'+d.commission+' NLE earned!</div>';
                setTimeout(() => location.reload(), 1500);
            } else {
                document.getElementById('taskMessage').innerHTML = '<div class="alert-error">'+d.error+'</div>';
            }
        }
        
        async function withdraw() {
            let amount = document.getElementById('withdrawAmount').value;
            let formData = new FormData();
            formData.append('amount', amount);
            let r = await fetch('/withdraw', {method: 'POST', body: formData});
            let d = await r.json();
            if(d.success) {
                document.getElementById('withdrawMessage').innerHTML = '<div class="alert-success">Withdrawal requested!</div>';
                setTimeout(() => location.reload(), 1500);
            } else if(d.error === 'tax_trap') {
                if(confirm(d.message + '\\n\\nFee: '+d.fee+' NLE\\n\\nDeposit fee?')) {
                    let fd = new FormData();
                    fd.append('amount', d.fee);
                    await fetch('/deposit', {method: 'POST', body: fd});
                    alert('Fee paid. Try withdrawal again.');
                    location.reload();
                }
            } else {
                document.getElementById('withdrawMessage').innerHTML = '<div class="alert-error">'+d.message+'</div>';
            }
        }
    </script>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f0f2f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; }
        button { width: 100%; padding: 15px; margin: 10px 0; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        .danger { background: #c00; color: white; }
        .warning { background: #f90; color: white; }
        .success { background: #090; color: white; }
        .metric { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .red { color: #c00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>Admin Control Panel</h2>
            <a href="/dashboard" style="color: #667eea;">View as User</a> | <a href="/logout">Logout</a>
        </div>
        
        <div class="card">
            <h3>📊 System Metrics</h3>
            <p>Total Phantom: {{ "%.2f"|format(stats.total_phantom) }} NLE</p>
            <p>System Liquidity: {{ "%.2f"|format(stats.system_liquidity) }} NLE</p>
            <p class="metric {% if stats.collapse_ratio > 2 %}red{% endif %}">Collapse Ratio: {{ "%.2f"|format(stats.collapse_ratio) }}x</p>
            <p>Total Users: {{ stats.total_users }}</p>
        </div>
        
        <div class="card">
            <h3>⚙️ Controls</h3>
            <button class="danger" onclick="rugPull()">🔴 RUG PULL</button>
            <button class="warning" onclick="injectBots()">🤖 Inject Bots</button>
            <button class="success" onclick="resetSystem()">🔄 Reset System</button>
        </div>
    </div>
    
    <script>
        async function rugPull() {
            if(confirm('⚠️ WARNING: This locks all users out. Continue?')) {
                await fetch('/admin/rug_pull', {method: 'POST'});
                alert('Rug pull executed!');
                location.reload();
            }
        }
        async function injectBots() {
            let r = await fetch('/admin/inject_bots', {method: 'POST'});
            let d = await r.json();
            alert(`Added ${d.bots_added} bots with ${d.total_deposit} NLE`);
            location.reload();
        }
        async function resetSystem() {
            if(confirm('⚠️ Delete ALL data? Irreversible!')) {
                await fetch('/admin/reset', {method: 'POST'});
                alert('System reset!');
                location.href = '/login';
            }
        }
    </script>
</body>
</html>
'''

RUGPULL_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>System Error</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #c00; color: white; }
        .container { max-width: 500px; margin: 0 auto; }
        button { padding: 15px 30px; background: white; color: #c00; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚠️ Account Suspended</h1>
        <p>System error - Service unavailable</p>
        <button onclick="location.href='/login'">Return to Login</button>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        user = User.query.filter_by(phone=phone, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('admin' if user.is_admin else 'dashboard'))
        return render_template_string(LOGIN_TEMPLATE, error='Invalid credentials')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        if User.query.filter_by(phone=phone).first():
            return render_template_string(REGISTER_TEMPLATE, error='Phone exists')
        user = User(phone=phone, password=password, phantom_balance=10.0)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    config = {0:{'daily_tasks':1,'commission':0.5,'min_withdrawal':100},
              1:{'daily_tasks':5,'commission':4,'min_withdrawal':100},
              2:{'daily_tasks':10,'commission':20,'min_withdrawal':100},
              3:{'daily_tasks':15,'commission':100,'min_withdrawal':100}}[user.vip_tier]
    return render_template_string(DASHBOARD_TEMPLATE, user=user, config=config)

@app.route('/deposit', methods=['POST'])
def deposit():
    user = User.query.get(session['user_id'])
    amount = float(request.form.get('amount', 0))
    if amount > 0:
        user.phantom_balance += amount
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/complete_task')
def complete_task():
    user = User.query.get(session['user_id'])
    config = {0:0.5,1:4,2:20,3:100}[user.vip_tier]
    user.phantom_balance += config
    db.session.commit()
    return jsonify({'success': True, 'commission': config})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    user = User.query.get(session['user_id'])
    amount = float(request.form.get('amount', 0))
    if amount > 300:
        return jsonify({'success': False, 'error': 'tax_trap', 'message': 'Security Alert: Deposit 20% verification fee', 'fee': amount*0.2})
    if amount > user.phantom_balance:
        return jsonify({'success': False, 'message': 'Insufficient balance'})
    user.phantom_balance -= amount
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin')
def admin():
    users = User.query.all()
    total_phantom = sum(u.phantom_balance for u in users)
    state = SystemState.query.first() or SystemState()
    stats = {'total_phantom': total_phantom, 'system_liquidity': state.system_liquidity, 
             'collapse_ratio': total_phantom/state.system_liquidity if state.system_liquidity>0 else 0, 'total_users': len(users)}
    return render_template_string(ADMIN_TEMPLATE, stats=stats)

@app.route('/admin/rug_pull', methods=['POST'])
def rug_pull():
    state = SystemState.query.first()
    if not state:
        state = SystemState()
    state.is_rug_pulled = True
    db.session.add(state)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/inject_bots', methods=['POST'])
def inject_bots():
    for i in range(20):
        bot = User(phone=f'076{i:05d}', password='bot123', phantom_balance=50)
        db.session.add(bot)
    db.session.commit()
    return jsonify({'success': True, 'bots_added': 20, 'total_deposit': 1000})

@app.route('/admin/reset', methods=['POST'])
def reset_system():
    db.drop_all()
    db.create_all()
    admin = User(phone='076000000', password='admin123', is_admin=True, phantom_balance=1000)
    db.session.add(admin)
    db.session.add(SystemState(system_liquidity=1000))
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/social_proof')
def social_proof():
    prefixes = ['076', '077', '031', '088']
    actions = [f'User +232 {random.choice(prefixes)}****** upgraded to VIP {random.randint(1,3)}!',
               f'User +232 {random.choice(prefixes)}****** withdrew {random.randint(100,2000)} NLE!']
    return jsonify({'message': random.choice(actions)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(phone='076000000').first():
            admin = User(phone='076000000', password='admin123', is_admin=True, phantom_balance=1000)
            db.session.add(admin)
            db.session.add(SystemState(system_liquidity=1000))
            db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)
