from pathlib import Path

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from utils.logger import log


BASE_DIR = Path(__file__).resolve().parent.parent
NOTES_DIR = BASE_DIR / "data" / "notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)


class NotesScreen(Screen):

    def new_note(self, instance):
        log.info("Notes: New pressed")
        self.manager.current = "editor"


    def go_back(self, instance):
        log.info("Notes: Back pressed")
        self.manager.current = "home"

    def refresh_notes(self):
        self.notes_box.clear_widgets()

        files = sorted(NOTES_DIR.glob("*.txt"))

        if not files:
            self.notes_box.add_widget(
                Label(text="No notes yet", font_size=24)
            )
            return

        for file in files:
            btn = Button(
                text=file.name,
                font_size=24
            )
            self.notes_box.add_widget(btn)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=10
        )

        title = Label(
            text="Notes",
            font_size=32,
            size_hint=(1, 0.15)
        )
        layout.add_widget(title)

        self.notes_box = BoxLayout(
            orientation="vertical",
            spacing=8,
            size_hint=(1, 0.70)
        )
        layout.add_widget(self.notes_box)

        bottom = BoxLayout(size_hint=(1, 0.15))

        new_btn = Button(text="New")
        new_btn.bind(on_press=self.new_note)
        bottom.add_widget(new_btn)

        bottom.add_widget(Button(text="Open"))
        bottom.add_widget(Button(text="Delete"))

        back_btn = Button(text="Back")
        back_btn.bind(on_press=self.go_back)
        bottom.add_widget(back_btn)

        layout.add_widget(bottom)
        self.add_widget(layout)

        self.refresh_notes()