import os
import json
import subprocess
import shutil
from flask import Flask, request, render_template, redirect, url_for, flash, session
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'json'}
app.config['SECRET_KEY'] = 'supersecretkey'

# Simulando um usuário e senha, para fins de exemplo
USER = 'admin'
PASSWORD = 'password'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_current_node_version():
    response = requests.get('https://nodejs.org/dist/index.json')
    if response.status_code == 200:
        versions = response.json()
        return versions[0]['version']
    return 'Unable to retrieve current Node.js version'

def clone_repo(repo_url, clone_dir):
    try:
        subprocess.run(['git', 'clone', repo_url, clone_dir], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    # Verificar se o usuário está autenticado
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        repo_url = request.form.get('repo_url')
        if repo_url:
            clone_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'repo')
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir)
            success = clone_repo(repo_url, clone_dir)
            if not success:
                flash('Failed to clone repository.')
                return redirect(request.url)
            package_json_path = os.path.join(clone_dir, 'package.json')
            if not os.path.exists(package_json_path):
                flash('package.json not found in the repository.')
                return redirect(request.url)
            try:
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                node_version = package_json.get('engines', {}).get('node', 'Not specified')
            except json.JSONDecodeError:
                flash('Invalid JSON file in repository.')
                return redirect(request.url)
            current_version = get_current_node_version()
            return render_template('result.html', node_version=node_version, current_version=current_version)
        else:
            flash('Please provide a repository URL.')
            return redirect(request.url)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username != USER or password != PASSWORD:
            error = 'Invalid credentials. Please try again.'
        else:
            session['logged_in'] = True
            flash('You were successfully logged in.')
            return redirect(url_for('upload_file'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were successfully logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
