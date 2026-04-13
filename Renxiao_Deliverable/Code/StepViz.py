"""
StepViz — Kid-Friendly Real-Time Gait Visualization
IOE 435 Final Project — Group 11 (K-Grams Fair)

Displays real-time gyroscope data from ankle-mounted IMU,
detects steps via peak detection, and shows results in a
colorful, child-friendly interface.

Usage:
    python StepViz.py          # live IMU mode
    python StepViz.py --demo   # simulated data for testing without hardware
"""

import sys
import time
import math
import collections
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import QTimer, QThreadPool, Qt
from PyQt6.QtGui import QFont, QColor
import pyqtgraph as pg

DEMO_MODE = "--demo" in sys.argv

# ---------------------------------------------------------------------------
# Simulated UDP handler for demo/testing without hardware
# ---------------------------------------------------------------------------
class DemoUDPHandler:
    """Generates fake walking data so the app can run without a sensor."""

    def __init__(self):
        self.receiving = [True]
        self._t0 = time.time()
        self._phase = 0.0
        self.current_data = {
            "timestamp": 0, "accl_x": 0, "accl_y": 0, "accl_z": 0,
            "gyro_x": 0, "gyro_y": 0, "gyro_z": 0,
            "mag_x": 0, "mag_y": 0, "mag_z": 0, "temp": 0, "emg": 0,
        }
        from DataUnpacker import NAxisSensor
        self.gyro_sensor = NAxisSensor(data=[0, 0, 0], timestamp=0, size=500)

    def handler_one_shot(self):
        t_ms = (time.time() - self._t0) * 1000
        self._phase += 0.12
        gz = 180 * math.sin(self._phase) + 40 * math.sin(3.7 * self._phase)
        gz += np.random.normal(0, 8)
        gx = np.random.normal(0, 15)
        gy = np.random.normal(0, 15)
        self.current_data["timestamp"] = t_ms
        self.current_data["gyro_x"] = gx
        self.current_data["gyro_y"] = gy
        self.current_data["gyro_z"] = gz
        self.gyro_sensor.set_val(t_ms, [gx, gy, gz])
        self.receiving[0] = True

    def on_finished(self):
        pass


# ---------------------------------------------------------------------------
# Import real UDPHandler + worker helpers
# ---------------------------------------------------------------------------
if not DEMO_MODE:
    from UDPHandler import UDPHandler
from DataUnpacker import NAxisSensor

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal


class WorkerSignals(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)


class RepeatedFunctionWorker(QRunnable):
    def __init__(self, function, interval, *args, **kwargs):
        super().__init__()
        self.function = function
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.is_running = True

    def run(self):
        self.signals.started.emit()
        try:
            while self.is_running:
                result = self.function(*self.args, **self.kwargs)
                self.signals.result.emit(result)
                time.sleep(self.interval)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()

    def stop(self):
        self.is_running = False


# ---------------------------------------------------------------------------
# Step detector
# ---------------------------------------------------------------------------
class StepDetector:
    """Simple peak-based step detector on gyro-Z angular velocity."""

    def __init__(self, threshold=120, cooldown_ms=350):
        self.threshold = threshold
        self.cooldown_ms = cooldown_ms
        self.step_count = 0
        self.step_timestamps = []
        self._last_step_time = -9999

    def reset(self):
        self.step_count = 0
        self.step_timestamps.clear()
        self._last_step_time = -9999

    def update(self, t_ms, gyro_z):
        if abs(gyro_z) > self.threshold:
            if (t_ms - self._last_step_time) > self.cooldown_ms:
                self.step_count += 1
                self.step_timestamps.append(t_ms)
                self._last_step_time = t_ms
                return True
        return False


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class StepVizWindow(QMainWindow):

    # Color palette
    BG_COLOR = "#1a1a2e"
    WAVE_COLOR = "#00d4ff"
    STEP_MARKER_COLOR = "#ff6b6b"
    ACCENT_GREEN = "#00e676"
    ACCENT_YELLOW = "#ffeb3b"
    TEXT_WHITE = "#ffffff"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Step Counter!")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(f"background-color: {self.BG_COLOR};")

        # --- Data backend ---
        if DEMO_MODE:
            self.udp = DemoUDPHandler()
        else:
            self.udp = UDPHandler()

        self.thread_pool = QThreadPool()
        self.worker = RepeatedFunctionWorker(self.udp.handler_one_shot, 0)
        self.worker.signals.finished.connect(self.udp.on_finished)
        self.thread_pool.start(self.worker)

        self.detector = StepDetector(threshold=120, cooldown_ms=350)

        self.time_buf = collections.deque(maxlen=600)
        self.gyro_z_buf = collections.deque(maxlen=600)
        self.step_x = []
        self.step_y = []

        self._build_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(30)

    # ---- UI Construction ----
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 10, 20, 10)

        # -- Title --
        title = QLabel("Walk, Jump, and See Your Steps!")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.ACCENT_YELLOW}; padding: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # -- Stats bar --
        stats = QHBoxLayout()

        self.step_label = QLabel("0")
        self.step_label.setFont(QFont("Arial", 96, QFont.Weight.Bold))
        self.step_label.setStyleSheet(f"color: {self.ACCENT_GREEN};")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step_caption = QLabel("STEPS")
        step_caption.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        step_caption.setStyleSheet(f"color: {self.TEXT_WHITE};")
        step_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step_box = QVBoxLayout()
        step_box.addWidget(self.step_label)
        step_box.addWidget(step_caption)

        self.status_label = QLabel("Waiting for sensor...")
        self.status_label.setFont(QFont("Arial", 18))
        self.status_label.setStyleSheet(f"color: {self.ACCENT_YELLOW};")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        reset_btn = QPushButton("Reset")
        reset_btn.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        reset_btn.setFixedSize(150, 60)
        reset_btn.setStyleSheet(
            f"background-color: {self.STEP_MARKER_COLOR}; color: white; "
            "border-radius: 12px; border: none;"
        )
        reset_btn.clicked.connect(self._reset)

        stats.addStretch()
        stats.addLayout(step_box)
        stats.addStretch()
        stats.addWidget(self.status_label)
        stats.addStretch()
        stats.addWidget(reset_btn)
        stats.addStretch()
        layout.addLayout(stats)

        # -- Plot --
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(QColor(20, 20, 46))
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.setLabel("bottom", "Time", units="s",
                                  **{"font-size": "16pt", "color": self.TEXT_WHITE})
        self.plot_widget.setLabel("left", "Motion Signal", units="°/s",
                                  **{"font-size": "16pt", "color": self.TEXT_WHITE})
        self.plot_widget.getAxis("bottom").setTickFont(QFont("Arial", 14))
        self.plot_widget.getAxis("left").setTickFont(QFont("Arial", 14))
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(self.TEXT_WHITE))
        self.plot_widget.getAxis("left").setPen(pg.mkPen(self.TEXT_WHITE))
        self.plot_widget.setYRange(-350, 350)

        pen = pg.mkPen(color=self.WAVE_COLOR, width=3)
        self.curve = self.plot_widget.plot([], [], pen=pen)
        self.step_scatter = pg.ScatterPlotItem(
            size=18, pen=pg.mkPen(None),
            brush=pg.mkBrush(self.STEP_MARKER_COLOR)
        )
        self.plot_widget.addItem(self.step_scatter)

        layout.addWidget(self.plot_widget, stretch=1)

        # -- Bottom hint --
        hint = QLabel("Strap the sensor to your ankle and start moving!")
        hint.setFont(QFont("Arial", 16))
        hint.setStyleSheet(f"color: #888; padding: 6px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    # ---- Update loop (called every 30 ms) ----
    def _update(self):
        if not self.udp.receiving[0]:
            self.status_label.setText("Waiting for sensor...")
            self.status_label.setStyleSheet(f"color: {self.ACCENT_YELLOW};")
            return

        self.status_label.setText("Connected!")
        self.status_label.setStyleSheet(f"color: {self.ACCENT_GREEN};")

        t_ms = self.udp.current_data["timestamp"]
        gz = self.udp.current_data["gyro_z"]
        t_sec = t_ms / 1000.0

        self.time_buf.append(t_sec)
        self.gyro_z_buf.append(gz)

        stepped = self.detector.update(t_ms, gz)
        if stepped:
            self.step_x.append(t_sec)
            self.step_y.append(gz)
            self.step_label.setText(str(self.detector.step_count))

        t_arr = np.array(self.time_buf)
        g_arr = np.array(self.gyro_z_buf)
        self.curve.setData(t_arr, g_arr)

        if self.step_x:
            vis_min = t_arr[0] if len(t_arr) else 0
            sx = np.array(self.step_x)
            sy = np.array(self.step_y)
            mask = sx >= vis_min
            self.step_scatter.setData(sx[mask], sy[mask])

        if len(t_arr) > 1:
            self.plot_widget.setXRange(t_arr[-1] - 6, t_arr[-1] + 0.2)

    def _reset(self):
        self.detector.reset()
        self.step_label.setText("0")
        self.step_x.clear()
        self.step_y.clear()
        self.step_scatter.setData([], [])

    def closeEvent(self, event):
        self.worker.stop()
        self.timer.stop()
        event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = StepVizWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
