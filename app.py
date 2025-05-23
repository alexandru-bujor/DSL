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

# Import dotenv to load environment variables from .env file
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
# This should be called before any config.update that uses these vars.
load_dotenv()


# ─── App & Extensions ──────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=None)

# Retrieve configuration from environment variables
app.config.update({
    'SECRET_KEY':              os.environ.get('FLASK_SECRET'), # No default here; it must be set in .env or env
    'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'), # No default; it must be set
    'SQLALCHEMY_TRACK_MODIFICATIONS': False, # Recommended to set to False for performance
    'JWT_SECRET_KEY':          os.environ.get('JWT_SECRET'),   # No default; it must be set
    'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=2),
})

# Get CORS origins from env, split by comma, or default to localhost
cors_origins_str = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
cors_origins_list = [origin.strip() for origin in cors_origins_str.split(',')]

CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": cors_origins_list}})

# Initialize extensions
db  = SQLAlchemy(app)
jwt = JWTManager(app)


# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # Using 'lazy=True' for relationship backref is generally fine.
    # For many-to-one or one-to-many relationships, it's efficient.
    # cascade='all, delete-orphan' ensures snippets are deleted when user is deleted
    snippets = db.relationship('Snippet', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

    def __repr__(self):
        return f'<User {self.email}>'

class Snippet(db.Model):
    __tablename__ = 'snippets'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(100), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    # For PostgreSQL, func.now() translates correctly to the appropriate timestamp function.
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Snippet {self.title}>'

# ─── Database Initialization ──────────────────────────────────────────────────

# It's crucial to ensure your database connection is valid before calling create_all().
# If DATABASE_URL is not set, this will fail.
with app.app_context():
    try:
        # This will attempt to connect and create tables if they don't exist.
        # In production, use Flask-Migrate/Alembic for schema management.
        db.create_all()
        print("Database tables checked/created successfully.")
    except Exception as e:
        print(f"Error connecting to or creating database tables: {e}")
        print("Please ensure your DATABASE_URL environment variable is correctly set and the database is accessible.")
        # Depending on your deployment strategy, you might want to exit here
        # or log the error more robustly for a production setup.


# ─── Auth Routes (/api/auth) ─────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify(msg="Email and password required"), 400

    try:
        if User.query.filter_by(email=email).first():
            return jsonify(msg="Email already in use"), 409

        u = User(email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return jsonify(msg="User registered"), 201
    except Exception as e:
        db.session.rollback() # Rollback in case of an error during commit
        print(f"Error during registration: {e}")
        # Log the full traceback for debugging in production
        traceback.print_exc()
        return jsonify(msg="An error occurred during registration"), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password','') # Default to empty string to avoid error on check_password_hash

    u = User.query.filter_by(email=email).first()
    if not u or not u.check_password(password):
        return jsonify(msg="Bad credentials"), 401

    token = create_access_token(identity=str(u.id))
    return jsonify(access_token=token), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def me():
    uid = get_jwt_identity() # This returns a string
    u   = User.query.get(int(uid)) # Convert back to int for querying primary key
    if not u: # Handle case where user might be deleted but token is still valid
        return jsonify(msg="User not found"), 404
    return jsonify(id=u.id, email=u.email), 200


# ─── Snippet Routes (/api/snippets) ───────────────────────────────────────────

@app.route('/api/snippets', methods=['GET'])
@jwt_required()
def list_snippets():
    uid = get_jwt_identity()
    # Ensure uid is an integer for query as user_id in Snippet is Integer
    try:
        user_id_int = int(uid)
    except ValueError:
        return jsonify(msg="Invalid user ID in token"), 400

    snips = Snippet.query.filter_by(user_id=user_id_int).all()
    return jsonify([
        {'id': s.id, 'title': s.title, 'content': s.content, 'created_at': s.created_at.isoformat()}
        for s in snips
    ]), 200

@app.route('/api/snippets', methods=['POST'])
@jwt_required()
def create_snippet():
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify(msg="Title and content required"), 400

    uid = get_jwt_identity()
    try:
        user_id_int = int(uid)
    except ValueError:
        return jsonify(msg="Invalid user ID in token"), 400

    try:
        s = Snippet(title=title, content=content, user_id=user_id_int)
        db.session.add(s)
        db.session.commit()
        return jsonify(id=s.id), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating snippet: {e}")
        traceback.print_exc()
        return jsonify(msg="An error occurred creating the snippet"), 500


@app.route('/api/snippets/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_snippet(id): # Renamed for clarity
    uid = get_jwt_identity()
    try:
        user_id_int = int(uid)
    except ValueError:
        return jsonify(msg="Invalid user ID in token"), 400

    s = Snippet.query.get(id) # Use get() instead of get_or_404 to handle not found explicitly

    if not s:
        return jsonify(msg="Snippet not found"), 404

    # Ensure the snippet belongs to the authenticated user
    if s.user_id != user_id_int:
        return jsonify(msg="Forbidden"), 403

    try:
        db.session.delete(s)
        db.session.commit()
        # It's common for DELETE to return 204 No Content if no response body is needed
        return jsonify(msg="Snippet deleted"), 200 # Or 204 No Content with no body
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting snippet: {e}")
        traceback.print_exc()
        return jsonify(msg="An error occurred deleting the snippet"), 500


# ─── Conversion Routes (/api/decode & /api/compile) ────────────────────────

def cleanup(path):
    """Helper to safely remove a file."""
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        print(f"Error cleaning up file {path}: {e}")
        traceback.print_exc()


@app.route('/api/decode', methods=['POST'])
@jwt_required()
def decode():
    if 'file' not in request.files:
        return jsonify({'error': 'No XML file uploaded'}), 400

    xml_file = request.files['file']
    if not xml_file.filename.lower().endswith('.xml'):
        return jsonify({'error': 'Only XML files are allowed'}), 400

    xml_bytes = xml_file.read()
    temp_xml, temp_dsl = None, None
    try:
        # Use tempfile.NamedTemporaryFile to create temporary files securely
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tx:
            tx.write(xml_bytes)
            temp_xml = tx.name
        with tempfile.NamedTemporaryFile(suffix='.dsl', delete=False) as td:
            temp_dsl = td.name

        # Ensure decode.py is in the PATH or specify its full path if not in the same directory
        # Consider using an absolute path for subprocess calls in production
        result = subprocess.run(
            ['python3', 'src/decode.py', temp_xml, temp_dsl], # Use python3 explicitly
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        if result.returncode != 0:
            print(f"Decode script failed: {result.stderr}")
            return jsonify(error='Conversion failed', stderr=result.stderr.strip()), 500

        dsl_code = open(temp_dsl, 'r', encoding='utf-8').read()
        rf_json  = json.loads(result.stdout)
        return jsonify(dsl=dsl_code, react_flow=rf_json), 200

    except json.JSONDecodeError as e:
        print(f"JSON decoding error in decode endpoint: {e}")
        traceback.print_exc()
        return jsonify(error='Invalid JSON response from conversion script', details=str(e)), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify(error='Internal error during decode', details=str(e)), 500

    finally:
        # Ensure temporary files are cleaned up
        for f in (temp_xml, temp_dsl):
            cleanup(f)


@app.route('/api/compile', methods=['POST'])
@jwt_required()
def compile_dsl(): # Renamed 'compile' to avoid conflict with built-in compile
    try:
        dsl_text = request.json.get("dsl")
        if not dsl_text:
            return jsonify(error="No DSL code provided"), 400

        with tempfile.NamedTemporaryFile(suffix='.dsl', delete=False, mode='w', encoding='utf-8') as tf:
            tf.write(dsl_text)
            dsl_path = tf.name

        # Ensure compile.py is in the PATH or specify its full path if not in the same directory
        # Consider using an absolute path for subprocess calls in production
        result = subprocess.run(
            ['python3', 'src/compile.py', dsl_path], # Use python3 explicitly
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )

        if result.returncode != 0:
            print(f"Compile script failed: {result.stderr}")
            return jsonify(error="Recompilation failed", stderr=result.stderr.strip()), 500

        rf_json = json.loads(result.stdout)
        return jsonify(react_flow=rf_json), 200

    except json.JSONDecodeError as e:
        print(f"JSON decoding error in compile endpoint: {e}")
        traceback.print_exc()
        return jsonify(error='Invalid JSON response from recompilation script', details=str(e)), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify(error="Internal error during compile", details=str(e)), 500
    finally:
        # Ensure temporary file is cleaned up
        if 'dsl_path' in locals() and dsl_path:
            cleanup(dsl_path)


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # When running with 'python app.py', Flask's development server is used.
    # For production, use Gunicorn (or uWSGI) instead.
    # Gunicorn will typically run your app on 0.0.0.0 and listen on a specific port (e.g., 8000).
    # Then Nginx reverse proxies requests from 80/443 to Gunicorn.
    # The 'debug=True' should NEVER be used in production.
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', host='0.0.0.0', port=5000)
