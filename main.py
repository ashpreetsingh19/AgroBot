import sys
import json
import os
import hashlib
import random
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QFrame, QLineEdit,
    QMessageBox, QMenu, QStackedLayout
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEvent
from PySide6.QtGui import QAction, QKeyEvent

# Import intents and responses from a separate Python file
try:
    from AgroBot.responses_data import intents as default_intents, responses as default_responses
except ImportError:
    default_intents = {}
    default_responses = {}

# Import weather API functions from weather_api.py
from AgroBot.weather_api import get_user_location, get_weather, get_weather_by_coordinates, get_7_day_forecast

# Import pest control advice from pest_control.py
from AgroBot.pest_control import PestControl

USERS_FILE = "users.json"
THEMES_FILE = "theme.json"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password_strength(password: str) -> bool:
    if len(password) < 6:
        return False
    if not re.search(r"[a-zA-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

def load_all_themes():
    if not os.path.exists(THEMES_FILE):
        QMessageBox.warning(None, "Theme Error", f"Theme file '{THEMES_FILE}' not found.")
        return {}
    try:
        with open(THEMES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        QMessageBox.warning(None, "Theme Error", f"Failed to load themes:\n{e}")
        return {}

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgroBot - Login / Signup")
        self.is_dark_mode = False
        self.users = self.load_users()
        self.setup_ui()
        self.apply_light_theme()
        self.showMaximized()

        self.login_username.returnPressed.connect(self.try_login_on_enter)
        self.login_password.returnPressed.connect(self.try_login_on_enter)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)

        self.title_label = QLabel("🌿 <b>AgroBot</b>")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 36px; margin-bottom: 20px; color: #2e7d32;")
        self.layout.addWidget(self.title_label)

        self.theme_toggle = QPushButton("🌙")
        self.theme_toggle.setFixedSize(36, 36)
        self.theme_toggle.setStyleSheet("border: none; font-size: 18px;")
        self.theme_toggle.clicked.connect(self.toggle_theme)

        top_right_layout = QHBoxLayout()
        top_right_layout.addStretch()
        top_right_layout.addWidget(self.theme_toggle)
        self.layout.addLayout(top_right_layout)

        self.card = QFrame()
        self.card.setFixedWidth(420)
        self.card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                padding: 30px;
            }
        """)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(12)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.status_label)

        self.stack = QStackedLayout()

        # Login form
        self.login_widget = QWidget()
        login_layout = QVBoxLayout(self.login_widget)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Username")
        self.login_username.setMinimumWidth(300)

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.login)

        self.switch_to_signup = QPushButton("Create an account")
        self.switch_to_signup.setFlat(True)
        self.switch_to_signup.setStyleSheet("color: #ffffff;")
        self.switch_to_signup.setCursor(Qt.PointingHandCursor)
        self.switch_to_signup.clicked.connect(self.switch_to_signup_form)

        login_layout.addWidget(self.login_username)
        login_layout.addWidget(self.login_password)
        login_layout.addWidget(self.login_button)
        login_layout.addWidget(self.switch_to_signup)
        self.login_widget.setLayout(login_layout)

        # Signup form
        self.signup_widget = QWidget()
        signup_layout = QVBoxLayout(self.signup_widget)

        self.signup_username = QLineEdit()
        self.signup_username.setPlaceholderText("Choose a username")
        self.signup_username.setMinimumWidth(300)

        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Choose a password")
        self.signup_password.setEchoMode(QLineEdit.Password)

        self.signup_confirm_password = QLineEdit()
        self.signup_confirm_password.setPlaceholderText("Confirm password")
        self.signup_confirm_password.setEchoMode(QLineEdit.Password)

        self.signup_button = QPushButton("Sign Up")
        self.signup_button.setCursor(Qt.PointingHandCursor)
        self.signup_button.clicked.connect(self.signup)

        self.switch_to_login = QPushButton("Already have an account?  Go to login")
        self.switch_to_login.setFlat(True)
        self.switch_to_login.setStyleSheet("color: #ffffff;")
        self.switch_to_login.setCursor(Qt.PointingHandCursor)
        self.switch_to_login.clicked.connect(self.switch_to_login_form)

        signup_layout.addWidget(self.signup_username)
        signup_layout.addWidget(self.signup_password)
        signup_layout.addWidget(self.signup_confirm_password)
        signup_layout.addWidget(self.signup_button)
        signup_layout.addWidget(self.switch_to_login)
        self.signup_widget.setLayout(signup_layout)

        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.signup_widget)

        self.card_layout.addLayout(self.stack)

        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(self.card)
        center_layout.addStretch()

        self.layout.addLayout(center_layout)

        self.login_username.setFocus()
        self.card.setLayout(self.card_layout)

    def switch_to_signup_form(self):
        self.stack.setCurrentWidget(self.signup_widget)
        self.status_label.clear()
        self.signup_username.clear()
        self.signup_password.clear()
        self.signup_confirm_password.clear()

    def switch_to_login_form(self):
        self.stack.setCurrentWidget(self.login_widget)
        self.status_label.clear()
        self.login_username.clear()
        self.login_password.clear()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.apply_dark_theme()
            self.theme_toggle.setText("🌞")
        else:
            self.apply_light_theme()
            self.theme_toggle.setText("🌙")

    def apply_light_theme(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #d5f4e6,
                    stop:1 #b2dfdb
                );
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QPushButton {
                padding: 8px;
                border-radius: 6px;
                background-color: #66bb6a;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4caf50;
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
        """)
        # Set frame color for light mode
        self.card.setStyleSheet("""
            QFrame {
                background-color: #e0f7fa;
                border-radius: 20px;
                padding: 30px;
            }
        """)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: white;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #666;
                border-radius: 6px;
                background-color: #2c2c2c;
                color: white;
            }
            QPushButton {
                padding: 8px;
                border-radius: 6px;
                background-color: #4caf50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66bb6a;
            }
            QPushButton:pressed {
                background-color: #81c784;
            }
        """)
        # Set frame color for dark mode
        self.card.setStyleSheet("""
            QFrame {
                background-color: #263238;
                border-radius: 20px;
                padding: 30px;
            }
        """)

    def load_users(self):
        if not os.path.exists(USERS_FILE):
            return {}
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed loading user data:\n{e}")
            return {}

    def save_users(self):
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed saving user data:\n{e}")

    def login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()
        if not re.match(r"^\w+$", username):
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("Username must be letters, numbers, or underscores only.")
            return
        if not username or not password:
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("Enter username and password")
            return
        hashed = hash_password(password)
        if username in self.users and self.users[username] == hashed:
            self.open_chat(username)
        else:
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("Invalid credentials")

    def signup(self):
        username = self.signup_username.text().strip()
        password = self.signup_password.text()
        confirm = self.signup_confirm_password.text()
        if not re.match(r"^\w+$", username):
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("Username must be letters, numbers, or underscores only.")
            return
        if not username or not password or not confirm:
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("All fields are required")
            return
        if password != confirm:
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("Passwords do not match")
            return
        if not check_password_strength(password):
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("Weak password: use letters and digits (min 6 chars)")
            return
        if username in self.users:
            self.status_label.setStyleSheet("color: #e53935; font-weight: bold;")
            self.status_label.setText("Username already taken")
            return

        self.users[username] = hash_password(password)
        self.save_users()
        QMessageBox.information(self, "Signup Successful", "Signup successful! You can now login.")
        self.switch_to_login_form()

    def open_chat(self, username):
        self.chat_window = ChatWindow(username)
        self.chat_window.showMaximized()
        self.hide()

    def showEvent(self, event):
        self.login_username.clear()
        self.login_password.clear()
        self.signup_username.clear()
        self.signup_password.clear()
        self.signup_confirm_password.clear()
        self.status_label.clear()
        self.login_username.setFocus()
        super().showEvent(event)

    def try_login_on_enter(self):
        if self.stack.currentWidget() == self.login_widget:
            if self.login_username.text().strip() and self.login_password.text():
                self.login()

class ChatBubble(QFrame):
    def __init__(self, text, is_user=False, theme=None):
        super().__init__()
        self.is_user = is_user
        self.theme = theme or {"bg": "#121212", "fg": "#FFFFFF"}
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.update_style(self.theme)
        self.label.setMaximumWidth(600)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if is_user:
            layout.addStretch()
            layout.addWidget(self.label)
        else:
            layout.addWidget(self.label)
            layout.addStretch()

    def update_style(self, theme):
        self.theme = theme
        if self.is_user:
            bubble_bg = theme.get("user_bg", "#1e88e5")
            bubble_fg = theme.get("user_fg", "#ffffff")
        else:
            bubble_bg = theme.get("bot_bg", theme.get("bg", "#121212"))
            bubble_fg = theme.get("bot_fg", theme.get("fg", "#FFFFFF"))
        self.label.setStyleSheet(f"""
            background-color: {bubble_bg};
            color: {bubble_fg};
            padding: 10px 14px;
            border-radius: 16px;
            font-size: 16px;
        """)

class ChatWindow(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"Chatbot: {username}")
        self._logging_out = False
        self.messages = []
        self.chat_history_file = f"chat_history_{username}.json"
        self.theme = {"bg": "#121212", "fg": "#FFFFFF"}
        self.animation = None
        self.init_ui()
        self.load_chat_history()
        theme = self.load_theme()
        if theme:
            self.theme = theme
        self.apply_theme(self.theme)
        self._welcome_shown = False

        # Use imported intents and responses
        self.intents = default_intents
        self.responses = default_responses

        # Use PestControl class for pest advice
        self.pest_control = PestControl()

        # Show welcome message only if chat is empty after loading history
        if not self.messages:
            self.add_message("Welcome to AgroBot! Type your question below.", is_user=False)
            self._welcome_shown = True

        self.input_box.setFocus()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)

        self.header = QHBoxLayout()
        self.user_label = QLabel(f"Logged in as: <b>{self.username}</b>")
        self.header.addWidget(self.user_label, alignment=Qt.AlignLeft)

        self.clear_button = QPushButton("Clear History")
        self.clear_button.setFixedSize(120, 35)
        self.clear_button.clicked.connect(self.confirm_clear_history)
        self.header.addWidget(self.clear_button)

        self.theme_button = QPushButton("Change Theme")
        self.theme_button.setFixedSize(120, 35)
        self.theme_button.clicked.connect(self.open_theme_menu)
        self.header.addWidget(self.theme_button)

        self.header.addStretch()
        self.logout_button = QPushButton("Logout")
        self.logout_button.setFixedSize(100, 35)
        self.logout_button.clicked.connect(self.logout)
        self.header.addWidget(self.logout_button, alignment=Qt.AlignRight)

        self.layout.addLayout(self.header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_widget)
        self.layout.addWidget(self.scroll_area)

        self.typing_label = QLabel("")
        self.typing_label.setAlignment(Qt.AlignCenter)
        self.typing_label.setStyleSheet("color: #888; font-style: italic;")
        self.layout.addWidget(self.typing_label)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Type your message here...\nPress Enter to send, Ctrl+Enter for new line.")
        self.input_box.setFixedHeight(80)
        self.input_box.installEventFilter(self)
        self.input_box.textChanged.connect(self.update_send_button_state)

        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(100, 40)
        self.send_button.clicked.connect(self.on_send)
        self.send_button.setEnabled(False)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)

        self.layout.addLayout(input_layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.input_box.setFocus()

    def add_message(self, text, is_user=False):
        bubble = ChatBubble(text, is_user, self.theme)
        bubble._is_user = is_user
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(100, self.scroll_to_bottom_smooth)

    def on_send(self):
        text = self.input_box.toPlainText().strip()
        if not text or self.send_button.isEnabled() is False:
            return
        self.add_message(text, is_user=True)
        self.messages.append({"user": text})
        self.input_box.clear()
        self.update_send_button_state()
        self.save_chat_history()
        self.typing_label.setText("Bot is typing...")
        self.send_button.setEnabled(False)
        self.nlp_response(text)

    def nlp_response(self, user_text):
        def respond():
            text = user_text.lower().strip()

            # 1. 7-day/weekly forecast (robust matching)
            weekly_patterns = [
                r"7[- ]?day forecast",
                r"seven day forecast",
                r"weekly forecast",
                r"weekly weather",
                r"weather for next 7 days",
                r"weather for the week",
                r"week's weather",
                r"weather next week"
            ]
            if any(re.search(pattern, text) for pattern in weekly_patterns):
                city_name, loc = get_user_location()
                if loc and loc[0] is not None and loc[1] is not None:
                    lat, lon = loc
                    forecast = get_7_day_forecast(lat, lon)
                    response = f"7-Day Forecast for {city_name or 'your location'}:\n{forecast}"
                else:
                    response = "Could not determine your location to provide the 7-day forecast."

            # 2. Weather in a specific city
            elif re.match(r"(?:what(?:'s| is) the )?weather in ([\w\s]+)\??", text):
                city_match = re.match(r"(?:what(?:'s| is) the )?weather in ([\w\s]+)\??", text)
                city = city_match.group(1).strip()
                response = get_weather(city)

            # 3. Weather for current location (weather, weather here, current weather, etc.)
            elif any(phrase in text for phrase in ["weather here", "current weather", "weather now", "weather"]):
                city_name, loc = get_user_location()
                if loc and loc[0] is not None and loc[1] is not None:
                    lat, lon = loc
                    response = get_weather_by_coordinates(lat, lon)
                    if city_name:
                        response = f"Weather in {city_name}: " + response.replace("Current Weather: ", "")
                else:
                    response = "Could not determine your location to provide the weather."

            # 4. Pest control Q&A
            elif re.search(r"(pest\s*(control|advice|problem|management|remedy|solution|issue|treatment).*\b(for|in)\b\s*([\w\s]+))", text):
                # Try to extract crop name after 'for' or 'in'
                match = re.search(r"\b(for|in)\b\s*([\w\s]+)", text)
                if match:
                    crop = match.group(2).strip()
                    response = self.pest_control.get_advice(crop)
                else:
                    response = "Please specify the crop you want pest control advice for (e.g., 'pest control for wheat')."

            # 5. Fallback to intents/responses
            else:
                matched_intent = "default"
                for intent, phrases in self.intents.items():
                    for phrase in phrases:
                        if phrase in text:
                            matched_intent = intent
                            break
                    if matched_intent != "default":
                        break
                resp = self.responses.get(matched_intent, self.responses.get("default", ["Sorry, I didn't quite understand that. Could you rephrase?"]))
                if isinstance(resp, list):
                    response = random.choice(resp)
                else:
                    response = resp

            self.add_message(response, is_user=False)
            self.messages.append({"bot": response})
            self.save_chat_history()
            self.typing_label.setText("")
            self.send_button.setEnabled(True)
            self.input_box.setFocus()
        QTimer.singleShot(400, respond)

    def scroll_to_bottom_smooth(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        end_value = scrollbar.maximum()
        animation = QPropertyAnimation(scrollbar, b"value", self)
        animation.setDuration(300)
        animation.setStartValue(scrollbar.value())
        animation.setEndValue(end_value)
        animation.start()
        self.animation = animation

    def update_send_button_state(self):
        text = self.input_box.toPlainText().strip()
        self.send_button.setEnabled(bool(text))

    def eventFilter(self, obj, event):
        if obj == self.input_box and event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent):
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    # Ctrl+Enter: insert new line
                    if event.modifiers() & Qt.ControlModifier:
                        cursor = self.input_box.textCursor()
                        cursor.insertText('\n')
                        return True
                    # Enter: send message
                    else:
                        if self.send_button.isEnabled():
                            self.on_send()
                        return True
        return super().eventFilter(obj, event)

    def save_chat_history(self):
        try:
            with open(self.chat_history_file, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed saving chat history:\n{e}")

    def load_chat_history(self):
        if not os.path.exists(self.chat_history_file):
            return
        try:
            with open(self.chat_history_file, "r", encoding="utf-8") as f:
                self.messages = json.load(f)
            for msg in self.messages:
                if "user" in msg:
                    self.add_message(msg["user"], is_user=True)
                elif "bot" in msg:
                    self.add_message(msg["bot"], is_user=False)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed loading chat history:\n{e}")

    def confirm_clear_history(self):
        reply = QMessageBox.question(self, 'Confirm', 'Clear all chat history?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.messages.clear()
            self.save_chat_history()
            for i in reversed(range(self.chat_layout.count() - 1)):
                widget = self.chat_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            self.scroll_area.verticalScrollBar().setValue(0)
            self.add_message("Welcome to AgroBot! Type your question below.", is_user=False)
            self._welcome_shown = True

    def open_theme_menu(self):
        menu = QMenu(self)
        themes = load_all_themes()
        for name, colors in themes.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, c=colors: self.apply_theme(c))
            menu.addAction(action)
        menu.exec_(self.theme_button.mapToGlobal(self.theme_button.rect().bottomLeft()))

    def apply_theme(self, theme):
        self.theme = theme
        self.save_theme()
        bg_color = theme.get("bg", "#121212")
        fg_color = theme.get("fg", "#FFFFFF")
        user_bg = theme.get("user_bg", "#1e88e5")
        user_fg = theme.get("user_fg", "#ffffff")
        bot_bg = theme.get("bot_bg", bg_color)
        bot_fg = theme.get("bot_fg", fg_color)
        clear_bg = theme.get("clear_bg", user_bg)
        clear_fg = theme.get("clear_fg", user_fg)
        theme_bg = theme.get("theme_bg", bot_bg)
        theme_fg = theme.get("theme_fg", bot_fg)
        self.setStyleSheet(f"background-color: {bg_color}; color: {fg_color};")
        self.user_label.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {fg_color};")
        self.input_box.setStyleSheet(f"""
            background-color: {bg_color};
            color: {fg_color};
            border: 1px solid #333;
            border-radius: 8px;
            padding: 6px 10px;
        """)
        self.clear_button.setStyleSheet(
            f"background-color: {clear_bg}; color: {clear_fg}; border-radius: 8px; font-weight: bold;"
        )
        self.theme_button.setStyleSheet(
            f"background-color: {theme_bg}; color: {theme_fg}; border-radius: 8px; font-weight: bold;"
        )
        self.send_button.setStyleSheet(f"background-color: #1e88e5; color: white; border-radius: 8px;")
        self.logout_button.setStyleSheet(f"background-color: #e53935; color: white; border-radius: 8px;")
        self.scroll_area.setStyleSheet(f"background-color: transparent; border: none; color: {fg_color};")
        for i in range(self.chat_layout.count() - 1):
            bubble = self.chat_layout.itemAt(i).widget()
            if isinstance(bubble, ChatBubble):
                bubble.update_style(theme)

    def save_theme(self):
        theme_file = f"theme_{self.username}.json"
        try:
            with open(theme_file, "w", encoding="utf-8") as f:
                json.dump(self.theme, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed saving theme:\n{e}")

    def load_theme(self):
        theme_file = f"theme_{self.username}.json"
        if not os.path.exists(theme_file):
            return None
        try:
            with open(theme_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed loading theme:\n{e}")
            return None

    def logout(self):
        reply = QMessageBox.question(
            self, 'Logout Confirmation',
            'Are you sure you want to logout?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._logging_out = True
            self.close()
            for w in QApplication.topLevelWidgets():
                if w is not self and isinstance(w, (ChatWindow, AuthWindow)):
                    w.close()
            self.auth_window = AuthWindow()
            self.auth_window.showMaximized()
            self._welcome_shown = False

    def closeEvent(self, event):
        if getattr(self, "_logging_out", False):
            event.accept()
            return
        reply = QMessageBox.question(self, 'Exit Confirmation',
                                     'Are you sure you want to exit?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.showMaximized()
    sys.exit(app.exec())