# server/gemini_handler.py

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool

class GeminiHandler:
    """Class to handle interaction with Google Gemini LLM."""

    def __init__(self, api_key):
        """Configures and initializes the Gemini model."""
        if not api_key:
            raise ValueError("Gemini API key not provided.")
        genai.configure(api_key=api_key)
        
        # Define tools (function declarations) for GitHub operations
        # This tells Gemini which functions are available.
        # All operations from your list have been added.
        self.github_tools = Tool(
            function_declarations=[
                # User and Authentication
                {'name': 'get_user_info', 'description': "Get authenticated user's GitHub information."},
                {'name': 'get_any_user_info', 'description': "Get public information of any GitHub user.", 'parameters': {'type': 'object', 'properties': {'username': {'type': 'string', 'description': 'GitHub username of the user.'}}, 'required': ['username']}},

                # Repository Operations
                {'name': 'list_repos', 'description': "List all repositories of the user.", 'parameters': {'type': 'object', 'properties': {'visibility': {'type': 'string', 'description': "Visibility of the repository ('all', 'public', 'private')"}}}},
                {'name': 'create_repo', 'description': "Create a new GitHub repository.", 'parameters': {'type': 'object', 'properties': {'name': {'type': 'string', 'description': "Name of the repository."}, 'description': {'type': 'string', 'description': "Description of the repository."}, 'private': {'type': 'boolean', 'description': "Whether the repository should be private."}}, 'required': ['name']}},
                {'name': 'delete_repo', 'description': "Delete a GitHub repository.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository to delete (e.g. 'username/repo-name')"}}, 'required': ['repo_full_name']}},
                {'name': 'fork_repo', 'description': "Fork another user's repository into your account.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository to fork (e.g. 'owner/repo-name')"}}, 'required': ['repo_full_name']}},
                {'name': 'get_repo_stats', 'description': "Get stats (stars, forks, watchers) of a repository.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}}, 'required': ['repo_full_name']}},

                # File and Content Management
                {'name': 'list_files', 'description': "List contents of a folder in a repository.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'path': {'type': 'string', 'description': "Path of the file or folder to view. Leave empty for root."}}, 'required': ['repo_full_name']}},
                {'name': 'get_file_content', 'description': "Read the content of a file in a repository.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'file_path': {'type': 'string', 'description': "Path of the file to read."}}, 'required': ['repo_full_name', 'file_path']}},
                {'name': 'create_file', 'description': "Create a new file in a repository.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'file_path': {'type': 'string', 'description': "Path of the file to create."}, 'commit_message': {'type': 'string', 'description': "Commit message."}, 'content': {'type': 'string', 'description': "Content of the file."}}, 'required': ['repo_full_name', 'file_path', 'commit_message', 'content']}},
                {'name': 'update_file', 'description': "Update an existing file in a repository.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'file_path': {'type': 'string', 'description': "Path of the file to update."}, 'commit_message': {'type': 'string', 'description': "Commit message."}, 'content': {'type': 'string', 'description': "New file content."}}, 'required': ['repo_full_name', 'file_path', 'commit_message', 'content']}},
                {'name': 'delete_file', 'description': "Delete a file from a repository.", 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'file_path': {'type': 'string', 'description': "Path of the file to delete."}, 'commit_message': {'type': 'string', 'description': "Commit message."}}, 'required': ['repo_full_name', 'file_path', 'commit_message']}},

                # Collaborators
                {'name': 'list_collaborators', 'description': 'List all collaborators of a repository.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository"}}, 'required': ['repo_full_name']}},
                {'name': 'add_collaborator', 'description': 'Add a collaborator to a repository.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository"}, 'username': {'type': 'string', 'description': "Username of the collaborator"}, 'permission': {'type': 'string', 'description': "Permission level ('pull', 'push', 'admin')"}}, 'required': ['repo_full_name', 'username']}},
                {'name': 'remove_collaborator', 'description': 'Remove a collaborator from a repository.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository"}, 'username': {'type': 'string', 'description': "Username of the collaborator to remove"}}, 'required': ['repo_full_name', 'username']}},

                # Issues
                {'name': 'create_issue', 'description': 'Create a new issue in a repository.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'title': {'type': 'string', 'description': "Title of the issue."}, 'body': {'type': 'string', 'description': "Optional description of the issue."}, 'assignee': {'type': 'string', 'description': "Username to assign the issue to (optional)."}}, 'required': ['repo_full_name', 'title']}},
                {'name': 'list_issues', 'description': 'List issues of a repository.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'state': {'type': 'string', 'description': "State of the issue ('open', 'closed', 'all')."}}, 'required': ['repo_full_name']}},
                {'name': 'close_issue', 'description': 'Close an issue.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'issue_number': {'type': 'integer', 'description': "Number of the issue to close."}}, 'required': ['repo_full_name', 'issue_number']}},

                # Branches
                {'name': 'list_branches', 'description': 'List all branches of a repository.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}}, 'required': ['repo_full_name']}},
                {'name': 'create_branch', 'description': 'Create a new branch in a repository.', 'parameters': {'type': 'object', 'properties': {'repo_full_name': {'type': 'string', 'description': "Full name of the repository."}, 'branch_name': {'type': 'string', 'description': "Name of the new branch."}, 'source_branch': {'type': 'string', 'description': "Name of the source branch (e.g. 'main')."}}, 'required': ['repo_full_name', 'branch_name', 'source_branch']}},

                # Search
                {'name': 'search_repos', 'description': 'Search for repositories on GitHub by keyword.', 'parameters': {'type': 'object', 'properties': {'query': {'type': 'string', 'description': "Query or keyword to search for."}}, 'required': ['query']}},
                {'name': 'search_users', 'description': 'Search for users on GitHub by keyword.', 'parameters': {'type': 'object', 'properties': {'query': {'type': 'string', 'description': "Query or keyword to search for."}}, 'required': ['query']}},
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
        Calls Gemini to analyze the user prompt and determine which GitHub function to call.
        """
        try:
            # Start chat session
            chat_session = self.model.start_chat()
            
            # Send prompt
            response = chat_session.send_message(prompt)
            
            # Check if the model returns a function call
            if response.candidates[0].content.parts[0].function_call:
                return response.candidates[0].content.parts[0].function_call
            
            return None # If no function call found
            
        except Exception as e:
            print(f"Error in getting response from Gemini: {e}")
            return None
