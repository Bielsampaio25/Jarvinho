JARVINHO - CHAT WEB + MQTT + ESP32-C3 + GEMINI
================================================

ARQUITETURA
-----------
1. O navegador publica a pergunta em jarvinho/chat/pergunta via MQTT WebSocket.
2. O ESP32-C3 recebe a pergunta via MQTT TCP/TLS.
3. O ESP32-C3 faz a requisição HTTPS para a API Gemini.
4. O ESP32-C3 publica a resposta em jarvinho/chat/resposta.
5. O navegador recebe a resposta e a exibe no chat.
6. O OLED continua mostrando o rosto; muda para "pensando" durante a consulta e "feliz" ao terminar.

IMPORTANTE: O ESP32-C3 deve estar conectado a uma rede Wi-Fi REAL de 2,4 GHz.
A rede Wokwi-GUEST é apenas do simulador.

A) CONFIGURAR O BROKER MQTT
--------------------------
Este projeto está preparado como exemplo para HiveMQ Cloud.

No painel do HiveMQ Cloud:
- Crie/abra seu cluster.
- Crie credenciais MQTT (username e password).
- Copie o hostname do cluster.
- Confirme o endpoint WebSocket seguro e a porta indicada no painel.

Preencha:
WEB/app.js:
  brokerWs: "wss://SEU-CLUSTER.s1.eu.hivemq.cloud:8884/mqtt"
  username / password

ESP32/Jarvinho_MQTT.ino:
  MQTT_HOST = "SEU-CLUSTER.s1.eu.hivemq.cloud"
  MQTT_PORT = 8883
  MQTT_USER / MQTT_PASSWORD

Atenção: o endpoint WebSocket e a porta podem variar conforme o serviço/plano.
Use os dados exibidos no painel do seu broker. Nunca coloque as credenciais reais em repositório público.

B) CONFIGURAR A APLICAÇÃO WEB
-----------------------------
1. Abra web/app.js.
2. Preencha brokerWs, username e password.
3. Salve os arquivos.
4. Abra web/index.html em um navegador moderno.
   Se o navegador bloquear recursos ao abrir como arquivo local, rode um servidor local:
   - VS Code: extensão Live Server; ou
   - Python: python -m http.server 5500 dentro da pasta web
   - Abra http://localhost:5500

C) CONFIGURAR O ESP32-C3
------------------------
Instale pelo Gerenciador de Bibliotecas do Arduino IDE:
- PubSubClient
- ArduinoJson
- Adafruit GFX Library
- Adafruit SSD1306

As bibliotecas WiFi, WiFiClientSecure, HTTPClient e Wire vêm com o pacote ESP32.

No arquivo Jarvinho_MQTT.ino, configure:
- WIFI_SSID e WIFI_PASSWORD (rede 2,4 GHz)
- GOOGLE_API_KEY (chave Gemini nova)
- GEMINI_URL (modelo habilitado na sua conta)
- MQTT_HOST, MQTT_USER e MQTT_PASSWORD

Selecione a placa ESP32C3 Dev Module e USB CDC On Boot = Enabled.
Confira OLED SDA=8, SCL=9 e endereço 0x3C com base na ligação física da sua placa.

D) TÓPICOS MQTT
---------------
jarvinho/chat/pergunta
  Publicação do navegador para o ESP32:
  {"id":"id-da-mensagem","message":"Oi, Jarvinho"}

jarvinho/chat/resposta
  Publicação do ESP32 para o navegador:
  {"id":"id-da-mensagem","message":"Olá! Como posso ajudar?"}

jarvinho/status
  Status publicado pelo ESP32:
  {"state":"thinking","detail":"Jarvinho esta consultando o Gemini"}

E) OBSERVAÇÕES DE SEGURANÇA
---------------------------
- Não publique a chave Gemini, senha Wi-Fi ou credenciais MQTT em GitHub.
- A chave Gemini fica no firmware ESP32 neste protótipo, mas pode ser extraída do firmware.
- O exemplo usa setInsecure() para simplificar o TLS durante prototipagem. Para produção, valide os certificados TLS.
- Use ACL no broker para limitar cada cliente aos tópicos necessários.
- A página web precisa das credenciais MQTT para conectar diretamente ao broker. Para uma aplicação pública, prefira um backend que autentique os usuários e controle o acesso MQTT.
- Se a resposta do Gemini for muito grande, aumente os limites de buffer com cuidado.

F) DIAGNÓSTICO
--------------
- Browser não conecta: verifique URL WSS, porta, caminho /mqtt, credenciais e TLS.
- ESP32 não conecta ao broker: verifique hostname, porta 8883, usuário e senha.
- Web conecta, mas não recebe resposta: confirme se ESP32 assinou jarvinho/chat/pergunta.
- Gemini falha: confira chave, modelo, cota e mensagem HTTP impressa no Serial.
- ESP32 sem Wi-Fi: use uma rede 2,4 GHz; ESP32-C3 não suporta 5 GHz.
