"""Distributed tracing for the reasoning pipeline.

This demonstrates how to instrument code for distributed tracing,
including spans, context propagation, and trace IDs.
"""

import time
import uuid

from dataclasses import dataclass
from dataclasses import field

from typing import Dict
from typing import List
from typing import Optional


@dataclass
class Span:
    """A trace span representing an operation.
    
    Attributes:
        span_id: Unique identifier for this span
        trace_id: Identifier for the entire trace
        parent_id: Optional parent span ID
        name: Human-readable span name
        start_time: Unix timestamp when span started
        end_time: Optional Unix timestamp when span ended
        attributes: Optional key-value attributes
        events: Optional list of events that occurred during the span
    """

    span_id: str
    trace_id: str
    parent_id: Optional[str]
    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, str] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)

    @property
    def duration_ms(self) -> Optional[float]:
        """Calculate span duration in milliseconds.
        
        Returns:
            Duration in milliseconds if span is finished, None otherwise
        """
        if self.end_time is None:
            return None

        return (self.end_time - self.start_time) * 1000


class Tracer:
    """Tracer for collecting distributed trace spans.
    
    This demonstrates basic distributed tracing patterns:
    - Creating trace hierarchies
    - Capturing timing information
    - Adding context attributes
    - Recording events
    
    In production, integrate with:
    - OpenTelemetry
    - Jaeger
    - Zipkin
    - AWS X-Ray
    - DataDog APM
    
    This demo tracer:
    - Stores spans in memory
    - Shows tracing patterns
    - Supports parent-child relationships
    - Can be exported to tracing systems
    """

    def __init__(self, trace_id: Optional[str] = None):
        """Initialize the tracer.
        
        Args:
            trace_id: Optional trace ID (generates one if not provided)
        """
        self._trace_id = trace_id or str(uuid.uuid4())
        self._spans: List[Span] = []
        self._active_span: Optional[Span] = None

    @property
    def trace_id(self) -> str:
        """Get the trace ID for this tracer.
        
        Returns:
            The trace ID string
        """
        return self._trace_id

    def start_span(self, name: str, attributes: Dict[str, str] | None = None) -> Span:
        """Start a new trace span.
        
        Args:
            name: Human-readable span name
            attributes: Optional key-value attributes
            
        Returns:
            The created span
        """
        span_id = str(uuid.uuid4())

        parent_id = self._active_span.span_id if self._active_span else None

        span = Span(span_id=span_id, trace_id=self._trace_id, parent_id=parent_id, name=name, start_time=time.time(), attributes=attributes or {})

        self._spans.append(span)

        self._active_span = span

        return span

    def end_span(self, span: Span) -> None:
        """End a trace span.
        
        Args:
            span: The span to end
        """
        span.end_time = time.time()

        if self._active_span == span:
            parent_span = self._find_span_by_id(span.parent_id) if span.parent_id else None

            self._active_span = parent_span

    def add_event(self, span: Span, event: str) -> None:
        """Add an event to a span.
        
        Args:
            span: The span to add the event to
            event: Event description
        """
        span.events.append(f"{time.time()}: {event}")

    def add_attribute(self, span: Span, key: str, value: str) -> None:
        """Add an attribute to a span.
        
        Args:
            span: The span to add the attribute to
            key: Attribute key
            value: Attribute value
        """
        span.attributes[key] = value

    def get_spans(self) -> List[Span]:
        """Get all collected spans.
        
        Returns:
            List of all spans in this trace
        """
        return self._spans.copy()

    def _find_span_by_id(self, span_id: str) -> Optional[Span]:
        """Find a span by its ID.
        
        Args:
            span_id: The span ID to find
            
        Returns:
            The span if found, None otherwise
        """
        for span in self._spans:
            if span.span_id == span_id:
                return span

        return None
