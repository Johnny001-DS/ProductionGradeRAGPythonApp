import pydantic


class RAGChunkAndSrc(pydantic.BaseModel):
    chunks: list[str]
    source_id: str = None


class RAGUpsertResult(pydantic.BaseModel):
    ingested: int


class RAGSearchResult(pydantic.BaseModel):
    contexts: list[str]
    sources: list[str]


class RAQQueryResult(pydantic.BaseModel):
    answer: str
    sources: list[str]
    num_contexts: int


class RAGEvaluationMetrics(pydantic.BaseModel):
    faithfulness: float | None = None
    answer_relevance: float | None = None
    context_relevance: float | None = None
    context_recall: float | None = None


class RAGQueryResultWithEval(pydantic.BaseModel):
    answer: str
    sources: list[str]
    num_contexts: int
    evaluation: RAGEvaluationMetrics | None = None