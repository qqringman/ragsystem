import os
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredExcelLoader,
    UnstructuredMarkdownLoader, UnstructuredHTMLLoader, JSONLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_and_split_documents(file_paths):
    docs = []
    for path in file_paths:
        ext = Path(path).suffix.lower()
        if ext == ".pdf":
            loader = PyPDFLoader(path)
        elif ext in [".doc", ".docx"]:
            loader = UnstructuredWordDocumentLoader(path)
        elif ext in [".xls", ".xlsx"]:
            loader = UnstructuredExcelLoader(path)
        elif ext == ".md":
            loader = UnstructuredMarkdownLoader(path)
        elif ext in [".html", ".htm"]:
            loader = UnstructuredHTMLLoader(path)
        elif ext == ".json":
            loader = JSONLoader(path, jq_schema=".", text_content=False)
        else:
            continue

        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_documents(docs)
