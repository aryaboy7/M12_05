from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

from utils.ui_scale import font, height


class TextEditorPopup:
    def __init__(self, title, text, on_save, multiline=True):
        self.title = title
        self.text = text or ""
        self.on_save = on_save
        self.multiline = multiline
        self.popup = None
        self.input = None

    def open(self):
        old_mode = Window.softinput_mode
        Window.softinput_mode = "resize"

        root = BoxLayout(
            orientation="vertical",
            spacing=height(8),
            padding=height(8)
        )

        top = BoxLayout(
            orientation="horizontal",
            spacing=height(8),
            size_hint=(1, 0.12)
        )

        save_btn = Button(
            text="Save",
            font_size=font(24),
            background_normal="",
            background_color=(0.12, 0.20, 0.35, 1)
        )

        cancel_btn = Button(
            text="Cancel",
            font_size=font(24),
            background_normal="",
            background_color=(0.10, 0.15, 0.25, 1)
        )

        top.add_widget(save_btn)
        top.add_widget(cancel_btn)
        root.add_widget(top)

        self.input = TextInput(
            text=self.text,
            font_size=font(24),
            multiline=self.multiline,
            size_hint=(1, 0.88),
            use_bubble=False,
            use_handles=False
        )
        root.add_widget(self.input)

        self.popup = Popup(
            title=self.title,
            content=root,
            size_hint=(0.96, 0.96),
            auto_dismiss=False
        )

        def do_save(instance):
            try:
                self.on_save(self.input.text)
            finally:
                Window.softinput_mode = old_mode
                self.popup.dismiss()

        def do_cancel(instance):
            Window.softinput_mode = old_mode
            self.popup.dismiss()

        save_btn.bind(on_release=do_save)
        cancel_btn.bind(on_release=do_cancel)

        self.popup.open()
        self.input.focus = True


def open_text_editor(title, text, on_save, multiline=True):
    editor = TextEditorPopup(title, text, on_save, multiline=multiline)
    editor.open()
    return editor
