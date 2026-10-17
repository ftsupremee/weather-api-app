"""Weather App: PyQt5 front end for weather_client.

The network request runs in a QThread, so the window never freezes while waiting.
"""

import sys

from dotenv import load_dotenv
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from weather_client import Weather, WeatherError, fetch_weather, get_api_key

STYLESHEET = """
    QWidget { font-family: calibri; }
    QLabel#title_label { font-size: 28px; font-style: italic; }
    QLineEdit#city_input { font-size: 28px; }
    QPushButton#search_button { font-size: 24px; font-weight: bold; }
    QLabel#location_label { font-size: 26px; }
    QLabel#temperature_label { font-size: 56px; }
    QLabel#description_label { font-size: 26px; }
    QLabel#details_label { font-size: 18px; color: #555; }
    QLabel#status_label { font-size: 18px; color: #b00020; }
"""


class WeatherThread(QThread):
    """Fetches weather off the UI thread and reports back through signals."""

    succeeded = pyqtSignal(object)  # Weather
    failed = pyqtSignal(str)

    def __init__(self, city: str, api_key: str, parent=None):
        super().__init__(parent)
        self.city = city
        self.api_key = api_key

    def run(self):
        try:
            self.succeeded.emit(fetch_weather(self.city, self.api_key))
        except WeatherError as error:
            self.failed.emit(str(error))
        except Exception:  # never let a worker thread die silently
            self.failed.emit("Something went wrong. Please try again.")


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.title_label = QLabel("Enter city name:", self)
        self.city_input = QLineEdit(self)
        self.search_button = QPushButton("Get weather", self)
        self.location_label = QLabel(self)
        self.temperature_label = QLabel(self)
        self.description_label = QLabel(self)
        self.details_label = QLabel(self)
        self.status_label = QLabel(self)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Weather App")
        self.resize(420, 520)

        layout = QVBoxLayout(self)
        for widget in (
            self.title_label,
            self.city_input,
            self.search_button,
            self.location_label,
            self.temperature_label,
            self.description_label,
            self.details_label,
            self.status_label,
        ):
            layout.addWidget(widget)
            if isinstance(widget, (QLabel, QLineEdit)):
                widget.setAlignment(Qt.AlignCenter)

        for name in (
            "title_label", "city_input", "search_button", "location_label",
            "temperature_label", "description_label", "details_label", "status_label",
        ):
            getattr(self, name).setObjectName(name)

        self.status_label.setWordWrap(True)
        self.setStyleSheet(STYLESHEET)

        self.search_button.clicked.connect(self.search)
        self.city_input.returnPressed.connect(self.search)

    # --- actions -----------------------------------------------------------
    def search(self):
        if self.worker is not None and self.worker.isRunning():
            return
        try:
            api_key = get_api_key()
        except WeatherError as error:
            self.show_error(str(error))
            return

        self.search_button.setEnabled(False)
        self.clear_results()
        self.status_label.setStyleSheet("color: #555;")
        self.status_label.setText("Loading...")

        self.worker = WeatherThread(self.city_input.text(), api_key, self)
        self.worker.succeeded.connect(self.show_weather)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self):
        self.search_button.setEnabled(True)

    def clear_results(self):
        for label in (
            self.location_label, self.temperature_label, self.description_label,
            self.details_label, self.status_label,
        ):
            label.clear()

    def show_error(self, message: str):
        self.clear_results()
        self.status_label.setStyleSheet("")  # fall back to the red from the stylesheet
        self.status_label.setText(message)

    def show_weather(self, weather: Weather):
        self.clear_results()
        self.location_label.setText(f"{weather.city}, {weather.country}")
        self.temperature_label.setText(f"{weather.temperature_c:.0f}°C")
        self.description_label.setText(weather.description)
        self.details_label.setText(
            f"Humidity {weather.humidity}%  ·  Wind {weather.wind_speed_ms:.1f} m/s"
        )

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait(2000)  # requests has a 10 s timeout; don't hang the exit on it
        super().closeEvent(event)


def main():
    load_dotenv()
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
