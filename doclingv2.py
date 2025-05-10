from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
import pandas as pd
import chromadb

import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
CHROMA_PATH = "chroma"


def main():
    # source = "http://portal.mec.gov.br/arquivos/pdf/texto.pdf"
    # guyton
    source = "https://cssjd.org.br/imagens/editor/files/2019/Abril/Tratado%20de%20Fisiologia%20M%C3%A9dica.pdf"

    # 1. Configurar o docling
    print("🔧 Configurando o docling...")
    doc_converter = setup_docling()
    print("✅ Docling configurado com sucesso!")

    # 2. Converter o PDF
    print("📄 Iniciando a conversão do PDF...")
    conv_result = convert_pdf(doc_converter, source)
    print("✅ Conversão do PDF concluída!")

    # 3. Extrair textos + metadados
    print("📝 Extraindo textos e metadados...")
    df = extract_texts(conv_result)
    print("✅ Textos e metadados extraídos!")

    # 4. Separar textos por página
    print("📑 Separando textos por página...")
    chunks_df = group_texts_by_page(df)
    print("✅ Textos separados por página!")

    # 5. Geração de embeddings via OpenAI
    print("🤖 Gerando embeddings via OpenAI...")
    embeddings = get_openai_embeddings(chunks_df["text"].tolist())
    print("✅ Embeddings gerados com sucesso!")

    # 6. Criar chromadb
    print("💾 Inicializando o ChromaDB...")
    db = chromadb.PersistentClient(path="./chroma")

    # 7. Armazenar no Chroma
    print("📥 Armazenando chunks no ChromaDB...")
    collection = db.get_or_create_collection(name="docling_rag")
    collection.add(
        documents=chunks_df["text"].tolist(),
        metadatas=[{"page": int(page)} for page in chunks_df["page"].tolist()],
        embeddings=embeddings,
        ids=chunks_df["ref"].tolist(),
    )

    print(
        f"🎉 {len(chunks_df)} chunks armazenados com sucesso no ChromaDB com metadados de página!"
    )


# 1. Configurar o docling
def setup_docling():
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = False

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options, backend=DoclingParseV2DocumentBackend
            )
        }
    )
    return doc_converter


# 2. Converter o PDF
def convert_pdf(doc_converter, source):
    conv_result = doc_converter.convert(source)
    return conv_result


# 3. Extrair textos + metadados
def extract_texts(conv_result):
    results_body = conv_result.document.dict()
    dict_list = []
    texts = results_body["texts"]
    for t in texts:
        ref = t["self_ref"]
        text_content = t["text"]
        page = t["prov"][0]["page_no"]
        dict_list.append({"ref": ref, "text": text_content, "page": page})
    return pd.DataFrame(dict_list)


# 4. Separar
def group_texts_by_page(df):
    grouped_texts = (
        df.groupby("page")["text"].apply(lambda texts: " ".join(texts)).reset_index()
    )

    # Criar uma nova lista com 2 chunks por página
    chunks_list = []

    def split_text_in_chunks(text: str, num_chunks: int = 2) -> list[str]:
        length = len(text)
        chunk_size = length // num_chunks
        chunks = [
            text[i * chunk_size : (i + 1) * chunk_size] for i in range(num_chunks)
        ]
        # Adiciona o restante de caracteres na última parte, se houver
        if length % num_chunks:
            chunks[-1] += text[num_chunks * chunk_size :]
        return chunks

    for _, row in grouped_texts.iterrows():
        page = row["page"]
        text = row["text"]
        for i, chunk in enumerate(split_text_in_chunks(text, num_chunks=2)):
            chunk_ref = f"page_{page}_chunk_{i+1}"
            chunks_list.append({"ref": chunk_ref, "page": page, "text": chunk})

    chunks_df = pd.DataFrame(chunks_list)
    return chunks_df


import concurrent.futures


# 4. Geração de embeddings via OpenAI (em lotes e paralelo)
def get_openai_embeddings(
    texts: list[str], batch_size: int = 10, max_workers: int = 4
) -> list[list[float]]:
    """
    Gera embeddings em lotes pequenos e executa em paralelo para evitar exceder o limite de tokens da API OpenAI.
    """

    def fetch_embeddings(batch):
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=batch,
        )
        return [d.embedding for d in response.data]

    all_embeddings = []
    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch_embeddings, batches))
        for emb in results:
            all_embeddings.extend(emb)
    return all_embeddings


# iniciar
if __name__ == "__main__":
    main()


# 1 pagina
# [conteudo] / 2 chunks

