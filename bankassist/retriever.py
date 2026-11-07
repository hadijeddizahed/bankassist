import hashlib
import math
from typing import Any, Protocol
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


from bankassist.core import Document


class EmbeddingFunction(Protocol):
    def embed_text(self, text: str) -> list[float]: ...
    def dimension(self)-> int: ...


class SimpleHashEmbedder:
    """Deterministic local embedding function for offline testing.
       Produces a normalized bag-of-words / n-gram hash vector of fixed dimension.
       No network calls or GPU required!
    """

    def __init__(self, dim: int = 128):
        self._dim = dim

    def dimension(self) -> int:
        return self._dim

    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        tokens = text.lower().split()
        if not tokens:
            return[0.0] * self._dim
        vector = [0.0] * self._dim
        for token in tokens:
            # Deterministic hash bucket
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            vector[idx] += 1.0
        # L2-normalize vector to unit length for cosine similarity
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector


class TitanEmbedder:
    """Live Bedrock embedding client using amazon.titan-embed-text-v2:0."""

    def __init__(self, region_name: str="eu-west-1", dimension: int = 512 ):
        import json
        import boto3

        self._dim = dimension
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = "amazon.titan-embed-text-v2:0"

    def embed_text(self, text: str) -> list[float]:
        import json
        body = json.dumps({
            "inputText": text,
            "dimensions": self._dim,
            "normalize": True,
        })
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        data = json.loads(response["body"].read())
        return data["embedding"]
    def dimension(self) -> int:
        return self._dim

class QdrantVectorRetriever:
    """Semantic vector search using Qdrant (runs in-memory or on disk)."""
    COLLECTION_NAME = "bank_policies"

    def __init__(
            self,
            embedder: EmbeddingFunction,
            location: str = ":memory:",
            score_threshold: float = 0.35,
    ):
        self.embedder = embedder
        self.score_threshold = score_threshold
        self.client = QdrantClient(location=location)
        self._recreate_collection()

    def _recreate_collection(self) -> None:
        if not self.client.collection_exists(self.COLLECTION_NAME):
           self.client.create_collection(
               collection_name=self.COLLECTION_NAME,
               vectors_config=VectorParams(
                   size=self.embedder.dimension(),
                   distance=Distance.COSINE,
              ),
           )
    def index_documents(self, documents: list[Document]) -> None:
        points = []
        for i, doc in enumerate(documents):
            vector = self.embedder.embed_text(doc.text)
            points.append(
                PointStruct(
                    id=i + 1,
                    vector=vector,
                    payload={"id": doc.id, "text": doc.text},
                )
            )
        if points:
            self.client.upsert(collection_name=self.COLLECTION_NAME, points=points)

    def retrieve(self, question: str, top_k: int = 2) -> list[Document]:
        query_vec = self.embedder.embed_text(question)
        search_result = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vec,
            limit=top_k,
            score_threshold=self.score_threshold,
            with_payload=True,
        )
        return [
            Document(
                id=hit.payload["id"],
                text=hit.payload["text"],
            )
            for hit in search_result.points
            if hit.payload is not None
        ]






