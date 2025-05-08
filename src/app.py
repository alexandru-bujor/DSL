import os
import json
import tempfile
import traceback
import subprocess
from datetime import timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

# ─── App & Extensions ──────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=None)
app.config.update({
    'SECRET_KEY':              os.environ.get('FLASK_SECRET', 'change-this!'),
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///data.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'JWT_SECRET_KEY':          os.environ.get('JWT_SECRET', 'another-secret'),
    'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=2),
})
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:3000"}})

db  = SQLAlchemy(app)
jwt = JWTManager(app)


# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    snippets = db.relationship('Snippet', backref='owner', lazy=True)

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

class Snippet(db.Model):
    __tablename__ = 'snippets'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(100), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


with app.app_context():
    db.create_all()


# ─── Auth Routes (/api/auth) ─────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    if not data.get('email') or not data.get('password'):
        return jsonify(msg="Email and password required"), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify(msg="Email already in use"), 409

    u = User(email=data['email'])
    u.set_password(data['password'])
    db.session.add(u)
    db.session.commit()
    return jsonify(msg="User registered"), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    u = User.query.filter_by(email=data.get('email')).first()
    if not u or not u.check_password(data.get('password','')):
        return jsonify(msg="Bad credentials"), 401

    token = create_access_token(identity=str(u.id))
    return jsonify(access_token=token), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def me():
    uid = get_jwt_identity()
    u   = User.query.get(uid)
    return jsonify(id=u.id, email=u.email), 200


# ─── Snippet Routes (/api/snippets) ───────────────────────────────────────────

@app.route('/api/snippets', methods=['GET'])
@jwt_required()
def list_snippets():
    uid = get_jwt_identity()
    snips = Snippet.query.filter_by(user_id=uid).all()
    return jsonify([
        {'id': s.id, 'title': s.title, 'content': s.content, 'created_at': s.created_at.isoformat()}
        for s in snips
    ]), 200

@app.route('/api/snippets', methods=['POST'])
@jwt_required()
def create_snippet():
    data = request.get_json() or {}
    if not data.get('title') or not data.get('content'):
        return jsonify(msg="Title and content required"), 400

    uid = get_jwt_identity()
    s = Snippet(title=data['title'], content=data['content'], user_id=uid)
    db.session.add(s)
    db.session.commit()
    return jsonify(id=s.id), 201

@app.route('/api/snippets/<int:id>', methods=['GET'])
@jwt_required()
def get_snippet(id):
    uid = get_jwt_identity()
    s = Snippet.query.get_or_404(id)
    if s.user_id != uid:
        return jsonify(msg="Forbidden"), 403
    return jsonify(id=s.id, title=s.title, content=s.content), 200


# ─── Conversion Routes (/api/convert & /api/reactflow) ────────────────────────

def cleanup(path):
    try: os.unlink(path)
    except: pass

@app.route('/api/convert', methods=['POST'])
@jwt_required()
def convert_xml_to_dsl():
    if 'file' not in request.files:
        return jsonify({'error': 'No XML file uploaded'}), 400

    xml_bytes = request.files['file'].read()
    temp_xml, temp_dsl = None, None
    try:
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tx:
            tx.write(xml_bytes); temp_xml = tx.name
        with tempfile.NamedTemporaryFile(suffix='.dsl', delete=False) as td:
            temp_dsl = td.name

        result = subprocess.run(
            ['python','xml2dsl.py', temp_xml, temp_dsl],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode != 0:
            return jsonify(error='Conversion failed', stderr=result.stderr), 500

        dsl_code = open(temp_dsl, 'r', encoding='utf-8').read()
        rf_json  = json.loads(result.stdout)
        return jsonify(dsl=dsl_code, react_flow=rf_json), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify(error='Internal error', details=str(e)), 500

    finally:
        for f in (temp_xml, temp_dsl):
            if f: cleanup(f)


@app.route('/api/reactflow', methods=['POST'])
@jwt_required()
def dsl_to_reactflow():
    dsl_text = request.get_data(as_text=True)
    if not dsl_text.strip():
        return jsonify({'error':'No DSL content provided'}), 400

    temp_dsl = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.dsl', delete=False, mode='w', encoding='utf-8') as td:
            td.write(dsl_text); temp_dsl = td.name

        result = subprocess.run(
            ['python','dsl2reactflow.py', temp_dsl],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode != 0:
            return jsonify(error='DSL→ReactFlow failed', stderr=result.stderr), 500

        rf_json = json.loads(result.stdout)
        return jsonify(react_flow=rf_json), 200

    except Exception as e:
        return jsonify(error='Internal error', details=str(e)), 500

    finally:
        if temp_dsl: cleanup(temp_dsl)


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
