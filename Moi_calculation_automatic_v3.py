#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
updated 2026

@author: basstijnen
"""

from datetime import datetime
import os
import time

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QTextEdit, QVBoxLayout, QHBoxLayout,
    QMessageBox, QGroupBox, QCheckBox, QProgressBar
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from functions_MoI_rig2 import Find_Moment_Of_Inertia, print_tau, calculate_expected_error
from track_marker_moi import track_all, no_audio, output_file_generation, frame_count


class MoIApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MoI Rig SW interface")

        self.canvas = None
        self.output_buffer = ""
        self.platform_moi = None  # stored in kg·m² internally
        self.init_ui()

    # ---------------- UI ---------------- #

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        input_box = QGroupBox("Input")
        output_box = QGroupBox("Output")

        main_layout.addWidget(input_box)
        main_layout.addWidget(output_box)

        input_layout = QVBoxLayout()
        output_layout = QVBoxLayout()

        input_box.setLayout(input_layout)
        output_box.setLayout(output_layout)

        # ---- File inputs ----
        self.input_path = QLineEdit()
        btn_in = QPushButton("Browse video")
        btn_in.clicked.connect(self.browse_input)

        self.output_path = QLineEdit()
        btn_out = QPushButton("Browse output")
        btn_out.clicked.connect(self.browse_output)

        input_layout.addWidget(QLabel("Input video"))
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(btn_in)

        input_layout.addWidget(QLabel("Output folder"))
        input_layout.addWidget(self.output_path)
        input_layout.addWidget(btn_out)
        self.calibration_toggle = QCheckBox("Calibration mode (platform only)")
        self.calibration_toggle.setChecked(True)
        input_layout.addWidget(self.calibration_toggle)


        # ---- Parameters ----
        self.mass_table = self.add_entry(input_layout, "Mass of table (g)")
        self.mass_object = self.add_entry(input_layout, "Mass of object (g)", "0")
        self.fps = self.add_entry(input_layout, "Frame rate (fps)", "50")
        self.R = self.add_entry(input_layout, "Radius (mm)", "225")
        self.L = self.add_entry(input_layout, "Cable length (mm)", "1250")
        self.centre_marker = self.add_entry(input_layout, "Centre marker veins", "5")
        self.outer_marker = self.add_entry(input_layout, "Outer marker veins", "4")
        self.kernel = self.add_entry(input_layout, "Marker size", "80")

        # ---- Buttons ----
        btn_process = QPushButton("Process")
        btn_process.clicked.connect(self.process_data)
        input_layout.addWidget(btn_process)

        # ---- Output labels ----
        self.I_label = QLabel("Object MoI kg·m²:")
        self.Tau_label = QLabel("Tau sec:")
        self.angle_label = QLabel("Angle deg:")
        self.error_label = QLabel("Expected MoI error %: ")
        self.platform_label = QLabel("Platform MoI [kg·m²]: not calibrated")

        output_layout.addWidget(self.platform_label)
        output_layout.addWidget(self.I_label)
        output_layout.addWidget(self.Tau_label)
        output_layout.addWidget(self.angle_label)
        output_layout.addWidget(self.error_label)

        # ---- Matplotlib canvas ----
        self.fig = plt.figure(figsize=(6, 4), dpi=80)
        self.canvas = FigureCanvas(self.fig)
        output_layout.addWidget(self.canvas)

        # ---- Progress Bar ----
        self.progress = QProgressBar()
        self.progress.setRange(0,100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        output_layout.addWidget(self.progress)

        # ---- Log output ----
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        output_layout.addWidget(self.log)

        # ---- Info button ----
        btn_info = QPushButton("Info")
        btn_info.clicked.connect(self.show_info)
        output_layout.addWidget(btn_info)

        self.calibration_toggle.stateChanged.connect(self.update_mode_ui)
        self.update_mode_ui()



    def update_mode_ui(self):
        is_calibration = self.calibration_toggle.isChecked()

    def set_progress(self, value: int, message: str):
        self.progress.setValue(value)
        if message:
            self.log_msg(message)
        QApplication.processEvents()

    def add_entry(self, layout, label, default=""):
        layout.addWidget(QLabel(label))
        entry = QLineEdit()
        entry.setText(default)
        layout.addWidget(entry)
        return entry

    # ---------------- Actions ---------------- #

    def log_msg(self, msg):
        self.output_buffer += msg + "\n"
        self.log.setText(self.output_buffer)
        self.log.verticalScrollBar().setValue(
            self.log.verticalScrollBar().maximum()
        )
        QApplication.processEvents()

    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select video", "", "Video files (*.mp4)"
        )
        if path:
            self.input_path.setText(path)

    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select output directory")
        if path:
            self.output_path.setText(path)

    def show_info(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Software info and licence")

        text = (
            "This software calculates the Mass Moment of Inertia.\n\n"
            "Complementary to Trifilar Pendulum project\n"
            "DOI: 10.17632/zww548rfbn.3\n\n"
            "Licensed under CC BY 4.0\n"
            "Developed at UCD School of Engineering"
        )
        msg.setText(text)

        pix = QPixmap("UCD_logo.png")
        if not pix.isNull():
            msg.setIconPixmap(pix.scaledToWidth(120, Qt.TransformationMode.SmoothTransformation))

        msg.exec()
    def show_calibration_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Calibration mode")
        msg.setIcon(QMessageBox.Icon.Warning)

        msg.setText("You are in calibration mode!")
        msg.setInformativeText(
            "Choose how this calibration run should be handled."
        )

        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        append_btn = msg.addButton(
            "Append and average calibration",
            QMessageBox.ButtonRole.ActionRole
        )
        overwrite_btn = msg.addButton(
            "Overwrite current calibration",
            QMessageBox.ButtonRole.DestructiveRole
        )

        msg.exec()

        clicked = msg.clickedButton()

        if clicked == cancel_btn:
            return "cancel"
        elif clicked == append_btn:
            return "append"
        elif clicked == overwrite_btn:
            return "overwrite"
        else:
            return "cancel"

    

    def process_data(self):
     
        # ---------- Read mode ----------
        is_calibration = self.calibration_toggle.isChecked()

        # ---------- Calibration dialog ----------
        if is_calibration:
            calibration_decision = self.show_calibration_dialog()
            if calibration_decision == "cancel":
                self.log_msg("Calibration cancelled by user.")
                return
        else:
            calibration_decision = None

            # ---------- Read inputs ----------
        try:
            m = float(self.mass_table.text()) + float(self.mass_object.text())  # g
            fps = float(self.fps.text())
            R = float(self.R.text())  # mm
            L = float(self.L.text())  # mm

            order1 = int(self.centre_marker.text())
            order2 = int(self.outer_marker.text())
            kernel = int(self.kernel.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid numeric input")
            return

        in_path = self.input_path.text()
        out_root = self.output_path.text()

        if not in_path or not out_root:
            QMessageBox.warning(self, "Error", "Select input and output paths")
            return

        # small helper function for keeping track of progress
        total_frames = frame_count(in_path)

        def tracking_progress(frame_idx):
            percent = 15 + int(35 * frame_idx / total_frames)  # 15 → 65
            self.progress.setValue(percent)
            QApplication.processEvents()



            # ---------- Processing ----------
        self.progress.setValue(0)
        self.log_msg("Starting process...")

        out_path = out_root + datetime.now().strftime("%Y%m%d%H%M")
        os.mkdir(out_path)
    
        self.set_progress(5, "Removing audio")
        cap = no_audio(in_path, out_path)

        self.set_progress(10, "Generating CSV files")
        output_file_generation()

        self.set_progress(15, "Tracking markers")
        total_frames = frame_count(in_path)
        track_all(cap, order1, order2, kernel, progress_cb=tracking_progress)

        time.sleep(1)

        self.set_progress(65, "Calculating MoI")
        I_total, frame, angle = Find_Moment_Of_Inertia(out_path, fps, m, R, L)
        self.set_progress(80, "Calculating period")
        Tau = print_tau(out_path, fps)

            # Convert once, consistently
        I_total_kgm2 = I_total / 1e6  # mm²·g → kg·m²
        self.set_progress(90, "Updating plots and results")
            # ---------- CALIBRATION ----------
        if is_calibration:
            if self.platform_moi is None:
                self.platform_moi = I_total_kgm2
                self.log_msg("Platform MoI stored (first calibration)")

            elif calibration_decision == "append":
                self.platform_moi = 0.5 * (self.platform_moi + I_total_kgm2)
                self.log_msg("Platform MoI updated (running average)")

            elif calibration_decision == "overwrite":
                self.platform_moi = I_total_kgm2
                self.log_msg("Platform MoI overwritten")

            self.platform_label.setText(f"Platform MoI kg·m²:{self.platform_moi:.2f}")
            self.Tau_label.setText(f"Tau: {Tau:.2f}")
            self.angle_label.setText(f"Angle: {angle:.2f}")
            self.error_label.setText("Expected MoI error [%]: —")

                # ---------- Plot ----------
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.plot(frame["frame_num"], frame["polar_12"])
            ax.set_xlabel("time [s]")
            ax.set_ylabel("rotation [rad]")
            self.canvas.draw()



            self.set_progress(100, "Calibration finished")
            return

        # ---------- MEASUREMENT ----------
        if self.platform_moi is None:
            QMessageBox.warning(
                self,
                "No calibration",
                "Please perform a calibration before measuring."
            )
            return

        I_object = I_total_kgm2 - self.platform_moi

        expected_error = calculate_expected_error(
            I_object=I_object,
            MoI_platform=self.platform_moi,
            L=L / 1000,
            R=R / 1000,
            m=m / 1000
        )

        self.I_label.setText(f"Object MoI: {I_object:.2f} kg·m²")
        self.Tau_label.setText(f"Tau: {Tau:.2f}")
        self.angle_label.setText(f"Angle: {angle:.2f}")
        self.error_label.setText(
            f"Expected MoI error [%]: {expected_error * 100:.2f}"
        )

        # ---------- Plot ----------
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.plot(frame["frame_num"], frame["polar_12"])
        ax.set_xlabel("time [s]")
        ax.set_ylabel("rotation [rad]")
        self.canvas.draw()

        self.log_msg("Measurement complete")

        self.set_progress(100, "Done!")


# ---------------- Entry point ---------------- #

if __name__ == "__main__":
    app = QApplication([])

    app.setStyleSheet("""
    QWidget {
        background-color: #121212;
        color: #e0e0e0;
        font-size: 12px;
    }
    QLineEdit, QTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #444;
        padding: 4px;
    }
    QPushButton {
        background-color: #2d89ef;
        color: white;
        padding: 6px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #1b5fa7;
    }
    QGroupBox {
        border: 1px solid #444;
        margin-top: 6px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px;
    }
    """)

    window = MoIApp()
    window.resize(1100, 600)
    window.show()
    app.exec()

