
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


def criar_chain_agente():

    caminho_pdf = Path(__file__).parent.parent / "Jarvinho.pdf"

    carregador = PyPDFLoader(str(caminho_pdf))
    documentos = carregador.load()

    separador = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    blocos = separador.split_documents(documentos)

    embeddings = OllamaEmbeddings(
        model="qwen3-embedding:0.6b"
    )

    banco_vetores = FAISS.from_documents(
        blocos,
        embeddings
    )

    buscador_contexto = banco_vetores.as_retriever(
        search_kwargs={"k": 4}
    )

    llm = ChatOllama(
        model="qwen3.5:0.8b",
        reasoning=False,
        temperature=0.3
    )

    prompt_template = ChatPromptTemplate.from_template(
        """
Você é o Jarvinho, um assistente virtual inteligente,
amigável e interativo, desenvolvido por Gabriel.

Sua função é conversar com o usuário, responder perguntas,
fornecer informações e ajudá-lo em diferentes tarefas.

Instruções:

- Utilize as informações do contexto para responder
  perguntas relacionadas ao documento.
- Não invente informações.
- Caso o contexto não contenha a informação necessária,
  informe que não possui essa informação.
- Responda sempre em português brasileiro.
- Utilize linguagem natural, amigável e descontraída.
- Seja claro, objetivo e direto.
- Evite respostas robóticas e repetitivas.

Contexto:
{context}

Pergunta:
{question}

Resposta:
"""
    )

    chain = (
        {
            "context": buscador_contexto,
            "question": RunnablePassthrough()
        }
        | prompt_template
        | llm
        | StrOutputParser()
    )

    return chain