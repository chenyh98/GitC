from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QFileDialog, QListWidget, QTextEdit,
    QHBoxLayout, QMessageBox
)
from controllers.git_controller import GitController
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtWidgets import QMenuBar, QApplication
from PySide6.QtGui import QAction
from views.commit_graph_view import CommitGraphView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_menu()

        self.setWindowTitle("GitC - Git 可视化工具")
        self.resize(1000, 600)

        self.repo_path = None
        self.git = None

        self.branch_label = QLabel("当前分支：-")
        self.status_list = QListWidget()
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.open_button = QPushButton("打开 Git 仓库")

        self.open_button.clicked.connect(self.open_repo)
        self.status_list.itemClicked.connect(self.display_diff)

        self.commit_button = QPushButton("提交变更")
        self.commit_button.clicked.connect(self.commit_changes)

        self.commit_msg = QTextEdit()
        self.commit_msg.setPlaceholderText("输入提交信息...")
        self.commit_msg.setFixedHeight(80)

        self.history_list = QTreeWidget()
        self.history_list.setHeaderLabels(["提交摘要", "作者", "时间"])
        self.history_list.itemClicked.connect(self.on_commit_selected)

        # 左侧：操作按钮 + 分支 + 文件列表
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.open_button)
        left_layout.addWidget(self.branch_label)
        left_layout.addWidget(QLabel("变更文件："))
        left_layout.addWidget(self.status_list)
        left_layout.addWidget(self.commit_button)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # 右侧：diff 显示

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("提交历史："))
        right_layout.addWidget(self.history_list)
        right_layout.addWidget(QLabel("差异内容："))
        right_layout.addWidget(self.diff_view)
        right_layout.addWidget(QLabel("提交信息："))
        right_layout.addWidget(self.commit_msg)



        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # 总布局：左右分栏
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_widget, 2)
        main_layout.addWidget(right_widget, 3)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def open_repo(self):
        path = QFileDialog.getExistingDirectory(self, "选择 Git 仓库")
        if path:
            try:
                self.repo_path = path
                self.git = GitController(path)
                self.branch_label.setText(f"当前分支：{self.git.get_branch()}")

                self.status_list.clear()
                status = self.git.get_changed_files()
                for file in status:
                    item = QListWidgetItem(file)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    self.status_list.addItem(item)
                self.diff_view.clear()
                self.load_commit_history()
                self.graph_view = CommitGraphView(self.git)
                self.right_layout.addWidget(QLabel("提交图谱："))
                self.right_layout.addWidget(self.graph_view)

            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开仓库失败：{str(e)}")

    def display_diff(self, item):
        filename = item.text().strip()
        if self.git:
            diff = self.git.get_diff(filename)
            self.diff_view.setPlainText(diff or "无差异或文件已删除")

    def commit_changes(self):
        if not self.git:
            QMessageBox.warning(self, "提示", "请先打开一个 Git 仓库")
            return

        message = self.commit_msg.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "提示", "请填写提交信息")
            return

        try:
            files = []
            for i in range(self.status_list.count()):
                item = self.status_list.item(i)
                if item.checkState() == Qt.Checked:
                    files.append(item.text().strip())

            if not files:
                QMessageBox.information(self, "提示", "请至少勾选一个文件")
                return

            self.git.add_files(files)
            self.git.commit(message)
            QMessageBox.information(self, "成功", "提交成功")

            self.commit_msg.clear()
            self.status_list.clear()
            status = self.git.get_changed_files()
            for file in status:
                self.status_list.addItem(file)
            self.diff_view.clear()
        except Exception as e:
            QMessageBox.critical(self, "提交失败", str(e))

    def load_commit_history(self):
        if not self.git:
            return

        self.history_list.clear()
        history = self.git.get_commit_history()
        for entry in history:
            item = QTreeWidgetItem([entry["summary"], entry["author"], entry["time"]])
            item.setData(0, Qt.UserRole, entry["hexsha"])
            self.history_list.addTopLevelItem(item)

    def on_commit_selected(self, item, column):
        data = item.data(0, Qt.UserRole)
        if isinstance(data, tuple):
            commit_hash, file_path = data
            diff = self.git.get_commit_diff(commit_hash, file_path)
            self.diff_view.setPlainText(diff)
        else:
            # 展开文件
            commit_hash = data
            files = self.git.get_commit_files(commit_hash)
            item.takeChildren()
            for file in files:
                child = QTreeWidgetItem([file])
                child.setData(0, Qt.UserRole, (commit_hash, file))
                item.addChild(child)
            item.setExpanded(True)

    def init_menu(self):
        menubar = self.menuBar()

        # === 文件菜单 ===
        file_menu = menubar.addMenu("文件")

        open_action = QAction("打开仓库", self)
        open_action.triggered.connect(self.open_repo)
        file_menu.addAction(open_action)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(exit_action)

        # === 视图菜单 ===
        view_menu = menubar.addMenu("视图")

        reload_action = QAction("刷新状态", self)
        reload_action.triggered.connect(self.refresh_all)
        view_menu.addAction(reload_action)

        # === 设置菜单 ===
        settings_menu = menubar.addMenu("设置")

        theme_action = QAction("切换浅/深主题", self)
        theme_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(theme_action)

        # === 帮助菜单 ===
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于 GitC", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def refresh_all(self):
        if not self.git:
            return
        self.branch_label.setText(f"当前分支：{self.git.get_branch()}")
        self.status_list.clear()
        for file in self.git.get_changed_files():
            item = QListWidgetItem(file)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.status_list.addItem(item)
        self.commit_msg.clear()
        self.diff_view.clear()
        self.load_commit_history()

    def toggle_theme(self):
        palette = self.palette()
        if palette.color(self.backgroundRole()).value() < 128:
            QApplication.setStyle("Fusion")  # 浅色
        else:
            dark = palette
            dark.setColor(self.backgroundRole(), Qt.black)
            dark.setColor(self.foregroundRole(), Qt.white)
            self.setPalette(dark)

    def show_about(self):
        QMessageBox.information(self, "关于 GitC",
                                "GitC 是一款开源 Git 可视化工具，支持基础 Git 操作和图形界面查看。\n\n作者：你\n框架：Python + PySide6")
