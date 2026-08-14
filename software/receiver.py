import sys
import struct
import binascii
import io
import time
import numpy as np
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, QGroupBox, 
                             QGridLayout, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
import serial
import ctypes

START_BYTE = 0x02
END_BYTE = 0x03
BAUD_RATE=38400


def calculate_crc16(data: bytes) -> int:
    return binascii.crc_hqx(data, 0xFFFF) & 0xFFFF

class ReceiverWorker(QThread):
    # Signale für die GUI
    image_init = pyqtSignal(int, int)
    tile_received = pyqtSignal(object) 
    stats_updated = pyqtSignal(int, int, int) # Packets, CRC Errors, Total Bytes
    error = pyqtSignal(str)

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.is_running = True

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
        except Exception as e:
            self.error.emit(f"Portfehler: {e}")
            return

        packets_received = 0
        crc_errors = 0
        total_bytes = 0

        pixel_buffer = None
        current_tile_x = 0
        current_tile_y = 0
        expected_tile_length = 0
        tile_buffer = bytearray()
        tile_corrupted = False

        while self.is_running:
            start_search = ser.read(1)
            if not start_search or start_search[0] != START_BYTE:
                continue
            
            header_bytes = ser.read(3)
            if len(header_bytes) < 3: 
                continue
                
            seq_num, length = struct.unpack(">HB", header_bytes)
            total_to_read = length + 3
            data_bytes = ser.read(total_to_read)
            
            if len(data_bytes) < total_to_read: 
                continue
            
            total_bytes += (4 + total_to_read)
            packets_received += 1
                
            payload = data_bytes[:length]
            received_crc = struct.unpack(">H", data_bytes[length:length+2])[0]
            end_byte = data_bytes[-1]
            
            if end_byte != END_BYTE: 
                continue
                
            if received_crc != calculate_crc16(header_bytes + payload):
                crc_errors += 1
                tile_corrupted = True
                self.stats_updated.emit(packets_received, crc_errors, total_bytes)
                continue

            self.stats_updated.emit(packets_received, crc_errors, total_bytes)

            # Global Meta Frame
            if seq_num == 0xFFFE:
                width, height = struct.unpack(">HH", payload)
                pixel_buffer = np.zeros((height, width, 3), dtype=np.uint8)
                self.image_init.emit(width, height)
                continue

            # Tile Meta Frame
            if seq_num == 0xFFFF:
                current_tile_x, current_tile_y, expected_tile_length = struct.unpack(">HHI", payload)
                tile_buffer = bytearray()
                tile_corrupted = False
                continue

            # Payload Frame
            if not tile_corrupted and expected_tile_length > 0:
                tile_buffer.extend(payload)
                
                if len(tile_buffer) >= expected_tile_length:
                    # Schutzabfrage: Wurde die Bildgröße bereits empfangen?
                    if pixel_buffer is not None:
                        try:
                            buf = io.BytesIO(tile_buffer[:expected_tile_length])
                            tile_img = Image.open(buf).convert('RGB')
                            tile_array = np.array(tile_img)
                            
                            h, w, _ = tile_array.shape
                            pixel_buffer[current_tile_y : current_tile_y+h, current_tile_x : current_tile_x+w] = tile_array
                            
                            # Konvertiere Numpy Array zu QImage für PyQt
                            height, width, channel = pixel_buffer.shape
                            bytes_per_line = 3 * width
                            
                            # WICHTIG: .copy() erzwingt, dass PyQt den Speicher übernimmt.
                            # Andernfalls stürzt das Programm ab, weil Numpy und GUI-Thread kollidieren.
                            q_img = QImage(pixel_buffer.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
                            
                            self.tile_received.emit(q_img)
                        except Exception as e:
                            print(f"Decodierfehler: {e}")
                    else:
                        print(f"Warnung: Kachel empfangen, aber Init-Frame fehlt noch.")
                    
                    expected_tile_length = 0

        ser.close()

    def stop(self):
        self.is_running = False
        self.wait()

class ReceiverGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laser Receiver GUI")
        self.resize(900, 700)
        self.worker = None
        self.start_time = None

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # --- Linke Bildfläche ---
        self.lbl_image = QLabel("Warte auf Bilddaten...")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setStyleSheet("background-color: #111; color: #888;")
        
        # WICHTIG: Erlaubt dem Label ignoriert zu werden bei der Größenberechnung
        # Verhindert, dass das Fenster durch große Bilder unkontrolliert wächst.
        self.lbl_image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.lbl_image.setMinimumSize(400, 300)
        
        layout.addWidget(self.lbl_image, 3)

        # --- Rechte Steuer- und Info-Fläche ---
        right_panel = QVBoxLayout()
        
        control_group = QGroupBox("Steuerung")
        clayout = QVBoxLayout()
        clayout.addWidget(QLabel("COM Port:"))
        default_port = "COM3" if sys.platform.startswith("win") else "/dev/tty.usbmodem1101"
        self.entry_port = QLineEdit(default_port)
        clayout.addWidget(self.entry_port)
        
        self.btn_toggle = QPushButton("Empfang starten")
        self.btn_toggle.clicked.connect(self.toggle_receiver)
        clayout.addWidget(self.btn_toggle)
        control_group.setLayout(clayout)
        right_panel.addWidget(control_group)

        stats_group = QGroupBox("Statistiken")
        grid = QGridLayout()
        self.lbl_time = QLabel("00:00")
        self.lbl_packets = QLabel("0")
        self.lbl_errors = QLabel("0")
        self.lbl_bytes = QLabel("0 B")

        grid.addWidget(QLabel("Laufzeit:"), 0, 0)
        grid.addWidget(self.lbl_time, 0, 1)
        grid.addWidget(QLabel("Pakete gesamt:"), 1, 0)
        grid.addWidget(self.lbl_packets, 1, 1)
        grid.addWidget(QLabel("CRC Fehler:"), 2, 0)
        grid.addWidget(self.lbl_errors, 2, 1)
        grid.addWidget(QLabel("Datenmenge:"), 3, 0)
        grid.addWidget(self.lbl_bytes, 3, 1)
        
        stats_group.setLayout(grid)
        right_panel.addWidget(stats_group)
        right_panel.addStretch()
        layout.addLayout(right_panel, 1)

        # Timer für die Laufzeit
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

    def toggle_receiver(self):
        if self.worker is None or not self.worker.isRunning():
            self.lbl_image.setText("Warte auf Init-Frame (0xFFFE)...")
            self.start_time = time.time()
            self.timer.start(1000)
            
            self.worker = ReceiverWorker(self.entry_port.text(), BAUD_RATE)
            self.worker.image_init.connect(self.on_image_init)
            self.worker.tile_received.connect(self.on_tile_received)
            self.worker.stats_updated.connect(self.update_stats)
            self.worker.error.connect(self.on_error) # WICHTIG: Signal verknüpft
            self.worker.start()
            
            self.btn_toggle.setText("Empfang stoppen")
        else:
            self.worker.stop()
            self.timer.stop()
            self.btn_toggle.setText("Empfang starten")

    def on_error(self, err_msg):
        # Fehler ordentlich anzeigen und GUI zurücksetzen
        self.worker.stop()
        self.timer.stop()
        self.btn_toggle.setText("Empfang starten")
        self.lbl_image.setText("Verbindungsfehler.")
        QMessageBox.critical(self, "Verbindungsfehler", err_msg)

    def on_image_init(self, w, h):
        self.lbl_image.setText(f"Bildgröße empfangen: {w}x{h}\nLade Kacheln...")

    def on_tile_received(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        # Bessere Skalierungs-Qualität durch SmoothTransformation
        scaled_pixmap = pixmap.scaled(
            self.lbl_image.width(), 
            self.lbl_image.height(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_image.setPixmap(scaled_pixmap)

    def update_stats(self, packets, errors, total_bytes):
        self.lbl_packets.setText(str(packets))
        self.lbl_errors.setText(str(errors))
        if total_bytes > 1024 * 1024:
            self.lbl_bytes.setText(f"{total_bytes/(1024*1024):.2f} MB")
        elif total_bytes > 1024:
            self.lbl_bytes.setText(f"{total_bytes/1024:.1f} KB")
        else:
            self.lbl_bytes.setText(f"{total_bytes} B")

    def update_timer(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.lbl_time.setText(f"{mins:02d}:{secs:02d}")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        event.accept()

if __name__ == '__main__':
    myappid = 'meinprojekt.laserreceiver.gui.1.0' 
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except AttributeError:
        pass # Für den Fall, dass das Skript nicht auf Windows läuft
        
    app = QApplication(sys.argv)
    window = ReceiverGUI()
    window.show()
    sys.exit(app.exec())
