from github import Github, GithubException

class GitHubHandler:
    """Handles all interactions with the GitHub API using PyGithub."""

    def __init__(self, token):
        """Initializes an authenticated GitHub object."""
        if not token:
            raise ValueError("GitHub access token not provided.")
        self.g = Github(token)
        try:
            # Attempt to fetch the user to verify the token
            self.user = self.g.get_user()
        except GithubException as e:
            raise Exception(f"Invalid GitHub token or failed to access the API: {e.status}") from e

    def get_user_info(self):
        """Returns basic information about the authenticated user."""
        return {
            'login': self.user.login,
            'name': self.user.name,
            'public_repos': self.user.public_repos,
            'private_repos': self.user.owned_private_repos,
        }

    def list_repos(self, visibility='all'):
        """Lists the user's repositories with the specified visibility."""
        try:
            repos = self.user.get_repos(affiliation='owner', visibility=visibility)
            repo_names = [repo.full_name for repo in repos]
            
            if not repo_names:
                return f"You have no '{visibility}' repositories."
            
            return f"Your {visibility} repositories:\n" + "\n".join(repo_names)
        except Exception as e:
            return f"Error listing repositories: {e}"

    def create_repo(self, name: str, description: str = "", private: bool = False):
        """Creates a new repository."""
        try:
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private
            )
            return f"Repository '{repo.full_name}' created successfully."
        except GithubException as e:
            if e.status == 422:  # Unprocessable Entity (often means name already exists)
                return f"Error: Repository with name '{name}' might already exist."
            return f"Error creating repository: {e}"

    def delete_repo(self, repo_full_name: str):
        """Deletes a repository."""
        try:
            repo = self.g.get_repo(repo_full_name)
            if repo.owner.login != self.user.login:
                return "Error: You can only delete repositories you own."
            
            repo.delete()
            return f"Repository '{repo_full_name}' deleted successfully."
        except GithubException as e:
            if e.status == 404:
                return f"Error: Repository '{repo_full_name}' not found."
            return f"Error deleting repository: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def list_collaborators(self, repo_full_name: str):
        """Lists collaborators for a repository."""
        try:
            repo = self.g.get_repo(repo_full_name)
            collaborators = repo.get_collaborators()
            collaborator_logins = [c.login for c in collaborators]
            if not collaborator_logins:
                return f"No collaborators found in repository '{repo_full_name}'."
            return f"Collaborators for '{repo_full_name}':\n" + "\n".join(collaborator_logins)
        except GithubException as e:
            if e.status == 404:
                return f"Error: Repository '{repo_full_name}' not found."
            return f"Error listing collaborators: {e}"

    def add_collaborator(self, repo_full_name: str, username: str, permission: str = 'push'):
        """Adds a collaborator to a repository with the specified permission."""
        valid_permissions = ['pull', 'push', 'admin', 'maintain', 'triage']
        if permission not in valid_permissions:
            return f"Invalid permission '{permission}'. Valid options are: {', '.join(valid_permissions)}"
        try:
            repo = self.g.get_repo(repo_full_name)
            repo.add_to_collaborators(username, permission=permission)
            return f"User '{username}' has been invited to '{repo_full_name}' with '{permission}' permissions."
        except GithubException as e:
            if e.status == 404:
                return f"Error: Repository '{repo_full_name}' or user '{username}' not found."
            return f"Error adding collaborator: {e}"
