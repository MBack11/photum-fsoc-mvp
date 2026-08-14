import sys
import os
import struct
import time
import binascii
import io
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QSlider, QSpinBox, QProgressBar, QLineEdit, QComboBox, 
                             QMessageBox, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image
import serial

# Konstanten für das Protokoll
START_BYTE = 0x02
END_BYTE = 0x03
PAYLOAD_SIZE = 32

def calculate_crc16(data: bytes) -> int:
    return binascii.crc_hqx(data, 0xFFFF) & 0xFFFF

def build_frame(seq_num: int, payload: bytes) -> bytes:
    length = len(payload)
    header = struct.pack(">BHB", START_BYTE, seq_num, length)
    crc_data = header[1:] + payload
    crc = calculate_crc16(crc_data)
    return header + payload + struct.pack(">HB", crc, END_BYTE)


# --- WORKER THREAD ---
class SenderWorker(QThread):
    progress = pyqtSignal(int, int) # Current, Total
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, pil_image, tile_size, quality, port, baudrate):
        super().__init__()
        self.image = pil_image
        self.tile_size = tile_size
        self.quality = quality
        self.port = port
        self.baudrate = baudrate
        self.is_running = True

    def run(self):
        try:
            frames = self.generate_tile_frames(self.image, self.tile_size, self.quality)
            if not frames:
                self.error.emit("Konnte keine Frames generieren.")
                return

            try:
                ser = serial.Serial(self.port, self.baudrate, timeout=2.0)
                time.sleep(2) # Warte auf Arduino Reset
            except Exception as e:
                self.error.emit(f"Portfehler: {e}")
                return

            total_frames = len(frames)
            for index, frame in enumerate(frames):
                if not self.is_running:
                    break # Sicherer Abbruch
                
                ser.write(frame)
                time.sleep(0.05)
                
                ack = ser.read(1)
                if not ack or ack[0] != 0x06:
                    self.error.emit(f"Kein ACK nach Paket {index+1}. Abbruch.")
                    break
                
                self.progress.emit(index + 1, total_frames)

            ser.close()
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False

    def generate_tile_frames(self, img, tile_size, quality):
        width, height = img.size
        frames = []
        global_meta = struct.pack(">HH", width, height)
        frames.append(build_frame(0xFFFE, global_meta))

        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                box = (x, y, min(x + tile_size, width), min(y + tile_size, height))
                tile = img.crop(box)
                buf = io.BytesIO()
                tile.save(buf, format='JPEG', quality=quality)
                jpeg_bytes = buf.getvalue()
                
                tile_meta = struct.pack(">HHI", x, y, len(jpeg_bytes))
                frames.append(build_frame(0xFFFF, tile_meta))
                
                seq_num = 0
                for i in range(0, len(jpeg_bytes), PAYLOAD_SIZE):
                    chunk = jpeg_bytes[i : i + PAYLOAD_SIZE]
                    frames.append(build_frame(seq_num, chunk))
                    seq_num += 1
        return frames


# --- MAIN GUI ---
class SenderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laser Sender GUI - Pro (mit Diashow)")
        self.resize(1050, 750)
        
        self.current_image = None
        self.worker = None
        self.camera = None
        
        # Diashow Status
        self.slideshow_files = []
        self.slideshow_index = 0
        self.slideshow_running = False
        
        self.init_ui()

        # Timer für die Kamera-Vorschau
        self.cam_timer = QTimer()
        self.cam_timer.timeout.connect(self.update_camera_frame)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # --- LINKE STEUERLEISTE ---
        control_layout = QVBoxLayout()
        
        # 1. Bildquelle Gruppe
        group_source = QGroupBox("Einzelbild Quelle")
        vbox_source = QVBoxLayout()
        
        self.btn_load = QPushButton("Einzelnes Bild laden")
        self.btn_load.clicked.connect(self.load_single_image)
        vbox_source.addWidget(self.btn_load)
        
        hbox_cam = QHBoxLayout()
        self.btn_cam_toggle = QPushButton("Kamera starten")
        self.btn_cam_toggle.clicked.connect(self.toggle_camera)
        self.btn_capture = QPushButton("📸 Foto auslösen")
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self.capture_photo)
        
        hbox_cam.addWidget(self.btn_cam_toggle)
        hbox_cam.addWidget(self.btn_capture)
        vbox_source.addLayout(hbox_cam)
        group_source.setLayout(vbox_source)
        control_layout.addWidget(group_source)

        # 2. Diashow Gruppe
        group_slideshow = QGroupBox("Diashow Modus")
        vbox_slide = QVBoxLayout()
        
        self.chk_slideshow = QCheckBox("Diashow aktivieren")
        self.chk_slideshow.stateChanged.connect(self.toggle_slideshow_mode)
        vbox_slide.addWidget(self.chk_slideshow)
        
        self.btn_folder = QPushButton("Bilder-Ordner auswählen")
        self.btn_folder.setEnabled(False)
        self.btn_folder.clicked.connect(self.load_folder)
        vbox_slide.addWidget(self.btn_folder)
        
        self.lbl_folder = QLabel("Kein Ordner gewählt (0 Bilder)")
        vbox_slide.addWidget(self.lbl_folder)
        
        hbox_delay = QHBoxLayout()
        hbox_delay.addWidget(QLabel("Pause (Sekunden):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 300)
        self.spin_delay.setValue(2)
        self.spin_delay.setEnabled(False)
        hbox_delay.addWidget(self.spin_delay)
        vbox_slide.addLayout(hbox_delay)
        
        group_slideshow.setLayout(vbox_slide)
        control_layout.addWidget(group_slideshow)

        # 3. Einstellungen Gruppe
        group_settings = QGroupBox("Übertragungs-Einstellungen")
        vbox_set = QVBoxLayout()
        
        vbox_set.addWidget(QLabel("Tile Size (Kachelgröße):"))
        self.spin_tile = QSpinBox()
        self.spin_tile.setRange(16, 256)
        self.spin_tile.setValue(64)
        self.spin_tile.setSingleStep(16)
        self.spin_tile.valueChanged.connect(self.update_preview)
        vbox_set.addWidget(self.spin_tile)

        self.lbl_qual_text = QLabel("JPEG Qualität: 70%")
        vbox_set.addWidget(self.lbl_qual_text)
        self.slider_qual = QSlider(Qt.Orientation.Horizontal)
        self.slider_qual.setRange(10, 100)
        self.slider_qual.setValue(70)
        self.slider_qual.valueChanged.connect(self.on_quality_changed)
        vbox_set.addWidget(self.slider_qual)
        
        self.lbl_qual_hint = QLabel("Modus: Gute Balance")
        self.lbl_qual_hint.setStyleSheet("color: #00aa00; font-style: italic;")
        vbox_set.addWidget(self.lbl_qual_hint)
        
        group_settings.setLayout(vbox_set)
        control_layout.addWidget(group_settings)

        # 4. Hardware Gruppe
        group_hw = QGroupBox("Hardware & Status")
        vbox_hw = QVBoxLayout()
        
        hbox_port = QHBoxLayout()
        hbox_port.addWidget(QLabel("COM Port:"))
        default_port = "COM4" if sys.platform.startswith("win") else "/dev/tty.usbmodem1101"
        self.entry_port = QLineEdit(default_port)
        hbox_port.addWidget(self.entry_port)
        vbox_hw.addLayout(hbox_port)

        hbox_baud = QHBoxLayout()
        hbox_baud.addWidget(QLabel("Baudrate:"))
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.combo_baud.setCurrentText("38400")
        hbox_baud.addWidget(self.combo_baud)
        vbox_hw.addLayout(hbox_baud)
        
        self.lbl_size = QLabel("Geschätzte Übertragungsgröße: -- KB")
        self.lbl_size.setStyleSheet("font-weight: bold; margin-top: 10px;")
        vbox_hw.addWidget(self.lbl_size)

        self.btn_send = QPushButton("Senden starten")
        self.btn_send.clicked.connect(self.start_sending)
        self.btn_send.setEnabled(False)
        vbox_hw.addWidget(self.btn_send)

        self.btn_abort = QPushButton("Senden abbrechen")
        self.btn_abort.setEnabled(False)
        self.btn_abort.setStyleSheet("color: #ff5555; font-weight: bold;")
        self.btn_abort.clicked.connect(self.abort_sending)
        vbox_hw.addWidget(self.btn_abort)

        self.progress_bar = QProgressBar()
        vbox_hw.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("Bereit.")
        vbox_hw.addWidget(self.lbl_status)
        
        group_hw.setLayout(vbox_hw)
        control_layout.addWidget(group_hw)
        
        control_layout.addStretch()
        layout.addLayout(control_layout, 1)

        # --- RECHTE BILDVORSCHAU ---
        self.lbl_image = QLabel("Kein Bild geladen oder Kamera aus")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setStyleSheet("background-color: #222; color: white;")
        layout.addWidget(self.lbl_image, 3)

    # --- DIASHOW LOGIK ---
    def toggle_slideshow_mode(self, state):
        is_active = (state == Qt.CheckState.Checked.value)
        
        self.btn_folder.setEnabled(is_active)
        self.spin_delay.setEnabled(is_active)
        
        # Deaktiviere Einzelbild-Funktionen, wenn Diashow an ist
        self.btn_load.setEnabled(not is_active)
        self.btn_cam_toggle.setEnabled(not is_active)
        self.btn_capture.setEnabled(not is_active)
        
        # Sende-Button aktualisieren
        if is_active:
            self.btn_send.setEnabled(len(self.slideshow_files) > 0)
        else:
            self.btn_send.setEnabled(self.current_image is not None)

    def load_folder(self):
        folderpath = QFileDialog.getExistingDirectory(self, "Ordner mit Bildern auswählen")
        if folderpath:
            valid_exts = ('.png', '.jpg', '.jpeg', '.bmp')
            self.slideshow_files = [
                os.path.join(folderpath, f) for f in os.listdir(folderpath) 
                if f.lower().endswith(valid_exts)
            ]
            self.slideshow_files.sort() # Alphabetisch sortieren
            
            folder_name = os.path.basename(folderpath)
            self.lbl_folder.setText(f".../{folder_name} ({len(self.slideshow_files)} Bilder)")
            
            if self.slideshow_files:
                self.btn_send.setEnabled(True)
                # Lade das erste Bild als Vorschau
                self.load_image_from_path(self.slideshow_files[0])
            else:
                self.btn_send.setEnabled(False)

    def send_next_slideshow_image(self):
        if not self.slideshow_running: 
            return
            
        if self.slideshow_index < len(self.slideshow_files):
            filepath = self.slideshow_files[self.slideshow_index]
            self.lbl_status.setText(f"Lade Bild {self.slideshow_index + 1} von {len(self.slideshow_files)}...")
            
            if self.load_image_from_path(filepath):
                self.trigger_worker()
            else:
                # Falls das Bild defekt ist, überspringen und nächstes versuchen
                self.slideshow_index += 1
                self.send_next_slideshow_image()
        else:
            self.lbl_status.setText("Diashow abgeschlossen!")
            self.slideshow_running = False
            self.reset_buttons()

    # --- KAMERA LOGIK ---
    def toggle_camera(self):
        if self.cam_timer.isActive():
            self.cam_timer.stop()
            if self.camera:
                self.camera.release()
            self.btn_cam_toggle.setText("Kamera starten")
            self.btn_capture.setEnabled(False)
            self.lbl_image.setText("Kamera gestoppt")
        else:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QMessageBox.warning(self, "Fehler", "Kamera konnte nicht gefunden werden.")
                return
            
            self.btn_cam_toggle.setText("Kamera stoppen")
            self.btn_capture.setEnabled(True)
            self.btn_send.setEnabled(False) 
            self.cam_timer.start(30)

    def update_camera_frame(self):
        ret, frame = self.camera.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            # WICHTIG: .copy() verhindert Abstürze beim Speichermanagement
            q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
            pixmap = QPixmap.fromImage(q_img)
            self.lbl_image.setPixmap(pixmap.scaled(self.lbl_image.width(), self.lbl_image.height(), Qt.AspectRatioMode.KeepAspectRatio))

    def capture_photo(self):
        if not self.camera or not self.camera.isOpened(): return
        ret, frame = self.camera.read()
        if ret:
            self.toggle_camera() 
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.current_image = Image.fromarray(frame_rgb)
            self.update_preview()
            self.btn_send.setEnabled(True)

    # --- DATEI LOGIK ---
    def load_single_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Bild auswählen", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if filepath:
            if self.cam_timer.isActive():
                self.toggle_camera()
            if self.load_image_from_path(filepath):
                self.btn_send.setEnabled(True)

    def load_image_from_path(self, filepath):
        try:
            self.current_image = Image.open(filepath).convert('RGB')
            self.update_preview()
            return True
        except Exception as e:
            QMessageBox.warning(self, "Ladefehler", f"Fehler beim Laden von {filepath}:\n{e}")
            return False

    # --- GUI UPDATES ---
    def on_quality_changed(self, value):
        self.lbl_qual_text.setText(f"JPEG Qualität: {value}%")
        if value < 30:
            self.lbl_qual_hint.setText("Modus: Extrem schnell (Artefakte)")
            self.lbl_qual_hint.setStyleSheet("color: #ff5555; font-style: italic;")
        elif value < 60:
            self.lbl_qual_hint.setText("Modus: Schnelle Übertragung")
            self.lbl_qual_hint.setStyleSheet("color: #ffaa00; font-style: italic;")
        elif value < 85:
            self.lbl_qual_hint.setText("Modus: Gute Balance (Empfohlen)")
            self.lbl_qual_hint.setStyleSheet("color: #00aa00; font-style: italic;")
        else:
            self.lbl_qual_hint.setText("Modus: Hohe Details (Lange Dauer!)")
            self.lbl_qual_hint.setStyleSheet("color: #0055ff; font-style: italic;")
            
        self.calculate_estimated_size()

    def calculate_estimated_size(self):
        if not self.current_image: return
        buf = io.BytesIO()
        self.current_image.save(buf, format='JPEG', quality=self.slider_qual.value())
        size_bytes = len(buf.getvalue())
        estimated_transfer_size = size_bytes * 1.2 
        self.lbl_size.setText(f"Geschätzte Übertragungsgröße: {estimated_transfer_size / 1024:.1f} KB")

    def update_preview(self):
        """Aktualisiert die Bildvorschau und zeichnet das Kachel-Raster ein."""
        if not self.current_image: return
        self.calculate_estimated_size()

        width, height = self.current_image.size
        bytes_per_line = 3 * width # WICHTIG: Behebt den Alignment-Crash bei krummen Auflösungen
        
        # WICHTIG: .copy() erzwingt, dass PyQt den Speicher sichert. Sonst löscht Python den Buffer -> Crash!
        img_data = self.current_image.tobytes("raw", "RGB")
        q_img = QImage(img_data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()
        
        pixmap = QPixmap.fromImage(q_img)
        
        painter = QPainter(pixmap)
        pen = QPen(QColor(255, 0, 0, 150))
        pen.setWidth(2)
        painter.setPen(pen)
        ts = self.spin_tile.value()
        for x in range(0, pixmap.width(), ts):
            painter.drawLine(x, 0, x, pixmap.height())
        for y in range(0, pixmap.height(), ts):
            painter.drawLine(0, y, pixmap.width(), y)
        painter.end()

        # Vorschau-Bild runterskalieren, damit riesige Bilder die GUI nicht sprengen
        scaled_pixmap = pixmap.scaled(
            self.lbl_image.width(), 
            self.lbl_image.height(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_image.setPixmap(scaled_pixmap)


    # --- SENDE LOGIK ---
    def start_sending(self):
        if self.chk_slideshow.isChecked() and self.slideshow_files:
            self.slideshow_running = True
            self.slideshow_index = 0
            self.send_next_slideshow_image()
        else:
            self.slideshow_running = False
            self.trigger_worker()

    def trigger_worker(self):
        if not self.current_image: return

        self.btn_send.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self.btn_cam_toggle.setEnabled(False)
        self.btn_load.setEnabled(False)
        self.btn_folder.setEnabled(False)
        
        if self.slideshow_running:
            self.lbl_status.setText(f"Sende Bild {self.slideshow_index + 1} von {len(self.slideshow_files)}...")
        else:
            self.lbl_status.setText("Sende...")
            
        self.progress_bar.setValue(0)

        baudrate = int(self.combo_baud.currentText())
        self.worker = SenderWorker(self.current_image, self.spin_tile.value(), 
                                   self.slider_qual.value(), self.entry_port.text(), baudrate)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.worker_finished)
        self.worker.error.connect(self.send_error)
        self.worker.start()

    def abort_sending(self):
        self.slideshow_running = False 
        if self.worker and self.worker.isRunning():
            self.lbl_status.setText("Abbruch wird eingeleitet...")
            self.btn_abort.setEnabled(False)
            self.worker.stop()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def worker_finished(self):
        if self.worker and not self.worker.is_running:
            self.lbl_status.setText("Vorgang abgebrochen.")
            self.slideshow_running = False
            self.reset_buttons()
        else:
            if self.slideshow_running:
                self.slideshow_index += 1
                if self.slideshow_index < len(self.slideshow_files):
                    delay = self.spin_delay.value()
                    self.lbl_status.setText(f"Warte {delay} Sekunden bis zum nächsten Bild...")
                    QTimer.singleShot(delay * 1000, self.send_next_slideshow_image)
                else:
                    self.lbl_status.setText("Diashow abgeschlossen!")
                    self.slideshow_running = False
                    self.reset_buttons()
            else:
                self.lbl_status.setText("Erfolgreich gesendet!")
                self.reset_buttons()

    def send_error(self, msg):
        self.slideshow_running = False
        QMessageBox.critical(self, "Übertragungsfehler", msg)
        self.lbl_status.setText("Fehler aufgetreten.")
        self.reset_buttons()
        
    def reset_buttons(self):
        self.btn_abort.setEnabled(False)
        
        is_slide = self.chk_slideshow.isChecked()
        self.btn_folder.setEnabled(is_slide)
        self.btn_load.setEnabled(not is_slide)
        self.btn_cam_toggle.setEnabled(not is_slide)
        
        if is_slide:
            self.btn_send.setEnabled(len(self.slideshow_files) > 0)
        else:
            self.btn_send.setEnabled(self.current_image is not None)

    def closeEvent(self, event):
        if self.cam_timer.isActive():
            self.camera.release()
        if self.worker:
            self.worker.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SenderGUI()
    window.show()
    sys.exit(app.exec())
