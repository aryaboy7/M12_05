import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup

from utils.logger import log
from utils.ui_scale import font, height


BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "data" / "backups"

BACKUP_ITEMS = [
    BASE_DIR / "config",
    BASE_DIR / "data" / "notes",
    BASE_DIR / "data" / "events",
    BASE_DIR / "data" / "alarms",
]


class BackupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.selected_backup = None
        self.mode = "backup"

        self.build_screen()

    def clear_screen(self):
        self.clear_widgets()

    def make_button(self, text, color=(0.12, 0.20, 0.35, 1)):
        return Button(
            text=text,
            font_size=font(24),
            background_normal="",
            background_color=color
        )

    def build_screen(self):
        self.clear_screen()

        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        root.add_widget(Label(
            text="Backup",
            font_size=font(38),
            bold=True,
            size_hint=(1, 0.10)
        ))

        tabs = BoxLayout(orientation="horizontal", spacing=8, size_hint=(1, 0.10))

        self.backup_tab = self.make_button("Backup")
        self.restore_tab = self.make_button("Restore")

        self.backup_tab.bind(on_press=self.show_backup_tab)
        self.restore_tab.bind(on_press=self.show_restore_tab)

        tabs.add_widget(self.backup_tab)
        tabs.add_widget(self.restore_tab)
        root.add_widget(tabs)

        self.body = BoxLayout(orientation="vertical", spacing=8, size_hint=(1, 0.68))
        root.add_widget(self.body)

        bottom = BoxLayout(orientation="horizontal", spacing=8, size_hint=(1, 0.10))

        settings_btn = self.make_button("< Settings", (0.10, 0.15, 0.25, 1))
        settings_btn.bind(on_press=self.go_settings)

        home_btn = self.make_button("< Home", (0.10, 0.15, 0.25, 1))
        home_btn.bind(on_press=self.go_home)

        bottom.add_widget(settings_btn)
        bottom.add_widget(home_btn)
        root.add_widget(bottom)

        self.add_widget(root)

        self.show_backup_tab(None)

    def show_backup_tab(self, instance):
        self.mode = "backup"
        self.body.clear_widgets()

        self.backup_tab.background_color = (0.10, 0.45, 0.20, 1)
        self.restore_tab.background_color = (0.12, 0.20, 0.35, 1)

        info = Label(
            text="Create backup of settings, notes, calendar, and alarms.",
            font_size=font(22),
            size_hint=(1, 0.22),
            halign="center",
            valign="middle"
        )
        info.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(info)

        create_btn = Button(
            text="Create Backup",
            font_size=font(30),
            size_hint=(1, 0.18),
            background_normal="",
            background_color=(0.10, 0.45, 0.20, 1)
        )
        create_btn.bind(on_press=self.create_backup)
        self.body.add_widget(create_btn)

        self.status_label = Label(
            text="",
            font_size=font(20),
            size_hint=(1, 0.40),
            halign="center",
            valign="middle"
        )
        self.status_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(self.status_label)

    def show_restore_tab(self, instance):
        self.mode = "restore"
        self.selected_backup = None
        self.body.clear_widgets()

        self.backup_tab.background_color = (0.12, 0.20, 0.35, 1)
        self.restore_tab.background_color = (0.10, 0.45, 0.20, 1)

        self.restore_status = Label(
            text="Select backup file.",
            font_size=font(20),
            size_hint=(1, 0.10),
            halign="center",
            valign="middle"
        )
        self.restore_status.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.body.add_widget(self.restore_status)

        scroll = ScrollView(size_hint=(1, 0.55), do_scroll_x=False, do_scroll_y=True)

        self.backup_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.backup_list.bind(minimum_height=self.backup_list.setter("height"))

        scroll.add_widget(self.backup_list)
        self.body.add_widget(scroll)

        restore_btn = Button(
            text="Restore Selected",
            font_size=font(26),
            size_hint=(1, 0.14),
            background_normal="",
            background_color=(0.45, 0.30, 0.10, 1)
        )
        restore_btn.bind(on_press=self.ask_restore_confirmation)
        self.body.add_widget(restore_btn)

        self.load_backup_list()

    def create_backup(self, instance):
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BACKUP_DIR / f"m12_backup_{stamp}.zip"

            with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zf:
                for item in BACKUP_ITEMS:
                    if not item.exists():
                        continue

                    if item.is_file():
                        arcname = item.relative_to(BASE_DIR)
                        zf.write(item, arcname)
                        continue

                    for path in item.rglob("*"):
                        if path.is_file():
                            arcname = path.relative_to(BASE_DIR)
                            zf.write(path, arcname)

            self.status_label.text = f"Backup Completed\n\n{backup_file.name}"
            log.info(f"Backup created: {backup_file}")

        except Exception as e:
            self.status_label.text = f"Backup failed:\n{e}"
            log.error(f"Backup failed: {e}")

    def load_backup_list(self):
        self.backup_list.clear_widgets()

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        backups = sorted(
            BACKUP_DIR.glob("m12_backup_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not backups:
            self.restore_status.text = "No backups found."
            return

        for backup in backups:
            btn = Button(
                text=backup.name,
                font_size=font(20),
                size_hint_y=None,
                height=height(64),
                background_normal="",
                background_color=(0.10, 0.15, 0.25, 1),
                halign="center",
                valign="middle"
            )
            btn.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            btn.bind(on_press=lambda instance, p=backup: self.select_backup(p))
            self.backup_list.add_widget(btn)

    def select_backup(self, backup_path):
        self.selected_backup = backup_path
        self.restore_status.text = f"Selected:\n{backup_path.name}"

    def ask_restore_confirmation(self, instance):
        if not self.selected_backup:
            self.restore_status.text = "Select a backup first."
            return

        box = BoxLayout(orientation="vertical", padding=height(10), spacing=height(8))

        msg = Label(
            text=(
                "Restore Backup?\n\n"
                f"{self.selected_backup.name}\n\n"
                "Current settings/data will be replaced."
            ),
            font_size=font(22),
            halign="center",
            valign="middle"
        )
        msg.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0] - height(20), val[1])))
        box.add_widget(msg)

        buttons = BoxLayout(orientation="horizontal", spacing=height(8), size_hint=(1, 0.25))

        yes_btn = Button(
            text="Yes Restore",
            font_size=font(24),
            background_normal="",
            background_color=(0.50, 0.15, 0.15, 1)
        )

        no_btn = Button(
            text="No",
            font_size=font(24),
            background_normal="",
            background_color=(0.12, 0.20, 0.35, 1)
        )

        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        box.add_widget(buttons)

        popup = Popup(
            title="Confirm Restore",
            content=box,
            size_hint=(0.90, 0.65),
            auto_dismiss=False
        )

        def confirm(instance):
            popup.dismiss()
            self.do_restore_selected()

        def cancel(instance):
            popup.dismiss()
            self.restore_status.text = "Restore cancelled."

        yes_btn.bind(on_press=confirm)
        no_btn.bind(on_press=cancel)

        popup.open()

    def do_restore_selected(self):
        try:
            restore_tmp = BASE_DIR / "data" / "restore_tmp"

            if restore_tmp.exists():
                shutil.rmtree(restore_tmp)

            restore_tmp.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(self.selected_backup, "r") as zf:
                zf.extractall(restore_tmp)

            for folder_name in ["config", "data/notes", "data/events", "data/alarms"]:
                src = restore_tmp / folder_name
                dst = BASE_DIR / folder_name

                if not src.exists():
                    continue

                if dst.exists():
                    shutil.rmtree(dst)

                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst)

            shutil.rmtree(restore_tmp)

            self.restore_status.text = (
                "Restore Complete\n"
                "Restart M12 OS recommended."
            )

            log.info(f"Backup restored: {self.selected_backup}")

        except Exception as e:
            self.restore_status.text = f"Restore failed:\n{e}"
            log.error(f"Restore failed: {e}")

    def go_settings(self, instance):
        if self.manager:
            self.manager.current = "settings"

    def go_home(self, instance):
        if self.manager:
            self.manager.current = "home"