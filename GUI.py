#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 16:57:07 2023

@author: Denis Tyutin
"""
import sys
import numpy as np
from datetime import datetime
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSettings
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import llt.utils.sin_params as sp

class ResizeDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ResizeDialog, self).__init__(parent)

        # Set window size
        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle("Resize")

        # Create widgets
        self.axis_x = QtWidgets.QWidget(self)
        # self.axis_x.setStyleSheet("background-color: #f2f2f2;")
        self.axis_y = QtWidgets.QWidget(self)
        # self.axis_y.setStyleSheet("background-color: #f2f2f2;")
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


        self.left_label = QtWidgets.QLabel("Left")
        self.right_label = QtWidgets.QLabel("Right")
        self.top_label = QtWidgets.QLabel("Top")
        self.bottom_label = QtWidgets.QLabel("Bottom")

        self.left_edit = QtWidgets.QLineEdit()
        self.right_edit = QtWidgets.QLineEdit()
        self.top_edit = QtWidgets.QLineEdit()
        self.bottom_edit = QtWidgets.QLineEdit()

        self.log_x = QtWidgets.QCheckBox("Log")
        self.log_y = QtWidgets.QCheckBox("Log")
        
        self.left_edit = QtWidgets.QLineEdit(str(parent.ax.get_xlim()[0]), self.axis_x)
        self.right_edit = QtWidgets.QLineEdit(str(parent.ax.get_xlim()[1]), self.axis_x)
        self.log_x.setChecked(parent.ax.get_xscale() == 'log')
        
        self.top_edit = QtWidgets.QLineEdit(str(parent.ax.get_ylim()[1]), self.axis_y)
        self.bottom_edit = QtWidgets.QLineEdit(str(parent.ax.get_ylim()[0]), self.axis_y)
        self.log_y.setChecked(parent.ax.get_yscale() == 'log')

        # Create main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.axis_x)
        main_layout.addWidget(self.axis_y)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Create axis X layout
        axis_x_layout = QtWidgets.QGridLayout()
        axis_x_layout.addWidget(QtWidgets.QLabel("Axis X"), 0, 0)
        axis_x_layout.addWidget(self.left_label, 1, 0)
        axis_x_layout.addWidget(self.left_edit, 1, 1)
        axis_x_layout.addWidget(self.right_label, 1, 2)
        axis_x_layout.addWidget(self.right_edit, 1, 3)
        axis_x_layout.addWidget(self.log_x, 2, 1)
        axis_x_layout.setColumnStretch(1, 1)
        axis_x_layout.setColumnStretch(3, 1)
        self.axis_x.setLayout(axis_x_layout)

        # Create axis Y layout
        axis_y_layout = QtWidgets.QGridLayout()
        axis_y_layout.addWidget(QtWidgets.QLabel("Axis Y"), 0, 0)
        axis_y_layout.addWidget(self.bottom_label, 1, 0)
        axis_y_layout.addWidget(self.bottom_edit, 1, 1)
        axis_y_layout.addWidget(self.top_label, 1, 2)
        axis_y_layout.addWidget(self.top_edit, 1, 3)
        axis_y_layout.addWidget(self.log_y, 2, 1)
        axis_y_layout.setColumnStretch(1, 1)
        axis_y_layout.setColumnStretch(3, 1)
        self.axis_y.setLayout(axis_y_layout)        

    def get_axis_data(self):

        return (self.left_edit.text(), 
                self.right_edit.text(), 
                self.top_edit.text(), 
                self.bottom_edit.text(), 
                self.log_x.isChecked(), 
                self.log_y.isChecked()
                )
    
        # Set initial position and size
        self.resize(400, 300)
        self.move(100, 100)
    
    def closeEvent(self, event):
        # Save position and size on close
        self.parent().settings.setValue("resize_dialog_geometry", self.saveGeometry())

    def showEvent(self, event):
        # Restore position and size on show
        if self.parent().settings.contains("resize_dialog_geometry"):
            self.restoreGeometry(self.parent().settings.value("resize_dialog_geometry"))

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window size
        self.setGeometry(100, 100, 1200, 800)
        self.settings = QSettings()

        # Create widgets
        panel = QtWidgets.QWidget(self, minimumWidth=260, maximumWidth=260)
        plot = QtWidgets.QWidget(self)
        status = QtWidgets.QWidget(self)

        # Create plot widget
        self.fig = Figure(figsize=(8, 5.5))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xscale('log')
        self.ax.set_yscale('linear')
        self.ax.set_xlim(1, 100000)
        self.ax.set_ylim(-160, 20)
        self.ax.set_xlabel('Frequency, Hz')
        self.ax.set_ylabel('Amplitude, dB')
        self.ax.grid(which='both', ls='--')
        self.canvas = FigureCanvas(self.fig)

        # Create status widget
        status_layout = QtWidgets.QGridLayout()
        # self.status_text = QtWidgets.QTextEdit()
        # self.status_text.setReadOnly(True)
        # status_layout.addWidget(self.status_text)
        status.setLayout(status_layout)

        # Create panel widget
        panel_layout = QtWidgets.QVBoxLayout()
        panel.setLayout(panel_layout)
        panel_layout.addWidget(QtWidgets.QLabel("Set Label"))
        
        # Create Display widget and add it to the panel widget
        self.display = QtWidgets.QGridLayout()
        self.display_font = QtGui.QFont()
        self.display_font.setPointSize(9)
        
        self.channel_display = []
        self.params_display = []
        self.harmonics_display = []
        
        self.setup_thd_display()
        
        panel_layout.addLayout(self.display)
        
        # Create QtWidgets.QLineEdit widget for Msps
        self.msps = QtWidgets.QLineEdit("1")
        
        # Create QtWidgets.QComboBox widget for Size
        self.num_samples = QtWidgets.QComboBox()
        self.num_samples.addItem("1024")
        self.num_samples.addItem("2048")
        self.num_samples.addItem("4096")
        self.num_samples.addItem("8192")
        self.num_samples.addItem("16384")
        self.num_samples.addItem("32768")
        self.num_samples.addItem("65536")
        self.num_samples.addItem("131072")
        self.num_samples.setCurrentIndex(6)
        
        # Create QtWidgets.QComboBox widget for Window
        self.window_combo_box = QtWidgets.QComboBox()
        self.window_combo_box.addItem("No Windowing")
        self.window_combo_box.addItem("Hamming")
        self.window_combo_box.addItem("Hann")
        self.window_combo_box.addItem("Blackman")
        self.window_combo_box.addItem("Exact Blackman")
        self.window_combo_box.addItem("Blackman-Harris 70dB")
        self.window_combo_box.addItem("Blackman-Harris 92dB")
        self.window_combo_box.addItem("Flat Top")
        self.window_combo_box.setCurrentIndex(6)
        
        # Create QtWidgets.QCheckBox widgets for Repeat and ADC Full Scale
        repeat_checkbox = QtWidgets.QCheckBox("Repeat")
        repeat_checkbox.setCheckState(Qt.Checked)
        adc_full_scale_checkbox = QtWidgets.QCheckBox("ADC Full Scale")
        adc_full_scale_checkbox.setCheckState(Qt.Checked)
        
        # Create a sub-layout for the Msps and Size widgets
        msps_size_layout = QtWidgets.QHBoxLayout()
        msps_size_layout.addWidget(QtWidgets.QLabel("Msps:"))
        msps_size_layout.addWidget(self.msps)
        msps_size_layout.addWidget(QtWidgets.QLabel("Size:"))
        msps_size_layout.addWidget(self.num_samples)
        panel_layout.addLayout(msps_size_layout)
        
        # Add the Window widget to the panel layout
        window_combo_box_layout = QtWidgets.QHBoxLayout()
        window_combo_box_layout.addWidget(QtWidgets.QLabel("Window:"),alignment=Qt.AlignRight)
        window_combo_box_layout.addWidget(self.window_combo_box,alignment=Qt.AlignRight)
        panel_layout.addLayout(window_combo_box_layout)
        
        # Add the Repeat and ADC Full Scale checkboxes to the panel layout
        panel_layout.addWidget(repeat_checkbox)
        panel_layout.addWidget(adc_full_scale_checkbox)
        
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.status_font = QtGui.QFont()
        self.status_font.setPointSize(9)
        self.status_text.setFont(self.status_font)
        self.status_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.status_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.status_text.setReadOnly(True)
        panel_layout.addWidget(QtWidgets.QLabel("Status Messages"))
        panel_layout.addWidget(self.status_text)
        
        # Create the Start button and add it to the panel widget
        self.start_button = QtWidgets.QPushButton("Start", panel)
        self.start_button.setStyleSheet("background-color: palegreen")
        self.start_button.clicked.connect(self.start_button_clicked)
        panel_layout.addWidget(self.start_button)
        
        panel_layout.setSpacing(10)

        # Create main layout
        main_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        plot_status_splitter = QtWidgets.QSplitter(Qt.Vertical)
        main_splitter.addWidget(panel)
        main_splitter.addWidget(plot_status_splitter)
        plot_status_splitter.addWidget(plot)
        plot_status_splitter.addWidget(status)

        # Set layout and add plot canvas to plot widget
        main_layout = QtWidgets.QGridLayout()
        main_layout.addWidget(main_splitter, 0, 0)
        plot.setLayout(QtWidgets.QGridLayout())
        plot.layout().setSpacing(10)
        plot.layout().addWidget(self.canvas)
        self.setCentralWidget(QtWidgets.QWidget(self))
        self.centralWidget().setLayout(main_layout)
        
 
        panel_layout.setSpacing(10)
        
        # Add context menu to the plot
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self.show_context_menu)
    
    def setup_thd_display(self):
        num_rows = 16
        num_col = 4
        
        # Defining label names
        ch_labels = []
        ch_labels.append(QtWidgets.QLabel("Channel 1"))
        ch_labels[0].setStyleSheet("background-color: grey; color: white;")
        ch_labels.append(QtWidgets.QLabel("fs"))
        ch_labels.append(QtWidgets.QLabel("F1"))
        ch_labels.append(QtWidgets.QLabel("Bin Width"))
        ch_labels.append(QtWidgets.QLabel("F1 Frequency"))
        ch_labels.append(QtWidgets.QLabel("F1 Amplitude"))
        
        param_labels = []
        param_labels.append(QtWidgets.QLabel("Parameters"))
        param_labels[0].setStyleSheet("background-color: grey; color: white;")
        param_labels.append(QtWidgets.QLabel("SNR"))
        param_labels.append(QtWidgets.QLabel("SINAD"))
        param_labels.append(QtWidgets.QLabel("THD"))
        param_labels.append(QtWidgets.QLabel("SFDR"))
        param_labels.append(QtWidgets.QLabel("ENOB"))
        param_labels.append(QtWidgets.QLabel("Maxcode"))
        param_labels.append(QtWidgets.QLabel("Mincode"))
        param_labels.append(QtWidgets.QLabel("DCLev"))
        param_labels.append(QtWidgets.QLabel("Flor"))
        
        harm_labels = []
        harm_labels.append(QtWidgets.QLabel("Harmonics"))
        harm_labels[0].setStyleSheet("background-color: grey; color: white;")
        for i in range(2,10,1):
            harm_labels.append(QtWidgets.QLabel("F{}".format(i)))
        harm_labels.append(QtWidgets.QLabel("Nyq"))
        
        ch_layout = self._line_assembler(ch_labels,self.channel_display)
        param_layout = self._line_assembler(param_labels,self.params_display)
        harm_layout = self._line_assembler(harm_labels,self.harmonics_display)
        
        for i,ch in enumerate(ch_layout):
            self.display.addLayout(ch,i,0,1,0)
        
        # Add QtWidgets.QPlainTextEdit widgets to the params box
        for i,param in enumerate(param_layout):
            self.display.addLayout(param,i+len(ch_layout),0)
        
        # Add QtWidgets.QPlainTextEdit widgets to the harmonics box
        for i,harm in enumerate(harm_layout):
            self.display.addLayout(harm,i+len(ch_layout),1)
            
    def _line_assembler(self,label_array,line_array):
        out = []
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        
        for i,label in enumerate(label_array):
            layout = QtWidgets.QGridLayout()
            layout.setSpacing(1)
            line_array.append(QtWidgets.QLabel(""))
            line_array[i].setFont(self.display_font)
            label.setFont(self.display_font)
            layout.addWidget(label,0,0)
            layout.addWidget(line_array[i],0,1)
            layout.addWidget(line,1,0)
            out.append(layout)
        return out
    
    def start_button_clicked(self):
        if self.start_button.text() == "Start":
            self.append_status_message("Starting collection...")
            self.start_button.setText("Collecting...")
            self.start_button.setStyleSheet("background-color: palevioletred")
            self.collect()
            self.start_button.setText("Start")
            self.start_button.setStyleSheet("background-color: palegreen")
    
    def collect(self):
        mean = 0.0
        std = 0.001
        num_samples = int(self.num_samples.currentText())
        fs = float(self.msps.text()) * 1e6

        noise = np.random.normal(mean,std,size=num_samples)

        time = np.linspace(0, num_samples/fs, num_samples)
        freqs = np.linspace(0, fs//2, num_samples//2+1)
        fund_freq = 1.0e3
        amplitude = 1.0

        sin = amplitude * np.sin( 2 * np.pi * fund_freq * time )

        #dataplot(data,xscale='lin')

        fft_data = sp.windowed_fft_mag(noise+sin,window_type=0x30)
        db_fft_data = 20 * np.log10(fft_data * np.sqrt(2.0) / 1.0)
        
        self.ax.plot(freqs,db_fft_data)
        
        # Update the canvas
        self.canvas.draw()
        
        # self.display_data()
        
        # Update the status text
        self.append_status_message("Data collection completed.")
    
    def show_context_menu(self, pos):
        # Create context menu and add options
        menu = QtWidgets.QMenu(self.canvas)
        resize_action = menu.addAction("Resize")
        autoscale_submenu = QtWidgets.QMenu("Autoscale",self.canvas)
        autoscale_x = autoscale_submenu.addAction("Asis X")
        autoscale_y = autoscale_submenu.addAction("Asis Y")
        autoscale_both = autoscale_submenu.addAction("Both")
        menu.addMenu(autoscale_submenu)
        # zoom_out_action = menu.addAction("Zoom Out")
        # zoom_fit_action = menu.addAction("Zoom to Fit")
        # save_action = menu.addAction("Save to File")
    
        # Get the position of the mouse and show the context menu
        action = menu.exec_(self.canvas.mapToGlobal(pos))
    
        # Perform the action based on the user's selection
        if action == resize_action:
            self.resize()
        elif action == autoscale_x:
            self.ax.autoscale_view(scalex=True,scaley=False)
            self.append_status_message("Autoscale X")
        elif action == autoscale_y:
            self.ax.autoscale_view(scalex=False,scaley=True)
            self.append_status_message("Autoscale Y")
        elif action == autoscale_both:
            self.ax.autoscale_view(scalex=True,scaley=True)
            self.append_status_message("Autoscale both")
        self.canvas.draw()
    
    def resize(self):
        dialog = ResizeDialog(self)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            left, right, top, bottom, log_x, log_y = dialog.get_axis_data()
            try:
                self.ax.set_xlim(float(left), float(right))
            except ValueError:
                pass
            try: 
                self.ax.set_ylim(float(bottom), float(top))
            except ValueError:
                pass
            self.ax.set_xscale('log' if log_x else 'linear')
            self.ax.set_yscale('log' if log_y else 'linear')
            self.canvas.draw()
        dialog.close()
        
    def append_status_message(self,message):
        self.status_text.insertPlainText(datetime.now().isoformat() + ": " + message + "\n")
        cursor = self.status_text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Start)
        self.status_text.setTextCursor(cursor)

    def display_data(self):
        # Add labels to the channel box
        for i in range(5):
            self.channel_display[i+1].setText(f"Channel {i+2}")
        
        # Add QtWidgets.QPlainTextEdit widgets to the params box
        for i in range(9):
            self.params_display[i+1].setText(f"Param {i+2}")
        
        # Add QtWidgets.QPlainTextEdit widgets to the harmonics box
        for i in range(9):
            self.harmonics_display[i+1].setText(f"Harmonic {i+2}")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())






