import sys
import numpy as np
import cv2
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QLineEdit, QPushButton, QComboBox
from PySide6.QtGui import QIcon
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import glob
import serial
from octoprint_client import OctoPrintClient
from camera_buffer_cleaner_thread import CameraBufferCleanerThread
import time

class ApplicationWindow(QMainWindow):
    def __init__(self):
        '''Initialiser la fenêtre de l'application.'''
        super().__init__()

        # Charger l'image en niveaux de gris
        self.image = cv2.imread('images/capture0.jpg')
        # Charger un array d'image à partir du dossier Images
        self.images = [cv2.imread(file) for file in glob.glob('images/*.jpg')]
        # Déclarer la caméra
        self.cap = None
        # Déclarer l'arduino
        self.arduino = None

        # Initialiser l'arduino
        try :
            self.arduino = serial.Serial('COM3', 9600)
        except:
            print("Erreur lors de la connexion à l'arduino.")
        # Déclarer le thread de nettoyage du tampon de la caméra
        self.cam_cleaner = None

        print(self.images.__len__())

        if self.images is None:
            print("Erreur lors du chargement des images. Veuillez vérifier la présence d'image dans le chemin.")
            sys.exit()

        self.initUI()

    def nextImage(self):
        """Afficher l'image suivante."""
        if self.current_image_index < self.images.__len__():
            self.image = self.images[self.current_image_index]
            print(self.current_image_index)
            self.current_image_index += 1
            self.updateImage()

    def previousImage(self):
        """Afficher l'image précédente."""
        if self.current_image_index > 0:
            self.image = self.images[self.current_image_index]
            print(self.current_image_index)
            self.current_image_index -= 1
            self.updateImage()

    def initUI(self):
        """Initialiser l'interface utilisateur."""
        self.setWindowTitle('Projet encolleuse')
        self.setGeometry(100, 100, 800, 600)
        # Changer l'icon de la fenêtre
        self.setWindowIcon(QIcon('images/icon.png'))

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QHBoxLayout(centralWidget)

        # Panneau de contrôle à gauche
        controlPanelLayout = QVBoxLayout()
        layout.addLayout(controlPanelLayout, 1)

        # Panneau d'affichage à droite
        displayPanelLayout = QVBoxLayout()
        layout.addLayout(displayPanelLayout, 3)

        # Créer un canevas pour afficher l'image et l'histogramme
        self.canvas = FigureCanvas(Figure(figsize=(5, 4)))
        self.canvas.figure.set_facecolor('#31363b')
        displayPanelLayout.addWidget(self.canvas)

        # Afficher un selecteur entre vidéo direct et image statique
        self.comboBox = QComboBox(self)
        self.comboBox.addItem("Image statique")
        self.comboBox.addItem("Vidéo direct")
        self.comboBox.currentTextChanged.connect(self.sourceSelected)
        controlPanelLayout.addWidget(self.comboBox)

        # Afficher des flèches pour passer d'une image à l'autre
        self.current_image_index = 0
        self.pushButtonPrevious = QPushButton("Précédent", self)
        self.pushButtonPrevious.clicked.connect(self.previousImage)
        controlPanelLayout.addWidget(self.pushButtonPrevious)
        self.pushButtonNext = QPushButton("Suivant", self)
        self.pushButtonNext.clicked.connect(self.nextImage)
        controlPanelLayout.addWidget(self.pushButtonNext)

        # Créer deux axes horizontal dans le canevas : un pour l'image et un pour l'histogramme horizontal
        self.ax1, self.ax2, self.ax3 = self.canvas.figure.subplots(3, 1, gridspec_kw={'height_ratios': [2, 1, 1]})

        # Afficher l'image et l'histogramme (ax1: image, ax2: histogramme, ax3: texte sur 5 lignes)
        # ax1
        self.ax1.imshow(self.image, cmap='gray')  # Afficher l'image en niveaux de gris par défaut
        self.ax1.axis('on')  # Cacher les axes pour l'image
        self.ax1.tick_params(axis='x', colors='#1de9b6')  # Couleur des graduations en x
        self.ax1.tick_params(axis='y', colors='#1de9b6')  # Couleur des graduations en y
        self.ax1.spines['bottom'].set_color('#1de9b6') # Couleur de l'image
        self.ax1.spines['top'].set_color('#1de9b6')
        self.ax1.spines['right'].set_color('#1de9b6')
        self.ax1.spines['left'].set_color('#1de9b6')
        # ax2
        self.ax2.set_facecolor('#31363b')  # Couleur de fond de l'histogramme
        self.ax2.tick_params(axis='x', colors='#1de9b6')  # Couleur des graduations en x
        self.ax2.tick_params(axis='y', colors='#1de9b6')  # Couleur des graduations en y
        self.ax2.spines['bottom'].set_color('#1de9b6')# couleur de l'histogramme
        self.ax2.spines['top'].set_color('#1de9b6')
        self.ax2.spines['right'].set_color('#1de9b6')
        self.ax2.spines['left'].set_color('#1de9b6')

        # Afficher le texte dans ax3
        self.ax3.axis('off')
        self.ax3.text(0, 0.8, "Contour gauche : ", ha='left', va='center', fontsize=14, color='#1de9b6')
        self.ax3.text(0, 0.6, "Contour droite : ", ha='left', va='center', fontsize=14, color='#1de9b6')
        self.ax3.text(0, 0.4, "Contour bas    : ", ha='left', va='center', fontsize=14, color='#1de9b6')
        self.ax3.text(0, 0.2, "Contour haut   : ", ha='left', va='center', fontsize=14, color='#1de9b6')


        # Afficher l'histogramme initial
        self.ax2.hist(self.image.ravel(), bins=256, range=[0,256], color='#1de9b6')
        self.ax2.set_xlim([0, 256])

        # Ajouter une case à cocher pour le filtre passe-bande
        self.checkBoxBandPassFilter = QCheckBox("Appliquer Filtre Passe-Bande", self)
        self.checkBoxBandPassFilter.stateChanged.connect(self.updateImage)
        controlPanelLayout.addWidget(self.checkBoxBandPassFilter)

        # Ajouter deux champs de texte pour les valeurs du filtre passe-bande
        # Valeur minimale
        self.lineEditMin = QLineEdit(self)
        self.lineEditMin.setPlaceholderText('Valeur minimale')
        self.lineEditMin.setText('0') # Valeur par défaut
        # Valeur maximale
        self.lineEditMax = QLineEdit(self)
        self.lineEditMax.setPlaceholderText('Valeur maximale')
        self.lineEditMax.setText('255') # Valeur par défaut
        # Connecter les champs de texte à la fonction de mise à jour
        self.lineEditMin.textChanged.connect(self.updateImage)
        self.lineEditMax.textChanged.connect(self.updateImage)
        # Ajouter les champs de texte à la mise en page
        controlPanelLayout.addWidget(self.lineEditMin)
        controlPanelLayout.addWidget(self.lineEditMax)

        # Ajouter une case à cocher pour le filtre laplacien
        self.checkBoxLaplaceFilter = QCheckBox("Appliquer filtre laplacien", self)
        self.checkBoxLaplaceFilter.stateChanged.connect(self.updateImage)
        controlPanelLayout.addWidget(self.checkBoxLaplaceFilter)

        # Ajouter une case à cocher pour la détection de contour
        self.checkBoxEdgeDetection = QCheckBox("Détection de contour", self)
        self.checkBoxEdgeDetection.stateChanged.connect(self.updateImage)
        controlPanelLayout.addWidget(self.checkBoxEdgeDetection)

        # Permettre la selection de la zone de collage
        self.checkBoxCollage = QCheckBox("Selection de la zone de collage", self)
        self.checkBoxCollage.stateChanged.connect(self.updateImage)
        controlPanelLayout.addWidget(self.checkBoxCollage)

        # Ajouter un bouton valider pour le bras robot
        self.pushButtonValider = QPushButton("Valider", self)
        self.pushButtonValider.clicked.connect(self.valider)
        controlPanelLayout.addWidget(self.pushButtonValider)

        # Ajout un bouton rebus pour le bras robot
        self.pushButtonRebus = QPushButton("Rebus", self)
        self.pushButtonRebus.clicked.connect(self.rebus)
        controlPanelLayout.addWidget(self.pushButtonRebus)

        # Ajout un bouton de test pour l'octoprint
        self.pushButtonInitPlateau = QPushButton("Initialiser le plateau", self)
        self.pushButtonInitPlateau.clicked.connect(self.deplacerPlateau)
        controlPanelLayout.addWidget(self.pushButtonInitPlateau)

        # Ajout d'un bouton pour le lancement du gcode
        self.pushButtonGcode = QPushButton("Lancer le gcode", self)
        self.pushButtonGcode.clicked.connect(self.lancerGcode)
        controlPanelLayout.addWidget(self.pushButtonGcode)

        # Ajouter un bouton pour initialiser la position de l'octoprint
        self.pushButtonInit = QPushButton("Initialiser", self)
        self.pushButtonInit.clicked.connect(self.initOctoPrint)
        controlPanelLayout.addWidget(self.pushButtonInit)

        # Ajouter un bouton rouge d'arrêt d'urgence
        self.pushButtonStop = QPushButton("Arrêt d'urgence", self)
        self.pushButtonStop.clicked.connect(self.stopOperation)
        self.pushButtonStop.setStyleSheet("background-color: red")
        controlPanelLayout.addWidget(self.pushButtonStop)

        # Ajout d'un bouton quitter pour fermer l'application
        self.pushButtonQuit = QPushButton("Quitter", self)
        self.pushButtonQuit.clicked.connect(self.closeApp)
        controlPanelLayout.addWidget(self.pushButtonQuit)

    def closeApp(self):
        """Fermer l'application."""
        # Fermer le thread s'il est en cours d'exécution
        if self.cam_cleaner is not None:
            self.cam_cleaner.stop()
        if self.arduino is not None:
            self.arduino.close()
        if self.cap is not None:
            self.cap.release()
        self.close()

    def initOctoPrint(self):
        '''Initialiser l'imprimante 3D'''
        octo_client = OctoPrintClient('http://10.167.50.3/api/', 'B611302D163841BFB5F0225A90BF0B2F')
        octo_client.init_position()

    def stopOperation(self):
        '''Arrêter l'opération en cours'''
        octo_client = OctoPrintClient('http://10.167.50.3/api/', 'B611302D163841BFB5F0225A90BF0B2F')
        octo_client.cancel_print()
        print("Arrêt d'urgence")

    def lancerGcode(self):
        '''Lancer le gcode sur l'imprimante 3D'''
        octo_client = OctoPrintClient('http://10.167.50.3/api/', 'B611302D163841BFB5F0225A90BF0B2F')
        #octo_client.start_print_job('/home/pi/.octoprint/uploads/global3.gcode')
        octo_client.start_print_job('global3.gcode', 'local')

    def deplacerPlateau(self):
        '''Envoyer une commande Gcode à l'imprimante 3D'''
        octo_client = OctoPrintClient('http://10.167.50.3/api/', 'B611302D163841BFB5F0225A90BF0B2F')
        octo_client.send_gcode_command(['G1 X117.00 Y250 Z20 F2000'])

    def valider(self):
        '''Envoyer la commande de validation au bras robot'''
        # Déplacer le plateau
        self.deplacerPlateau()
        # Attendre 1 demi seconde
        time.sleep(0.5)
        # Envoyer la commande au bras robot
        self.arduino.write(b'1')
        print("Valider")

    def rebus(self):
        '''Envoyer la commande de rebus au bras robot'''
        # Déplacer le plateau
        self.deplacerPlateau()
        # Attendre 1 demi seconde
        time.sleep(0.5)
        # Envoyer la commande au bras robot
        self.arduino.write(b'2')
        print("Rebus")

    def sourceSelected(self, text):
        """Afficher l'image statique ou la vidéo en direct depuis une ip en fonction de l'option sélectionnée."""
        if text == "Image statique":
            # release la caméra si elle est ouverte
            if self.cap is not None:
                self.cap.release()
            self.image = self.images[self.current_image_index]
            # redimensionner l'image pour l'affichage
            self.image = cv2.resize(self.image, (800, 500))
            self.updateImage()
            print("Image statique")
        elif text == "Vidéo direct":
            # Initialiser la caméra
            try:
                self.cap = cv2.VideoCapture('http://10.167.50.3/webcam/?action=stream')
                # Créer un thread pour nettoyer le tampon de la caméra
                cam_cleaner = CameraBufferCleanerThread(self.cap)
                while True:
                    if cam_cleaner.last_frame is not None:
                        self.image = cam_cleaner.last_frame
                        self.updateImage()

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                # Arrêter le nettoyage du tampon de la caméra
                cam_cleaner.stop()
            except:
                print("Erreur lors de la connexion à la caméra.")
                # Rebasculer sur l'image statique
                self.comboBox.setCurrentIndex(0)

    def detecterContours(self, image):
        '''
        Détecter les contours dans une image
        '''
        # Définir les zones de détection de contour dans l'image
        if self.comboBox.currentText() == "Image statique":
            zones = [
                #       x1   y1   x2   y2
                (70, 75, 100, 170),  # Zone gauche
                (320, 75, 360, 180),  # Zone droite
                (110, 55, 300, 80),  # Zone haut
                (110, 170, 300, 220)   # Zone bas
            ]
        elif self.comboBox.currentText() == "Vidéo direct":
            zones = [
            #       x1   y1   x2   y2
                   (230, 290, 260, 370),  # Zone gauche
                   (280, 380, 490, 405),  # Zone droite
                   (500, 290, 520, 370),  # Zone haut
                   (280, 245, 490, 270)   # Zone bas
               ]

       # Appliquer la détection de contour uniquement dans les zones sélectionnées
        if self.checkBoxEdgeDetection.isChecked():

            distance_px = [0, 0, 0, 0]

            for zone in zones:
                x1, y1, x2, y2 = zone
                # Appliquer un filtre laplacien pour accentuer les contours
                edges = cv2.Canny(image[y1:y2, x1:x2], 100, 200, 5, L2gradient=True)

                # Extraire les contours de l'image filtrée pour chaque zone
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # Ajuster les coordonnées des contours à la position réelle dans l'image
                adjusted_contours = [contour + np.array([[x1, y1]]) for contour in contours]

                # Afficher les contours sur l'image
                cv2.drawContours(image, adjusted_contours, -1, (29, 233, 182), 3)

                # Calculer la distance minimale entre les contours
                zone_index = zones.index(zone)
                distance_px[zone_index] = self.find_min_distance(contours[0:1], contours[1:2])

            # Dessiner simplement un rectangle autour de chaque zone de collage
            for zone in zones:
               x1, y1, x2, y2 = zone
               cv2.rectangle(image, (x1, y1), (x2, y2), (29, 233, 182), 2)

            print(distance_px)

            # Mettre à jour l'affichage
            self.ax3.text(0, 0.8, f"Contour gauche : {distance_px[0]*0.2:.2f} mm.", ha='left', va='center', fontsize=14, color='#1de9b6')
            self.ax3.text(0, 0.6, f"Contour droite : {distance_px[1]*0.2:.2f} mm.", ha='left', va='center', fontsize=14, color='#1de9b6')
            self.ax3.text(0, 0.4, f"Contour bas    : {distance_px[2]*0.2:.2f} mm.", ha='left', va='center', fontsize=14, color='#1de9b6')
            self.ax3.text(0, 0.2, f"Contour haut   : {distance_px[3]*0.2:.2f} mm.", ha='left', va='center', fontsize=14, color='#1de9b6')

            # Mettre à jour l'affichage
            self.ax1.clear()
            self.ax1.imshow(image, cmap='gray')
            self.ax1.axis('on')
            self.canvas.draw()
        else:
           # Dessiner simplement un rectangle autour de chaque zone de collage
           for zone in zones:
               x1, y1, x2, y2 = zone
               cv2.rectangle(image, (x1, y1), (x2, y2), (29, 233, 182), 2)

           # Mettre à jour l'affichage
           self.ax1.clear()
           self.ax1.imshow(image, cmap='gray')
           self.ax1.axis('on')
           self.canvas.draw()

    # Fonction pour le calcul de la distance minimale entre deux contours
    def find_min_distance(self, contours1, contours2):
           """Calcul de la distance minimale entre deux ensembles de contours."""
           min_dist = np.inf
           for contour1 in contours1:
               for contour2 in contours2:
                   # Convertir les contours en numpy arrays pour le calcul de distance
                   contour_array1 = np.squeeze(contour1)
                   contour_array2 = np.squeeze(contour2)
                   # Calculer toutes les distances entre les points des deux contours
                   # distance = sqrt((x1 - x2)^2 + (y1 - y2)^2)
                   dist = np.sqrt(np.sum((contour_array1[:, None, :] - contour_array2[None, :, :]) ** 2, axis=2))
                   # Trouver la distance minimale
                   min_dist = min(min_dist, np.min(dist))
           return min_dist

    def updateImage(self):
        """Mettre à jour l'image et l'histogramme en fonction des cases à cocher."""
        # Réinitialiser l'image filtrée à l'image originale
        image_filtree = self.image.copy()
        # Appliquer le filtre passe-bande
        if self.checkBoxBandPassFilter.isChecked():
            # Convert self.lineEditMin.text() and self.lineEditMax.text() to integers
            int_min = int(self.lineEditMin.text())
            int_max = int(self.lineEditMax.text())
            image_filtree = np.where((image_filtree >= int_min) & (image_filtree <= int_max), image_filtree, 0)
        # Appliquer le filtre laplacien
        if self.checkBoxLaplaceFilter.isChecked():
            # convertir l'image en niveaux de gris
            image_filtree = cv2.cvtColor(image_filtree, cv2.COLOR_BGR2GRAY)
            image_filtree = cv2.Laplacian(image_filtree, cv2.CV_64F)
        # Appliquer la détection de contour
        if self.checkBoxCollage.isChecked() or self.checkBoxEdgeDetection.isChecked():
            self.detecterContours(image_filtree)

        # Mettre à jour l'image et l'histogramme
        self.ax1.clear()
        self.ax1.imshow(image_filtree, cmap='gray')
        self.ax1.axis('on')
        # Afficher l'index de l'image et la distance entre les contours si elle existe sinon l'index de l'image
        if self.comboBox.currentText() == "Image statique":
            self.ax1.set_title(f"Image {self.current_image_index}", color='#1de9b6')

        elif self.comboBox.currentText() == "Vidéo direct":
            self.ax1.set_title(f"Image en direct", color='#1de9b6')


        self.ax2.clear()
        self.ax2.hist(image_filtree.ravel(), bins=256, range=[0, 256], color='#1de9b6')
        self.ax2.set_xlim([0, 256])
        # Mettre à jour le canevas
        self.canvas.draw()
