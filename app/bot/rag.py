from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any, Protocol

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.vectorstores import InMemoryVectorStore

from app.bot.kb import load_knowledge_base
from app.bot.service import MISS_MESSAGE

TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]")


class SupportsInvoke(Protocol):
    def invoke(self, *args: Any, **kwargs: Any) -> object: ...


class HashEmbeddings(Embeddings):
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in self._tokens(text):
            index = hash(token) % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _tokens(self, text: str) -> list[str]:
        basic_tokens = TOKEN_RE.findall(text.lower())
        bigrams = [
            text[index:index + 2]
            for index in range(len(text) - 1)
            if not text[index:index + 2].isspace()
        ]
        return basic_tokens + bigrams


class LangChainRAGResponder:
    def __init__(
        self,
        kb_path: str,
        llm: SupportsInvoke,
        min_score: float = 0.10,
        cache_path: str | None = None,
    ) -> None:
        self.llm = llm
        self.kb_path = kb_path
        self.min_score = min_score
        self.cache_path = Path(cache_path) if cache_path else None
        self.session_history: dict[str, list[tuple[str, str]]] = {}
        self.vector_store = self._load_or_build_vector_store()
        runnable_llm = llm if isinstance(llm, Runnable) else RunnableLambda(self._invoke_llm)
        self.chain = (
            ChatPromptTemplate.from_template(
                "???????????????????????????\n"
                "???????????????????????????????\n\n"
                "?????\n{history}\n\n"
                "??????\n{context}\n\n"
                "?????{query}"
            )
            | runnable_llm
            | StrOutputParser()
        )

    def _manifest_path(self) -> Path | None:
        if self.cache_path is None:
            return None
        return self.cache_path.with_suffix(".meta.json")

    def _kb_signature(self) -> str:
        payload = Path(self.kb_path).read_text(encoding="utf-8")
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _collection_name(self) -> str:
        base = self.cache_path.name if self.cache_path is not None else "knowledge-base"
        return re.sub(r"[^a-zA-Z0-9_-]", "-", base) or "knowledge-base"

    def _load_or_build_vector_store(self) -> InMemoryVectorStore | Chroma:
        if self.cache_path is not None:
            manifest_path = self._manifest_path()
            if self.cache_path.exists() and not self.cache_path.is_dir():
                self.cache_path.unlink()
            if (
                manifest_path is not None
                and self.cache_path.exists()
                and manifest_path.exists()
            ):
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("kb_signature") == self._kb_signature():
                    return Chroma(
                        collection_name=self._collection_name(),
                        embedding_function=HashEmbeddings(),
                        persist_directory=str(self.cache_path),
                    )

        vector_store = self._build_vector_store(self.kb_path)
        if self.cache_path is not None:
            if self.cache_path.exists():
                if self.cache_path.is_dir():
                    shutil.rmtree(self.cache_path, ignore_errors=True)
                else:
                    self.cache_path.unlink()
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path = self._manifest_path()
            if manifest_path is not None:
                manifest_path.write_text(
                    json.dumps({"kb_signature": self._kb_signature()}, ensure_ascii=False),
                    encoding="utf-8",
                )
        return vector_store

    def _build_vector_store(self, kb_path: str) -> InMemoryVectorStore | Chroma:
        documents: list[Document] = []
        for row in load_knowledge_base(kb_path):
            question = str(row.get("question", "")).strip()
            answer = str(row.get("answer", "")).strip()
            raw_keywords = row.get("keywords", [])
            keywords = (
                ", ".join(str(item).strip() for item in raw_keywords if str(item).strip())
                if isinstance(raw_keywords, list)
                else ""
            )
            page_content = "\n".join(
                part
                for part in [
                    f"???{question}" if question else "",
                    f"???{answer}" if answer else "",
                    f"????{keywords}" if keywords else "",
                ]
                if part
            )
            if not page_content:
                continue
            documents.append(
                Document(
                    page_content=page_content,
                    metadata={
                        "question": question,
                        "answer": answer,
                        "keywords": keywords,
                    },
                )
            )

        if self.cache_path is None:
            return InMemoryVectorStore.from_documents(
                documents=documents,
                embedding=HashEmbeddings(),
            )
        return Chroma.from_documents(
            documents=documents,
            embedding=HashEmbeddings(),
            collection_name=self._collection_name(),
            persist_directory=str(self.cache_path),
        )

    def _invoke_llm(self, prompt_value: object) -> str:
        response = self.llm.invoke(prompt_value)
        content = getattr(response, "content", response)
        return str(content).strip()

    def _retrieve_context(self, query: str, session_id: str | None = None) -> str:
        search_query = query
        if session_id and session_id in self.session_history:
            previous_questions = " ".join(
                question for question, _ in self.session_history[session_id][-2:]
            )
            if previous_questions:
                search_query = f"{previous_questions} {query}"
        results = self.vector_store.similarity_search_with_score(search_query, k=3)
        filtered = [
            document.page_content
            for document, score in results
            if score >= self.min_score and document.page_content
        ]
        return "\n\n".join(filtered)

    def _format_history(self, session_id: str | None) -> str:
        if not session_id:
            return "?"
        items = self.session_history.get(session_id, [])
        if not items:
            return "?"
        return "\n".join(
            f"???{question}\n???{answer}"
            for question, answer in items[-3:]
        )

    def _remember(self, session_id: str | None, query: str, answer: str) -> None:
        if not session_id:
            return
        items = self.session_history.setdefault(session_id, [])
        items.append((query, answer))
        if len(items) > 6:
            del items[:-6]

    def answer(self, query: str, session_id: str | None = None) -> str:
        context = self._retrieve_context(query, session_id=session_id)
        if not context.strip():
            return MISS_MESSAGE
        answer = str(
            self.chain.invoke(
                {
                    "history": self._format_history(session_id),
                    "context": context,
                    "query": query,
                }
            )
        ).strip() or MISS_MESSAGE
        self._remember(session_id, query, answer)
        return answer
