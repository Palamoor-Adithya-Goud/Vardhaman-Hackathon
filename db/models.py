"""
SQLAlchemy database models for persistence.
Stores user queries, recommendations, collaborations, projects, feedback, and logs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from db.database import Base

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(500), nullable=False)
    response_text = Column(Text, nullable=False)
    mode = Column(String(50), default="chat") # chat, collaborate, professor, etc.
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    recommendations = relationship("Recommendation", back_populates="query_log", cascade="all, delete-orphan")
    collaborations = relationship("Collaboration", back_populates="query_log", cascade="all, delete-orphan")
    projects = relationship("ProjectSuggestion", back_populates="query_log", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="query_log", cascade="all, delete-orphan")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    query_log_id = Column(Integer, ForeignKey("query_logs.id"))
    faculty_name = Column(String(200), nullable=False)
    reasoning = Column(Text, nullable=False)
    is_fallback = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Link to query
    query_log = relationship("QueryLog", back_populates="recommendations")


class Collaboration(Base):
    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, index=True)
    query_log_id = Column(Integer, ForeignKey("query_logs.id"))
    faculty_a = Column(String(200), nullable=False)
    faculty_b = Column(String(200), nullable=False)
    synergy_reason = Column(Text, nullable=False)
    project_idea = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Link to query
    query_log = relationship("QueryLog", back_populates="collaborations")


class ProjectSuggestion(Base):
    __tablename__ = "project_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    query_log_id = Column(Integer, ForeignKey("query_logs.id"))
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    target_faculty = Column(String(500), nullable=True) # comma separated list
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Link to query
    query_log = relationship("QueryLog", back_populates="projects")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    query_log_id = Column(Integer, ForeignKey("query_logs.id"))
    rating = Column(Integer, nullable=True) # e.g. 1 to 5, or binary
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Link to query
    query_log = relationship("QueryLog", back_populates="feedback")


class FacultyWorkload(Base):
    __tablename__ = "faculty_workload"

    id = Column(Integer, primary_key=True, index=True)
    faculty_name = Column(String(200), nullable=False, unique=True)
    active_projects = Column(Integer, default=0)
    project_titles = Column(JSON, nullable=True)  # List of project title strings
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

