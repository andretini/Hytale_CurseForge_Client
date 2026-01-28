from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QFrame, QHBoxLayout, QLabel, QWidget, QScrollArea, \
    QPushButton

from ui.workers.image_worker import ImageWorker


class ModDetailsDialog(QDialog):
    def __init__(self, mod_data, is_installed=False, has_update=False,
                 install_callback=None, update_callback=None, remove_callback=None, parent=None):
        super().__init__(None)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(mod_data['name'])
        self.resize(900, 700)

        self.mod_data = mod_data
        self.install_callback = install_callback
        self.update_callback = update_callback
        self.remove_callback = remove_callback
        self.is_installed = is_installed
        self.has_update = has_update

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setup_header(layout, mod_data)

        tabs = QTabWidget()
        self.setup_overview_tab(tabs, mod_data)
        self.setup_files_tab(tabs, mod_data)
        self.setup_info_tab(tabs, mod_data)
        layout.addWidget(tabs)

        self.setup_footer(layout)

    def setup_header(self, layout, mod):
        banner = QFrame()
        banner.setObjectName("ModalHeader")

        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(25, 25, 25, 25)
        banner_layout.setSpacing(20)

        logo_lbl = QLabel()
        logo_lbl.setFixedSize(80, 80)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setObjectName("ModalLogo")

        logo_url = mod.get('logo', {}).get('thumbnailUrl')
        if logo_url:
            self.w_logo = ImageWorker(logo_url, (80, 80))
            self.w_logo.loaded.connect(logo_lbl.setPixmap)
            self.w_logo.start()
        else:
            logo_lbl.setText("📦")

        text_col = QVBoxLayout()
        text_col.setSpacing(5)

        title = QLabel(mod['name'])
        title.setObjectName("ModalTitle")
        text_col.addWidget(title)

        authors_layout = QHBoxLayout()
        authors_layout.setSpacing(10)
        lbl_by = QLabel("by")
        lbl_by.setObjectName("DimLabel")
        authors_layout.addWidget(lbl_by)

        for author in mod.get('authors', []):
            a_frame = QFrame()
            a_frame.setObjectName("AuthorChip")
            a_row = QHBoxLayout(a_frame)
            a_row.setContentsMargins(0, 0, 10, 0)
            a_row.setSpacing(8)

            avatar_lbl = QLabel()
            avatar_lbl.setFixedSize(30, 30)
            avatar_lbl.setStyleSheet(
                "background-color: #444; border-radius: 15px;")

            if author.get('avatarUrl'):
                worker_name = f"w_auth_{author['id']}"
                setattr(self, worker_name, ImageWorker(author['avatarUrl'], (30, 30)))
                getattr(self, worker_name).loaded.connect(avatar_lbl.setPixmap)
                getattr(self, worker_name).start()

            name_lbl = QLabel(author['name'])

            a_row.addWidget(avatar_lbl)
            a_row.addWidget(name_lbl)
            authors_layout.addWidget(a_frame)

        authors_layout.addStretch()
        text_col.addLayout(authors_layout)

        cat_layout = QHBoxLayout()
        cat_layout.setSpacing(8)
        for cat in mod.get('categories', []):
            c_lbl = QLabel(f" {cat['name']} ")
            c_lbl.setObjectName("CategoryLabel")
            cat_layout.addWidget(c_lbl)
        cat_layout.addStretch()
        text_col.addLayout(cat_layout)

        banner_layout.addWidget(logo_lbl)
        banner_layout.addLayout(text_col)
        layout.addWidget(banner)

    def setup_overview_tab(self, tabs, mod):
        tab = QWidget()
        vbox = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        c_layout = QVBoxLayout(content)

        summary = mod.get('summary', '')
        if summary:
            lbl = QLabel(summary)
            lbl.setWordWrap(True)
            lbl.setObjectName("SummaryBox")
            c_layout.addWidget(lbl)

        screenshots = mod.get('screenshots', [])
        if screenshots:
            c_layout.addWidget(QLabel("Gallery"))
            for shot in screenshots:
                f = QFrame()
                f.setObjectName("GalleryFrame")
                fl = QVBoxLayout(f)
                if shot.get('title'):
                    fl.addWidget(QLabel(shot['title']))

                img = QLabel("Loading Preview...")
                img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                img.setMinimumHeight(200)
                img.setStyleSheet("background-color: black; color: #555;")
                fl.addWidget(img)

                w_shot = ImageWorker(shot['thumbnailUrl'] or shot['url'])
                w_shot.loaded.connect(
                    lambda p, l=img: (l.setPixmap(p.scaledToWidth(750, Qt.TransformationMode.SmoothTransformation)), l.setText("")))
                w_shot.start()
                setattr(self, f"w_shot_{shot['id']}", w_shot)
                c_layout.addWidget(f)
        c_layout.addStretch()
        scroll.setWidget(content)
        vbox.addWidget(scroll)
        tabs.addTab(tab, "Overview")

    def setup_files_tab(self, tabs, mod):
        tab = QWidget()
        vbox = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for f in mod.get('latestFiles', []):
            row = QFrame()
            row.setObjectName("FileRow")
            rl = QHBoxLayout(row)

            rtype = f.get('releaseType', 1)
            color = "#4CAF50" if rtype == 1 else "#FFC107" if rtype == 2 else "#F44336"

            status = QLabel("●")
            status.setStyleSheet(f"color: {color}; font-size: 14px;")
            rl.addWidget(status)

            name = QLabel(f.get('displayName', f['fileName']))
            name.setObjectName("BoldLabel")
            rl.addWidget(name)
            rl.addStretch()

            raw_date = f.get('fileDate', '')[:10]
            rl.addWidget(QLabel(raw_date))
            c_layout.addWidget(row)

        scroll.setWidget(content)
        vbox.addWidget(scroll)
        tabs.addTab(tab, "Files")

    def setup_info_tab(self, tabs, mod):
        tab = QWidget()
        vbox = QVBoxLayout(tab)
        vbox.setContentsMargins(30, 30, 30, 30)

        vbox.addWidget(QLabel("External Links"))

        links_layout = QHBoxLayout()
        links = mod.get('links', {})
        link_map = {'sourceUrl': ('Source Code', '💻'), 'issuesUrl': ('Issue Tracker', '🐛'), 'wikiUrl': ('Wiki', '📖'),
                    'websiteUrl': ('Website', '🌐')}
        for key, (label, icon) in link_map.items():
            url = links.get(key)
            if url:
                btn = QPushButton(f"  {icon}  {label}")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setObjectName("LinkBtn")
                btn.clicked.connect(lambda _, u=url: QDesktopServices.openUrl(QUrl(u)))
                links_layout.addWidget(btn)
        links_layout.addStretch()
        vbox.addLayout(links_layout)
        vbox.addSpacing(20)

        vbox.addWidget(QLabel("Technical Details"))
        grid = QFrame()
        grid.setObjectName("InfoGrid")
        gl = QVBoxLayout(grid)

        def add_row(k, v):
            r = QHBoxLayout()
            r.addWidget(QLabel(k))
            r.addStretch()
            r.addWidget(QLabel(str(v)))
            gl.addLayout(r)

        add_row("Mod ID", mod.get('id'))
        add_row("Downloads", f"{int(mod.get('downloadCount', 0)):,}")
        add_row("Date Created", mod.get('dateCreated', '')[:10])
        add_row("Last Updated", mod.get('dateModified', '')[:10])
        vbox.addWidget(grid)
        vbox.addStretch()
        tabs.addTab(tab, "Info")

    def setup_footer(self, layout):
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 10, 20, 15)

        self.action_btn = QPushButton("Check Status")
        self.action_btn.setFixedSize(150, 40)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self.on_action_click)

        self.update_btn = QPushButton("⬆ Update")
        self.update_btn.setFixedSize(120, 40)
        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn.setObjectName("ActionBtn")
        self.update_btn.clicked.connect(self.on_update_click)
        self.update_btn.setVisible(self.has_update and self.is_installed)

        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        close_btn.clicked.connect(self.close)

        footer.addWidget(self.action_btn)
        footer.addWidget(self.update_btn)
        footer.addStretch()
        footer.addWidget(close_btn)
        layout.addLayout(footer)
        self.update_action_button()

    def update_action_button(self):
        if self.is_installed:
            self.action_btn.setText("🗑 Uninstall")
            self.action_btn.setObjectName("DeleteBtn")
        else:
            self.action_btn.setText("⬇ Install Mod")
            self.action_btn.setObjectName("ActionBtn")

        self.action_btn.style().unpolish(self.action_btn)
        self.action_btn.style().polish(self.action_btn)
        self.action_btn.setEnabled(True)

    def on_action_click(self):
        if self.is_installed:
            if self.remove_callback:
                if self.remove_callback():
                    self.is_installed = False
                    self.update_action_button()
        else:
            if self.install_callback:
                self.action_btn.setText("Downloading...")
                self.action_btn.setEnabled(False)
                self.install_callback(self.action_btn, self.on_install_finished)

    def on_update_click(self):
        if self.update_callback:
            self.update_btn.setText("Updating...")
            self.update_btn.setEnabled(False)
            self.update_callback(self.update_btn, self.on_update_finished)

    def on_update_finished(self, success=True):
        if success:
            self.has_update = False
            self.update_btn.setVisible(False)
        else:
            self.update_btn.setText("⬆ Update")
            self.update_btn.setEnabled(True)
        self.update_action_button()

    def on_install_finished(self, success=True):
        if success: self.is_installed = True
        self.update_action_button()
