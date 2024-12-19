from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import requests
import os
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required
from auth import User, login_tracker
from werkzeug.middleware.proxy_fix import ProxyFix

# 加载环境变量
load_dotenv()

app = Flask(__name__)
# 在生产环境中使用强随机密钥
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
# 修改安全相关的配置
app.config['SESSION_COOKIE_SECURE'] = False  # 允许HTTP访问cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问cookie
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # session有效期1小时
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制请求大小为16MB

# 支持反向代理
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user = User.get_user()
    return user

# Portainer API配置
PORTAINER_URL = os.getenv('PORTAINER_URL')
PORTAINER_USERNAME = os.getenv('PORTAINER_USERNAME')
PORTAINER_PASSWORD = os.getenv('PORTAINER_PASSWORD')

def get_auth_token():
    """获取Portainer认证token"""
    auth_url = f"{PORTAINER_URL}/api/auth"
    response = requests.post(auth_url, json={
        "username": PORTAINER_USERNAME,
        "password": PORTAINER_PASSWORD
    })
    if response.status_code == 200:
        return response.json()['jwt']
    return None

def get_endpoints():
    """获取所有可用的endpoints"""
    token = get_auth_token()
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}'}
    endpoints_url = f"{PORTAINER_URL}/api/endpoints"
    response = requests.get(endpoints_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 检查是否可以尝试登录
        can_attempt, error_message = login_tracker.can_attempt_login(username)
        
        if not can_attempt:
            print('Login attempt failed:', error_message)
            if error_message:
                flash(error_message)
            return render_template('login.html')

        # 验证凭据
        credentials_valid = User.check_credentials(username, password)
        
        if credentials_valid:
            # 登录成功
            success, _ = login_tracker.record_attempt(username, True)
            user = User.get_user()
            login_user(user, remember=True)  # 启用"记住我"功能
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        # 登录失败
        print('Login failed - Recording failed attempt')
        _, error_message = login_tracker.record_attempt(username, False)
        if error_message:
            flash(error_message)

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/containers')
@login_required
def get_containers():
    """获取容器列表"""
    token = get_auth_token()
    if not token:
        return jsonify({"error": "Authentication failed"}), 401

    # 获取endpoints
    endpoints = get_endpoints()
    if not endpoints:
        return jsonify({"error": "No endpoints found"}), 404

    # 使用第一个可用的endpoint
    endpoint_id = endpoints[0]['Id']

    headers = {'Authorization': f'Bearer {token}'}
    containers_url = f"{PORTAINER_URL}/api/endpoints/{endpoint_id}/docker/containers/json?all=true"

    response = requests.get(containers_url, headers=headers)
    return jsonify(response.json())

@app.route('/api/container/<container_id>/<action>', methods=['POST'])
@login_required
def container_action(container_id, action):
    """容器操作（启动/停止/重启）"""
    token = get_auth_token()
    if not token:
        return jsonify({"error": "Authentication failed"}), 401

    # 获取endpoints
    endpoints = get_endpoints()
    if not endpoints:
        return jsonify({"error": "No endpoints found"}), 404

    # 使用第一个可用的endpoint
    endpoint_id = endpoints[0]['Id']

    headers = {'Authorization': f'Bearer {token}'}
    action_url = f"{PORTAINER_URL}/api/endpoints/{endpoint_id}/docker/containers/{container_id}/{action}"

    response = requests.post(action_url, headers=headers)
    return jsonify({"status": "success" if response.status_code == 204 else "error"})

if __name__ == '__main__':
    # 生产环境不应该使用debug模式
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    app.run(debug=debug_mode, host=host, port=port)
