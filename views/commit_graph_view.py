from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import QRectF, Qt

class CommitGraphView(QGraphicsView):
    def __init__(self, git_controller, parent=None):
        super().__init__(parent)
        self.git = git_controller
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHints(self.renderHints() | Qt.Antialiasing)
        self.draw_graph()

    def draw_graph(self):
        self.scene.clear()
        if not self.git:
            return

        commits = self.git.get_commit_graph_data(max_count=30)
        x_offset = 50
        y_spacing = 80

        for i, commit in enumerate(commits):
            y = i * y_spacing
            color = QColor(commit["color"])
            node = self.scene.addEllipse(QRectF(x_offset, y, 20, 20),
                                         QPen(Qt.black), QBrush(color))
            node.setToolTip(f"{commit['summary']}\n{commit['author']} @ {commit['time']}")
            label = self.scene.addText(commit["summary"])
            label.setPos(x_offset + 30, y - 5)

            # draw edge to parent
            for parent_index in commit["parents"]:
                py = parent_index * y_spacing + 10
                self.scene.addLine(x_offset + 10, y + 10, x_offset + 10, py, QPen(Qt.gray))

        self.setMinimumHeight(600)
