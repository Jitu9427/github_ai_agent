# server/server.py
import os
import webbrowser
import requests
from flask import Flask, request, jsonify, redirect
from dotenv import load_dotenv
from github_handler import GitHubHandler
from gemini_handler import GeminiHandler

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# GitHub OAuth app credentials
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Store authentication tokens in memory (use a database in production)
# This is a simple way to manage user sessions
user_tokens = {}

# Initialize Gemini handler
try:
    gemini = GeminiHandler(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error initializing Gemini Handler: {e}")
    gemini = None

# --- OAuth Routes ---

@app.route("/")
def home():
    """Homepage that indicates the server is running."""
    return "GitHub chatbot server is running. Use the client to authenticate."

@app.route('/login')
def login():
    """Redirects the user to the GitHub authentication page."""
    # Use a 'state' parameter to identify the user
    # For this example, we use a default user_id = 'main_user'
    user_id = "main_user"
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}"
        f"&scope=repo,delete_repo,user&state={user_id}"
    )
    return redirect(github_auth_url)

@app.route('/callback')
def callback():
    """Handles the GitHub OAuth callback."""
    session_code = request.args.get('code')
    state = request.args.get('state')  # This is the user_id we sent earlier
    
    # Exchange the session code for an access token
    token_url = 'https://github.com/login/oauth/access_token'
    headers = {'Accept': 'application/json'}
    payload = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': session_code
    }
    
    response = requests.post(token_url, headers=headers, data=payload)
    response_data = response.json()
    
    print("DEBUG: GitHub token response:", response_data)

    access_token = response_data.get('access_token')
    
    if access_token:
        # Store the token with the user's state (user_id)
        user_tokens[state] = access_token
        print(f"Token successfully obtained for user '{state}'.")
        return "Authentication successful! You can close this window and return to the client."
    else:
        return "Failed to obtain access token. Please try again.", 400


# --- API Routes ---

@app.route('/check_auth')
def check_auth():
    """Checks if the user is authenticated."""
    user_id = request.args.get('user_id', 'main_user')
    if user_id in user_tokens:
        try:
            handler = GitHubHandler(user_tokens[user_id])
            user_info = handler.get_user_info()
            return jsonify({"logged_in": True, "user": user_info})
        except Exception as e:
            # If the token is invalid, remove it
            del user_tokens[user_id]
            return jsonify({"logged_in": False, "error": f"Invalid token: {e}"})
    return jsonify({"logged_in": False})


@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat messages from the client."""
    data = request.json
    user_id = data.get('user_id', 'main_user')
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"response": "Please provide a message so I can understand."}), 400

    if user_id not in user_tokens:
        return jsonify({"response": "You are not logged in. Please log in first."}), 401

    if not gemini:
        return jsonify({"response": "Gemini handler is not properly configured."}), 500

    try:
        # Get the function call from Gemini
        function_call = gemini.get_github_operation(prompt)
        
        if not function_call:
            # If no specific function was found, return a general response
            return jsonify({"response": "I couldn't understand which GitHub action to perform. Please clarify."})

        # Initialize the GitHub handler
        handler = GitHubHandler(user_tokens[user_id])
        
        # Determine which function to call and its parameters
        function_name = function_call.name
        function_args = {key: value for key, value in function_call.args.items()}
        
        # Dynamically call the method on the GitHub handler
        if hasattr(handler, function_name):
            method_to_call = getattr(handler, function_name)
            result = method_to_call(**function_args)
            return jsonify({"response": result})
        else:
            return jsonify({"response": f"Error: No action named '{function_name}' found."}), 400

    except Exception as e:
        print(f"Error while processing chat: {e}")
        return jsonify({"response": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    # Allow OAuth over HTTP for development (not recommended in production)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Run the app
    app.run(port=5000, debug=True)
    print("Client ID:", GITHUB_CLIENT_ID)
    print("Client Secret:", GITHUB_CLIENT_SECRET)
    
    