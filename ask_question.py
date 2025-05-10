import chromadb
from dotenv import load_dotenv
import openai
import os

# Carregar variáveis de ambiente
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

# Inicializar o ChromaDB local
db = chromadb.PersistentClient(path="./chroma")
collection = db.get_collection(name="docling_rag")

# Pergunta do usuário
user_question = input("❓ Faça sua pergunta: ")

# Obter o embedding da pergunta
query_embedding = (
    openai.embeddings.create(
        model="text-embedding-ada-002",
        input=[user_question],
    )
    .data[0]
    .embedding
)

# Buscar os 5 documentos mais relevantes
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    include=["documents", "metadatas"],
)

# Construir o contexto com os resultados
context = ""
for i, doc in enumerate(results["documents"][0]):
    page = results["metadatas"][0][i]["page"]
    context += f"[Página {page}]: {doc}\n"

# Criar o prompt para o modelo
print("\n🔍 Contexto encontrado:" f"\n{context}")

prompt = f"""Você é um assistente especializado em responder perguntas com base em documentos fornecidos.

Abaixo está o contexto extraído dos documentos, com indicação das páginas de onde cada trecho foi retirado:

{context}

Com base apenas nas informações acima, responda de forma clara e objetiva à seguinte pergunta do usuário:

"{user_question}"

Regras importantes:
- Sempre cite explicitamente as páginas dos documentos usados na resposta (ex: [Página X]).
- Se a resposta não estiver presente nos documentos, responda: "Desculpe, não sei.".
- Não inclua informações externas ou inventadas.

Responda em português.
"""

# Chamada ao modelo GPT-4o-mini
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Responda com base nos documentos fornecidos, de forma clara e direta.",
        },
        {"role": "user", "content": prompt},
    ],
)

# Exibir a resposta do chatbot
print("\n🤖 Resposta do Chatbot:")
print(response.choices[0].message.content)
