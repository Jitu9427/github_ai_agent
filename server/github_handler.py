# server/github_handler.py

from github import Github, GithubException, UnknownObjectException

class GitHubHandler:
    """Handles all interactions with the GitHub API using PyGithub."""

    def __init__(self, token):
        """Initializes an authenticated GitHub object."""
        if not token:
            raise ValueError("GitHub access token not provided.")
        self.g = Github(token)
        try:
            self.user = self.g.get_user()
        except GithubException as e:
            raise Exception(f"Invalid GitHub token or unable to access API: {e.status}") from e

    # --- Helper Function ---
    def _get_repo(self, repo_full_name):
        """Helper to get a repository object and handle 404 errors."""
        try:
            return self.g.get_repo(repo_full_name)
        except UnknownObjectException:
            return None

    # --- User and Authentication ---
    def get_user_info(self):
        """Returns information about the authenticated user."""
        return (f"Logged in user: {self.user.login} ({self.user.name})\n"
                f"Public Repos: {self.user.public_repos}\n"
                f"Private Repos (Owned): {self.user.owned_private_repos}\n"
                f"Followers: {self.user.followers}")
    
    def get_any_user_info(self, username: str):
        """Fetches public information of any user."""
        try:
            user = self.g.get_user(username)
            return (f"User: {user.login} ({user.name})\n"
                    f"Bio: {user.bio}\n"
                    f"Public Repos: {user.public_repos}\n"
                    f"Followers: {user.followers}")
        except UnknownObjectException:
            return f"Error: User '{username}' not found."

    # --- Repository Operations ---
    def list_repos(self, visibility='all'):
        """Returns list of user's repositories."""
        repos = self.user.get_repos(affiliation='owner', visibility=visibility)
        repo_names = [repo.full_name for repo in repos]
        if not repo_names: return f"You have no '{visibility}' repositories."
        return f"Your {visibility} repositories:\n" + "\n".join(repo_names)

    def create_repo(self, name: str, description: str = "", private: bool = False):
        """Creates a new repository."""
        try:
            repo = self.user.create_repo(name=name, description=description, private=private)
            return f"Repository '{repo.full_name}' created successfully."
        except GithubException as e:
            if e.status == 422: return f"Error: Repository with name '{name}' might already exist."
            return f"Error creating repository: {e}"

    def delete_repo(self, repo_full_name: str):
        """Deletes a repository."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        if repo.owner.login != self.user.login: return "Error: You can only delete your own repository."
        try:
            repo.delete()
            return f"Repository '{repo_full_name}' deleted successfully."
        except GithubException as e:
            return f"Error deleting repository: {e}"

    def fork_repo(self, repo_full_name: str):
        """Forks a repository."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            forked_repo = self.user.create_fork(repo)
            return f"Repository '{repo.full_name}' successfully forked as '{forked_repo.full_name}'."
        except GithubException as e:
            return f"Error forking repository: {e}"

    def get_repo_stats(self, repo_full_name: str):
        """Fetches repository statistics."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        return (f"Stats for '{repo.full_name}':\n"
                f"  - Stars: {repo.stargazers_count}\n"
                f"  - Forks: {repo.forks_count}\n"
                f"  - Watchers: {repo.subscribers_count}\n"
                f"  - Language: {repo.language}")

    # --- File and Content Management ---
    def list_files(self, repo_full_name: str, path: str = ""):
        """Lists files and folders in a repository."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            contents = repo.get_contents(path)
            file_list = [f"[{item.type}] {item.name}" for item in contents]
            return f"Contents of '{repo.full_name}/{path}':\n" + "\n".join(file_list)
        except UnknownObjectException:
            return f"Error: Path '{path}' not found in '{repo.full_name}'."

    def get_file_content(self, repo_full_name: str, file_path: str):
        """Fetches content of a file."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            file_content = repo.get_contents(file_path)
            return f"--- Content of '{file_path}' ---\n{file_content.decoded_content.decode('utf-8')}"
        except UnknownObjectException:
            return f"Error: File '{file_path}' not found."
        except GithubException:
            return f"Error: Is '{file_path}' a folder? I can only read file content."

    def create_file(self, repo_full_name: str, file_path: str, commit_message: str, content: str):
        """Creates a new file."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            repo.create_file(file_path, commit_message, content)
            return f"File '{file_path}' created successfully in '{repo.full_name}'."
        except GithubException as e:
            if e.status == 422: return f"Error: File '{file_path}' might already exist."
            return f"Error creating file: {e}"

    def update_file(self, repo_full_name: str, file_path: str, commit_message: str, content: str):
        """Updates an existing file."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            file_to_update = repo.get_contents(file_path)
            repo.update_file(file_path, commit_message, content, file_to_update.sha)
            return f"File '{file_path}' updated successfully in '{repo.full_name}'."
        except UnknownObjectException:
            return f"Error: File '{file_path}' not found."
        except GithubException as e:
            return f"Error updating file: {e}"

    def delete_file(self, repo_full_name: str, file_path: str, commit_message: str):
        """Deletes a file."""
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            file_to_delete = repo.get_contents(file_path)
            repo.delete_file(file_path, commit_message, file_to_delete.sha)
            return f"File '{file_path}' deleted successfully."
        except UnknownObjectException:
            return f"Error: File '{file_path}' not found."
        except GithubException as e:
            return f"Error deleting file: {e}"

    # --- Collaborator Operations ---
    def list_collaborators(self, repo_full_name: str):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        collaborators = repo.get_collaborators()
        logins = [c.login for c in collaborators]
        if not logins: return f"No collaborators found in '{repo.full_name}'."
        return f"Collaborators in '{repo.full_name}':\n" + "\n".join(logins)

    def add_collaborator(self, repo_full_name: str, username: str, permission: str = 'push'):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            repo.add_to_collaborators(username, permission=permission)
            return f"Invitation sent to user '{username}' as collaborator in '{repo.full_name}'."
        except GithubException as e:
            return f"Error adding collaborator: {e}"

    def remove_collaborator(self, repo_full_name: str, username: str):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            repo.remove_from_collaborators(username)
            return f"User '{username}' removed as collaborator from '{repo.full_name}'."
        except GithubException as e:
            return f"Error removing collaborator: {e}"
            
    # --- Issues ---
    def create_issue(self, repo_full_name: str, title: str, body: str = "", assignee: str = None):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            issue = repo.create_issue(title=title, body=body, assignee=assignee)
            return f"Issue #{issue.number} ('{title}') created successfully."
        except GithubException as e:
            return f"Error creating issue: {e}"

    def list_issues(self, repo_full_name: str, state: str = 'open'):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        issues = repo.get_issues(state=state)
        issue_list = [f"#{i.number}: {i.title}" for i in issues]
        if not issue_list: return f"No '{state}' issues found in '{repo.full_name}'."
        return f"{state.capitalize()} issues in '{repo.full_name}':\n" + "\n".join(issue_list)

    def close_issue(self, repo_full_name: str, issue_number: int):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            issue = repo.get_issue(issue_number)
            issue.edit(state='closed')
            return f"Issue #{issue_number} closed successfully."
        except UnknownObjectException:
            return f"Error: Issue #{issue_number} not found."
        except GithubException as e:
            return f"Error closing issue: {e}"

    # --- Branches ---
    def list_branches(self, repo_full_name: str):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        branches = [b.name for b in repo.get_branches()]
        return f"Branches in '{repo.full_name}':\n" + "\n".join(branches)

    def create_branch(self, repo_full_name: str, branch_name: str, source_branch: str = 'main'):
        repo = self._get_repo(repo_full_name)
        if not repo: return f"Error: Repository '{repo_full_name}' not found."
        try:
            source = repo.get_branch(source_branch)
            repo.create_git_ref(ref=f'refs/heads/{branch_name}', sha=source.commit.sha)
            return f"Branch '{branch_name}' created successfully from '{source_branch}'."
        except GithubException as e:
            if e.status == 422: return f"Error: Branch '{branch_name}' might already exist."
            return f"Error creating branch: {e}"

    # --- Search ---
    def search_repos(self, query: str):
        repos = self.g.search_repositories(query)
        repo_list = [r.full_name for r in repos[:10]] # Show top 10 only
        if not repo_list: return f"No repositories found for '{query}'."
        return f"Search results for '{query}':\n" + "\n".join(repo_list)

    def search_users(self, query: str):
        users = self.g.search_users(query)
        user_list = [u.login for u in users[:10]] # Show top 10 only
        if not user_list: return f"No users found for '{query}'."
        return f"Search results for '{query}':\n" + "\n".join(user_list)
