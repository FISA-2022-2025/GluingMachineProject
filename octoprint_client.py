import requests

class OctoPrintClient:
    def __init__(self, base_url, api_key):
        """
        Initialise le client OctoPrint.
        :param base_url: URL de base du serveur OctoPrint, e.g., 'http://10.167.50.3/api/'
        :param api_key: Clé API pour l'authentification avec le serveur OctoPrint.
        """
        self.base_url = base_url
        self.headers = {'X-Api-Key': api_key}


    def init_position(self):
        """
        Initialise la position de l'extrudeuse.
        """
        self.send_gcode_command('G28')
        self.send_gcode_command('G1 Z30 F600')


    def send_gcode_command(self, commands):
        """
        Envoie une commande G-code au serveur OctoPrint.
        :param commands: Une liste de commandes G-code à envoyer.
        """
        if not isinstance(commands, list):
            commands = [commands]

        data = {"commands": commands}
        response = requests.post(self.base_url + 'printer/command', json=data, headers=self.headers)

        if response.status_code == 204:
            print("Commande G-code envoyée avec succès.")
        else:
            print(f"Erreur lors de l'envoi de la commande G-code: {response.status_code}")
            print(response.text)

    def start_print_job(self, file_path, location='local'):
            """
            Sélectionne et démarre une impression d'un fichier G-code stocké sur OctoPrint.
            :param file_path: Le chemin du fichier G-code sur OctoPrint.
            :param location: L'emplacement du fichier, 'local' ou 'sd', par défaut à 'local'.
            """
            # Sélection du fichier pour l'impression
            select_payload = {
                "command": "select",
                "print": True  # Ne démarre pas l'impression immédiatement après la sélection
            }
            select_response = requests.post(f"{self.base_url}files/{location}/{file_path}", json=select_payload, headers=self.headers)

            if select_response.status_code == 204:
                print("Fichier G-code selectionné avec succès.")
            else:
                print(f"Erreur lors de la sélection du fichier G-code: {select_response.status_code}")
                print(select_response.text)

    def cancel_print(self):
        """
        Annule l'impression en cours.
        """
        self.send_gcode_command('M112')
