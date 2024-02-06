import sys
import numpy as np
import cv2
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QCheckBox, QLineEdit
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Charger l'image en niveaux de gris
        self.image = cv2.imread('images/capture0.jpg')

        if self.image is None:
            print("Erreur lors du chargement de l'image. Veuillez vérifier le chemin.")
            sys.exit()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Projet encolleuse')
        self.setGeometry(100, 100, 800, 600)

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        self.canvas = FigureCanvas(Figure(figsize=(5, 4)))
        layout.addWidget(self.canvas)

        # Créer deux axes dans le canevas : un pour l'image et un pour l'histogramme
        self.ax1, self.ax2 = self.canvas.figure.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})

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


    def updateImage(self, state):
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
                roi = cv2.Canny(image_filtree[y1:y2, x1:x2], 100, 200)
                masque[y1:y2, x1:x2, 0] = roi  # Appliquer le contour en canal Bleu pour l'exemple
                #masque[y1:y2, x1:x2, 1] = roi  # Appliquer le contour en canal Vert pour l'exemple
                #masque[y1:y2, x1:x2, 2] = roi  # Conserver le rouge où il n'y a pas de contour

                # Ajouter le masque à l'image filtrée
                image_filtree = np.where(masque > 0, 255, image_filtree)  # Assigne une intensité élevée aux contours
            else:
                # Si la détection de contour n'est pas sélectionnée, dessiner simplement un rectangle autour de la zone de collage
                image_filtree = cv2.rectangle(image_filtree, (x1, y1), (x2, y2), (0, 255, 0), 2)


        # Mettre à jour l'image et l'histogramme
        self.ax1.clear()
        self.ax1.imshow(image_filtree, cmap='gray')
        self.ax1.axis('on')

        self.ax2.clear()
        self.ax2.hist(image_filtree.ravel(), bins=256, range=[0, 256], color='black')
        self.ax2.set_xlim([0, 256])
        # Mettre à jour le canevas
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ApplicationWindow()
    ex.show()
    sys.exit(app.exec())
