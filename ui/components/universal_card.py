from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, )
from PySide6.QtCore import Qt

from ui.workers.image_worker import ImageWorker

class UniversalCard(QFrame):
    def __init__(
            self,
            title,
            subtitle,
            icon_url=None,
            is_installed=False,
            has_update=False,
            install_callback=None,
            update_callback=None,
            delete_callback=None,
            click_callback=None,
            icon_char="📦",
    ):
        super().__init__()
        self.click_callback = click_callback
        self.setObjectName("UniversalCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(90)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 4, 0, 4)

        self.surface = QWidget()
        self.surface.setObjectName("UniversalCardSurface")
        self.surface.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        outer_layout.addWidget(self.surface)

        layout = QHBoxLayout(self.surface)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(15)

        self.icon_lbl = QLabel(icon_char)
        self.icon_lbl.setFixedSize(48, 48)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setObjectName("CardIcon")
        layout.addWidget(self.icon_lbl)

        if icon_url:
            worker = ImageWorker(icon_url, (48, 48))
            worker.loaded.connect(self.set_icon_safe)
            worker.start()

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")
        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setObjectName("CardSubtitle")

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(subtitle_lbl)
        layout.addLayout(text_layout)
        layout.addStretch()

        if is_installed:
            status_layout = QHBoxLayout()
            status_layout.setSpacing(6)

            if has_update:
                update_lbl = QLabel("UPDATE AVAILABLE")
                update_lbl.setObjectName("WarningLabel")
                update_lbl.setStyleSheet("color: #FFC107; font-weight: bold; font-size: 11px;")
                status_layout.addWidget(update_lbl)
            else:
                check_lbl = QLabel("✔")
                check_lbl.setObjectName("SuccessLabel")
                text_inst_lbl = QLabel("INSTALLED")
                text_inst_lbl.setObjectName("SuccessLabel")
                status_layout.addWidget(check_lbl)
                status_layout.addWidget(text_inst_lbl)

            layout.addLayout(status_layout)

            if has_update and update_callback:
                update_btn = QPushButton("⬆ Update")
                update_btn.setFixedSize(100, 36)
                update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                update_btn.setObjectName("ActionBtn")
                update_btn.clicked.connect(lambda: update_callback(update_btn))
                layout.addWidget(update_btn)

            if delete_callback:
                delete_btn = QPushButton("🗑 Uninstall")
                delete_btn.setFixedSize(110, 36)
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.setObjectName("DeleteBtn")
                delete_btn.clicked.connect(lambda: delete_callback())
                layout.addWidget(delete_btn)

        elif install_callback:
            install_btn = QPushButton("⬇ Install")
            install_btn.setFixedSize(100, 36)
            install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            install_btn.setObjectName("ActionBtn")
            install_btn.clicked.connect(lambda: install_callback(install_btn))
            layout.addWidget(install_btn)

    def set_icon_safe(self, pixmap):
        try:
            self.icon_lbl.setPixmap(pixmap)
            self.icon_lbl.setText("")
        except RuntimeError:
            pass

    def mouseReleaseEvent(self, event):
        try:
            child = self.childAt(event.position().toPoint())
            if (
                event.button() == Qt.MouseButton.LeftButton
                and self.click_callback
                and not isinstance(child, QPushButton)
            ):
                self.click_callback()
            super().mouseReleaseEvent(event)
        except RuntimeError:
            pass
