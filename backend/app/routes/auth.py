from flask import Blueprint, jsonify, request
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
from app import bcrypt
from app.db import create_user_database, get_user_db
import datetime

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    """Route for user registration."""
    try:
        if current_user.is_authenticated:
            return jsonify({"message": "Already authenticated", "redirect": "/chat"}), 200
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        # Validate input data
        if not data.get('full_name') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Check if email already exists
        if User.find_by_email(data.get('email')):
            return jsonify({"error": "Email already registered"}), 400
        
        # Hash the password
        hashed_pw = bcrypt.generate_password_hash(data.get('password')).decode('utf-8')
        
        # Create user in the system database
        user = User.create(email=data.get('email'), 
                         password_hash=hashed_pw, full_name=data.get('full_name'))
        
        # Create user-specific database and ArangoDB user using the same hashed password
        if create_user_database(user.id, data.get('email'), hashed_pw):
            # Create a "me" document in the user's database
            try:
                user_db = get_user_db(user.id)
                
                # Create a "me" collection if it doesn't exist
                if not user_db.has_collection("me"):
                    user_db.create_collection("me")
                
                # Store user's personal information in the "me" document
                me_doc = {
                    "_key": "me",
                    "full_name": data.get('full_name'),
                    "email": data.get('email'),
                    "created_at": datetime.datetime.utcnow().isoformat()
                }
                user_db.collection("me").insert(me_doc, overwrite=True)
            except Exception as e:
                print(f"Error creating 'me' document: {str(e)}")
                # Continue with signup even if me document creation fails
            
            return jsonify({"message": "Your account has been created! You can now log in."}), 201
        else:
            return jsonify({"error": "Failed to create user database"}), 500
    except Exception as e:

        import traceback
        error_trace = traceback.format_exc()
        print(error_trace)
        return jsonify({"error": f"Account creation failed: {str(e)}"}), 500

@auth.route('/signin', methods=['POST'])
def signin():
    """Route for user authentication."""
    try:
        if current_user.is_authenticated:
            return jsonify({"message": "Already authenticated", "redirect": "/chat"}), 200
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        # Validate input data
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing email or password"}), 400
            
        user = User.find_by_email(data.get('email'))
        if user and bcrypt.check_password_hash(user.password, data.get('password')):
            login_user(user)
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email
                }
            }), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@auth.route('/logout')
@login_required
def logout():
    """Route for user logout."""
    try:
        logout_user()
        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500

