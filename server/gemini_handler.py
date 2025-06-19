# server/gemini_handler.py

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool

class GeminiHandler:
    """Class to handle interaction with the Google Gemini LLM."""

    def __init__(self, api_key):
        """Configures and initializes the Gemini model."""
        if not api_key:
            raise ValueError("Gemini API key not provided.")
        genai.configure(api_key=api_key)
        
        # Define tools (function declarations) for GitHub operations
        # This tells Gemini which functions are available
        self.github_tools = Tool(
            function_declarations=[
                # User operations
                {'name': 'get_user_info', 'description': "Retrieve information of the authenticated user."},
                
                # Repository operations
                {
                    'name': 'list_repos', 
                    'description': "List all repositories of the user.",
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'visibility': {'type': 'string', 'description': "Visibility of the repo ('all', 'public', 'private')"},
                        },
                    }
                },
                {
                    'name': 'create_repo', 
                    'description': "Create a new GitHub repository.",
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string', 'description': "Name of the repository."},
                            'description': {'type': 'string', 'description': "A short description of the repository."},
                            'private': {'type': 'boolean', 'description': "Whether the repository should be private."},
                        },
                        'required': ['name']
                    }
                },
                {
                    'name': 'delete_repo', 
                    'description': "Delete a GitHub repository.",
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'repo_full_name': {'type': 'string', 'description': "Full name of the repo to delete (e.g. 'username/repo-name')"},
                        },
                        'required': ['repo_full_name']
                    }
                },

                # Collaborator operations
                {
                    'name': 'list_collaborators',
                    'description': 'List all collaborators for a repository.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'repo_full_name': {'type': 'string', 'description': "Full name of the repository (e.g. 'username/repo-name')"}
                        },
                        'required': ['repo_full_name']
                    }
                },
                {
                    'name': 'add_collaborator',
                    'description': 'Add a collaborator to a repository.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'repo_full_name': {'type': 'string', 'description': "Full name of the repository (e.g. 'username/repo-name')"},
                            'username': {'type': 'string', 'description': "GitHub username of the collaborator to add."},
                            'permission': {'type': 'string', 'description': "Permission level ('pull', 'push', 'admin', 'maintain', 'triage'). Default is 'push'."}
                        },
                        'required': ['repo_full_name', 'username']
                    }
                },
            ]
        )
        
        # Initialize the Gemini model
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config=GenerationConfig(temperature=0),
            tools=[self.github_tools]
        )

    def get_github_operation(self, prompt: str):
        """
        Calls Gemini to analyze the user's prompt and determine the GitHub function to invoke.
        """
        try:
            # Start a new chat session
            chat_session = self.model.start_chat()
            
            # Send the prompt
            response = chat_session.send_message(prompt)
            
            # Check if the model returns a function call
            if response.candidates[0].content.parts[0].function_call:
                return response.candidates[0].content.parts[0].function_call
            
            return None  # If no function call is found
            
        except Exception as e:
            print(f"Error receiving response from Gemini: {e}")
            return None
