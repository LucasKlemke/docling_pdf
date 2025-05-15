from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
import pandas as pd
import chromadb
import os
import openai
from dotenv import load_dotenv

# define virtual environment
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
CHROMA_PATH = "chroma"

# add books here
books = [
    # {
    #     "name": "robbins",
    #     "subject": "patologia",
    #     "url": "https://farmatecaunicatolica.wordpress.com/wp-content/uploads/2017/12/robbins-cotran-patologia-bases-patolc3b3gicas-das-doenc3a7as-8ed.pdf",
    # },
    {
        "name": "3porcos",
        "subject": "infancia",
        "url": "https://alfabetizacao.mec.gov.br/images/conta-pra-mim/livros/versao_digital/os_3_porquinhos_versao_digital.pdf",
    },
    # {
    #     "name": "lehninger",
    #     "subject": "bioquimica",
    #     "url": "https://dmapk.com.br/wp-content/uploads/2025/02/Principios-de-Bioquimica-Lehninger-8°-edicao-2022.pdf",
    # },
    # {
    #     "name": "moore",
    #     "subject": "anatomia",
    #     "url": "https://archive.org/details/AnatomiaOrientadaParaAClnicaMoore7EdioEbookPortugusByAclertonPinheiro/page/n491/mode/2up",
    # },
    # {
    #     "name": "junqueira_histologia",
    #     "subject": "histologia",
    #     "url": "https://archive.org/details/histologia-basica-texto-atlas-junqueira-carneiro-13.-ed.-www.meulivro.biz-compressed-compressed/page/n1615/mode/2up",
    # },
    # {
    #     "name": "junqueira_biologia",
    #     "subject": "biologia",
    #     "url": "https://archive.org/details/BiologiaCelularEMolecularJunqueiraECarneiro9Ed/page/n175/mode/2up",
    # },
    # {
    #     "name": "abbas_imunologia",
    #     "subject": "imunologia",
    #     "url": "https://pt.slideshare.net/slideshow/imunologia-celular-e-molecular-abbas-8edpdf/251970695#20",
    # },
    # {
    #     "name": "porto_semiologia",
    #     "subject": "clinica_medica",
    #     "url": "https://archive.org/details/SemiologiaMedicaPorto7Ed.2014Pt/page/n41/mode/2up",
    # },
]


def main():

    # 1. Configurar o docling
    print("🔧 Configurando o docling...")
    doc_converter = setup_docling()
    print("✅ Docling configurado com sucesso!")
    initial_chunks_df = pd.DataFrame()
    initial_embeddings = []

    for book in books:
        # 2. Converter o PDF
        print("📄 Iniciando a conversão do PDF...")
        conv_result = convert_pdf(doc_converter, book["url"])
        print("✅ Conversão do PDF concluída!")

        # 3. Extrair textos + metadados
        print("📝 Extraindo textos e metadados...")
        df = extract_texts(conv_result, book["name"], book["subject"], book["url"])

        print("✅ Textos e metadados extraídos!")

        # 4. Separar textos por página
        print("📑 Separando textos por página...")
        chunks_df = group_texts_by_page(df, book["name"], book["subject"], book["url"])
        print("✅ Textos separados por página!")

        # 5. Geração de embeddings via OpenAI
        print("🤖 Gerando embeddings via OpenAI...")
        embeddings = get_openai_embeddings(chunks_df["text"].tolist())
        print("✅ Embeddings gerados com sucesso!")

        # Concatenar resultados
        initial_chunks_df = pd.concat([initial_chunks_df, chunks_df], ignore_index=True)
        initial_embeddings.extend(embeddings)

    # Após o loop, use os dados concatenados
    chunks_df = initial_chunks_df
    embeddings = initial_embeddings

    # 6. Criar chromadb
    print("💾 Inicializando o ChromaDB...")
    db = chromadb.PersistentClient(path="./chroma")

    # 7. Armazenar no Chroma
    print("📥 Armazenando chunks no ChromaDB...")
    collection = db.get_or_create_collection(name="books_rag")

    collection.add(
        documents=chunks_df["text"].tolist(),
        metadatas=[
            {
                "page": int(row["page"]),
                "bookName": row["bookName"],
                "relatedSubject": row["relatedSubject"],
                "url": row["url"],
            }
            for _, row in chunks_df.iterrows()
        ],
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
def extract_texts(conv_result, name, subject, url):
    results_body = conv_result.document.model_dump()
    dict_list = []
    texts = results_body["texts"]
    for t in texts:
        ref = t["self_ref"]
        text_content = t["text"]
        page = t["prov"][0]["page_no"]
        bookName = name
        relatedSubject = subject
        url = url
        dict_list.append(
            {
                "ref": ref,
                "text": text_content,
                "page": page,
                "bookName": bookName,
                "relatedSubject": relatedSubject,
                "url": url,
            }
        )
    return pd.DataFrame(dict_list)


# 4. Separar
def group_texts_by_page(df, bookName, relatedSubject, url):
    grouped_texts = (
        df.groupby("page")["text"].apply(lambda texts: " ".join(texts)).reset_index()
    )
    print(grouped_texts)

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
        relatedSubject = relatedSubject
        bookName = bookName
        url = url
        for i, chunk in enumerate(split_text_in_chunks(text, num_chunks=2)):
            chunk_ref = f"page_{page}_chunk_{i+1}"
            chunks_list.append(
                {
                    "ref": chunk_ref,
                    "page": page,
                    "text": chunk,
                    "bookName": bookName,
                    "relatedSubject": relatedSubject,
                    "url": url,
                }
            )

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
