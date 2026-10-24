
import sys
import json
import time
import threading
from pathlib import Path

from pynput import mouse, keyboard
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QSpinBox, QComboBox, QLineEdit,
    QTabWidget, QColorDialog, QMessageBox
)

APP_DIR = Path.home() / ".config" / "clicky"
CONFIG = APP_DIR / "settings.json"
PROFILES = APP_DIR / "profiles"
APP_DIR.mkdir(parents=True, exist_ok=True)
PROFILES.mkdir(parents=True, exist_ok=True)

DEFAULTS = {
    "theme": "Catppuccin Mocha",
    "bg": "#1e1e2e",
    "panel": "#313244",
    "text": "#cdd6f4",
    "accent": "#cba6f7",
    "radius": 10,
    "font": 13,
    "interval": 100,
    "button": "Left",
    "hotkey": "F6",
    "limit": 0,
    "delay": 0,
}

THEMES = {
    "Catppuccin Mocha": {
        "bg": "#1e1e2e", "panel": "#313244",
        "text": "#cdd6f4", "accent": "#cba6f7",
        "radius": 10, "font": 13,
    },
    "Catppuccin Latte": {
        "bg": "#eff1f5", "panel": "#e6e9ef",
        "text": "#4c4f69", "accent": "#8839ef",
        "radius": 10, "font": 13,
    },
    "Brutalist": {
        "bg": "#171717", "panel": "#242424",
        "text": "#e5e5e5", "accent": "#d6ff00",
        "radius": 0, "font": 14,
    },
    "Midnight": {
        "bg": "#101318", "panel": "#202630",
        "text": "#e7edf5", "accent": "#55d6be",
        "radius": 6, "font": 13,
    },
}

settings = DEFAULTS.copy()
try:
    settings.update(json.loads(CONFIG.read_text()))
except (OSError, ValueError):
    pass

running = threading.Event()
shutdown = threading.Event()
click_count = 0
clicker = mouse.Controller()


class Events(QObject):
    toggle = Signal()
    finished = Signal()
    error = Signal(str)


events = Events()


def save():
    CONFIG.write_text(json.dumps(settings, indent=2))


def click_worker():
    global click_count

    while not shutdown.is_set():
        if not running.is_set():
            time.sleep(0.02)
            continue

        interval = max(1, int(settings["interval"])) / 1000
        button_name = settings["button"]
        limit = int(settings["limit"])

        try:
            button = {
                "Left": mouse.Button.left,
                "Right": mouse.Button.right,
                "Middle": mouse.Button.middle,
            }[button_name]
            clicker.click(button)
        except Exception as exc:
            running.clear()
            events.error.emit(str(exc))
            events.finished.emit()
            continue

        click_count += 1

        # Zero means unlimited clicks.
        if limit > 0 and click_count >= limit:
            running.clear()
            events.finished.emit()
            continue

        deadline = time.monotonic() + interval
        while running.is_set() and not shutdown.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.005))


def on_key(key):
    try:
        name = key.name
    except AttributeError:
        return

    if name and name.lower() == settings["hotkey"].lower():
        events.toggle.emit()


class Clicky(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clicky")
        self.setMinimumWidth(410)
        self.setStyleSheet(self.css())

        events.toggle.connect(self.toggle)
        events.finished.connect(self.stopped)
        events.error.connect(self.show_error)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Clicky")
        title.setStyleSheet("font-size: 26px; font-weight: 800;")
        header.addWidget(title)
        header.addStretch()

        self.status = QLabel("● READY")
        header.addWidget(self.status)
        root.addLayout(header)

        subtitle = QLabel("AUTOCLICKER / CACHYOS")
        subtitle.setStyleSheet("color: #a6adc8; font-size: 10px;")
        root.addWidget(subtitle)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Clicking settings
        click_tab = QWidget()
        form = QFormLayout(click_tab)

        self.interval = QSpinBox()
        self.interval.setRange(1, 60000)
        self.interval.setSuffix(" ms")
        self.interval.setValue(int(settings["interval"]))
        self.interval.valueChanged.connect(self.set_interval)
        form.addRow("Click interval", self.interval)

        self.cps = QLabel()
        form.addRow("Click speed", self.cps)
        self.update_cps(self.interval.value())

        self.mouse_button = QComboBox()
        self.mouse_button.addItems(["Left", "Right", "Middle"])
        self.mouse_button.setCurrentText(settings["button"])
        self.mouse_button.currentTextChanged.connect(
            lambda value: self.change("button", value)
        )
        form.addRow("Mouse button", self.mouse_button)

        self.limit = QSpinBox()
        self.limit.setRange(0, 1000000)
        self.limit.setSpecialValueText("Unlimited")
        self.limit.setValue(int(settings["limit"]))
        self.limit.valueChanged.connect(
            lambda value: self.change("limit", value)
        )
        form.addRow("Click limit (0 = infinite)", self.limit)

        self.delay = QSpinBox()
        self.delay.setRange(0, 60000)
        self.delay.setSuffix(" ms")
        self.delay.setValue(int(settings["delay"]))
        self.delay.valueChanged.connect(
            lambda value: self.change("delay", value)
        )
        form.addRow("Start delay", self.delay)

        self.tabs.addTab(click_tab, "Clicking")

        # Appearance settings
        appearance = QWidget()
        appearance_layout = QVBoxLayout(appearance)
        appearance_form = QFormLayout()
        appearance_layout.addLayout(appearance_form)

        self.theme = QComboBox()
        self.theme.addItems(list(THEMES.keys()) + ["Custom"])
        self.theme.setCurrentText(settings["theme"])
        self.theme.currentTextChanged.connect(self.set_theme)
        appearance_form.addRow("Theme", self.theme)

        self.colour_inputs = {}

        for key, label in [
            ("bg", "Background"),
            ("panel", "Panels"),
            ("text", "Text"),
            ("accent", "Accent"),
        ]:
            line = QLineEdit(settings[key])
            line.setMaxLength(7)
            line.editingFinished.connect(
                lambda k=key, widget=line:
                    self.set_colour(k, widget.text())
            )

            choose = QPushButton("Choose")
            choose.clicked.connect(
                lambda checked=False, k=key, widget=line:
                    self.pick_colour(k, widget)
            )

            row = QHBoxLayout()
            row.addWidget(line)
            row.addWidget(choose)
            appearance_form.addRow(label, row)
            self.colour_inputs[key] = line

        self.radius = QSpinBox()
        self.radius.setRange(0, 24)
        self.radius.setValue(int(settings["radius"]))
        self.radius.valueChanged.connect(
            lambda value: self.change("radius", value, True)
        )
        appearance_form.addRow("Corner radius", self.radius)

        self.font_size = QSpinBox()
        self.font_size.setRange(9, 24)
        self.font_size.setValue(int(settings["font"]))
        self.font_size.valueChanged.connect(
            lambda value: self.change("font", value, True)
        )
        appearance_form.addRow("Font size", self.font_size)

        appearance_layout.addStretch()
        self.tabs.addTab(appearance, "Appearance")

        # Hotkeys and profiles
        controls = QWidget()
        controls_form = QFormLayout(controls)

        self.hotkey = QComboBox()
        self.hotkey.addItems([
            "F6", "F7", "F8", "F9", "F10",
            "F11", "F12", "Pause",
        ])
        self.hotkey.setCurrentText(settings["hotkey"])
        self.hotkey.currentTextChanged.connect(self.set_hotkey)
        controls_form.addRow("Toggle hotkey", self.hotkey)

        self.profile = QComboBox()
        self.profile.addItem("Select profile...")
        self.profile.currentTextChanged.connect(self.load_profile)
        controls_form.addRow("Load profile", self.profile)

        self.profile_name = QLineEdit()
        self.profile_name.setPlaceholderText("Profile name")
        controls_form.addRow("Save as", self.profile_name)

        save_button = QPushButton("Save profile")
        save_button.clicked.connect(self.save_profile)
        controls_form.addRow(save_button)

        self.tabs.addTab(controls, "Settings")

        self.start = QPushButton("▶   Start clicking")
        self.start.setObjectName("start")
        self.start.clicked.connect(self.toggle)
        root.addWidget(self.start)

        self.hint = QLabel("Hotkey: " + settings["hotkey"])
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.hint)

        self.refresh_profiles()
        self.listener = keyboard.Listener(on_press=on_key)
        self.listener.start()

    def css(self):
        bg = settings["bg"]
        panel = settings["panel"]
        text = settings["text"]
        accent = settings["accent"]
        radius = settings["radius"]
        font = settings["font"]
        border = (
            "#444444" if settings["theme"] == "Brutalist"
            else "#45475a"
        )

        return f"""
        QWidget {{
            background: {bg};
            color: {text};
            font-size: {font}px;
        }}
        QTabWidget::pane {{
            border: 1px solid {border};
            border-radius: {radius}px;
        }}
        QTabBar::tab {{
            background: {panel};
            padding: 9px 12px;
            margin-right: 3px;
            border-radius: {radius}px;
        }}
        QTabBar::tab:selected {{
            color: {accent};
            border: 1px solid {accent};
        }}
        QPushButton, QComboBox, QSpinBox, QLineEdit {{
            background: {panel};
            color: {text};
            border: 1px solid {border};
            border-radius: {radius}px;
            padding: 8px;
        }}
        QPushButton:hover {{
            border: 1px solid {accent};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 26px;
            border-left: 1px solid {border};
        }}
        QComboBox::down-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {accent};
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            width: 20px;
            background: {panel};
            border: none;
        }}
        QSpinBox::up-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid {accent};
        }}
        QSpinBox::down-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {accent};
        }}
        QPushButton#start {{
            background: {accent};
            color: {bg};
            font-weight: bold;
            padding: 12px;
        }}
        """

    def change(self, key, value, restyle=False):
        settings[key] = value
        save()
        if restyle:
            self.setStyleSheet(self.css())

    def set_interval(self, value):
        self.change("interval", value)
        self.update_cps(value)

    def update_cps(self, ms):
        self.cps.setText(f"{1000 / ms:.2f} clicks per second")

    def set_theme(self, name):
        settings["theme"] = name
        if name in THEMES:
            settings.update(THEMES[name])
        save()

        for key, widget in self.colour_inputs.items():
            widget.setText(settings[key])

        self.radius.setValue(settings["radius"])
        self.font_size.setValue(settings["font"])
        self.setStyleSheet(self.css())

    def set_colour(self, key, value):
        if QColor.isValidColor(value):
            settings["theme"] = "Custom"
            settings[key] = value
            self.theme.setCurrentText("Custom")
            save()
            self.setStyleSheet(self.css())

    def pick_colour(self, key, widget):
        colour = QColorDialog.getColor(QColor(settings[key]), self)
        if colour.isValid():
            widget.setText(colour.name())
            self.set_colour(key, colour.name())

    def set_hotkey(self, value):
        self.change("hotkey", value)
        self.hint.setText("Hotkey: " + value)

    def toggle(self):
        if running.is_set():
            running.clear()
            self.stopped()
            return

        self.start.setEnabled(False)
        delay = int(settings["delay"])

        if delay:
            self.status.setText("● WAITING")
            QTimer.singleShot(delay, self.begin)
        else:
            self.begin()

    def begin(self):
        if shutdown.is_set():
            return

        global click_count
        click_count = 0
        running.set()
        self.start.setEnabled(True)
        self.start.setText("■   Stop clicking")
        self.status.setText("● CLICKING")

    def stopped(self):
        running.clear()
        self.start.setEnabled(True)
        self.start.setText("▶   Start clicking")
        self.status.setText("● READY")

    def show_error(self, message):
        self.status.setText("● CLICK ERROR")
        QMessageBox.warning(
            self,
            "Clicky couldn't simulate a click",
            "The mouse click failed:\n\n"
            + message
            + "\n\nLinux Wayland may restrict simulated mouse input."
        )

    def save_profile(self):
        name = self.profile_name.text().strip()

        if (
            not name
            or "/" in name
            or "\\" in name
            or name in (".", "..")
        ):
            self.status.setText("Enter a valid profile name")
            return

        (PROFILES / f"{name}.json").write_text(
            json.dumps(settings, indent=2)
        )
        self.profile_name.clear()
        self.refresh_profiles()
        self.status.setText("● PROFILE SAVED")

    def refresh_profiles(self):
        self.profile.blockSignals(True)
        self.profile.clear()
        self.profile.addItem("Select profile...")
        self.profile.addItems(
            sorted(path.stem for path in PROFILES.glob("*.json"))
        )
        self.profile.blockSignals(False)

    def load_profile(self, name):
        if name == "Select profile...":
            return

        try:
            loaded = json.loads(
                (PROFILES / f"{name}.json").read_text()
            )

            if running.is_set():
                running.clear()
                self.stopped()

            settings.update(loaded)
            save()

            # Apply profile values to existing controls.
            self.interval.setValue(int(settings["interval"]))
            self.mouse_button.setCurrentText(settings["button"])
            self.limit.setValue(int(settings["limit"]))
            self.delay.setValue(int(settings["delay"]))
            self.hotkey.setCurrentText(settings["hotkey"])
            self.theme.setCurrentText(settings["theme"])

            for key, widget in self.colour_inputs.items():
                widget.setText(settings[key])

            self.radius.setValue(int(settings["radius"]))
            self.font_size.setValue(int(settings["font"]))
            self.setStyleSheet(self.css())
            self.update_cps(self.interval.value())
            self.hint.setText("Hotkey: " + settings["hotkey"])
            self.status.setText("● PROFILE LOADED")

        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.status.setText("Couldn't load profile")
            QMessageBox.warning(self, "Profile error", str(exc))

    def closeEvent(self, event):
        running.clear()
        shutdown.set()
        self.listener.stop()
        event.accept()


threading.Thread(target=click_worker, daemon=True).start()

app = QApplication(sys.argv)
app.setStyle("Fusion")
window = Clicky()
window.show()
sys.exit(app.exec())

