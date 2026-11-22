
from rag import criar_chain_agente

print("Inicializando o Jarvinho...")

chain = criar_chain_agente()

print("\nJarvinho está pronto!")

while True:

    pergunta = input("\nVocê: ")

    if pergunta.lower() in ["sair", "exit"]:

        print("Encerrando o Jarvinho...")
        break

    resposta = chain(pergunta)

    print("\nJarvinho:", resposta)