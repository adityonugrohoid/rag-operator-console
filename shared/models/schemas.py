"""Data models and schemas for the RAG Operator Console."""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    ADDRESS = "address"
    NAME = "name"


class ChunkMetadata(BaseModel):
    """Metadata for document chunks stored in ChromaDB"""
    document_id: str
    filename: str
    chunk_index: int
    start_char: int
    end_char: int
    ingested_at: str
    data_classification: DataClassification = DataClassification.INTERNAL
    pii_detected: bool = False
    pii_types: List[PIIType] = []
    retention_days: int = 365
    embedding_time_ms: Optional[float] = None
    chunk_size_tokens: Optional[int] = None


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class DocumentResponse(BaseModel):
    success: bool
    document_id: str
    chunks_created: int
    pii_detected: bool = False


# --- Phase 1 carry-forward: model selection + parameters in request ---

class QueryRequest(BaseModel):
    """RAG query request with model selection and parameters"""
    query: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 512
    clarification_context: Optional[str] = None
    skip_retrieval: bool = False


# --- Full observability response schema ---

class PipelineMetrics(BaseModel):
    """Timing breakdown for each RAG pipeline stage"""
    embedding_ms: float = 0
    retrieval_ms: float = 0
    assembly_ms: float = 0
    llm_ms: float = 0
    total_ms: float = 0
    tokens_generated: int = 0
    tokens_per_sec: float = 0


class PromptAssemblyMetadata(BaseModel):
    """Metadata about how the prompt was assembled"""
    system_tokens: int = 0
    retrieved_docs_tokens: int = 0
    retrieved_docs_used: int = 0
    clarification_included: bool = False
    clarification_tokens: int = 0
    question_tokens: int = 0
    total_tokens: int = 0
    budget: int = 0


class RetrievedChunkInfo(BaseModel):
    """Debug info for a single retrieved chunk"""
    source: str = ""
    chunk_index: int = 0
    score: float = 0.0
    tokens: int = 0
    preview: str = ""
    pii_detected: bool = False
    included_in_prompt: bool = True


class QueryResponse(BaseModel):
    """RAG query response with full observability data"""
    success: bool
    answer: str
    sources: List[str] = []
    model: str = ""
    pipeline_metrics: PipelineMetrics = Field(default_factory=PipelineMetrics)
    prompt_assembly: PromptAssemblyMetadata = Field(
        default_factory=PromptAssemblyMetadata
    )
    retrieved_chunks: List[RetrievedChunkInfo] = []
