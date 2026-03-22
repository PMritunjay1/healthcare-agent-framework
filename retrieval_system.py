from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

import re


class RetrievalSystem:
    def __init__(self, file_path):
        self.file_path = file_path
        self.vector_store = self._create_vector_store()
        print("Retrieval System: Vector store created successfully from chunks.")

    def _extract_patient_name(self, chunk):
        match = re.search(r"Patient:\s*(.+)", chunk)
        return match.group(1).strip() if match else "UNKNOWN"

    def _create_vector_store(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        chunks = [c.strip() for c in text.split('\n---\n') if c.strip()]
        print(f"Split the document into {len(chunks)} chunks.")

        documents = []
        for chunk in chunks:
            patient = self._extract_patient_name(chunk)
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={"patient": patient}
                )
            )

        embeddings = OllamaEmbeddings(model="llama3:8b")
        return FAISS.from_documents(documents, embeddings)

    def retrieve(self, patient_name):
        return self.vector_store.similarity_search(
            patient_name,
            filter={"patient": patient_name}
        )
    def refresh(self):
        print("Retrieval System: Refreshing vector store...")
        self.vector_store = self._create_vector_store()
    
