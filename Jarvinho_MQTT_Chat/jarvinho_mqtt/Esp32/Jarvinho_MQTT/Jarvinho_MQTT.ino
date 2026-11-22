#include <WiFi.h>
#include <WiFiClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// =====================================================
// CONFIGURACOES DE REDE
// =====================================================

const char* WIFI_SSID = "Gabriel_Planet/3212-1433-2.4";
const char* WIFI_PASSWORD = "As250407";

const char* MQTT_HOST = "broker.emqx.io";
const int MQTT_PORT = 1883;

// O backend Python recebe as perguntas e publica as respostas.
// O ESP32 nao deve assinar o topico de perguntas nem publicar
// respostas para evitar duplicidade com o backend.

const char* TOPIC_STATUS = "jarvinho/status";

// =====================================================
// CONFIGURACOES DO DISPLAY OLED
// =====================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_SDA 8
#define OLED_SCL 9

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// =====================================================
// MQTT
// =====================================================

WiFiClient mqttWifiClient;
PubSubClient mqtt(mqttWifiClient);

String expressaoAtual = "neutro";

unsigned long ultimaPiscada = 0;
unsigned long proximaPiscada = 4000;

unsigned long ultimaTentativaWiFi = 0;
unsigned long ultimaTentativaMQTT = 0;

const unsigned long INTERVALO_WIFI = 5000;
const unsigned long INTERVALO_MQTT = 3000;

// =====================================================
// DESENHO DO ROSTO
// =====================================================

void desenharRosto(const String& expressao) {
  expressaoAtual = expressao;

  display.clearDisplay();

  if (expressao == "feliz") {
    display.fillCircle(37, 25, 9, SSD1306_WHITE);
    display.fillCircle(91, 24, 9, SSD1306_WHITE);

    display.fillCircle(37, 25, 5, SSD1306_BLACK);
    display.fillCircle(91, 24, 5, SSD1306_BLACK);

    display.fillCircle(64, 42, 11, SSD1306_WHITE);
    display.fillCircle(64, 37, 11, SSD1306_BLACK);

  } else if (expressao == "pensando") {
    display.fillCircle(37, 25, 9, SSD1306_WHITE);
    display.fillCircle(91, 24, 9, SSD1306_WHITE);

    display.fillCircle(37, 23, 5, SSD1306_BLACK);
    display.fillCircle(91, 22, 5, SSD1306_BLACK);

    display.drawLine(54, 41, 74, 41, SSD1306_WHITE);

    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(113, 7);
    display.print("?");

  } else if (expressao == "piscando") {
    display.drawLine(30, 25, 46, 25, SSD1306_WHITE);
    display.drawLine(82, 25, 98, 25, SSD1306_WHITE);
    display.drawLine(54, 43, 74, 43, SSD1306_WHITE);

  } else if (expressao == "raiva") {
    display.fillCircle(37, 25, 9, SSD1306_WHITE);
    display.fillCircle(91, 24, 9, SSD1306_WHITE);

    display.drawLine(42, 51, 59, 41, SSD1306_WHITE);
    display.drawLine(59, 41, 75, 51, SSD1306_WHITE);
    display.drawLine(75, 51, 91, 41, SSD1306_WHITE);

  } else if (expressao == "morteSubita") {
    display.drawLine(46, 44, 86, 44, SSD1306_WHITE);

    display.drawLine(32, 15, 43, 30, SSD1306_WHITE);
    display.drawLine(43, 15, 32, 30, SSD1306_WHITE);

    display.drawLine(87, 15, 98, 30, SSD1306_WHITE);
    display.drawLine(98, 15, 87, 30, SSD1306_WHITE);

  } else {
    display.fillCircle(37, 25, 9, SSD1306_WHITE);
    display.fillCircle(37, 25, 5, SSD1306_BLACK);

    display.fillCircle(91, 24, 9, SSD1306_WHITE);
    display.fillCircle(91, 24, 5, SSD1306_BLACK);

    display.drawLine(46, 47, 81, 47, SSD1306_WHITE);
  }

  display.display();
}

// =====================================================
// PISCADAS
// =====================================================

void verificarPiscada() {
  if (millis() - ultimaPiscada >= proximaPiscada) {
    String expressaoAnterior = expressaoAtual;

    desenharRosto("piscando");
    delay(140);
    desenharRosto(expressaoAnterior);

    ultimaPiscada = millis();
    proximaPiscada = random(3000, 7000);
  }
}

// =====================================================
// RECEBIMENTO DE STATUS DO BACKEND PYTHON
// =====================================================

void callback(char* topic, byte* payload, unsigned int length) {
  String topicStr = String(topic);

  if (topicStr != TOPIC_STATUS) {
    return;
  }

  String mensagem;
  mensagem.reserve(length + 1);

  for (unsigned int i = 0; i < length; i++) {
    mensagem += (char) payload[i];
  }

  StaticJsonDocument<512> doc;

  DeserializationError erro = deserializeJson(doc, mensagem);

  if (erro) {
    Serial.println("Status MQTT recebido com JSON invalido.");
    return;
  }

  String state = doc["state"] | "";
  String detail = doc["detail"] | "";

  Serial.print("Status recebido: ");
  Serial.println(state);

  if (detail.length() > 0) {
    Serial.print("Detalhe: ");
    Serial.println(detail);
  }

  if (state == "thinking") {
    desenharRosto("pensando");

  } else if (state == "ready") {
    desenharRosto("feliz");

  } else if (state == "error") {
    desenharRosto("raiva");
  }
}

// =====================================================
// CONEXAO WIFI
// =====================================================

void iniciarWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("Iniciando conexao Wi-Fi...");
}

void verificarWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  if (millis() - ultimaTentativaWiFi < INTERVALO_WIFI) {
    return;
  }

  ultimaTentativaWiFi = millis();

  Serial.println("Wi-Fi desconectado. Tentando reconectar...");
  WiFi.reconnect();
}

// =====================================================
// CONEXAO MQTT
// =====================================================

void conectarMQTT() {
  if (WiFi.status() != WL_CONNECTED || mqtt.connected()) {
    return;
  }

  if (millis() - ultimaTentativaMQTT < INTERVALO_MQTT) {
    return;
  }

  ultimaTentativaMQTT = millis();

  Serial.print("Conectando ao broker MQTT... ");

  String mac = WiFi.macAddress();
  mac.replace(":", "");

  String clientId = "Jarvinho-ESP32-" + mac;

  if (mqtt.connect(clientId.c_str())) {
    Serial.println("conectado!");

    if (mqtt.subscribe(TOPIC_STATUS, 1)) {
      Serial.println("Inscrito no topico de status.");

      desenharRosto("neutro");
    } else {
      Serial.println("Falha ao assinar o topico de status.");
    }

  } else {
    Serial.print("Falha na conexao MQTT. Estado: ");
    Serial.println(mqtt.state());
  }
}

// =====================================================
// SETUP
// =====================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  randomSeed(micros());

  Wire.begin(OLED_SDA, OLED_SCL);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("Erro ao iniciar OLED.");

    while (true) {
      delay(1000);
    }
  }

  desenharRosto("neutro");

  iniciarWiFi();

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(callback);
  mqtt.setBufferSize(1024);
  mqtt.setKeepAlive(60);
  mqtt.setSocketTimeout(5);

  ultimaPiscada = millis();
  proximaPiscada = random(3000, 7000);
}

// =====================================================
// LOOP PRINCIPAL
// =====================================================

void loop() {
  verificarPiscada();

  verificarWiFi();

  if (WiFi.status() == WL_CONNECTED) {
    if (!mqtt.connected()) {
      conectarMQTT();
    } else {
      mqtt.loop();
    }
  }
}