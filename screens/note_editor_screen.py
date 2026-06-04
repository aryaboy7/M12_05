from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class NoteEditorScreen(Screen):

    def go_back(self, instance):
        self.manager.current = "notes"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=10
        )

        title = Label(
            text="Note Editor",
            font_size=32
        )

        layout.add_widget(title)

        layout.add_widget(
            Label(
                text="Editor coming next..."
            )
        )

        back_btn = Button(text="Back")
        back_btn.bind(on_press=self.go_back)

        layout.add_widget(back_btn)

        self.add_widget(layout)