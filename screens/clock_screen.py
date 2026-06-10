from datetime import datetime

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from utils.ui_scale import font
from utils.logger import log


class ClockScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_box = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=12
        )

        top = BoxLayout(size_hint=(1, 0.12))

        back_btn = Button(
            text="< Back",
            font_size=font(20),
            background_normal="",
            background_color=(0.12, 0.20, 0.35, 1)
        )
        back_btn.bind(on_press=self.go_back)

        top.add_widget(back_btn)
        self.root_box.add_widget(top)

        self.time_label = Label(
            text="00:00 AM",
            font_size=font(68),
            bold=True,
            size_hint=(1, 0.38)
        )
        self.root_box.add_widget(self.time_label)

        self.date_label = Label(
            text="Date",
            font_size=font(26),
            size_hint=(1, 0.16)
        )
        self.root_box.add_widget(self.date_label)

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint=(1, 0.15)
        )

        timer_btn = Button(
            text="Timer",
            font_size=font(22),
            background_normal="",
            background_color=(0.12, 0.20, 0.35, 1)
        )
        timer_btn.bind(on_press=self.open_timer)
        buttons.add_widget(timer_btn)

        stopwatch_btn = Button(
            text="Stopwatch",
            font_size=font(22),
            background_normal="",
            background_color=(0.12, 0.20, 0.35, 1)
        )
        stopwatch_btn.bind(on_press=self.open_stopwatch)
        buttons.add_widget(stopwatch_btn)

        self.root_box.add_widget(buttons)

        self.info_label = Label(
            text="M12 Clock",
            font_size=font(18),
            size_hint=(1, 0.12)
        )
        self.root_box.add_widget(self.info_label)

        self.add_widget(self.root_box)

        Window.bind(size=self.on_window_size)

    def on_enter(self):
        log.info("Clock: opened")
        self.apply_layout()
        Clock.unschedule(self.update_clock)
        Clock.schedule_interval(self.update_clock, 1)
        self.update_clock(0)

    def on_leave(self):
        Clock.unschedule(self.update_clock)

    def on_window_size(self, *args):
        self.apply_layout()

    def apply_layout(self):
        portrait = Window.height > Window.width

        if portrait:
            self.time_label.font_size = font(44)
            self.date_label.font_size = font(20)
            self.info_label.font_size = font(16)
            self.time_label.size_hint = (1, 0.34)
            self.date_label.size_hint = (1, 0.15)
        else:
            self.time_label.font_size = font(68)
            self.date_label.font_size = font(26)
            self.info_label.font_size = font(18)
            self.time_label.size_hint = (1, 0.38)
            self.date_label.size_hint = (1, 0.16)

    def update_clock(self, dt):
        now = datetime.now()

        portrait = Window.height > Window.width

        if portrait:
            self.time_label.text = now.strftime("%I:%M\n%p")
            self.date_label.text = now.strftime("%a, %b %d, %Y")
        else:
            self.time_label.text = now.strftime("%I:%M:%S %p")
            self.date_label.text = now.strftime("%A, %B %d, %Y")

    def go_back(self, instance):
        log.info("Clock: Back pressed")
        self.manager.current = "home"

    def open_stopwatch(self, instance):
        log.info("Clock: Stopwatch pressed")
        self.manager.current = "stopwatch"

    def open_timer(self, instance):
        log.info("Clock: Timer pressed")
        self.manager.current = "timer"