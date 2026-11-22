import json
import threading

import paho.mqtt.client as mqtt

from rag import criar_chain_agente


BROKER = "broker.emqx.io"
PORT = 1883

TOPIC_QUESTION = "jarvinho/chat/pergunta"
TOPIC_ANSWER = "jarvinho/chat/resposta"
TOPIC_STATUS = "jarvinho/status"


print("Inicializando o sistema RAG...")

chain = criar_chain_agente()

print("RAG inicializado com sucesso!")


def publicar_status(client, state, detail):

    payload = json.dumps({
        "state": state,
        "detail": detail
    }, ensure_ascii=False)

    client.publish(
        TOPIC_STATUS,
        payload,
        qos=1
    )


def processar_pergunta(client, data):

    message_id = data.get("id", "")
    pergunta = data.get("message", "").strip()

    if not pergunta:
        return

    print(f"Pergunta recebida: {pergunta}")

    publicar_status(
        client,
        "thinking",
        "Jarvinho está consultando o Qwen3.5"
    )

    try:

        resposta = chain(pergunta)

        payload = json.dumps({
            "id": message_id,
            "message": resposta
        }, ensure_ascii=False)

        client.publish(
            TOPIC_ANSWER,
            payload,
            qos=1
        )

        publicar_status(
            client,
            "ready",
            "Resposta enviada pelo Qwen3.5"
        )

        print(f"Resposta: {resposta}")

    except Exception as erro:

        print(f"Erro ao processar pergunta: {erro}")

        payload = json.dumps({
            "id": message_id,
            "message": "Tive um problema ao processar sua pergunta."
        }, ensure_ascii=False)

        client.publish(
            TOPIC_ANSWER,
            payload,
            qos=1
        )

        publicar_status(
            client,
            "error",
            "Falha ao consultar o modelo local"
        )


def on_connect(client, userdata, flags, reason_code, properties):

    if reason_code == 0:

        print("Conectado ao broker MQTT público da EMQX!")

        client.subscribe(TOPIC_QUESTION, qos=1)

        publicar_status(
            client,
            "ready",
            "Jarvinho conectado ao backend Python"
        )

    else:

        print(f"Falha na conexão MQTT: {reason_code}")


def on_message(client, userdata, msg):

    try:

        data = json.loads(msg.payload.decode("utf-8"))

        threading.Thread(
            target=processar_pergunta,
            args=(client, data),
            daemon=True
        ).start()

    except Exception as erro:

        print(f"Erro ao receber mensagem MQTT: {erro}")


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="Jarvinho_Qwen_Backend"
)

client.on_connect = on_connect
client.on_message = on_message


print("Conectando ao broker MQTT público da EMQX...")

client.connect(BROKER, PORT, 60)

client.loop_forever()