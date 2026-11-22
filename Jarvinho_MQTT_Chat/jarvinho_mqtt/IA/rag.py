
from pathlib import Path

from ddgs import DDGS

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from langchain_ollama import OllamaEmbeddings, ChatOllama

from langchain_core.prompts import ChatPromptTemplate


def criar_chain_agente():

    caminho_pdf = Path(__file__).parent / "Jarvinho.pdf"

    carregador = PyPDFLoader(str(caminho_pdf))
    documentos = carregador.load()

    separador = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    blocos = separador.split_documents(documentos)

    embeddings = OllamaEmbeddings(
        model="qwen3-embedding:0.6b",
        base_url="http://ollama:11434"
    )

    llm = ChatOllama(
        model="qwen3.5:0.8b",
        reasoning=False,
        temperature=0.5,
        base_url="http://ollama:11434"
    )

    banco_vetores = FAISS.from_documents(
        blocos,
        embeddings
    )

    buscador_contexto = banco_vetores.as_retriever(
        search_kwargs={"k": 4}
    )

    def formatar_contexto(documentos):

        return "\n\n".join(
            documento.page_content
            for documento in documentos
        )

    prompt_decisao = ChatPromptTemplate.from_template(
        """
Você é responsável por decidir se o Jarvinho precisa
pesquisar na internet antes de responder uma pergunta.

Analise a pergunta do usuário.

Responda SIM quando a pergunta depender de informações
atuais, recentes ou que possam mudar com o tempo.

Exemplos:
- Previsão do tempo atual.
- Notícias recentes.
- Resultados de jogos.
- Cotações de moedas.
- Preços atuais.
- Eventos que estão acontecendo.
- Informações atualizadas sobre empresas e tecnologias.
- Situação atual de lugares e serviços.

Responda NAO quando a pergunta puder ser respondida
com conhecimento geral ou com a base de conhecimento
do Jarvinho.

Exemplos:
- O que é inteligência artificial?
- Quem foi Albert Einstein?
- Como funciona a gravidade?
- Explique orientação a objetos.
- O que é o Jarvinho?

Não explique sua decisão.
Não escreva nenhuma outra palavra.
Responda somente SIM ou NAO.

Pergunta do usuário:
{pergunta}
"""
    )

    prompt_resposta = ChatPromptTemplate.from_template(
        """
Você é o Jarvinho, um assistente virtual inteligente,
amigável e interativo, desenvolvido por Gabriel.

IDIOMA:

- Todas as suas respostas devem ser em português brasileiro.
- O usuário sempre poderá conversar em português.
- Mesmo que os resultados da internet estejam em inglês,
  interprete as informações e responda em português.
- Não responda em inglês, a menos que o usuário solicite.
- Utilize uma linguagem natural e adequada ao português do Brasil.

PERSONALIDADE:

- Seja amigável, natural e descontraído.
- Converse de maneira espontânea.
- Seja claro, objetivo e didático.
- Evite respostas robóticas e repetitivas.
- Adapte o nível de explicação à pergunta do usuário.

CONHECIMENTO GERAL:

- Utilize seu conhecimento sobre história, ciência,
  tecnologia, matemática, cultura, programação,
  geografia, culinária e outros assuntos.
- Não dependa exclusivamente dos documentos ou da internet.
- Se os contextos fornecidos não forem relevantes,
  responda utilizando seu conhecimento geral.
- Não invente fatos, datas ou acontecimentos.
- Quando não souber, seja transparente.

BASE DE CONHECIMENTO DO JARVINHO:

- O contexto do documento foi recuperado do PDF
  cadastrado na base de conhecimento do Jarvinho.
- Utilize esse conteúdo quando for relevante.
- Quando o usuário perguntar especificamente sobre
  o Jarvinho ou informações do documento, priorize
  o contexto recuperado.
- Não invente informações e não atribua ao documento
  informações que não estejam presentes nele.
- Se não houver informações suficientes no contexto
  para responder a uma pergunta específica sobre o
  documento, informe essa limitação.

PESQUISA NA INTERNET:

- Os resultados da pesquisa foram obtidos por meio
  de uma ferramenta de busca na internet.
- Utilize os resultados quando estiverem relacionados
  à pergunta do usuário.
- Priorize informações recentes e relevantes.
- Os resultados podem conter páginas em inglês.
  Interprete o conteúdo e responda em português brasileiro.
- Não confunda a data de publicação de uma página
  com a data de um acontecimento.
- Não invente informações que não estejam nos resultados.
- Não trate uma descrição resumida de uma página como
  confirmação de todos os detalhes do assunto.
- Se os resultados forem insuficientes ou contraditórios,
  informe isso ao usuário.
- Se a pesquisa não encontrar resultados, não invente
  informações atuais.
- Não afirme que pesquisou quando não houver resultados
  de pesquisa disponíveis.

INSTRUÇÕES PARA A RESPOSTA:

- Responda diretamente à pergunta.
- Organize a explicação quando necessário.
- Não repita desnecessariamente a pergunta.
- Quando houver resultados da internet, utilize-os
  como fonte de informação.
- Não invente links ou fontes.
- Não apresente informações incertas como fatos.

CONTEXTO DO DOCUMENTO:

{contexto_documento}

RESULTADOS DA INTERNET:

{resultados_internet}

PERGUNTA DO USUÁRIO:

{pergunta}

Resposta do Jarvinho em português brasileiro:
"""
    )

    def pesquisar_internet(pergunta):

        try:

            print("Pesquisando na internet...")

            with DDGS() as ddgs:

                resultados = ddgs.text(
                    pergunta,
                    backend="bing",
                    max_results=5
                )

            if not resultados:
                print("Nenhum resultado encontrado.")

                return "", []

            textos = []
            fontes = []

            for item in resultados:

                titulo = item.get("title", "")
                url = item.get("href", "")
                descricao = item.get("body", "")

                textos.append(
                    f"Título: {titulo}\n"
                    f"Conteúdo: {descricao}\n"
                    f"URL: {url}"
                )

                if url:
                    fontes.append({
                        "titulo": titulo,
                        "url": url
                    })

            print(f"{len(textos)} resultados encontrados.")

            return "\n\n".join(textos), fontes

        except Exception as erro:

            print(f"Erro na pesquisa: {erro}")

            return "", []

    def processar_pergunta(pergunta):

        print("\nAnalisando pergunta do usuário...")

        decisao = llm.invoke(
            prompt_decisao.format(
                pergunta=pergunta
            )
        )

        decisao_texto = decisao.content.strip().upper()

        resultados_internet = ""
        fontes = []

        if decisao_texto.startswith("SIM"):

            resultados_internet, fontes = pesquisar_internet(
                pergunta
            )

        else:

            print("Pesquisa na internet não necessária.")

        print("Consultando base de conhecimento...")

        documentos_relevantes = buscador_contexto.invoke(
            pergunta
        )

        contexto_documento = formatar_contexto(
            documentos_relevantes
        )

        if not resultados_internet:

            if decisao_texto.startswith("SIM"):

                resultados_internet = (
                    "A pesquisa foi solicitada, mas não foi "
                    "possível obter resultados da internet. "
                    "Não existem fontes atuais disponíveis "
                    "para confirmar informações recentes."
                )

            else:

                resultados_internet = (
                    "Nenhuma pesquisa na internet foi realizada. "
                    "Responda utilizando o conhecimento geral "
                    "e o contexto do documento, quando relevante."
                )

        print("Gerando resposta do Jarvinho...")

        resposta = llm.invoke(
            prompt_resposta.format(
                contexto_documento=contexto_documento,
                resultados_internet=resultados_internet,
                pergunta=pergunta
            )
        )

        texto_resposta = resposta.content

        if fontes:

            texto_resposta += "\n\n**Fontes consultadas:**\n"

            for fonte in fontes:

                texto_resposta += (
                    f"- [{fonte['titulo']}]({fonte['url']})\n"
                )

        return texto_resposta

    return processar_pergunta