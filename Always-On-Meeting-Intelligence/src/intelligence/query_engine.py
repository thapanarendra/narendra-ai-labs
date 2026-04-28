"""
Meeting query engine for the Meeting Intelligence Agent.
Enables semantic search and Q&A over past meetings.
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import logging
import json

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import numpy as np


@dataclass
class SearchResult:
    """A search result from the query engine."""
    meeting_id: str
    text: str
    score: float
    timestamp: Optional[float] = None
    speaker: Optional[str] = None
    meeting_title: Optional[str] = None
    meeting_date: Optional[datetime] = None
    context: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'meeting_id': self.meeting_id,
            'text': self.text,
            'score': self.score,
            'timestamp': self.timestamp,
            'speaker': self.speaker,
            'meeting_title': self.meeting_title,
            'meeting_date': self.meeting_date.isoformat() if self.meeting_date else None,
            'context': self.context
        }


@dataclass
class QueryAnswer:
    """Answer to a meeting query."""
    answer: str
    confidence: float
    sources: List[SearchResult] = field(default_factory=list)
    related_meetings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'sources': [s.to_dict() for s in self.sources],
            'related_meetings': self.related_meetings
        }
    
    def format_answer(self) -> str:
        """Format answer with citations."""
        parts = [self.answer, "\n\n**Sources:**"]
        
        for i, source in enumerate(self.sources, 1):
            meeting_info = source.meeting_title or source.meeting_id
            if source.meeting_date:
                meeting_info += f" ({source.meeting_date.strftime('%Y-%m-%d')})"
            
            parts.append(f"\n[{i}] {meeting_info}")
            if source.speaker:
                parts.append(f"    {source.speaker}: \"{source.text[:100]}...\"")
            else:
                parts.append(f"    \"{source.text[:100]}...\"")
        
        return "".join(parts)


class MeetingIndex:
    """
    Indexes meeting transcripts for semantic search.
    Uses sentence embeddings and ChromaDB for efficient retrieval.
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        persist_path: str = "./data/vector_db",
        collection_name: str = "meetings"
    ):
        """
        Initialize the meeting index.
        
        Args:
            embedding_model: Sentence transformer model name
            persist_path: Path to persist the vector database
            collection_name: Name of the collection
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("sentence-transformers is required for semantic search")
        if not HAS_CHROMADB:
            raise ImportError("chromadb is required for vector storage")
        
        self.embedding_model = embedding_model
        self.persist_path = persist_path
        self.collection_name = collection_name
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self._encoder = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        self._client = chromadb.PersistentClient(
            path=persist_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Meeting index initialized with {self._collection.count()} documents")
    
    def add_meeting(
        self,
        meeting_id: str,
        transcript: str,
        segments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a meeting to the index.
        
        Args:
            meeting_id: Unique meeting identifier
            transcript: Full transcript text
            segments: Optional list of transcript segments with metadata
            metadata: Optional meeting metadata
            
        Returns:
            Number of chunks indexed
        """
        chunks = []
        chunk_metadata = []
        
        if segments:
            # Index each segment
            for seg in segments:
                text = seg.get('text', '')
                if len(text.strip()) < 10:
                    continue
                
                chunks.append(text)
                chunk_metadata.append({
                    'meeting_id': meeting_id,
                    'start_time': seg.get('start_time', 0),
                    'end_time': seg.get('end_time', 0),
                    'speaker': seg.get('speaker', ''),
                    'meeting_title': metadata.get('title', '') if metadata else '',
                    'meeting_date': metadata.get('date', '') if metadata else ''
                })
        else:
            # Split transcript into chunks
            chunks = self._split_text(transcript)
            for i, chunk in enumerate(chunks):
                chunk_metadata.append({
                    'meeting_id': meeting_id,
                    'chunk_index': i,
                    'meeting_title': metadata.get('title', '') if metadata else '',
                    'meeting_date': metadata.get('date', '') if metadata else ''
                })
        
        if not chunks:
            return 0
        
        # Generate embeddings
        embeddings = self._encoder.encode(chunks).tolist()
        
        # Generate unique IDs
        ids = [f"{meeting_id}_{i}" for i in range(len(chunks))]
        
        # Add to collection
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=chunk_metadata
        )
        
        logger.info(f"Indexed {len(chunks)} chunks for meeting {meeting_id}")
        return len(chunks)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        meeting_id: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for relevant content.
        
        Args:
            query: Search query
            top_k: Number of results to return
            meeting_id: Optionally filter by meeting ID
            min_score: Minimum similarity score
            
        Returns:
            List of SearchResult objects
        """
        # Generate query embedding
        query_embedding = self._encoder.encode([query])[0].tolist()
        
        # Build filter
        where = None
        if meeting_id:
            where = {"meeting_id": meeting_id}
        
        # Search
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                # ChromaDB returns distances, convert to similarity
                distance = results['distances'][0][i] if results['distances'] else 0
                score = 1 - distance  # Cosine distance to similarity
                
                if score < min_score:
                    continue
                
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                
                search_results.append(SearchResult(
                    meeting_id=metadata.get('meeting_id', ''),
                    text=results['documents'][0][i],
                    score=score,
                    timestamp=metadata.get('start_time'),
                    speaker=metadata.get('speaker'),
                    meeting_title=metadata.get('meeting_title'),
                    meeting_date=datetime.fromisoformat(metadata['meeting_date']) if metadata.get('meeting_date') else None
                ))
        
        return search_results
    
    def delete_meeting(self, meeting_id: str) -> int:
        """Delete a meeting from the index."""
        # Get all IDs for this meeting
        results = self._collection.get(
            where={"meeting_id": meeting_id},
            include=[]
        )
        
        if results['ids']:
            self._collection.delete(ids=results['ids'])
            logger.info(f"Deleted {len(results['ids'])} chunks for meeting {meeting_id}")
            return len(results['ids'])
        
        return 0
    
    def _split_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.strip()) > 20:
                chunks.append(chunk)
        
        return chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'total_chunks': self._collection.count(),
            'embedding_model': self.embedding_model,
            'collection_name': self.collection_name
        }


class MeetingQueryEngine:
    """
    Query engine for asking questions about past meetings.
    Uses RAG (Retrieval Augmented Generation) for accurate answers.
    """
    
    SYSTEM_PROMPT = """You are a meeting assistant that answers questions based on meeting transcripts.

You will be given:
1. A user's question
2. Relevant excerpts from past meetings

Your job is to:
1. Answer the question based ONLY on the provided excerpts
2. Cite which meeting/speaker said what
3. If the answer isn't in the excerpts, say so
4. Be concise but complete

Format your response as JSON:
{
    "answer": "Your answer here with citations like [1], [2]",
    "confidence": 0.0-1.0,
    "found_in_meetings": ["meeting_id_1", "meeting_id_2"]
}"""

    def __init__(
        self,
        index: Optional[MeetingIndex] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        top_k: int = 5,
        min_similarity: float = 0.3
    ):
        """
        Initialize the query engine.
        
        Args:
            index: MeetingIndex instance
            api_key: OpenAI API key
            model: GPT model to use
            top_k: Number of results to retrieve
            min_similarity: Minimum similarity score
        """
        if not HAS_OPENAI:
            raise ImportError("openai is required for query answering")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.top_k = top_k
        self.min_similarity = min_similarity
        
        self._index = index
        self._client = OpenAI(api_key=self.api_key)
    
    def set_index(self, index: MeetingIndex):
        """Set the meeting index."""
        self._index = index
    
    def query(
        self,
        question: str,
        meeting_id: Optional[str] = None
    ) -> QueryAnswer:
        """
        Answer a question about meetings.
        
        Args:
            question: The question to answer
            meeting_id: Optionally limit to a specific meeting
            
        Returns:
            QueryAnswer object
        """
        if not self._index:
            return QueryAnswer(
                answer="No meeting index available.",
                confidence=0.0
            )
        
        # Search for relevant content
        results = self._index.search(
            query=question,
            top_k=self.top_k,
            meeting_id=meeting_id,
            min_score=self.min_similarity
        )
        
        if not results:
            return QueryAnswer(
                answer="I couldn't find any relevant information in the meeting transcripts.",
                confidence=0.0
            )
        
        # Build context from results
        context = self._build_context(results)
        
        # Generate answer
        answer = self._generate_answer(question, context, results)
        
        return answer
    
    def _build_context(self, results: List[SearchResult]) -> str:
        """Build context string from search results."""
        parts = []
        
        for i, result in enumerate(results, 1):
            meeting_info = result.meeting_title or result.meeting_id
            if result.meeting_date:
                meeting_info += f" ({result.meeting_date.strftime('%Y-%m-%d')})"
            
            speaker_info = f"{result.speaker}: " if result.speaker else ""
            
            parts.append(f"[{i}] From {meeting_info}:")
            parts.append(f"{speaker_info}{result.text}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _generate_answer(
        self,
        question: str,
        context: str,
        results: List[SearchResult]
    ) -> QueryAnswer:
        """Generate answer using GPT."""
        prompt = f"""Question: {question}

Relevant meeting excerpts:
{context}

Answer the question based on these excerpts."""

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        return QueryAnswer(
            answer=result.get('answer', ''),
            confidence=result.get('confidence', 0.5),
            sources=results,
            related_meetings=result.get('found_in_meetings', [])
        )
    
    def search(
        self,
        query: str,
        meeting_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Simple semantic search without answer generation.
        
        Args:
            query: Search query
            meeting_id: Optionally filter by meeting
            
        Returns:
            List of SearchResult objects
        """
        if not self._index:
            return []
        
        return self._index.search(
            query=query,
            top_k=self.top_k,
            meeting_id=meeting_id,
            min_score=self.min_similarity
        )
    
    def get_meeting_summary_qa(
        self,
        meeting_id: str,
        questions: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Answer common questions about a meeting.
        
        Args:
            meeting_id: Meeting to query
            questions: Optional custom questions
            
        Returns:
            Dictionary of question -> answer pairs
        """
        default_questions = [
            "What was the main topic of this meeting?",
            "What decisions were made?",
            "What are the next steps or action items?",
            "Were there any concerns or issues raised?"
        ]
        
        questions = questions or default_questions
        answers = {}
        
        for question in questions:
            result = self.query(question, meeting_id=meeting_id)
            answers[question] = result.answer
        
        return answers


class SimpleQueryEngine:
    """
    Simple query engine without vector database.
    Uses basic keyword matching and GPT.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o"
    ):
        """Initialize simple query engine."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        
        self._meetings: Dict[str, Dict[str, Any]] = {}
        
        if HAS_OPENAI and self.api_key:
            self._client = OpenAI(api_key=self.api_key)
        else:
            self._client = None
    
    def add_meeting(
        self,
        meeting_id: str,
        transcript: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a meeting transcript."""
        self._meetings[meeting_id] = {
            'transcript': transcript,
            'metadata': metadata or {},
            'added_at': datetime.now().isoformat()
        }
    
    def query(self, question: str) -> str:
        """Answer a question about meetings."""
        if not self._client:
            return "Query engine not available (no API key)."
        
        if not self._meetings:
            return "No meetings available to query."
        
        # Build context from all meetings
        context_parts = []
        for meeting_id, data in self._meetings.items():
            title = data['metadata'].get('title', meeting_id)
            context_parts.append(f"=== {title} ===")
            # Truncate long transcripts
            transcript = data['transcript'][:5000]
            context_parts.append(transcript)
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Query GPT
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Answer questions based on meeting transcripts. Be concise and cite which meeting you found the answer in."},
                {"role": "user", "content": f"Meeting transcripts:\n{context}\n\nQuestion: {question}"}
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
