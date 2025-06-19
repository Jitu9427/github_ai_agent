# client/client.py

import requests
import time

# Base URL of the server
SERVER_URL = "http://127.0.0.1:5000"
USER_ID = "main_user"  # Unique identifier for this client

def check_auth():
    """Contact the server to check if the user is logged in."""
    try:
        response = requests.get(f"{SERVER_URL}/check_auth", params={'user_id': USER_ID})
        response.raise_for_status()
        data = response.json()
        if data.get("logged_in"):
            user_info = data.get("user", {})
            if isinstance(user_info, dict):
                print(f"You are logged in as '{user_info.get('login', 'Unknown')}'.")
            else:
                print(user_info)  # Just print the message if it's a string
            return True
        else:
            print("You are not logged in.")
            print(f"Please visit this URL to authenticate: {SERVER_URL}/login")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to the server: {e}")
        print("Did you start the server (server.py)?")
        return False


def chat_with_bot(prompt):
    """Sends a chat message to the server and receives the response."""
    try:
        payload = {"user_id": USER_ID, "prompt": prompt}
        response = requests.post(f"{SERVER_URL}/chat", json=payload)
        response.raise_for_status()
        return response.json().get("response", "No response received.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "Error: You are not logged in. Please restart the app to authenticate."
        else:
            error_details = e.response.json().get('response', str(e))
            return f"Server error ({e.response.status_code}): {error_details}"
    except requests.exceptions.RequestException as e:
        return f"Failed to connect to the server: {e}"

def main():
    """Main client loop."""
    print("--- Welcome to the GitHub AI Agent ---")
    
    # Check authentication status on startup
    if not check_auth():
        print("\nPlease restart this client after logging in.")
        return

    print("\nYou can start chatting with the bot. Type 'exit' to quit.")
    print("Examples: 'meri public repos list karo' or 'ek test repo banao'")
    
    while True:
        try:
            prompt = input("\nYou: ")
            if prompt.lower() == 'exit':
                print("Goodbye!")
                break
            
            if not prompt:
                continue

            print("Bot: Thinking...")
            response = chat_with_bot(prompt)
            print(f"Bot: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
