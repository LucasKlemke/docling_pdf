from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
import pandas as pd


# fonte ( link de pdf )
source = "http://portal.mec.gov.br/arquivos/pdf/texto.pdf"

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False  # pick what you need
pipeline_options.do_table_structure = False  # pick what you need

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options, backend=DoclingParseV2DocumentBackend
        )  # switch to beta PDF backend
    }
)
conv_result = doc_converter.convert(source)

print(conv_result)
print("Document Name:", conv_result.document.origin.filename)
print("Document Type:", conv_result.document.origin.mimetype)
print("Number of pages:", len(conv_result.document.pages.keys()))

# Extrair metadata com conteúdo e página
results_body = conv_result.document.dict()
dict_list = []
texts = results_body["texts"]
for t in texts:
    ref = t["self_ref"]
    text_content = t["text"]
    page = t["prov"][0]["page_no"]
    dict_list.append({
        "ref": ref,
        "text": text_content[:100],
        "page": page
    })
    

df = pd.DataFrame(dict_list)
print(df)
