import sys
import numpy as np
import cv2
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QCheckBox, QLineEdit, QPushButton, QComboBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import glob
import serial
import asyncio

class ApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Charger l'image en niveaux de gris
        self.image = cv2.imread('images/capture0.jpg')
        # Charger un array d'image à partir du dossier Images
        self.images = [cv2.imread(file) for file in glob.glob('images/*.jpg')]
        # Initialiser la caméra
        self.cap = cv2.VideoCapture('http://10.167.50.3/webcam/?action=stream')

        # Initialiser l'arduino
        self.arduino = serial.Serial('COM3', 9600)

        print(self.images.__len__())

        if self.images is None:
            print("Erreur lors du chargement des images. Veuillez vérifier la présence d'image dans le chemin.")
            sys.exit()

        self.initUI()

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
                    dist = np.sqrt(np.sum((contour_array1[:, None, :] - contour_array2[None, :, :]) ** 2, axis=2))
                    # Trouver la distance minimale
                    min_dist = min(min_dist, np.min(dist))
            return min_dist

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

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        self.canvas = FigureCanvas(Figure(figsize=(5, 4)))
        layout.addWidget(self.canvas)

        # Afficher un selecteur entre vidéo direct et image statique
        self.comboBox = QComboBox(self)
        self.comboBox.addItem("Image statique")
        self.comboBox.addItem("Vidéo direct")
        self.comboBox.currentTextChanged.connect(self.sourceSelected)
        layout.addWidget(self.comboBox)


        # Afficher des flèches pour passer d'une image à l'autre
        self.current_image_index = 0
        self.pushButtonPrevious = QPushButton("Précédent", self)
        self.pushButtonPrevious.clicked.connect(self.previousImage)
        layout.addWidget(self.pushButtonPrevious)
        self.pushButtonNext = QPushButton("Suivant", self)
        self.pushButtonNext.clicked.connect(self.nextImage)
        layout.addWidget(self.pushButtonNext)

        # Créer deux axes horizontal dans le canevas : un pour l'image et un pour l'histogramme horizontal
        self.ax1, self.ax2 = self.canvas.figure.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

        self.ax1.imshow(self.image, cmap='gray')  # Afficher l'image en niveaux de gris par défaut
        self.ax1.axis('on')  # Cacher les axes pour l'image

        # Afficher l'histogramme initial
        self.ax2.hist(self.image.ravel(), bins=256, range=[0,256], color='black')
        self.ax2.set_xlim([0, 256])

        # Ajouter une case à cocher pour le filtre passe-bande
        self.checkBoxBandPassFilter = QCheckBox("Appliquer Filtre Passe-Bande", self)
        self.checkBoxBandPassFilter.stateChanged.connect(self.updateImage)
        layout.addWidget(self.checkBoxBandPassFilter)

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
        layout.addWidget(self.lineEditMin)
        layout.addWidget(self.lineEditMax)

        # Ajouter une case à cocher pour le filtre laplacien
        self.checkBoxLaplaceFilter = QCheckBox("Appliquer filtre laplacien", self)
        self.checkBoxLaplaceFilter.stateChanged.connect(self.updateImage)
        layout.addWidget(self.checkBoxLaplaceFilter)

        # Ajouter une case à cocher pour la détection de contour
        self.checkBoxEdgeDetection = QCheckBox("Détection de contour", self)
        self.checkBoxEdgeDetection.stateChanged.connect(self.updateImage)
        layout.addWidget(self.checkBoxEdgeDetection)

        # Permettre la selection de la zone de collage
        self.checkBoxCollage = QCheckBox("Selection de la zone de collage", self)
        self.checkBoxCollage.stateChanged.connect(self.updateImage)
        layout.addWidget(self.checkBoxCollage)

        # Ajouter un bouton valider pour le bras robot
        self.pushButtonValider = QPushButton("Valider", self)
        self.pushButtonValider.clicked.connect(self.valider)
        layout.addWidget(self.pushButtonValider)

        # Ajout un bouton rebus pour le bras robot
        self.pushButtonRebus = QPushButton("Rebus", self)
        self.pushButtonRebus.clicked.connect(self.rebus)
        layout.addWidget(self.pushButtonRebus)

        # Ajout d'un bouton quitter pour fermer l'application
        self.pushButtonQuit = QPushButton("Quitter", self)
        self.pushButtonQuit.clicked.connect(self.close)
        layout.addWidget(self.pushButtonQuit)

    def valider(self):
        # Envoyer la commande au bras robot
        self.arduino.write(b'1')
        print("Valider")

    def rebus(self):
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
            self.updateImage()
            print("Image statique")
        elif text == "Vidéo direct":
            # Vérifier si la caméra est ouverte
            if not self.cap.isOpened():
                print("Erreur lors de l'ouverture de la caméra.")
                # Rebasculer sur l'image statique
                self.comboBox.setCurrentIndex(0)
                return
            while True:
                # Lire l'image depuis la caméra
                ret, frame = self.cap.read()
                if ret:
                    # remplacer l'image par la nouvelle image
                    self.image = frame
                    self.updateImage()
                # Quitter la boucle si la touche 'q' est enfoncée
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break


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
            x1, y1, x2, y2 = 100, 150, 300, 200  # Coordonnées de la zone de collage, TODO : interactif
            # Appliquer la détection de contour uniquement dans la zone sélectionnée
            if self.checkBoxEdgeDetection.isChecked():
                # Créer un masque rouge
                masque = np.zeros_like(image_filtree)
                masque[:] = [0, 0, 0]  # Rouge en BGR

                # Appliquer une opération, comme la détection de contours, dans la zone sélectionnée
                edges = cv2.Canny(image_filtree[y1:y2, x1:x2], 100, 200)
                masque[y1:y2, x1:x2, 0] = edges  # Appliquer le contour en canal Bleu pour l'exemple
                #masque[y1:y2, x1:x2, 1] = edges  # Appliquer le contour en canal Vert pour l'exemple
                #masque[y1:y2, x1:x2, 2] = edges  # Conserver le rouge où il n'y a pas de contour

                # Ajouter le masque à l'image filtrée
                image_filtree = np.where(masque > 0, 255, image_filtree)  # Assigne une intensité élevée aux contours

                # Extraire les contours de l'image filtrée
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # Ajuster les coordonnées des contours à la position réelle dans l'image
                adjusted_contours = [contour + np.array([[x1, y1]]) for contour in contours]

                # Calculer la distance entre les deux premiers contours trouvés
                if len(contours) > 1:
                    distance_px = self.find_min_distance(contours[0:1], contours[1:2])
                    # TODO : convertir la distance en mm
                    print(f"Distance minimale entre les deux premiers contours: {distance_px} pixels soit {distance_px*0.2:.2f} mm.")

                    # Afficher les contours et la distance sur l'image
                    cv2.drawContours(image_filtree, adjusted_contours, -1, (0, 255, 0), 3)
                    self.ax1.clear()
                    self.ax1.imshow(image_filtree, cmap='gray')
                    self.ax1.axis('on')
                    self.canvas.draw()
                else:
                    print("Moins de deux contours ont été détectés.")
            else:
                # Si la détection de contour n'est pas sélectionnée, dessiner simplement un rectangle autour de la zone de collage
                image_filtree = cv2.rectangle(image_filtree, (x1, y1), (x2, y2), (0, 255, 0), 2)


        # Mettre à jour l'image et l'histogramme
        self.ax1.clear()
        self.ax1.imshow(image_filtree, cmap='gray')
        self.ax1.axis('on')
        # Afficher l'index de l'image et la distance entre les contours si elle existe sinon l'index de l'image
        if self.checkBoxEdgeDetection.isChecked():
            self.ax1.set_title(f"Image {self.current_image_index} - Distance entre les contours: {distance_px*0.2:.2f} mm")
        else:
            self.ax1.set_title(f"Image {self.current_image_index}")


        self.ax2.clear()
        self.ax2.hist(image_filtree.ravel(), bins=256, range=[0, 256], color='black')
        self.ax2.set_xlim([0, 256])
        # Mettre à jour le canevas
        self.canvas.draw()

if __name__ == '__main__':
    """Exécuter l'application."""
    app = QApplication(sys.argv)
    ex = ApplicationWindow()
    ex.show()
    sys.exit(app.exec())
