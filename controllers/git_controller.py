from git import Repo, InvalidGitRepositoryError

class GitController:
    def __init__(self, repo_path):
        try:
            self.repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            self.repo = None
            raise

    def get_branch(self):
        if self.repo:
            return self.repo.active_branch.name
        return "-"

    def get_status(self):
        if not self.repo:
            return []
        return self.repo.git.status().splitlines()

    def get_changed_files(self):
        if not self.repo:
            return []
        diff_files = self.repo.git.diff('--name-only')
        untracked_files = self.repo.untracked_files
        return diff_files.splitlines() + untracked_files

    def get_diff(self, filename):
        try:
            if filename in self.repo.untracked_files:
                with open(self.repo.working_tree_dir + '/' + filename, 'r') as f:
                    return f.read()
            else:
                return self.repo.git.diff(filename)
        except Exception as e:
            return f"获取差异失败：{str(e)}"

    def add_files(self, files):
        if self.repo:
            self.repo.index.add(files)

    def commit(self, message):
        if self.repo:
            self.repo.index.commit(message)

    def get_commit_history(self, max_count=20):
        if not self.repo:
            return []

        commits = list(self.repo.iter_commits('HEAD', max_count=max_count))
        history = []
        for commit in commits:
            history.append({
                "hexsha": commit.hexsha,
                "summary": commit.summary,
                "author": commit.author.name,
                "time": commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            })
        return history

    def get_commit_files(self, commit_hash):
        commit = self.repo.commit(commit_hash)
        return list(commit.stats.files.keys())

    def get_commit_diff(self, commit_hash, file_path):
        commit = self.repo.commit(commit_hash)
        parent = commit.parents[0] if commit.parents else None
        if parent:
            diffs = parent.diff(commit, paths=file_path)
            for diff in diffs:
                if diff.a_blob and diff.b_blob:
                    return diff.diff.decode("utf-8", errors="ignore")
        return "(无 diff 数据)"

    def get_commit_graph_data(self, max_count=30):
        """
        返回结构化的 commit 图数据：
        [
            {
                'summary': 'Fix bug',
                'author': 'Alice',
                'time': '2024-04-21 10:22',
                'parents': [1],  # 第 i 个 commit 的父是第 1 个（按时间倒序）
                'color': '#3498db'
            },
            ...
        ]
        """
        if not self.repo:
            return []

        commits = list(self.repo.iter_commits('HEAD', max_count=max_count))
        id_map = {c.hexsha: i for i, c in enumerate(commits)}
        data = []
        colors = ['#3498db', '#e67e22', '#2ecc71', '#9b59b6']  # 支持多分支线条颜色

        for i, commit in enumerate(commits):
            data.append({
                "summary": commit.summary,
                "author": commit.author.name,
                "time": commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "parents": [id_map.get(p.hexsha, -1) for p in commit.parents],
                "color": colors[i % len(colors)],
            })
        return data

