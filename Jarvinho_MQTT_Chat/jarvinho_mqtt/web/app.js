

const MQTT_CONFIG = {
    brokerWs: "ws://broker.emqx.io:8083/mqtt",
    topicQuestion: "jarvinho/chat/pergunta",
    topicAnswer: "jarvinho/chat/resposta",
    topicStatus: "jarvinho/status"
};

const clientId =
    "jarvinho_web_" + Math.random().toString(16).slice(2, 10);

const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const typing = document.getElementById("typing");
const statusDot = document.getElementById("statusDot");
const connectionTitle = document.getElementById("connectionTitle");
const connectionText = document.getElementById("connectionText");
const headerStatus = document.getElementById("headerStatus");
const clearButton = document.getElementById("clearButton");

let mqttClient = null;
let pending = new Map();

function setConnection(state, detail) {

    statusDot.className =
        "status-dot" +
        (state === "online"
            ? " online"
            : state === "error"
                ? " error"
                : "");

    connectionTitle.textContent =
        state === "online"
            ? "Conectado ao broker"
            : state === "error"
                ? "Falha na conexão"
                : "Desconectado";

    connectionText.textContent = detail;
    headerStatus.textContent = detail;

    input.disabled = state !== "online";
    sendButton.disabled = state !== "online";
}

function adicionarTextoFormatado(elemento, texto) {

    const regex =
        /(\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|\*\*([^*]+)\*\*)/g;

    let ultimoIndice = 0;
    let resultado;

    while ((resultado = regex.exec(texto)) !== null) {

        if (resultado.index > ultimoIndice) {

            elemento.appendChild(
                document.createTextNode(
                    texto.substring(ultimoIndice, resultado.index)
                )
            );
        }

        if (resultado[2] && resultado[3]) {

            const link = document.createElement("a");

            link.textContent = resultado[2];
            link.href = resultado[3];
            link.target = "_blank";
            link.rel = "noopener noreferrer";

            elemento.appendChild(link);

        } else if (resultado[4]) {

            const negrito = document.createElement("strong");

            negrito.textContent = resultado[4];

            elemento.appendChild(negrito);
        }

        ultimoIndice = regex.lastIndex;
    }

    if (ultimoIndice < texto.length) {

        elemento.appendChild(
            document.createTextNode(
                texto.substring(ultimoIndice)
            )
        );
    }
}

function addMessage(text, sender, id = "") {

    welcome.hidden = true;

    const row = document.createElement("div");
    row.className = "message " + sender;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    bubble.style.whiteSpace = "pre-wrap";

    adicionarTextoFormatado(bubble, text);

    if (id) {

        const meta = document.createElement("span");

        meta.className = "meta";
        meta.textContent = id;

        bubble.appendChild(meta);
    }

    row.appendChild(bubble);

    messages.appendChild(row);

    messages.scrollTop = messages.scrollHeight;
}

function connectMqtt() {

    if (!window.mqtt) {

        setConnection(
            "error",
            "Não foi possível carregar a biblioteca MQTT."
        );

        return;
    }

    setConnection(
        "offline",
        "Conectando ao broker público EMQX..."
    );

    mqttClient = mqtt.connect(MQTT_CONFIG.brokerWs, {

        clientId: clientId,
        clean: true,
        connectTimeout: 10000,
        reconnectPeriod: 3000,
        keepalive: 30

    });

    mqttClient.on("connect", () => {

        console.log("Conectado ao broker público EMQX!");

        mqttClient.subscribe(
            [
                MQTT_CONFIG.topicAnswer,
                MQTT_CONFIG.topicStatus
            ],
            { qos: 1 },
            (err) => {

                if (err) {

                    setConnection(
                        "error",
                        "Não foi possível assinar os tópicos MQTT."
                    );

                } else {

                    setConnection(
                        "online",
                        "Conectado. Aguardando o Jarvinho."
                    );
                }
            }
        );
    });

    mqttClient.on("reconnect", () => {

        setConnection(
            "offline",
            "Reconectando ao broker MQTT..."
        );
    });

    mqttClient.on("close", () => {

        setConnection(
            "offline",
            "Conexão MQTT encerrada."
        );
    });

    mqttClient.on("error", (err) => {

        console.error("Erro MQTT:", err);

        setConnection(
            "error",
            "Erro MQTT: " + err.message
        );
    });

    mqttClient.on("message", (topic, payload) => {

        let data;

        try {

            data = JSON.parse(payload.toString());

        } catch (erro) {

            console.error("Mensagem MQTT inválida:", erro);

            return;
        }

        if (topic === MQTT_CONFIG.topicStatus) {

            if (data.state === "thinking") {

                typing.hidden = false;
            }

            if (
                data.state === "ready" ||
                data.state === "error"
            ) {

                typing.hidden = true;
            }

            return;
        }

        if (topic === MQTT_CONFIG.topicAnswer) {

            typing.hidden = true;

            const id = data.id || "";

            const answer =
                data.message ||
                "O Jarvinho enviou uma resposta vazia.";

            addMessage(
                answer,
                "assistant",
                id ? "Jarvinho · " + id : "Jarvinho"
            );

            if (id) {

                pending.delete(id);
            }
        }
    });
}

form.addEventListener("submit", (event) => {

    event.preventDefault();

    const message = input.value.trim();

    if (
        !message ||
        !mqttClient ||
        !mqttClient.connected
    ) {

        return;
    }

    const id = (
        crypto.randomUUID
            ? crypto.randomUUID()
            : Date.now().toString(36) +
                Math.random().toString(36).slice(2)
    );

    const payload = JSON.stringify({

        id: id,
        message: message

    });

    addMessage(message, "user", "Você");

    pending.set(id, Date.now());

    typing.hidden = false;

    mqttClient.publish(
        MQTT_CONFIG.topicQuestion,
        payload,
        { qos: 1 },
        (err) => {

            if (err) {

                typing.hidden = true;

                addMessage(
                    "Não consegui enviar a mensagem pelo MQTT. Verifique a conexão.",
                    "assistant"
                );

                pending.delete(id);
            }
        }
    );

    input.value = "";

    input.focus();
});

clearButton.addEventListener("click", () => {

    messages.replaceChildren();

    welcome.hidden = false;

    messages.appendChild(welcome);

});

connectMqtt();