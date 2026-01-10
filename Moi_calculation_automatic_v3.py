#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 2023

@author: basstijnen
"""

from datetime import datetime
import os
import sys
import time

from functions_MoI_rig2 import Find_Moment_Of_Inertia, print_tau
from track_marker_moi import track_all, no_audio, output_file_generation

import numpy as np
import matplotlib
matplotlib.use("QtAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPlainTextEdit
)


class MoIWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MoI Rig SW interface")
        self.canvas = None
        self.output_buffer = ""

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        input_layout = QGridLayout()
        output_layout = QVBoxLayout()

        main_layout.addLayout(input_layout)
        main_layout.addLayout(output_layout)

        # ---- Input widgets ----
        row = 0

        def add_row(label, widget):
            nonlocal row
            input_layout.addWidget(QLabel(label), row, 0)
            input_layout.addWidget(widget, row, 1)
            row += 1

        self.input_path = QLineEdit()
        browse_input = QPushButton("Browse")
        browse_input.clicked.connect(self.browse_input)

        input_layout.addWidget(QLabel("Input video:"), row, 0)
        input_layout.addWidget(self.input_path, row, 1)
        input_layout.addWidget(browse_input, row, 2)
        row += 1

        self.output_path = QLineEdit()
        browse_output = QPushButton("Browse")
        browse_output.clicked.connect(self.browse_output)

        input_layout.addWidget(QLabel("Output path:"), row, 0)
        input_layout.addWidget(self.output_path, row, 1)
        input_layout.addWidget(browse_output, row, 2)
        row += 1

        self.mass = QLineEdit()
        add_row("Mass (g):", self.mass)

        self.fps = QLineEdit("50")
        add_row("FPS:", self.fps)

        self.R = QLineEdit("225")
        add_row("Radius (mm):", self.R)

        self.L = QLineEdit("1250")
        add_row("Cable length (mm):", self.L)

        self.centre_order = QLineEdit("5")
        add_row("Centre dot order:", self.centre_order)

        self.outer_order = QLineEdit("4")
        add_row("Outer dot order:", self.outer_order)

        self.kernel = QLineEdit("80")
        add_row("Kernel size:", self.kernel)

        process_btn = QPushButton("Process")
        process_btn.clicked.connect(self.process_data)
        input_layout.addWidget(process_btn, row, 0, 1, 3)
        row += 1

        # ---- Output widgets ----
        self.text_output = QPlainTextEdit()
        self.text_output.setReadOnly(True)
        output_layout.addWidget(self.text_output)

        self.I_label = QLabel("I:")
        self.Tau_label = QLabel("Tau:")
        self.angle_label = QLabel("Angle:")

        output_layout.addWidget(self.I_label)
        output_layout.addWidget(self.Tau_label)
        output_layout.addWidget(self.angle_label)

        self.fig = Figure(figsize=(6, 4))
        self.canvas = FigureCanvasQTAgg(self.fig)
        output_layout.addWidget(self.canvas)

        info_btn = QPushButton("Info")
        info_btn.clicked.connect(self.show_info)
        output_layout.addWidget(info_btn)

    # ---------- Utility ----------
    def log(self, text):
        self.output_buffer += text + "\n"
        self.text_output.setPlainText(self.output_buffer)
        self.text_output.verticalScrollBar().setValue(
            self.text_output.verticalScrollBar().maximum()
        )

    # ---------- Dialogs ----------
    def browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select video", "", "Video Files (*.mp4)")
        if path:
            self.input_path.setText(path)

    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select output directory")
        if path:
            self.output_path.setText(path)

    def show_info(self):
        QMessageBox.information(
            self,
            "Software info",
            "Mass Moment of Inertia calculator\n"
            "Trifilar Pendulum project\n"
            "License: CC BY 4.0\n"
            "UCD School of Engineering"
        )

    # ---------- Core processing ----------
    def process_data(self):
        try:
            m = float(self.mass.text())
            fps = float(self.fps.text())
            R = float(self.R.text())
            L = float(self.L.text())
            order1 = int(self.centre_order.text())
            order2 = int(self.outer_order.text())
            kernel = int(self.kernel.text())
        except ValueError:
            QMessageBox.warning(self, "Input error", "Invalid numeric input.")
            return

        input_path = self.input_path.text()
        output_base = self.output_path.text()

        if not input_path or not output_base:
            QMessageBox.warning(self, "Input error", "Please select input and output paths.")
            return

        output_path = os.path.join(output_base, datetime.now().strftime('%Y%m%d%H%M'))
        os.mkdir(output_path)

        self.log("Removing audio...")
        cap = no_audio(input_path, output_path)

        output_file_generation()

        self.log("Tracking markers...")
        track_all(cap, order1, order2, kernel)

        time.sleep(1)

        self.log("Calculating MoI...")
        I, frame, angle = Find_Moment_Of_Inertia(output_path, fps, m, R, L)
        Tau = print_tau(output_path, fps)

        self.I_label.setText(f"I: {I}")
        self.Tau_label.setText(f"Tau: {Tau}")
        self.angle_label.setText(f"Angle: {angle}")

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.plot(frame["frame_num"], frame["polar_12"])
        ax.set_xlabel("time [s]")
        ax.set_ylabel("rotation [rad]")
        self.canvas.draw()

        self.log("Done.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MoIWindow()
    window.resize(1100, 600)
    window.show()
    sys.exit(app.exec())
