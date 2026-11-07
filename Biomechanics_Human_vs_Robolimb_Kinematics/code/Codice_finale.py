# Import delle librerire 
from ctypes.wintypes import RGB

import pip

from PyQt6 import uic, QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow
import matplotlib.pyplot as plt
import math
import cv2
import numpy as np
from filterpy.kalman import KalmanFilter
import pyqtgraph as pg
import socket
import os
import sys
import csv
import json
import time
from datetime import datetime
from pathlib import Path

class Trace:
    def __init__(self, name,u,v):

        # Setup attributi riguardanti la bounding box
        self.name = name
        self.x = u # Posizione del centroide lungo x

        self.y = v # Posizione del centroide lungo y 

        self.id = [] # ID della traccia 

        self.traj_x = [] # Buffer posizioni lungo x

        self.traj_y = [] # Buffer posizioni lungo y

        self.w = [] # Larghezza della bounding box

        self.h = [] # Altezza della bounding box

        # Visible count
        self.not_visible_count = 0
        '''
        Inizializzazione del Filtro di Kalman

        '''
        self.traj_x_filt = [] # Buffer posizioni filtrate lungo x

        self.traj_y_filt = [] # Buffer posizioni filtrate lungo y

        self.vel_x_filt = []  # Buffer velocità filtrate lungo x
        self.vel_y_filt = []  # Buffer velocità filtrate lungo y

        self.delta_t = 0.033 # Frequenza aggiornamento della webcam 

        self.Kalman = KalmanFilter (dim_x=4, dim_z=2)

        self.Kalman.x = np.array([[u], # Poisizione lungo x
                                [v],   # Posizione lungo  y
                                [0.],  # Velocità lungo x
                                [0.]]) # Velocità lungo y
        

        # Definisco la matrice di state extrapolation
        self.Kalman.F = np.array([
            [1,     0,      self.delta_t,     0      ],
            [0,     1,           0,      self.delta_t],
            [0,     0,           1,          0       ],
            [0,     0,           0,          1       ],
        ])

        # Definisco la matrice di osservazione
        self.Kalman.H = np.array([
                [1,     0,     0,     0],
                [0,     1,     0,     0],
                                        ])
        
        self.Kalman.P *= 1e-8  # Incertezza della stima
        self.Kalman.Q *= 1e8   # Rumore di processo
        self.Kalman.R *=10     # Rumore della misura
        

        # Attributo per il Labelling
        self.name_setted = False

        

    def update_centroid(self,x,y,w,h): # Metodo che aggiorna le posizioni grezze e filtrate dei centroidi 
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.traj_x.append(x+w/2)
        self.traj_y.append(y+h/2)


        # Contatore unvisible count
        self.not_visible_count = 0

        #                                               PREDICO LA NUOVA POSIZIONE DELLE TRACCE

        # Applico Kalman 
        self.Kalman.predict()
        self.Kalman.update(np.array([[x+w/2],
                                      [y+h/2]]))
        self.traj_x_filt.append(self.Kalman.x_post[0,0])
        self.traj_y_filt.append(self.Kalman.x_post[1,0])
        self.vel_x_filt.append(self.Kalman.x_post[2,0]) # Stato 2 è la velocità vx
        self.vel_y_filt.append(self.Kalman.x_post[3,0]) # Stato 3 è la velocità vy

    def update_not_visible(self):
        # Contatore unvisible count
        self.not_visible_count = self.not_visible_count+1

    # Metodo per il labelling 
    def set_name(self,label_name):
        '''
            Questa funzione permette di modificare il nome associato alla traccia e porre a True 'self.name_setted'
            self.name_setted --> indica se il nome della traccia è stato cambiato o no 
        '''
        self.name = label_name
        self.name_setted = True 


    
# Creiamo la classe GUI
class My_GUI(QMainWindow):

    def _promote_frame_to_plotwidget(self, frame, widget_class):
        """Inserisce un widget pyqtgraph dentro un QFrame della GUI.

        Serve perché nel file .ui plot_frame, plot_frame_2 e plot_frame_3
        sono QFrame, ma il codice originale li usa come grafici pyqtgraph.in realtà si può rendere più carino e si puo fare
        con html direttamente dalla gui promuovendo i plotframe
        """
        if isinstance(frame, widget_class):
            return frame

        layout = frame.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(frame)
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            while layout.count():
                item = layout.takeAt(0)
                child = item.widget()
                if child is not None:
                    child.setParent(None)

        plot_widget = widget_class(frame)
        layout.addWidget(plot_widget)
        return plot_widget

    def _read_widget_text(self, widget):
        """Legge testo sia da QTextEdit sia da QLineEdit.L'ho aggiunto perchè sto down de programma non lo leggeva"""
        if hasattr(widget, "toPlainText"):
            return widget.toPlainText().strip()
        if hasattr(widget, "text"):
            return widget.text().strip()
        return ""

    # Costruttore della classe GUI e Setup dei Tasti
    def __init__(self,MainWindow):      
        super().__init__() # Consente alla classe figli di invocare il costruttore della classe padre 
        uic.loadUi("gui_finale_prese.ui", self)

        if hasattr(self, "checkBox_LIBERA") and hasattr(self, "checkBox_BIDIGITALE"):
            # Imposta "LIBERA" come attiva di default per evitare lo stato vuoto
            self.checkBox_LIBERA.setChecked(True)
            self.checkBox_BIDIGITALE.setChecked(False)

            # Collega i click ai metodi di controllo della mutua esclusività
            self.checkBox_LIBERA.clicked.connect(self.exclusive_libera)
            self.checkBox_BIDIGITALE.clicked.connect(self.exclusive_bidigitale)
    
        if not hasattr(self, "Trace_name_textbox") and hasattr(self, "lineedit_joint_name"):
            self.Trace_name_textbox = self.lineedit_joint_name

        
        if not hasattr(self, "Image_name_textbox"):
            self.Image_name_textbox = QtWidgets.QLineEdit(self)
            self.Image_name_textbox.hide()

        # Nella tua gui non c'è Skin_checkbox: per non riscrivere tutta la logica
        # creo una checkbox nascosta sempre non selezionata.
        if not hasattr(self, "Skin_checkbox"):
            self.Skin_checkbox = QtWidgets.QCheckBox(self)
            self.Skin_checkbox.hide()

        # qui facciamo la promozione dei plotframe altrimenti per come erano stati implementati non andava(vedi commento sopra)
        self.plot_frame = self._promote_frame_to_plotwidget(self.plot_frame, pg.PlotWidget)
        self.plot_frame_2 = self._promote_frame_to_plotwidget(self.plot_frame_2, pg.PlotWidget)
        self.plot_frame_3 = self._promote_frame_to_plotwidget(self.plot_frame_3, pg.GraphicsLayoutWidget)

        # Setup ON Button
        
        self.ON_button.clicked.connect(self.start_webcam) # Trigger per avviare la webcam


        # Setup OFF Button 
        
        self.OFF_button.clicked.connect(self.stop_webcam) # Trigger per spegnere la webcam



        # Setup della Webcam 
        
        self.webcam_active = False # Flag Camera
        self.cap = None # Inizializzo l'oggeto camera

        # Rende Skin e Marker mutuamente esclusive
        self.Skin_checkbox.clicked.connect(self.exclusive_skin)
        self.Marker_checkbox.clicked.connect(self.exclusive_marker)

        try:
            data = np.load('calib_data.npz')
            self.camera_matrix = data['camera_matrix']
            self.dist_coeffs = data['dist_coeffs']
        except FileNotFoundError:
            print("Errore: File 'calib_data.npz' non trovato. Assicurati che sia nella stessa cartella dello script.") 

        # QtCore.QTimer() è una classe di PyQt5 che crea un timer per eseguire operazioni periodiche o ritardate senza bloccare l'interfaccia grafica (GUI).
        self.timer = QtCore.QTimer()

        # Passati 33 ms chiamo la funzione di update del frame 
        self.timer.timeout.connect(self.update_frame)

        # Setup Text Box per il nome dell'immagine salvata
        self.Image_name_textbox.setPlaceholderText("Write Image Name") # Setto placeholder per ricordare di scrivere il nome dell'immagine 

        # Setup Capture Button 
        self.Capture_button.clicked.connect(self.save_image) # Trigger per salvare l'immagine

        # Trigger per associare un nome alle tracce
        self.Label_button.clicked.connect(self.set_label_Name) # Trigger per avviare la webcam

        # Cambio Lo stato del Thresholding
        self.Thresholiding_checkbox.setEnabled(False)

        # Cambio Lo stato del Skin Segmentation 
        self.Marker_checkbox.setEnabled(False)

        # Cambio lo stato del Tracking
        self.Tracking_checkbox.setEnabled(False)

        self.Skin_checkbox.setEnabled(False)

        '''

        Inizializzazione della lista delle tracce

        '''
        self.TRACKS = [] # Inizializzo il Vettore delle Tracce

        self.new_TRACKS = [] # Inizializzo il Vettore delle nuove tracce


        # Inizializzazione variabile per il labelling
        self.label_name = ""

        '''
        Inizializzazione varibili per i plot degli angoli di giunto 

        '''
        self.theta_flessione = []
        self.alpha_flessione = []
        self.beta_flessione  = []
        # Lunghezze segmenti (calcolate al primo frame utile)
        self.segment_lengths = None  # None finché non sono state calcolate

        self.time = []


        '''
        Inizializzazione grafico 
        
        '''

        self.plot_frame.setBackground("w") # set dello sfondo  ---> Altro Metodo --> self.plot_frame.setBackground((255, 255, 255)) # set dello sfondo 
        self.pen = pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.PenStyle.SolidLine) # Qt.SolidLine, Qt.DotLine, Qt.DashDotLine, Qt.DashDotDotLine
        #self.plot_frame.showGrid(x=True, y=True) # True consente di mettere la griglia sia su l'asse x sia y
        styles = {"color": "black", "font-size": "14px"}
        self.plot_frame.setTitle("Realtime Angle", **styles)
        self.plot_frame.setLabel("left", "Angle [deg]", **styles)
        self.plot_frame.setLabel("bottom", "Time [s]", **styles)
        self.plot_frame.setYRange(-10, 100 )
        self.plot_frame.setXRange(0, 3 )
        self.plot_frame.addLegend()

        # AGGIUNTA PLOT PER SCHELETRO DITO
        # -----------------------------------------------------------------------------------------
        # Setup scheletro dito
        self.plot_frame_2.setBackground("w")
        self.plot_frame_2.setTitle("Finger Skeleton", **{"color": "black", "font-size": "14px"})
        self.plot_frame_2.setAspectLocked(True)
        self.plot_frame_2.invertY(True)
        self.plot_frame_2.hideAxis('bottom')
        self.plot_frame_2.hideAxis('left')

        # Segmenti scheletro: palm-mcp, mcp-pip, pip-dip, dip-tip (4 segmenti)
        self.skeleton_lines = []
        for _ in range(4):
            line = self.plot_frame_2.plot([], [], pen=pg.mkPen(color=(0, 150, 255), width=4))
            self.skeleton_lines.append(line)

        # Punti articolazioni (5 punti: palm, mcp, pip, dip, tip)
        self.skeleton_points = pg.ScatterPlotItem(
            size=14,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(255, 80, 0, 255)
        )
        self.plot_frame_2.addItem(self.skeleton_points)

        # Label nomi articolazioni
        self.skeleton_labels = []
        label_names = ["PALM", "MCP", "PIP", "DIP", "TIP"]
        colors = [(0,100,200), (0,180,0), (200,100,0), (180,0,0), (120,0,180)]
        for name, color in zip(label_names, colors):
            text = pg.TextItem(text=name, color=color, anchor=(0.5, 1.5))
            text.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Weight.Bold))
            self.plot_frame_2.addItem(text)
            self.skeleton_labels.append(text)

        # -----------------------------------------------------------------------------------------
            # TRACKING POS E VEL DEL TIP
        # --- BUFFER PER DATI KALMAN (Marker TIP) ---
        self.kalman_time = []
        self.kalman_x = []
        self.kalman_y = []
        self.kalman_vx = []
        self.kalman_vy = []
        self.kalman_v_tot = []

        # --- SETUP PLOT FRAME 3 (1 riga, 2 colonne) ---
        self.plot_frame_3.setBackground("w")
        layout_3 = self.plot_frame_3
        
        # Subplot 1: Posizione X e Y
        self.p1_tip = layout_3.addPlot(title="Posizione TIP (Kalman)")
        self.p1_tip.setLabel("bottom", "Tempo [s]", **{"color": "black"})
        self.p1_tip.setLabel("left", "Posizione [px]", **{"color": "black"})
        
        layout_3.nextColumn()

        # Subplot 2: Velocità vx, vy e V_tot
        self.p2_tip = layout_3.addPlot(title="Velocità TIP (Kalman)")
        self.p2_tip.setLabel("bottom", "Tempo [s]", **{"color": "black"})
        self.p2_tip.setLabel("left", "Velocità [px/s]", **{"color": "black"})
        # ------------------------------------------------








        #

        # Questo script permette di cambiare di cambiare il font di xtick e ytick
        '''font = QtGui.QFont()
        font.setPointSize(10)  # Adjust size as needed
        self.plot_frame.getAxis("bottom").setStyle(tickFont = font)
        self.plot_frame.getAxis("left").setStyle(tickFont = font)'''

        # Sender UDP
        self.send= False
        self.obj_grasp = str('0')
                    
        #Cambio lo stato del Sender UDP
        self.UDP_Sender.setEnabled(False)
        self.last_sent_grasp = None

        #Session manager (cartelle,salvataggio,ecc)
        self.data_root = Path("data")
        self.session_dir = None
        self.images_dir = None
        self.is_saving = False
        self.record_start_time = None
        self.record_frame_index = 0

        self.log_angles = []       # time, MCP, PIP, DIP
        self.log_tip_px = []       # time, x/y/vx/vy/vtot del TIP in pixel
        self.log_markers_px = []   # time, dati di tutti i marker tracciati
        self.log_events = []

        self.fixed_distances_cm = None

        # Se la combo dei soggetti è vuota, creo una base semplice.
        if hasattr(self, "combo_subject") and self.combo_subject.count() == 0:
            self.combo_subject.addItems(["S01", "S02", "S03"] )

        if hasattr(self, "btn_initialize_session"):
            self.btn_initialize_session.clicked.connect(self.initialize_session)
        if hasattr(self, "btn_new_subject"):
            self.btn_new_subject.clicked.connect(self.add_new_subject)
        if hasattr(self, "start_button"):
            self.start_button.clicked.connect(self.start_saving)
        if hasattr(self, "stop_button"):
            self.stop_button.clicked.connect(self.stop_saving)
        if hasattr(self, "btn_export"):
            self.btn_export.clicked.connect(self.export_current_trial)
        if hasattr(self, "btn_open_data_folder"):
            self.btn_open_data_folder.clicked.connect(self.open_data_folder)
        if hasattr(self, "btn_current_trial"):
            self.btn_current_trial.clicked.connect(self.reset_current_trial)

        # ==========================================================
        # MODALITÀ UOMO/ROBOT + OBJECT DETECTION + UDP + DATABASE
        # ==========================================================
        self.tracking_mode = self._current_mode().upper()
        if hasattr(self, "combo_mode"):
            self.combo_mode.currentTextChanged.connect(self._on_mode_changed)

        # YOLO 
        self.yolo_model = None
        self.yolo_available = None
        self.yolo_weights = "yolov8s.pt"
        self.yolo_classes_to_detect = [41]  # COCO: 41 = cup
        self.yolo_conf = 0.25
        self.yolo_iou = 0.45
        self.obj_grasp = "0"
        self.last_detected_object = "None"

        # Tab Communication Settings e Database
        self._setup_communication_tab()
        self._setup_database_tab()
        self._on_mode_changed(self._current_mode())
        
        # ==========================================================
        # BOTTONI RAPIDI UDP NEL TAB ACQUISITION
        # ==========================================================

        if hasattr(self, "btn_acq_send_free"):
            self.btn_acq_send_free.clicked.connect(
                lambda: self._send_udp_message(
                    self.edit_udp_free_msg.text().strip() if hasattr(self, "edit_udp_free_msg") else "0",
                    force=True
                )
            )

        if hasattr(self, "btn_acq_send_grasp"):
            self.btn_acq_send_grasp.clicked.connect(
                lambda: self._send_udp_message(
                    # ANCHE QUI
                    # self.edit_udp_grasp_msg.text().strip() if hasattr(self, "edit_udp_grasp_msg") else "2",
                    self.edit_udp_grasp_msg.text().strip() if hasattr(self, "edit_udp_grasp_msg") else "B",
                    force=True
                )
            )
    # ==========================================================
    # METODI PER MUTUA ESCLUSIVITA' PRESE
    # ==========================================================
    def exclusive_libera(self):
        # Se l'utente cerca di togliere la spunta mentre è l'unica attiva, la mantengo attiva
        if not self.checkBox_LIBERA.isChecked():
            self.checkBox_LIBERA.setChecked(True)
            return
        # Altrimenti, disattivo l'altra opzione
        self.checkBox_BIDIGITALE.setChecked(False)

    def exclusive_bidigitale(self):
        # Se l'utente cerca di togliere la spunta mentre è l'unica attiva, la mantengo attiva
        if not self.checkBox_BIDIGITALE.isChecked():
            self.checkBox_BIDIGITALE.setChecked(True)
            return
        # Altrimenti, disattivo l'altra opzione
        self.checkBox_LIBERA.setChecked(False)

    # ==========================================================
    # MODALITÀ UOMO / ROBOT
    # ==========================================================
    def _on_mode_changed(self, mode_text):
        """Aggiorna la modalità di tracking quando selezioni Human/Robot.

        Human: label ordinate da sinistra a destra e ROM MCP rispetto all'asse x.
        Robot: label ordinate dal basso verso l'alto e ROM MCP rispetto all'asse y.
        """
        mode = (mode_text or "Human").strip().upper()
        if mode.startswith("ROBOT"):
            self.tracking_mode = "ROBOT"
            msg = "Modalità ROBOT: labeling dal basso verso l'alto, ROM rispetto all'asse y."
        else:
            self.tracking_mode = "HUMAN"
            msg = "Modalità HUMAN: labeling da sinistra a destra, ROM rispetto all'asse x."

        self._reset_tracking_state_for_new_mode()
        print(msg)

    def _reset_tracking_state_for_new_mode(self):
        """Reset leggero quando si cambia modalità, per evitare label vecchie."""
        if hasattr(self, "TRACKS"):
            self.TRACKS.clear()
        if hasattr(self, "new_TRACKS"):
            self.new_TRACKS.clear()
        for buffer_name in [
            "theta_flessione", "alpha_flessione", "beta_flessione", "time",
            "kalman_time", "kalman_x", "kalman_y", "kalman_vx", "kalman_vy", "kalman_v_tot"
        ]:
            if hasattr(self, buffer_name):
                getattr(self, buffer_name).clear()
        if hasattr(self, "Label_button"):
            self.Label_button.setEnabled(True)
            self.Label_button.setStyleSheet("background-color : rgb(0, 255, 0)")
        if hasattr(self, "Trace_name_textbox"):
            self.Trace_name_textbox.setEnabled(True)

    def _sort_contours_for_current_mode(self, contours):
        """Ordina i marker nel modo coerente con il labeling scelto."""
        if getattr(self, "tracking_mode", "HUMAN") == "ROBOT":
            # Coordinate immagine: y aumenta verso il basso. Dal basso verso l'alto
            # significa y decrescente, quindi reverse=True.
            return sorted(contours, key=lambda c: cv2.boundingRect(c)[1], reverse=True)
        # Umano: da sinistra a destra, quindi x crescente.
        return sorted(contours, key=lambda c: cv2.boundingRect(c)[0], reverse=False)

    def _angle_between_vectors_deg(self, v1, v2):
        """Angolo in gradi tra due vettori, con protezione su norme nulle."""
        v1 = np.array(v1, dtype=float)
        v2 = np.array(v2, dtype=float)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            raise ZeroDivisionError("Vettore nullo nel calcolo del ROM.")
        cosang = np.dot(v1, v2) / (n1 * n2)
        return float(np.rad2deg(np.arccos(np.clip(cosang, -1.0, 1.0))))

    def _compute_rom_angles(self, palm, mcp, pip, dip, tip):
        """Calcola MCP, PIP, DIP con riferimento diverso per Human/Robot.

        - Human: MCP rispetto all'asse x orizzontale.
        - Robot: MCP rispetto all'asse y verticale. Uso [0, -1] perché nel frame
          immagine l'alto è y negativa.
        PIP e DIP restano angoli relativi tra segmenti successivi.
        """
        vect_mcp_pip = pip - mcp
        vect_pip_dip = dip - pip
        vect_dip_tip = tip - dip

        if getattr(self, "tracking_mode", "HUMAN") == "ROBOT":
            reference_axis = np.array([0.0, -1.0])
        else:
            reference_axis = np.array([1.0, 0.0])

        theta_mcp = self._angle_between_vectors_deg(reference_axis, vect_mcp_pip)
        theta_pip = self._angle_between_vectors_deg(vect_mcp_pip, vect_pip_dip)
        theta_dip = self._angle_between_vectors_deg(vect_pip_dip, vect_dip_tip)
        return theta_mcp, theta_pip, theta_dip

    # ==========================================================
    # OBJECT DETECTION YOLO DINAMICA SU WEBCAM
    # ==========================================================
    def _load_yolo_if_needed(self):
        if self.yolo_model is not None:
            return True
        if self.yolo_available is False:
            return False
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(self.yolo_weights)
            self.yolo_available = True
            print(f"YOLO caricato: {self.yolo_weights}")
            return True
        except Exception as e:
            self.yolo_available = False
            self.yolo_model = None
            print(f"YOLO non disponibile: {e}")
            if hasattr(self, "check_object_detection"):
                self.check_object_detection.setChecked(False)
            return False

    def _run_object_detection(self, frame_bgr):
        """Esegue YOLO sul frame della webcam. Niente immagine statica Cup.png."""
        self.obj_grasp = "0"
        self.last_detected_object = "None"

        if not hasattr(self, "check_object_detection") or not self.check_object_detection.isChecked():
            return frame_bgr
        if not self._load_yolo_if_needed():
            return frame_bgr

        try:
            results = self.yolo_model.predict(
                source=frame_bgr,
                imgsz=(320, 256),
                conf=self.yolo_conf,
                iou=self.yolo_iou,
                classes=self.yolo_classes_to_detect,
                verbose=False,
            )

            if len(results[0].boxes) > 0:
                detected_cls = results[0].boxes.cls.cpu().numpy().astype(int).tolist()
                if any(c in self.yolo_classes_to_detect for c in detected_cls):
                    self.obj_grasp = "2"   # presa cilindrica / cup
                    self.last_detected_object = "Cup"

                for box in results[0].boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidenza = float(box.conf[0])
                    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (50, 205, 0), 3)
                    cv2.putText(frame_bgr, f"Cup {confidenza:.2f}", (x1, max(20, y1 - 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 205, 0), 2)
        except Exception as e:
            print(f"Errore YOLO nel frame corrente: {e}")
            self.obj_grasp = "0"

        self._update_communication_status_labels()
        return frame_bgr

    # ==========================================================
    # COMMUNICATION SETTINGS / UDP
    # ==========================================================
    def _setup_communication_tab(self):
        """Crea controlli UDP nel tab settings, senza modificare la .ui."""
        parent = getattr(self, "tab_settings", None)
        if parent is None:
            return
        layout = parent.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(parent)

        group = QtWidgets.QGroupBox("Communication Settings - UDP", parent)
        form = QtWidgets.QGridLayout(group)

        self.edit_udp_ip = QtWidgets.QLineEdit("192.168.14.24")
        self.spin_udp_port = QtWidgets.QSpinBox()
        self.spin_udp_port.setRange(1, 65535)
        self.spin_udp_port.setValue(5006)
        self.edit_udp_free_msg = QtWidgets.QLineEdit("0")
        # ANCHE QUI DAVIDE QUI PRESA SFERICA
        # self.edit_udp_grasp_msg = QtWidgets.QLineEdit("2")
        self.edit_udp_grasp_msg = QtWidgets.QLineEdit("B")
        
        self.btn_udp_test_free = QtWidgets.QPushButton("Send FREE test")
        self.btn_udp_test_grasp = QtWidgets.QPushButton("Send GRASP test")
        self.label_udp_last_sent = QtWidgets.QLabel("Last sent: None")
        self.label_yolo_status = QtWidgets.QLabel("Object: None | Grasp code: 0")

        form.addWidget(QtWidgets.QLabel("Receiver IP"), 0, 0)
        form.addWidget(self.edit_udp_ip, 0, 1)
        form.addWidget(QtWidgets.QLabel("Receiver Port"), 1, 0)
        form.addWidget(self.spin_udp_port, 1, 1)
        form.addWidget(QtWidgets.QLabel("Free message"), 2, 0)
        form.addWidget(self.edit_udp_free_msg, 2, 1)
        form.addWidget(QtWidgets.QLabel("Grasp message"), 3, 0)
        form.addWidget(self.edit_udp_grasp_msg, 3, 1)
        form.addWidget(self.btn_udp_test_free, 4, 0)
        form.addWidget(self.btn_udp_test_grasp, 4, 1)
        form.addWidget(self.label_udp_last_sent, 5, 0, 1, 2)
        form.addWidget(self.label_yolo_status, 6, 0, 1, 2)
        layout.addWidget(group)
        layout.addStretch(1)

        self.btn_udp_test_free.clicked.connect(lambda: self._send_udp_message(self.edit_udp_free_msg.text().strip() or "0", force=True))
        # ANCHE QUI
        # self.btn_udp_test_grasp.clicked.connect(lambda: self._send_udp_message(self.edit_udp_grasp_msg.text().strip() or "2", force=True))
        self.btn_udp_test_grasp.clicked.connect(lambda: self._send_udp_message(self.edit_udp_grasp_msg.text().strip() or "B", force=True))

    def _send_udp_message(self, message, force=False):
        ip = self.edit_udp_ip.text().strip() if hasattr(self, "edit_udp_ip") else "127.0.0.1"
        port = int(self.spin_udp_port.value()) if hasattr(self, "spin_udp_port") else 5006
        message = str(message)
        if not force and message == getattr(self, "last_sent_grasp", None):
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(message.encode("utf-8"), (ip, port))
            self.last_sent_grasp = message
            if hasattr(self, "label_udp_last_sent"):
                self.label_udp_last_sent.setText(f"Last sent: {message} → {ip}:{port}")
        except Exception as e:
            print(f"Errore invio UDP: {e}")

    def _update_udp_sender(self):
        """Invia via UDP lo stato corrente solo in modalità automatica YOLO."""
        if not hasattr(self, "UDP_Sender"):
            return

        free_msg = self.edit_udp_free_msg.text().strip() if hasattr(self, "edit_udp_free_msg") else "0"
        # ANCHE QUI PRESA SFERICA
        # grasp_msg = self.edit_udp_grasp_msg.text().strip() if hasattr(self, "edit_udp_grasp_msg") else "2"
        grasp_msg = self.edit_udp_grasp_msg.text().strip() if hasattr(self, "edit_udp_grasp_msg") else "B"

        # Se UDP_Sender non è attivo, non mando continuamente comandi.
        if not self.UDP_Sender.isChecked():
            return

        # Se object detection non è attiva, NON fare override automatico.
        # In questo caso funzionano solo i bottoni manuali Send FREE / Send GRASP.
        if not hasattr(self, "check_object_detection") or not self.check_object_detection.isChecked():
            return

        # Modalità automatica: YOLO decide.
        message = grasp_msg if self.obj_grasp == "2" else free_msg
        self._send_udp_message(message)

    def _update_communication_status_labels(self):
        if hasattr(self, "label_yolo_status"):
            self.label_yolo_status.setText(f"Object: {self.last_detected_object} | Grasp code: {self.obj_grasp}")

    # ==========================================================
    # DATABASE TAB
    # ==========================================================
    def _setup_database_tab(self):
        parent = getattr(self, "tab_database", None)
        if parent is None:
            return
        layout = parent.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(parent)

        self.db_table = QtWidgets.QTableWidget(0, 8, parent)
        self.db_table.setHorizontalHeaderLabels([
            "Mode", "Subject", "Trial folder", "Created", "Angles rows", "Markers rows", "Tip rows", "Path"
        ])
        self.db_table.horizontalHeader().setStretchLastSection(True)
        # ==========================================================
        # STYLE TABELLA DATABASE - TEMA SCURO
        # ==========================================================

        self.db_table.setStyleSheet("""
            QTableWidget {
                background-color: #0b1117;
                color: #f2f6fa;
                gridline-color: #2b3a46;
                border: 1px solid #2b3a46;
                alternate-background-color: #121b24;
                selection-background-color: #2563eb;
                selection-color: white;
                font-size: 11pt;
            }

            QTableWidget::item {
                padding: 4px;
                border: none;
            }

            QTableWidget::item:selected {
                background-color: #2563eb;
                color: white;
            }

            QHeaderView::section {
                background-color: #1c2833;
                color: #ffffff;
                padding: 6px;
                border: 1px solid #2b3a46;
                font-weight: bold;
                font-size: 10pt;
            }

            QTableCornerButton::section {
                background-color: #1c2833;
                border: 1px solid #2b3a46;
            }

            QScrollBar:vertical {
                background: #0b1117;
                width: 12px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #475569;
            }

            QScrollBar:horizontal {
                background: #0b1117;
                height: 12px;
                margin: 0px;
            }

            QScrollBar::handle:horizontal {
                background: #334155;
                min-width: 20px;
                border-radius: 5px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #475569;
            }
        """)

        self.db_table.setAlternatingRowColors(True)

        self.db_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.db_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )

        self.db_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.db_table.horizontalHeader().setStretchLastSection(True)

        self.db_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.db_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.db_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_db_refresh = QtWidgets.QPushButton("Refresh Database")
        self.btn_db_open = QtWidgets.QPushButton("Open Selected Folder")
        btn_row.addWidget(self.btn_db_refresh)
        btn_row.addWidget(self.btn_db_open)
        btn_row.addStretch(1)

        layout.addLayout(btn_row)
        layout.addWidget(self.db_table)
        self.btn_db_refresh.clicked.connect(self.refresh_database)
        self.btn_db_open.clicked.connect(self.open_selected_database_folder)
        self.refresh_database()

    def _count_csv_rows(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return max(0, sum(1 for _ in f) - 1)
        except Exception:
            return 0

    def refresh_database(self):
        if not hasattr(self, "db_table"):
            return
        rows = []
        if self.data_root.exists():
            for config_path in self.data_root.glob("*/*/trial_*/config.json"):
                session_dir = config_path.parent
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except Exception:
                    cfg = {}
                rows.append({
                    "mode": cfg.get("mode", session_dir.parents[1].name),
                    "subject": cfg.get("subject", session_dir.parent.name),
                    "trial": session_dir.name,
                    "created": cfg.get("created_at", ""),
                    "angles": self._count_csv_rows(session_dir / "angles.csv"),
                    "markers": self._count_csv_rows(session_dir / "markers_px.csv"),
                    "tip": self._count_csv_rows(session_dir / "tip_kinematics.csv"),
                    "path": str(session_dir.resolve()),
                })
        rows.sort(key=lambda r: r["created"], reverse=True)
        self.db_table.setRowCount(len(rows))
        for r, item in enumerate(rows):
            values = [item["mode"], item["subject"], item["trial"], item["created"],
                      str(item["angles"]), str(item["markers"]), str(item["tip"]), item["path"]]
            for c, value in enumerate(values):
                self.db_table.setItem(r, c, QtWidgets.QTableWidgetItem(value))
        self.db_table.resizeColumnsToContents()

    def open_selected_database_folder(self):
        if not hasattr(self, "db_table"):
            return
        row = self.db_table.currentRow()
        if row < 0:
            print("Seleziona prima una sessione nel tab Database.")
            return
        item = self.db_table.item(row, 7)
        if item is None:
            return
        folder = item.text()
        try:
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", folder])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            print(f"Impossibile aprire la cartella: {e}")
            print(folder)


    # Funzioni per rendere le checkbox esclusive
    def exclusive_skin(self):
        if self.Skin_checkbox.isChecked():
            self.Marker_checkbox.setChecked(False)

            self.Color_space_box.setCurrentText("YCbCr")

    def exclusive_marker(self):
        if self.Marker_checkbox.isChecked():
            self.Skin_checkbox.setChecked(False)

            self.Color_space_box.setCurrentText("YCbCr")

    # Funzione per accendere la webcam
    def start_webcam(self):
        """Starts the webcam feed and updates QLabel"""
        if not self.webcam_active:
            self.cap = cv2.VideoCapture(0)  # Open default webcam (0)
            self.webcam_active = True # Flag per indicare che la Camera è Attiva 
            self.timer.start(33)  #  avvia un QTimer che genera eventi periodici ogni 33 millisecondi.

            # Cambio Lo stato del Thresholding
            self.Thresholiding_checkbox.setEnabled(True)

            # Cambio Lo stato del Skin Segmentation 
            self.Marker_checkbox.setEnabled(True)

            # Cambio lo stato del Tracking
            self.Tracking_checkbox.setEnabled(True)

            # Cambio lo stato del Tracking
            self.Skin_checkbox.setEnabled(True)

            #Cambio lo stato del Sender UDP
            self.UDP_Sender.setEnabled(True)
        
    # Funzione per spegnere la webcam
    def stop_webcam(self):
        if self.webcam_active:
            self.timer.stop() # Stoppo il timer 
            self.cap.release() # Stoppo la webcam
            self.webcam_active = False # Cambio lo stato del Flag
            self.Camera_frame.setText("Camera OFF") # Cambio la visualizzazione in Camera Frame
            self.Mask_frame.setText("Mask OFF") # Cambio la visualizzazione in MASK Frame


            # Cambio Lo stato del Thresholding
            self.Thresholiding_checkbox.setChecked(False)
            self.Thresholiding_checkbox.setEnabled(False)

            # Cambio lo stato del Tracking
            self.Tracking_checkbox.setEnabled(False)

            # Cambio Lo stato del Skin Segmentation 
            self.Marker_checkbox.setChecked(False)
            self.Marker_checkbox.setEnabled(False)

            self.Skin_checkbox.setChecked(False)
            self.Skin_checkbox.setEnabled(False)

            # Cambio lo stato del Sender UDP
            self.UDP_Sender.setChecked(False)
            self.UDP_Sender.setEnabled(False)

    # Funzione per salvare l'immagine
    def save_image(self):

        if self.webcam_active == True and hasattr(self, "frame"):
            # Se la sessione non è stata inizializzata, la creo automaticamente.
            self._ensure_session()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = self.images_dir / f"capture_{timestamp}.png"

            # self.frame qui è RGB; cv2.imwrite vuole BGR. Non sovrascrivo self.frame
            # per evitare problemi nei frame successivi.
            frame_bgr = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(filename), frame_bgr)
            print(f"Frame salvato: {filename}")
        else:
            print("Impossibile salvare: webcam non attiva o frame non disponibile.")

    # ==========================================================
    # SESSION MANAGER E EXPORT CSV
    # ==========================================================
    def _current_mode(self):
        if hasattr(self, "combo_mode"):
            return self.combo_mode.currentText().strip() or "Human"
        return "Human"

    def _current_subject(self):
        if hasattr(self, "combo_subject"):
            text = self.combo_subject.currentText().strip()
            return text if text else "S01"
        return "S01"

    def _current_trial(self):
        if hasattr(self, "spin_trial"):
            return int(self.spin_trial.value())
        return 1

    def add_new_subject(self):
        # Crea automaticamente il prossimo ID soggetto: S01, S02, ...
        if not hasattr(self, "combo_subject"):
            return
        existing = [self.combo_subject.itemText(i) for i in range(self.combo_subject.count())]
        nums = []
        for item in existing:
            if item.upper().startswith("S") and item[1:].isdigit():
                nums.append(int(item[1:]))
        next_id = max(nums, default=0) + 1
        subject = f"S{next_id:02d}"
        self.combo_subject.addItem(subject)
        self.combo_subject.setCurrentText(subject)
        print(f"Nuovo soggetto aggiunto: {subject}")

    def initialize_session(self):
        mode = self._current_mode()
        base_subject = self._current_subject()
        trial = self._current_trial()
        

        # ── DETERMINAZIONE DEL TIPO DI PRESA ──
        presa = "LIBERA" # Valore di default fallback
        if hasattr(self, "checkBox_BIDIGITALE") and self.checkBox_BIDIGITALE.isChecked():
            presa = "BIDIGITALE"
        elif hasattr(self, "checkBox_LIBERA") and self.checkBox_LIBERA.isChecked():
            presa = "LIBERA"
            
        # Creazione del nome della cartella (es. S01_LIBERA)
        subject_folder = f"{base_subject}_{presa}"

        # Utilizzo subject_folder per il percorso di salvataggio
        self.session_dir = self.data_root / mode / subject_folder / f"trial_{trial:03d}"
        self.images_dir = self.session_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "mode": mode,
            "subject": subject_folder, # Aggiornato per riflettere il nome combinato
            "trial": trial,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "tracking_mode": getattr(self, "tracking_mode", "HUMAN"),
            "udp_ip": self.edit_udp_ip.text().strip() if hasattr(self, "edit_udp_ip") else "127.0.0.1",
            "udp_port": int(self.spin_udp_port.value()) if hasattr(self, "spin_udp_port") else 5006,
            "object_detection_enabled": bool(self.check_object_detection.isChecked()) if hasattr(self, "check_object_detection") else False,
            "notes": "Sessione generata da gui_demo.ui; conversione pixel-cm non inclusa in questa versione."
        }
        with open(self.session_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        print(f"Sessione inizializzata: {self.session_dir}")
        return self.session_dir

    def _ensure_session(self):
        if self.session_dir is None:
            self.initialize_session()

    def reset_current_trial(self):
        self.is_saving = False
        self.record_start_time = None
        self.record_frame_index = 0
        self.log_angles.clear()
        self.log_tip_px.clear()
        self.log_markers_px.clear()
        self.log_events.clear()
        print("Buffer del trial corrente resettati.")

    def start_saving(self):
        self._ensure_session()
        self.log_angles.clear()
        self.log_tip_px.clear()
        self.log_markers_px.clear()
        self.log_events.clear()
        self.record_frame_index = 0
        self.record_start_time = time.time()
        self.is_saving = True
        self.log_events.append({
            "event": "start_recording",
            "time_iso": datetime.now().isoformat(timespec="seconds")
        })
        print("Registrazione dati avviata.")

    def stop_saving(self):
        if not self.is_saving:
            print("Nessuna registrazione in corso.")
            return

        self.is_saving = False
        self.log_events.append({
            "event": "stop_recording",
            "time_iso": datetime.now().isoformat(timespec="seconds")
        })
        self.export_current_trial()
        print("Registrazione dati fermata.")

    def _record_current_sample(self, theta_mcp, theta_pip, theta_dip):
        if not self.is_saving:
            return

        if self.record_start_time is None:
            self.record_start_time = time.time()

        t = time.time() - self.record_start_time
        self.record_frame_index += 1

        # Estraggo le distanze correnti (se non ancora calibrate mette 0.0)
        f_p_m, f_m_p, f_p_d, f_d_t = self.fixed_distances_cm if self.fixed_distances_cm is not None else (0.0, 0.0, 0.0, 0.0)

        # ── SALVATAGGIO ANGOLI E LUNGHEZZE ──
        self.log_angles.append({
            "frame": self.record_frame_index,
            "time_s": t,
            "MCP_deg": float(theta_mcp),
            "PIP_deg": float(theta_pip),
            "DIP_deg": float(theta_dip),
            "L_palm_mcp_cm": f_p_m,
            "L_mcp_pip_cm": f_m_p,
            "L_pip_dip_cm": f_p_d,
            "L_dip_tip_cm": f_d_t
        })

        # ── SALVATAGGIO DEL TIP CON CONVERSIONE IN CENTIMETRI (Zc = 20cm) ──
        for track in self.TRACKS:
            if track.name == "t" and len(track.traj_x_filt) > 0:
                vx = float(track.vel_x_filt[-1]) if len(track.vel_x_filt) > 0 else 0.0
                vy = float(track.vel_y_filt[-1]) if len(track.vel_y_filt) > 0 else 0.0
                kx = float(track.traj_x_filt[-1])
                ky = float(track.traj_y_filt[-1])

                # Valori di default
                x_cm, y_cm, vx_cm, vy_cm, vtot_cm = 0.0, 0.0, 0.0, 0.0, 0.0

                # Se la matrice di calibrazione esiste, eseguo la proiezione in cm
                if hasattr(self, 'camera_matrix') and self.camera_matrix is not None:
                    fx = self.camera_matrix[0, 0]
                    fy = self.camera_matrix[1, 1]
                    cx = self.camera_matrix[0, 2]
                    cy = self.camera_matrix[1, 2]
                    Zc = 20.0  # Profondità fissata a 20cm

                    x_cm = (kx - cx) / fx * Zc
                    y_cm = (ky - cy) / fy * Zc
                    vx_cm = vx * (Zc / fx)
                    vy_cm = vy * (Zc / fy)
                    vtot_cm = math.sqrt(vx_cm**2 + vy_cm**2)

                self.log_tip_px.append({
                    "frame": self.record_frame_index,
                    "time_s": t,
                    "x_px": kx,
                    "y_px": ky,
                    "vx_px_s": vx,
                    "vy_px_s": vy,
                    "vtot_px_s": float(math.sqrt(vx**2 + vy**2)),
                    "x_cm": x_cm,
                    "y_cm": y_cm,
                    "vx_cm_s": vx_cm,
                    "vy_cm_s": vy_cm,
                    "vtot_cm_s": vtot_cm
                })
                break

        # Salvo i marker raw (invariato)
        for track in self.TRACKS:
            if len(track.traj_x_filt) == 0:
                continue
            vx = float(track.vel_x_filt[-1]) if len(track.vel_x_filt) > 0 else 0.0
            vy = float(track.vel_y_filt[-1]) if len(track.vel_y_filt) > 0 else 0.0
            self.log_markers_px.append({
                "frame": self.record_frame_index,
                "time_s": t,
                "marker": track.name,
                "x_raw_px": float(track.traj_x[-1]) if len(track.traj_x) > 0 else "",
                "y_raw_px": float(track.traj_y[-1]) if len(track.traj_y) > 0 else "",
                "x_filt_px": float(track.traj_x_filt[-1]),
                "y_filt_px": float(track.traj_y_filt[-1]),
                "vx_px_s": vx,
                "vy_px_s": vy,
                "bbox_x": int(track.x),
                "bbox_y": int(track.y),
                "bbox_w": int(track.w),
                "bbox_h": int(track.h),
            })
            
    def _write_csv(self, filename, rows, fieldnames):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def export_current_trial(self):
        self._ensure_session()

        # Aggiorno l'export inserendo le intestazioni delle lunghezze
        self._write_csv(
            self.session_dir / "angles.csv",
            self.log_angles,
            [
                "frame", "time_s", "MCP_deg", "PIP_deg", "DIP_deg", 
                "L_palm_mcp_cm", "L_mcp_pip_cm", "L_pip_dip_cm", "L_dip_tip_cm"
            ]
        )
        
        # Rinominato rimuovendo "_px" e aggiunte colonne cm
        self._write_csv(
            self.session_dir / "tip_kinematics.csv",  
            self.log_tip_px,
            [
                "frame", "time_s", 
                "x_px", "y_px", "vx_px_s", "vy_px_s", "vtot_px_s",
                "x_cm", "y_cm", "vx_cm_s", "vy_cm_s", "vtot_cm_s"
            ]
        )
        
        self._write_csv(
            self.session_dir / "markers_px.csv",
            self.log_markers_px,
            ["frame", "time_s", "marker", "x_raw_px", "y_raw_px", "x_filt_px", "y_filt_px",
             "vx_px_s", "vy_px_s", "bbox_x", "bbox_y", "bbox_w", "bbox_h"]
        )
        with open(self.session_dir / "events.json", "w", encoding="utf-8") as f:
            json.dump(self.log_events, f, indent=4)

        print(f"Dati del trial esportati in: {self.session_dir}")
        self.refresh_database()

    def open_data_folder(self):
        self._ensure_session()
        folder = str(self.session_dir.resolve())
        try:
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", folder])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            print(f"Impossibile aprire la cartella automaticamente: {e}")
            print(f"Cartella dati: {folder}")

    # Funzione settare il nome alla traccia 
    def set_label_Name(self):
        for track in self.TRACKS: # Scorro lungo le tracce

            if track.name_setted == False: # Individuo le tracce il cui nome non è stato cambiato

                label_name = self._read_widget_text(self.Trace_name_textbox).strip().lower()

                if label_name == "":
                    return

                track.set_name(label_name) # Estraggo il nome dalla casella di testo

                self.Trace_name_textbox.clear() # Pulisco la Text box

                break  # Questo break serve per cambiare solo il nome della prima traccia il cui nome non è stato cambiato (i.e. track.name_setted = False)    


    def update_frame(self):
        """Captures video frames and updates QLabel"""
        ret, self.frame = self.cap.read() # Leggo il frame 

        # ==========================================================
        # OBJECT DETECTION DINAMICA + COMUNICAZIONE UDP
        # ==========================================================
        # YOLO lavora sul frame BGR grezzo della webcam, prima della conversione RGB.
        # Se check_object_detection è spento, questa funzione non fa nulla e obj_grasp resta "0".
        if ret:
            self.frame = self._run_object_detection(self.frame)
        self._update_udp_sender()

        """
        if ret:

            h, w = self.frame.shape[:2]

            new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
                self.camera_matrix,
                self.dist_coeffs,
                (w, h),
                0, # alpha
                (w, h)
            )

            self.frame = cv2.undistort(
                self.frame,
                self.camera_matrix,
                self.dist_coeffs,
                None,
                new_camera_matrix
            )

            # 2. ECCO LA PARTE MANCANTE: Il ritaglio dell'immagine utile
            x, y, w, h = roi
            self.frame = self.frame[y:y+h, x:x+w]

            """
        if ret:
            # ==========================================
            # CALIBRAZIONE
            # ==========================================
            # Applica l'undistort SOLO se il file di calibrazione è stato caricato correttamente
            if hasattr(self, 'camera_matrix') and hasattr(self, 'dist_coeffs'):
                h, w = self.frame.shape[:2]

                new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
                    self.camera_matrix,
                    self.dist_coeffs,
                    (w, h),
                    0, # alpha
                    (w, h)
                )

                self.frame = cv2.undistort(
                    self.frame,
                    self.camera_matrix,
                    self.dist_coeffs,
                    None,
                    new_camera_matrix
                )

                # Ritaglio dell'immagine utile
                x, y, w, h = roi
                self.frame = self.frame[y:y+h, x:x+w]

            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)  # Convert0 BGR to RGB
              
            if self.Thresholiding_checkbox.isChecked(): # Se il thresholding è abilitato


                if self.Marker_checkbox.isChecked():
                    self.raw_image = cv2.cvtColor(self.frame, cv2.COLOR_RGB2YCrCb)

                    self.Slider_1.setRange(0, 255)
                    self.Slider_2.setRange(0, 255)
                    self.Slider_3.setRange(0, 255)
                    
                    threshold_1 = self.Slider_1.value()
                    threshold_2 = self.Slider_2.value()
                    threshold_3 = self.Slider_3.value()
                    
                    self.Channel_name_1.setText("Y")
                    self.Channel_name_2.setText("Cr")
                    self.Channel_name_3.setText("Cb")

                    Y = self.raw_image[:, :, 0] > threshold_1
                    Cr = self.raw_image[:, :, 1] > threshold_2
                    Cb = self.raw_image[:, :, 2] > threshold_3

                    self.valore1.setText(str(threshold_1))
                    self.valore2.setText(str(threshold_2))
                    self.valore3.setText(str(threshold_3))
                    
                    # 1. Maschera: Cerchiamo la mano
                    self.mask = np.uint8(Y & Cr & Cb)
                    self.mask = self.mask * 255
                    
                    # Filtraggio a mediana mobile
                    self.filtered_img = cv2.medianBlur(self.mask, 35)

                    #Operazioni morfologiche per la SEGMENTAZIONE

                    kernel = np.ones((9,9), np.uint8)
                    self.filled_image = cv2.morphologyEx(self.filtered_img, cv2.MORPH_CLOSE, kernel)
                    
                    kernel = np.ones((9,9), np.uint8)
                    self.filled_image = cv2.morphologyEx(self.filled_image, cv2.MORPH_OPEN, kernel)
                    
                    # 3. Preparazione della tela: usiamo il fotogramma a colori reale!
                    self.output_image = self.frame.copy()
            
                    # Cerchiamo i contorni (i marker)
                    contours, _ = cv2.findContours(self.filled_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    for contour in contours:    
                        area = cv2.contourArea(contour)
                        
                        # 4. Area: Se è più piccolo tot pixel è rumore
                        if area < 14400:
                            continue

                        # Troviamo le coordinate di QUESTO singolo marker
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # 5. Disegniamo il rettangolo e il cerchio in ROSSO (0, 0, 255)
                        cv2.rectangle(self.output_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        
                        # Pallino centrale al marker (leggermente più piccolo, radius=3)
                        cv2.circle(self.output_image, (int(x + w/2), int(y + h/2)), radius=3, color=(0, 0, 255), thickness=-1)

                        self.output_image = self.frame.copy() 

                else:

                    # Estraggo lo space coloro dove voglio effettuare la segmentazione
                    selected_color_space = self.Color_space_box.currentText()


                    # Estraggo valori dagli slider
                    threshold_1 = self.Slider_1.value()
                    threshold_2 = self.Slider_2.value()
                    threshold_3 = self.Slider_3.value()
                    

                    if selected_color_space == "RGB":

                        # Cambio i nomi dei channel
                        self.Channel_name_1.setText("R")
                        self.Channel_name_2.setText("G")
                        self.Channel_name_3.setText("B")

                        # Applico le treashold per RGB
                        M_red = self.frame[:, :, 0] > threshold_1 
                        M_green = self.frame[:, :, 1] > threshold_2
                        M_blue = self.frame[:, :, 2] > threshold_3

                        # Creo la maschera
                        self.mask = np.uint8(M_red & M_green & M_blue)  # Convert boolean mask to uint8

                        # Moltiplico per 255 al fine di visualizzare meglio la maschera
                        self.mask = self.mask*255



                    elif selected_color_space == "YCbCr": 

                        self.raw_image = cv2.cvtColor(self.frame, cv2.COLOR_RGB2YCrCb)

                        # Cambio i nomi dei channel
                        self.Channel_name_1.setText("Y")
                        self.Channel_name_2.setText("Cr")
                        self.Channel_name_3.setText("Cb")

                        # Applico le treashold per YCrCb
                        Y = self.raw_image[:, :, 0] > threshold_1 
                        Cr = self.raw_image[:, :, 1] > threshold_2
                        Cb = self.raw_image[:, :, 2] > threshold_3

                        # Genero la maschera 
                        self.mask = np.uint8(Y & Cr & Cb)
                        self.mask = self.mask*255

                    else:

                        self.raw_image = cv2.cvtColor(self.frame, cv2.COLOR_RGB2HSV)

                        # Cambio i nomi dei channel
                        self.Channel_name_1.setText("H")
                        self.Channel_name_2.setText("S")
                        self.Channel_name_3.setText("V")

                        # Applico le treashold per HSV
                        H = self.raw_image[:, :, 0] > threshold_1 
                        S = self.raw_image[:, :, 1] > threshold_2
                        V = self.raw_image[:, :, 2] > threshold_3

                        # Genero la maschera 
                        self.mask = np.uint8(H & S & V)
                        self.mask = self.mask*255

                self.filtered_img = cv2.medianBlur(self.mask, 35) # Filtraggio a mediana mobile (image, più dimensioni kernel quadato) --> La dimensione del Kernel deve essere dispari !!!!

                # Applico operazione morfologica (CLOSE) per il filling
                kernel = np.ones((10,10), np.uint8)  # Define a kernel size
                self.filled_image = cv2.morphologyEx(self.filtered_img, cv2.MORPH_CLOSE, kernel)
                
                # Applico operazione morfologica (OPEN) per eliminare ulteriori rumori
                kernel = np.ones((10,10), np.uint8)
                self.filled_image = cv2.morphologyEx(self.filled_image, cv2.MORPH_OPEN, kernel)

                # Passo da grayscale a RGB al fine di avere bounding box rosse
                self.output_image = cv2.cvtColor(self.filled_image, cv2.COLOR_GRAY2RGB)

                '''
                                                               Object Detction 
                '''
                contours, _ = cv2.findContours(self.filled_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # Funzione che serve per trovare le bounding box

                # Ordino i contorni i ordine discente/ascedente prendo i considerazione la loro coordinata x

                contours = self._sort_contours_for_current_mode(contours)  # Human: x crescente; Robot: y decrescente
                # 1) lista da ordinare 
                # 2) Key --> Funzione per specificare il criterio di sorting
                # 3) lamda function ritorna il valore lungo la x, dell'i-esimo contorno
                # 4) reverse = TRUE/FALSE indica ordine discendente/ascendente


                # Verificio se il tracking è abilitato
                if self.Tracking_checkbox.isChecked():

                    # ==========================================================
                    # 1. AUTO-INIZIALIZZAZIONE DEL TRACKING
                    # ==========================================================
                    if len(self.TRACKS) == 0:
                        
                        # Controllo di aver trovato ESATTAMENTE 5 marker (contours)
                        # Controllo di aver trovato ESATTAMENTE 5 marker (contours)
                        if len(contours) == 5:
                            labels = ['b', 'm', 'p', 'd', 't']
                            
                            # Lista temporanea per salvare i centroidi e calcolare le distanze
                            initial_centroids = []
                            
                            for i in range(5):
                                # Estraggo i centroidi e le dimensioni della bounding box
                                x, y, w, h = cv2.boundingRect(contours[i]) 
                                initial_centroids.append((x, y))
                                
                                # Creo la traccia con la label corretta e aggiorno il centroide
                                new_trace = Trace(labels[i], x, y)
                                new_trace.update_centroid(x, y, w, h)
                                
                                # Sblocca i calcoli geometrici e i grafici
                                new_trace.name_setted = True 

                                # Appendo la traccia alla lista
                                self.TRACKS.append(new_trace)
                                
                            print("✅ Tracking automatico inizializzato con successo!")
                            
                            # ==========================================================
                            # CALCOLO AUTOMATICO DELLE LUNGHEZZE IN CENTIMETRI
                            # ==========================================================
                            # Estraggo le coordinate X, Y dei 5 punti (b, m, p, d, t)
                            xb, yb = initial_centroids[0]
                            xm, ym = initial_centroids[1]
                            xp, yp = initial_centroids[2]
                            xd, yd = initial_centroids[3]
                            xt, yt = initial_centroids[4]
                            
                            # Calcolo le distanze Euclidee in PIXEL
                            dist_bm_px = math.sqrt((xm - xb)**2 + (ym - yb)**2)
                            dist_mp_px = math.sqrt((xp - xm)**2 + (yp - ym)**2)
                            dist_pd_px = math.sqrt((xd - xp)**2 + (yd - yp)**2)
                            dist_dt_px = math.sqrt((xt - xd)**2 + (yt - yd)**2)
                            
                            # Fattore di conversione (assumendo Z = 400 mm come nel tuo codice originale)
                            # Se hai self.camera_matrix, usiamo f_x, altrimenti un valore di default
                            if hasattr(self, "camera_matrix"):
                                f_x = self.camera_matrix[0, 0]
                                Z_mm = 400.0  # Distanza stimata della mano dalla telecamera in mm
                                conv_factor = Z_mm / (f_x * 10.0) # Converte in cm
                            else:
                                conv_factor = 0.026458333  # Fallback generico (1 pixel ~ 0.026 cm)
                                
                            # Converto in centimetri e salvo in memoria
                            self.fixed_distances_cm = (
                                dist_bm_px * conv_factor,
                                dist_mp_px * conv_factor,
                                dist_pd_px * conv_factor,
                                dist_dt_px * conv_factor
                            )
                            print(f"📏 Distanze salvate (cm): {self.fixed_distances_cm}")
                            
                        else:
                            # Se non vede 5 marker, stampo un messaggio sul video in rosso e aspetto
                            cv2.putText(self.output_image, f"In attesa... Trovati {len(contours)}/5 marker", 
                                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    else: # Se la lista delle tracce non è vuota --> effettuo l'update                            
                            
                            for contour in contours:
                                ''' Bisogna associare ogni box ad ogni traccia  ---> Utilizzo la distanza Euclidea  '''

                                # Calcolo la metrica di distanza rispetto agli elementi della lista
                                u, v, w, h = cv2.boundingRect(contour)

                                # Genero una lista dove salvo tutti i valori di distanza 
                                vettore_delle_distanze = [] 

                                # Calcolo tutte le distanze per quella bounding box 
                                for track in self.TRACKS:
                                    # Calcolo la distanza euclidea
                                    distance = np.sqrt( (track.traj_x_filt[-1]- (u + w/2) )**2 + (track.traj_y_filt[-1] - (v + h/2))**2) # Valuto distanza tra i centri delle bounding box
                                    vettore_delle_distanze.append(distance)

                                # Trovo la distanza più piccola 
                                minimum = min(vettore_delle_distanze)

                                # IF PER GENERARE NUOVE TRACCE --> se la distanza supera una soglia di threshold 
                                if minimum > 70:
                            
                                    # Aggiungo le nuove tracce 
                                    #self.new_TRACKS.append(Traccia("Box_N" + str(self.box_number+1), u, v))
                                    '''
                                                                Update delle tracce (KALMAN)
                                    '''
                                    self.new_TRACKS.append(Trace(self.label_name, u, v))
                                    self.new_TRACKS[-1].update_centroid(u,v,w,h)

                                else:
                                    '''
                                                                Update delle tracce (KALMAN)
                                    '''
                                    idx = vettore_delle_distanze.index(minimum)
                                    self.TRACKS[idx].update_centroid(u, v, w, h)

                            
                            # Start included, step e stop(not included )
                            for i in range(len(self.TRACKS) - 1, -1, -1):  


                                # Update not visible count 
                                self.TRACKS[i].update_not_visible()

                                # Elimino le tracce non visibile per un tot di frame
                                if self.TRACKS[i].not_visible_count > 20: # Elimino la traccia se il suo not_visible_count è maggiore di 20
                                    del self.TRACKS[i]
                        

                            # Merge delle liste 
                            self.TRACKS = self.TRACKS + self.new_TRACKS
                            self.new_TRACKS = []

                            # Check se tutte le tracce sono state etichettate 
                            not_labeled = 0

                            # Check per verificare se tutte le tracce sono state etichettate 
                            for track in self.TRACKS:
                                if track.name_setted == False:
                                    #not_labeled = not_labeled + 1
                                    not_labeled = not_labeled + 1
                            
                            if not_labeled == 0: # Se tutte le tracce sono etichettate

                                self.Label_button.setEnabled(False) # Disabilito il push button del labelling 
                                self.Label_button.setStyleSheet("background-color : rgb(255, 0, 0)") # Cambio colore del push button
                                self.Trace_name_textbox.setEnabled(False) # Disabilito la scrittura della text box 

                            #
                            else: # Se tutte le tracce non sono etichettate
                                self.Label_button.setEnabled(True) # Abilito il push button del labelling 
                                self.Label_button.setStyleSheet("background-color : rgb(0, 255, 0)") # Cambio il colore del push button
                                self.Trace_name_textbox.setEnabled(True) # Abilito la scrittura della text box


                            # Calcolo angolo di giunto --> (pip in questo caso)
                            if not_labeled == 0: # Se tutte le tracce sono etichettate
                                palm = mcp = pip = dip = tip = None
                                # Salvo le posizioni dei marker in variabili di appoggio per stimare l'angolo
                                # Stima dell'angolo di giunto: mediante angolo compreso tra due vettori
                                
                                try:
                                    # Recupero posizioni filtrate dei 4 marker
                                    for track in self.TRACKS:
                                        if track.name == "b":
                                            palm = np.array([track.traj_x_filt[-1], track.traj_y_filt[-1]])
                                        elif track.name == "m":
                                            mcp = np.array([track.traj_x_filt[-1], track.traj_y_filt[-1]])
                                        elif track.name == "p":
                                            pip = np.array([track.traj_x_filt[-1], track.traj_y_filt[-1]])
                                        elif track.name == "d":
                                            dip = np.array([track.traj_x_filt[-1], track.traj_y_filt[-1]])
                                        elif track.name == "t":
                                            tip = np.array([track.traj_x_filt[-1], track.traj_y_filt[-1]])
                                            kx = track.traj_x_filt[-1]
                                            ky = track.traj_y_filt[-1]
                                            kvx = track.vel_x_filt[-1]
                                            kvy = track.vel_y_filt[-1]
                                            
                                            self.kalman_x.append(kx)
                                            self.kalman_y.append(ky)
                                            self.kalman_vx.append(kvx)
                                            self.kalman_vy.append(kvy)
                                            
                                            # Velocità totale 
                                            kv_tot = math.sqrt(kvx**2 + kvy**2)
                                            self.kalman_v_tot.append(kv_tot)
                                            
                                            # Tempo
                                            self.kalman_time.append(len(self.kalman_x) * 0.033)


                                    # ── Al primo frame utile: salva lunghezze ──
                                    # Lunghezze falangi fisiologiche (proporzione aurea φ = 1.618)
                                    # Rapporto distale : media : prossimale = 1 : 1.618 : 2.618
                                    # Valori in pixel calibrati per il widget (321x241)
                                    phi = 1.618
                                    L_distale   = 10            # DIP → TIP  (falange distale)
                                    L_media     = math.ceil(L_distale * phi)        # PIP → DIP  (falange media)  
                                    L_prossimale = math.ceil(L_media * phi)    # MCP → PIP  (falange prossimale) 
                                    L_metacarpo  = math.ceil(L_prossimale * phi)    # PALM → MCP (metacarpo) 

                                    self.segment_lengths = (L_metacarpo, L_prossimale, L_media, L_distale)

                                    # ==========================================================
                                    # CALCOLO DISTANZE REALI IN CM (CALIBRAZIONE SPAZIALE)
                                    # ==========================================================
                                    if self.fixed_distances_cm is None and hasattr(self, "camera_matrix"):
                                        fx = self.camera_matrix[0, 0]
                                        fy = self.camera_matrix[1, 1]
                                        cx = self.camera_matrix[0, 2]
                                        cy = self.camera_matrix[1, 2]
                                        Zc = 20.0  # Profondità stimata fissa a 20cm

                                        def px_to_cm(pt):
                                            return np.array([(pt[0] - cx) / fx * Zc, (pt[1] - cy) / fy * Zc])

                                        # Calcolo la distanza reale e la congelo
                                        d_palm_mcp = float(np.linalg.norm(px_to_cm(mcp) - px_to_cm(palm)))
                                        d_mcp_pip = float(np.linalg.norm(px_to_cm(pip) - px_to_cm(mcp)))
                                        d_pip_dip = float(np.linalg.norm(px_to_cm(dip) - px_to_cm(pip)))
                                        d_dip_tip = float(np.linalg.norm(px_to_cm(tip) - px_to_cm(dip)))

                                        self.fixed_distances_cm = (d_palm_mcp, d_mcp_pip, d_pip_dip, d_dip_tip)
                                        print(f"Segmenti reali calibrati: {d_palm_mcp:.1f}cm, {d_mcp_pip:.1f}cm, {d_pip_dip:.1f}cm, {d_dip_tip:.1f}cm")

                                    # Se i centimetri sono stati calcolati, stampali in giallo sul video
                                    if self.fixed_distances_cm is not None:
                                        f_p_m, f_m_p, f_p_d, f_d_t = self.fixed_distances_cm
                                        cv2.putText(self.output_image, f"{f_p_m:.1f}cm", (int((palm[0]+mcp[0])/2), int((palm[1]+mcp[1])/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                                        cv2.putText(self.output_image, f"{f_m_p:.1f}cm", (int((mcp[0]+pip[0])/2), int((mcp[1]+pip[1])/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                                        cv2.putText(self.output_image, f"{f_p_d:.1f}cm", (int((pip[0]+dip[0])/2), int((pip[1]+dip[1])/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                                        cv2.putText(self.output_image, f"{f_d_t:.1f}cm", (int((dip[0]+tip[0])/2), int((dip[1]+tip[1])/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                                    # ==========================================================


                                    # ── Calcolo ROM modo-specifico ──
                                    # Human: MCP rispetto all'asse x. Robot: MCP rispetto all'asse y.
                                    theta_mcp, theta_pip, theta_dip = self._compute_rom_angles(
                                        palm, mcp, pip, dip, tip
                                    )
                                    self.theta_flessione.append(theta_pip)
                                    self.alpha_flessione.append(theta_mcp)
                                    self.beta_flessione.append(theta_dip)
                                    self.time.append(len(self.theta_flessione) / 33)

                                    # Salvataggio dati: se START RECORDING è attivo,
                                    # registro angoli, marker e cinematica TIP in pixel.
                                    self._record_current_sample(theta_mcp, theta_pip, theta_dip)

                                    # ── Plot angoli sovrapposti ──
                                    if len(self.theta_flessione) > 33:
                                        y = self.theta_flessione[-32:-1]
                                        x = self.time[-32:-1]
                                        z = self.alpha_flessione[-32:-1]
                                        
                                        self.plot_frame.clear()
                                        self.plot_frame.addLegend()
                                        self.plot_frame.plot(x, y, pen=self.pen, name="PIP angle")
                                        self.plot_frame.plot(x, z, pen=pg.mkPen('b', width=3), name="MCP angle")
                                        
                                        self.plot_frame.setXRange(self.time[-32], self.time[-1])
                                    
                                    # ── Plot Posizione e Velocità Kalman su plot_frame_3 ──
                                    if len(self.kalman_time) > 33:
                                        t = self.kalman_time[-32:-1]
                                        
                                        # 1. Plot Posizioni filtrate
                                        self.p1_tip.clear()
                                        self.p1_tip.addLegend()
                                        self.p1_tip.plot(t, self.kalman_x[-32:-1], pen=pg.mkPen('r', width=3), name="X Pos")
                                        self.p1_tip.plot(t, self.kalman_y[-32:-1], pen=pg.mkPen('g', width=3), name="Y Pos")
                                        
                                        # 2. Plot Velocità filtrate
                                        self.p2_tip.clear()
                                        self.p2_tip.addLegend()
                                        self.p2_tip.plot(t, self.kalman_vx[-32:-1], pen=pg.mkPen('r', width=1, style=QtCore.Qt.PenStyle.DashLine), name="Vx")
                                        self.p2_tip.plot(t, self.kalman_vy[-32:-1], pen=pg.mkPen('g', width=1, style=QtCore.Qt.PenStyle.DashLine), name="Vy")
                                        self.p2_tip.plot(t, self.kalman_v_tot[-32:-1], pen=pg.mkPen('b', width=3), name="V Totale")

                                    # ── Ricostruzione cinematica scheletro con lunghezze fisse ──


                                    # Lunghezza totale del dito (per settare il range del plot)
                                    L_tot = L_metacarpo + L_prossimale + L_media + L_distale  # Lunghezza totale del dito (per settare il range del plot)

                                    # PALM fisso: centro sinistra del widget
                                    # X range: 0 → L_tot + margine   Y range: centrato su P0
                                    margin_x = 20  # margine a destra del dito
                                    margin_y = L_tot // 2  # mezzo dito sopra e sotto

                                    P0 = np.array([0.0, 0.0])   # PALM: origine in (0, 0)
                                    P1 = P0 + L_metacarpo * np.array([np.cos(np.deg2rad(0)), np.sin(np.deg2rad(0))])
                                    P2 = P1 + L_prossimale * np.array([np.cos(np.deg2rad(theta_mcp)),  np.sin(np.deg2rad(theta_mcp))])
                                    P3 = P2 + L_media * np.array([np.cos(np.deg2rad(theta_mcp+theta_pip)),  np.sin(np.deg2rad(theta_mcp+theta_pip))])
                                    P4 = P3 + L_distale * np.array([np.cos(np.deg2rad(theta_mcp+theta_pip+theta_dip)),  np.sin(np.deg2rad(theta_mcp+theta_pip+theta_dip))])

                                    joints = [P0, P1, P2, P3, P4]

                                    # Range fissi: X da -margin_x a L_tot+margin_x, Y centrato su 0
                                    self.plot_frame_2.setXRange(-margin_x, L_tot + margin_x, padding=0)
                                    self.plot_frame_2.setYRange(-margin_y, margin_y, padding=0)

                                    # Aggiorno i 4 segmenti
                                    connections = [(P0, P1), (P1, P2), (P2, P3), (P3, P4)]
                                    for i, (pt_a, pt_b) in enumerate(connections):
                                        self.skeleton_lines[i].setData(
                                            [pt_a[0], pt_b[0]],
                                            [pt_a[1], pt_b[1]]
                                        )

                                    # Aggiorno punti e label
                                    self.skeleton_points.setData(
                                        x=[p[0] for p in joints],
                                        y=[p[1] for p in joints]
                                    )
                                    for label, joint in zip(self.skeleton_labels, joints):
                                        label.setPos(joint[0], joint[1])

                                except (NameError, ZeroDivisionError, ValueError, TypeError):
                                    pass
                                                              
                        
                        # Plotto le tracce ottenute 

                            for track in self.TRACKS:

                                if track.name_setted == True:

                                    cv2.rectangle(self.output_image, (track.x, track.y), (track.x + track.w, track.y + track.h), (0, 255, 0), 2)

                                else:

                                    cv2.rectangle(self.output_image, (track.x, track.y), (track.x + track.w, track.y + track.h), (255, 0, 0), 2)


                                # Mostro il nome assegnato alla Trace
                                cv2.putText(self.output_image, track.name, (int(track.x -10),int(track.y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                                if(len(track.traj_y)>15):

                                    # Mostro la traiettoria grezza 
                                    spline_pts = np.vstack((track.traj_x[-14:-1], track.traj_y[-14:-1])).T.astype(np.int32)
                                    cv2.polylines(self.output_image, [spline_pts], isClosed=False, color=(255, 0, 0), thickness=2)

                                    # Mostro la traiettoria filtrata
                                    spline_pts_filt = np.vstack((track.traj_x_filt[-14:-1], track.traj_y_filt[-14:-1])).T.astype(np.int32)
                                    cv2.polylines(self.output_image, [spline_pts_filt], isClosed=False, color=(0, 255, 0), thickness=2)
                
                else: # Se hai tolto la spunta dal Tracking_checkbox
                    if len(self.TRACKS) > 0:
                        print("Tracking fermato. Reset delle tracce e dei centimetri.")
                    self.TRACKS.clear()
                    self.fixed_distances_cm = None  # Resetta i centimetri in memoria

                h, w, ch = self.output_image.shape
                bytes_per_line =  ch*w 
                qt_mask = QtGui.QImage(self.output_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
                self.Mask_frame.setPixmap(QtGui.QPixmap.fromImage(qt_mask))

                

                                
            else: # Se il thresholding NON è abilitato
                self.Mask_frame.setText("Mask OFF") # Disabilito la visualizzazione della maschera

            # Per l'immagine non segmentata
            h, w, ch = self.frame.shape 
            bytes_per_line =  ch * w 
            qt_frame = QtGui.QImage(self.frame.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
            self.Camera_frame.setPixmap(QtGui.QPixmap.fromImage(qt_frame))


# MAIN del programma 
if __name__ == "__main__":
    
    # YOLO viene caricato solo se abiliti Object Detection dalla GUI.

    app = QApplication([]) 
    MainWindow = QtWidgets.QMainWindow()
    window = My_GUI(MainWindow)  
    window.show() 
    app.exec()  