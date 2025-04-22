from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend

source = "https://cssjd.org.br/imagens/editor/files/2019/Abril/Tratado%20de%20Fisiologia%20M%C3%A9dica.pdf"

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

print(conv_result.document.export_to_markdown())
with open("output.md", "w") as f:
    f.write(conv_result.document.export_to_markdown())
