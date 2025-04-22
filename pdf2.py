source = "https://alfabetizacao.mec.gov.br/images/conta-pra-mim/livros/versao_digital/os_3_porquinhos_versao_digital.pdf"

from docling.document_converter import DocumentConverter

print("Iniciou")
converter = DocumentConverter()
print("Convertendo documento...")
result = converter.convert(source)
print(result.document.export_to_markdown())

with open("output.md", "w") as f:
    f.write(result.document.export_to_markdown())
