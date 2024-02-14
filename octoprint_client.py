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
