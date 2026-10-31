"""
Task 4: Vector & Metadata Document Store.
Stores document version, product, region, access level, effective date, and expiry date.
Performs semantic similarity search with TF-IDF indexing.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class RAGDocument:
    def __init__(self, doc_id: str, title: str, content: str, version: str = "1.0",
                 product: str = "general", region: str = "GLOBAL", access_level: str = "public",
                 effective_date: str = "2020-01-01", expiry_date: Optional[str] = None):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.version = version
        self.product = product
        self.region = region
        self.access_level = access_level # public, internal, confidential
        self.effective_date = effective_date
        self.expiry_date = expiry_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "version": self.version,
            "product": self.product,
            "region": self.region,
            "access_level": self.access_level,
            "effective_date": self.effective_date,
            "expiry_date": self.expiry_date
        }

class VectorStore:
    def __init__(self):
        self.documents: Dict[str, RAGDocument] = {}
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        self.tfidf_matrix = None
        self.indexed_doc_ids: List[str] = []

    def add_document(self, doc: RAGDocument):
        """Adds a document to store and flags re-indexing needed."""
        self.documents[doc.doc_id] = doc
        self._reindex()

    def add_documents(self, docs: List[RAGDocument]):
        for d in docs:
            self.documents[d.doc_id] = d
        self._reindex()

    def _reindex(self):
        """Builds TF-IDF matrix over corpus titles and contents."""
        if not self.documents:
            self.tfidf_matrix = None
            self.indexed_doc_ids = []
            return

        corpus = []
        self.indexed_doc_ids = []
        for doc_id, doc in self.documents.items():
            corpus.append(f"{doc.title} {doc.content} {doc.product}")
            self.indexed_doc_ids.append(doc_id)

        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def search_similar(self, query: str, top_k: int = 5) -> List[tuple[RAGDocument, float]]:
        """Searches documents by semantic relevance."""
        if self.tfidf_matrix is None or not self.indexed_doc_ids:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        ranked_indices = np.argsort(scores)[::-1]
        results = []
        for idx in ranked_indices[:top_k]:
            score = float(scores[idx])
            if score > 0.05: # Minimum relevance threshold
                doc_id = self.indexed_doc_ids[idx]
                results.append((self.documents[doc_id], score))

        return results

def seed_default_documents(store: VectorStore):
    default_docs = [
        RAGDocument(
            doc_id="DOC-WAR-DEFAULT",
            title="Laptop Hardware Warranty Policy",
            content="Standard laptop hardware warranty covers all manufacturing defects, screen issues, and battery replacements for 2 years from delivery.",
            version="2.0",
            product="laptop",
            access_level="public",
            effective_date="2024-01-01",
            expiry_date=None
        ),
        RAGDocument(
            doc_id="DOC-RET-DEFAULT",
            title="General Return and Refund Policy",
            content="Customers may return products within 14 days of delivery in original condition. Refunds are credited within 5 to 7 business days.",
            version="2.0",
            product="general",
            access_level="public",
            effective_date="2024-01-01",
            expiry_date=None
        ),
        RAGDocument(
            doc_id="DOC-PAY-DEFAULT",
            title="Payment Processing and Duplicate Debit Policy",
            content="Duplicate payments are identified within 24 hours. Full refund for the secondary charge is automatically initiated back to the original payment source.",
            version="1.0",
            product="billing",
            access_level="public",
            effective_date="2024-01-01",
            expiry_date=None
        )
    ]
    store.add_documents(default_docs)

rag_vector_store = VectorStore()
seed_default_documents(rag_vector_store)
