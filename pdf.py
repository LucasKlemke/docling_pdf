source = "https://cssjd.org.br/imagens/editor/files/2019/Abril/Tratado%20de%20Fisiologia%20M%C3%A9dica.pdf"

from docling.document_converter import DocumentConverter

print('Iniciou')
converter = DocumentConverter()
print('Convertendo documento...')
result = converter.convert(source)
print(result.document.export_to_markdown())

with open('output.md', 'w') as f:
    f.write(result.document.export_to_markdown())