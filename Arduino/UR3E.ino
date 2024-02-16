#define INPUT_4 13 
#define INPUT_5 12 

void setup() {
  // Initialise les pins comme sortie
  pinMode(INPUT_4, OUTPUT);
  pinMode(INPUT_5, OUTPUT);
  
  //leds.init();
  // Démarre la communication série à 9600 bauds
  Serial.begin(9600);
}

void loop() {
  // Vérifie si des données sont disponibles à lire sur le port série
  if (Serial.available() > 0) {
    // Lit le premier byte disponible (ne lit pas plus d'un caractère à la fois)
    char receivedChar = Serial.read();
    
    // Active ou désactive la sortie en fonction du caractère reçu
    if (receivedChar == '1') {
      digitalWrite(INPUT_4, HIGH); // Active la sortie
      delay(500);
      digitalWrite(INPUT_4, LOW); // Désactive la sortie
    }
    if (receivedChar == '2') {
      digitalWrite(INPUT_5, HIGH);
      delay(500);
      digitalWrite(INPUT_5, LOW); // Désactive la sortie
    }
    else if (receivedChar == '0') {
      digitalWrite(INPUT_4, LOW); // Désactive la sortie
      digitalWrite(INPUT_4, LOW); // Désactive la sortie
      digitalWrite(INPUT_5, LOW); // Désactive la sortie

    }
  }
}
