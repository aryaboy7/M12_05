import json
from datetime import datetime
from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

from utils.ui_scale import font, height
from utils.logger import log


BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_DIR = BASE_DIR / "data" / "events"
EVENTS_FILE = EVENTS_DIR / "events.json"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)


def device_profile():
    w = Window.width
    h = Window.height

    if h >= 1800:
        return "phone"
    if w < 700 and h >= 900:
        return "m12"
    if h >= 1100:
        return "tablet"
    return "desktop"


def cal_font(base):
    profile = device_profile()

    if profile == "phone":
        scale = 1.75
    elif profile == "tablet":
        scale = 1.45
    elif profile == "m12":
        scale = 1.30
    else:
        scale = 1.00

    return max(14, int(base * scale))


def event_row_height():
    profile = device_profile()

    # Event rows have 3 lines:
    # title, date/time, countdown.
    if profile == "phone":
        return height(135)
    if profile == "tablet":
        return height(120)
    if profile == "m12":
        return height(112)
    return height(96)


class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.events = []
        self.selected_index = None
        self.mode = "list"

        self.root_box = BoxLayout(
            orientation="vertical",
            padding=height(10),
            spacing=height(8)
        )
        self.add_widget(self.root_box)

        self.build_list_view()

    def load_events(self):
        if not EVENTS_FILE.exists():
            return []

        try:
            data = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception as e:
            log.error(f"Calendar: load failed {e}")

        return []

    def save_events(self):
        try:
            EVENTS_FILE.write_text(json.dumps(self.events, indent=4), encoding="utf-8")
            log.info("Calendar: events saved")
        except Exception as e:
            log.error(f"Calendar: save failed {e}")

    def normalize_event(self, event):
        return {
            "title": str(event.get("title", "")).strip() or "Untitled Event",
            "date": str(event.get("date", "")).strip(),
            "time": str(event.get("time", "")).strip(),
            "notes": str(event.get("notes", "")).strip()
        }

    def parse_event_datetime(self, event):
        try:
            date_text = event.get("date", "").strip()
            time_text = event.get("time", "").strip() or "00:00"
            return datetime.strptime(f"{date_text} {time_text}", "%Y-%m-%d %H:%M")
        except Exception:
            return None

    def sort_events(self):
        def sort_key(event):
            dt = self.parse_event_datetime(event)
            return dt if dt else datetime.max

        self.events = sorted(self.events, key=sort_key)

    def countdown_text(self, event):
        dt = self.parse_event_datetime(event)

        if not dt:
            return "Invalid date/time"

        diff = dt - datetime.now()

        if diff.total_seconds() < 0:
            return "Past event"

        days = diff.days
        seconds = diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if days > 0:
            return f"In {days}d {hours}h {minutes}m"
        if hours > 0:
            return f"In {hours}h {minutes}m"
        return f"In {minutes}m"

    def event_display_text(self, event):
        title = event.get("title", "Untitled Event")
        date = event.get("date", "")
        time = event.get("time", "")
        countdown = self.countdown_text(event)

        when = f"{date} {time}" if time else date
        return f"{title}\n{when}\nCountdown: {countdown}"

    def on_enter(self):
        self.events = [self.normalize_event(e) for e in self.load_events()]
        self.sort_events()
        self.build_list_view()
        Clock.unschedule(self.refresh_countdowns)
        Clock.schedule_interval(self.refresh_countdowns, 60)

    def on_leave(self):
        Clock.unschedule(self.refresh_countdowns)

    def refresh_countdowns(self, dt):
        if self.mode == "list":
            self.build_list_view()

    def clear(self):
        self.root_box.clear_widgets()

    def make_btn(self, text, callback, color=(0.10, 0.15, 0.25, 1)):
        btn = Button(
            text=text,
            font_size=cal_font(18),
            background_normal="",
            background_color=color
        )
        btn.bind(on_press=callback)
        return btn

    def build_list_view(self, *args):
        self.mode = "list"
        self.clear()

        self.root_box.add_widget(Label(
            text="Calendar Events",
            font_size=cal_font(30),
            bold=True,
            size_hint=(1, 0.09)
        ))

        info = Label(
            text="Tap event to select. Countdown is from current time.",
            font_size=cal_font(14),
            size_hint=(1, 0.06),
            halign="center",
            valign="middle"
        )
        info.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.root_box.add_widget(info)

        selected_text = "Select an event to see countdown here."
        if self.selected_index is not None and 0 <= self.selected_index < len(self.events):
            ev = self.events[self.selected_index]
            selected_text = (
                f"Selected: {ev.get('title', 'Event')}\n"
                f"{self.countdown_text(ev)}"
            )

        self.countdown_label = Label(
            text=selected_text,
            font_size=cal_font(18),
            bold=True,
            size_hint=(1, 0.10),
            halign="center",
            valign="middle"
        )
        self.countdown_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.root_box.add_widget(self.countdown_label)

        scroll = ScrollView(size_hint=(1, 0.54), do_scroll_x=False, do_scroll_y=True)

        self.list_box = GridLayout(cols=1, spacing=height(6), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))

        if not self.events:
            self.list_box.add_widget(Label(
                text="No events yet.\nPress Add Event.",
                font_size=cal_font(22),
                size_hint_y=None,
                height=event_row_height() * 2
            ))
        else:
            for index, event in enumerate(self.events):
                color = (0.25, 0.45, 0.75, 1) if index == self.selected_index else (0.12, 0.20, 0.35, 1)

                btn = Button(
                    text=self.event_display_text(event),
                    font_size=cal_font(18),
                    size_hint_y=None,
                    height=event_row_height(),
                    halign="left",
                    valign="middle",
                    background_normal="",
                    background_color=color
                )
                btn.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0] - height(16), val[1])))
                btn.bind(on_press=lambda inst, i=index: self.select_event(i))
                self.list_box.add_widget(btn)

        scroll.add_widget(self.list_box)
        self.root_box.add_widget(scroll)

        buttons1 = BoxLayout(orientation="horizontal", spacing=height(6), size_hint=(1, 0.10))
        buttons1.add_widget(self.make_btn("Add", self.add_event_view, (0.12, 0.20, 0.35, 1)))
        buttons1.add_widget(self.make_btn("Edit", self.edit_selected_event))
        buttons1.add_widget(self.make_btn("Delete", self.delete_selected_event, (0.35, 0.12, 0.12, 1)))
        self.root_box.add_widget(buttons1)

        buttons2 = BoxLayout(orientation="horizontal", spacing=height(6), size_hint=(1, 0.10))
        buttons2.add_widget(self.make_btn("Refresh", self.build_list_view))
        buttons2.add_widget(self.make_btn("< Back", self.go_back))
        self.root_box.add_widget(buttons2)

    def select_event(self, index):
        self.selected_index = index
        log.info(f"Calendar: selected event {index}")
        self.build_list_view()

    def add_event_view(self, *args):
        self.build_edit_view(None)

    def edit_selected_event(self, *args):
        if self.selected_index is None:
            return
        if self.selected_index < 0 or self.selected_index >= len(self.events):
            return

        self.build_edit_view(self.selected_index)

    def delete_selected_event(self, *args):
        if self.selected_index is None:
            return
        if self.selected_index < 0 or self.selected_index >= len(self.events):
            return

        deleted = self.events.pop(self.selected_index)
        self.selected_index = None
        self.save_events()
        log.info(f"Calendar: deleted {deleted.get('title')}")
        self.build_list_view()

    def build_edit_view(self, index):
        self.mode = "edit"
        self.clear()

        is_new = index is None
        event = {
            "title": "",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "09:00",
            "notes": ""
        }

        if not is_new:
            event = dict(self.events[index])

        title = "Add Event" if is_new else "Edit Event"

        self.root_box.add_widget(Label(
            text=title,
            font_size=cal_font(30),
            bold=True,
            size_hint=(1, 0.09)
        ))

        self.title_input = TextInput(
            text=event.get("title", ""),
            hint_text="Event title",
            font_size=cal_font(20),
            multiline=False,
            size_hint=(1, 0.10),
            use_bubble=False,
            use_handles=False
        )
        self.root_box.add_widget(self.title_input)

        self.date_input = TextInput(
            text=event.get("date", ""),
            hint_text="Tap to pick date",
            font_size=cal_font(20),
            multiline=False,
            readonly=True,
            size_hint=(1, 0.10),
            use_bubble=False,
            use_handles=False
        )
        self.date_input.bind(on_touch_down=self.date_field_touched)
        self.root_box.add_widget(self.date_input)

        self.time_input = TextInput(
            text=event.get("time", ""),
            hint_text="Tap to pick time",
            font_size=cal_font(20),
            multiline=False,
            readonly=True,
            size_hint=(1, 0.10),
            use_bubble=False,
            use_handles=False
        )
        self.time_input.bind(on_touch_down=self.time_field_touched)
        self.root_box.add_widget(self.time_input)

        self.notes_input = TextInput(
            text=event.get("notes", ""),
            hint_text="Notes",
            font_size=cal_font(18),
            multiline=True,
            size_hint=(1, 0.39),
            use_bubble=False,
            use_handles=False
        )
        self.root_box.add_widget(self.notes_input)

        self.status_label = Label(
            text="Tap Date or Time to change.",
            font_size=cal_font(14),
            size_hint=(1, 0.07),
            halign="center",
            valign="middle"
        )
        self.status_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.root_box.add_widget(self.status_label)

        buttons = BoxLayout(orientation="horizontal", spacing=height(6), size_hint=(1, 0.12))
        buttons.add_widget(self.make_btn("Save", lambda inst: self.save_event(index), (0.12, 0.20, 0.35, 1)))
        buttons.add_widget(self.make_btn("Cancel", self.build_list_view))
        self.root_box.add_widget(buttons)

    def date_field_touched(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.open_date_picker()
            return True

        return False

    def time_field_touched(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.open_time_picker()
            return True

        return False

    def open_date_picker(self):
        try:
            current = datetime.strptime(self.date_input.text.strip(), "%Y-%m-%d")
        except Exception:
            current = datetime.now()

        values = {
            "year": current.year,
            "month": current.month,
            "day": current.day
        }

        box = BoxLayout(
            orientation="vertical",
            spacing=height(8),
            padding=height(8)
        )

        title = Label(
            text="Pick Date",
            font_size=cal_font(28),
            bold=True,
            size_hint=(1, 0.12)
        )
        box.add_widget(title)

        display = Label(
            text=self.format_picker_date(values),
            font_size=cal_font(26),
            bold=True,
            size_hint=(1, 0.14)
        )
        box.add_widget(display)

        def refresh():
            self.clamp_day(values)
            display.text = self.format_picker_date(values)

        def add_row(label, key, step):
            row = BoxLayout(
                orientation="horizontal",
                spacing=height(6),
                size_hint=(1, 0.17)
            )

            minus = Button(
                text="-",
                font_size=cal_font(28),
                background_normal="",
                background_color=(0.35, 0.12, 0.12, 1)
            )

            mid = Label(
                text=label,
                font_size=cal_font(22),
                bold=True
            )

            plus = Button(
                text="+",
                font_size=cal_font(28),
                background_normal="",
                background_color=(0.12, 0.20, 0.35, 1)
            )

            def dec(instance):
                values[key] -= step

                if key == "month" and values[key] < 1:
                    values[key] = 12
                    values["year"] -= 1

                if key == "day" and values[key] < 1:
                    values[key] = self.days_in_month(values["year"], values["month"])

                refresh()

            def inc(instance):
                values[key] += step

                if key == "month" and values[key] > 12:
                    values[key] = 1
                    values["year"] += 1

                if key == "day" and values[key] > self.days_in_month(values["year"], values["month"]):
                    values[key] = 1

                refresh()

            minus.bind(on_press=dec)
            plus.bind(on_press=inc)

            row.add_widget(minus)
            row.add_widget(mid)
            row.add_widget(plus)
            box.add_widget(row)

        add_row("Year", "year", 1)
        add_row("Month", "month", 1)
        add_row("Day", "day", 1)

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=height(6),
            size_hint=(1, 0.16)
        )

        pop = Popup(
            title="Date",
            content=box,
            size_hint=(0.90, 0.80)
        )

        def set_today(instance):
            now = datetime.now()
            values["year"] = now.year
            values["month"] = now.month
            values["day"] = now.day
            refresh()

        def apply_date(instance):
            self.clamp_day(values)
            self.date_input.text = f"{values['year']:04}-{values['month']:02}-{values['day']:02}"
            pop.dismiss()

        today_btn = Button(
            text="Today",
            font_size=cal_font(20),
            background_normal="",
            background_color=(0.10, 0.15, 0.25, 1)
        )
        today_btn.bind(on_press=set_today)

        ok_btn = Button(
            text="OK",
            font_size=cal_font(20),
            background_normal="",
            background_color=(0.12, 0.20, 0.35, 1)
        )
        ok_btn.bind(on_press=apply_date)

        cancel_btn = Button(
            text="Cancel",
            font_size=cal_font(20),
            background_normal="",
            background_color=(0.10, 0.15, 0.25, 1)
        )
        cancel_btn.bind(on_press=lambda inst: pop.dismiss())

        buttons.add_widget(today_btn)
        buttons.add_widget(ok_btn)
        buttons.add_widget(cancel_btn)
        box.add_widget(buttons)

        pop.open()

    def open_time_picker(self):
        try:
            current = datetime.strptime(self.time_input.text.strip(), "%H:%M")
            hour = current.hour
            minute = current.minute
        except Exception:
            now = datetime.now()
            hour = now.hour
            minute = now.minute

        values = {
            "hour": hour,
            "minute": minute
        }

        box = BoxLayout(
            orientation="vertical",
            spacing=height(8),
            padding=height(8)
        )

        title = Label(
            text="Pick Time",
            font_size=cal_font(28),
            bold=True,
            size_hint=(1, 0.14)
        )
        box.add_widget(title)

        display = Label(
            text=self.format_picker_time(values),
            font_size=cal_font(34),
            bold=True,
            size_hint=(1, 0.18)
        )
        box.add_widget(display)

        def refresh():
            display.text = self.format_picker_time(values)

        def add_row(label, key, step, max_value):
            row = BoxLayout(
                orientation="horizontal",
                spacing=height(6),
                size_hint=(1, 0.19)
            )

            minus = Button(
                text="-",
                font_size=cal_font(30),
                background_normal="",
                background_color=(0.35, 0.12, 0.12, 1)
            )

            mid = Label(
                text=label,
                font_size=cal_font(24),
                bold=True
            )

            plus = Button(
                text="+",
                font_size=cal_font(30),
                background_normal="",
                background_color=(0.12, 0.20, 0.35, 1)
            )

            def dec(instance):
                values[key] -= step
                if values[key] < 0:
                    values[key] = max_value
                refresh()

            def inc(instance):
                values[key] += step
                if values[key] > max_value:
                    values[key] = 0
                refresh()

            minus.bind(on_press=dec)
            plus.bind(on_press=inc)

            row.add_widget(minus)
            row.add_widget(mid)
            row.add_widget(plus)
            box.add_widget(row)

        add_row("Hour", "hour", 1, 23)
        add_row("Minute", "minute", 5, 55)

        buttons = BoxLayout(
            orientation="horizontal",
            spacing=height(6),
            size_hint=(1, 0.16)
        )

        pop = Popup(
            title="Time",
            content=box,
            size_hint=(0.90, 0.72)
        )

        def set_now(instance):
            now = datetime.now()
            values["hour"] = now.hour
            values["minute"] = (now.minute // 5) * 5
            refresh()

        def apply_time(instance):
            self.time_input.text = f"{values['hour']:02}:{values['minute']:02}"
            pop.dismiss()

        now_btn = Button(
            text="Now",
            font_size=cal_font(20),
            background_normal="",
            background_color=(0.10, 0.15, 0.25, 1)
        )
        now_btn.bind(on_press=set_now)

        ok_btn = Button(
            text="OK",
            font_size=cal_font(20),
            background_normal="",
            background_color=(0.12, 0.20, 0.35, 1)
        )
        ok_btn.bind(on_press=apply_time)

        cancel_btn = Button(
            text="Cancel",
            font_size=cal_font(20),
            background_normal="",
            background_color=(0.10, 0.15, 0.25, 1)
        )
        cancel_btn.bind(on_press=lambda inst: pop.dismiss())

        buttons.add_widget(now_btn)
        buttons.add_widget(ok_btn)
        buttons.add_widget(cancel_btn)
        box.add_widget(buttons)

        pop.open()

    def days_in_month(self, year, month):
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)

        this_month = datetime(year, month, 1)
        return (next_month - this_month).days

    def clamp_day(self, values):
        max_day = self.days_in_month(values["year"], values["month"])

        if values["day"] > max_day:
            values["day"] = max_day

        if values["day"] < 1:
            values["day"] = 1

    def format_picker_date(self, values):
        try:
            dt = datetime(values["year"], values["month"], values["day"])
            return dt.strftime("%A\n%B %d, %Y")
        except Exception:
            return f"{values['year']:04}-{values['month']:02}-{values['day']:02}"

    def format_picker_time(self, values):
        hour = values["hour"]
        minute = values["minute"]

        ampm = "AM" if hour < 12 else "PM"
        hour12 = hour % 12
        if hour12 == 0:
            hour12 = 12

        return f"{hour12:02}:{minute:02} {ampm}\n({hour:02}:{minute:02})"

    def validate_date_time(self, date_text, time_text):
        try:
            datetime.strptime(f"{date_text} {time_text}", "%Y-%m-%d %H:%M")
            return True
        except Exception:
            return False

    def save_event(self, index):
        title = self.title_input.text.strip() or "Untitled Event"
        date_text = self.date_input.text.strip()
        time_text = self.time_input.text.strip() or "00:00"
        notes = self.notes_input.text.strip()

        if not date_text:
            self.status_label.text = "Date is required."
            return

        if not self.validate_date_time(date_text, time_text):
            self.status_label.text = "Invalid date/time. Use YYYY-MM-DD and HH:MM."
            return

        event = {
            "title": title,
            "date": date_text,
            "time": time_text,
            "notes": notes
        }

        if index is None:
            self.events.append(event)
            log.info(f"Calendar: added {title}")
        else:
            self.events[index] = event
            log.info(f"Calendar: edited {title}")

        self.sort_events()
        self.save_events()
        self.selected_index = None
        self.build_list_view()

    def go_back(self, *args):
        self.manager.current = "home"
