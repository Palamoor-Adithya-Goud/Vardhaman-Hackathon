"""
Professor Mode Agent Orchestrator.
Exposes CLI and API interaction hooks for the Professor Mode Intelligence System.
Maintains strict separation between analysis and action layers.
"""

from datetime import datetime, timezone
from core.logger import logger
from db.database import SessionLocal
from db.models import QueryLog, ProjectSuggestion, Recommendation, Feedback
from professor_mode.orchestrator import ProfessorOrchestrator
from professor_mode.email_generator import EmailGenerator

class ProfessorAgent:
    def __init__(self):
        self.orchestrator = ProfessorOrchestrator()
        self.email_gen = EmailGenerator()

    def run_analysis_report(self, topic: str) -> dict:
        """Runs the complete analysis layer (pure read-only)."""
        return self.orchestrator.run_analysis(topic)

    def log_recommendation_to_db(self, topic: str, report: dict, project_idx: int) -> int:
        """
        Action Layer: Logs the selected project recommendation and analysis report into database.
        Returns the created query_log.id.
        """
        db = SessionLocal()
        try:
            # 1. Log query orchestrator query log
            q_log = QueryLog(
                query_text=f"Professor Mode analysis for: {topic}",
                response_text=f"Analyzed trends, gaps, and workloads. Recommendations logged for project index {project_idx}.",
                mode="professor"
            )
            db.add(q_log)
            db.commit()
            db.refresh(q_log)

            # 2. Extract selected project
            projects = report.get("project_suggestions", [])
            if 0 <= project_idx < len(projects):
                p = projects[project_idx]
                
                # Log Project Suggestion
                p_sug = ProjectSuggestion(
                    query_log_id=q_log.id,
                    title=p["title"],
                    description=p["description"],
                    target_faculty=", ".join(p["faculty"])
                )
                db.add(p_sug)

                # Log Recommendations for each professor
                for fac in p["faculty"]:
                    rec = Recommendation(
                        query_log_id=q_log.id,
                        faculty_name=fac,
                        reasoning=f"Synergy: {p['trend_alignment']}. Gap Alignment: {p['gap_alignment']}.",
                        is_fallback=False
                    )
                    db.add(rec)
                
                db.commit()
                logger.info(f"[ProfessorAgent] Recommendation successfully logged. QueryLog ID: {q_log.id}")
            return q_log.id
        except Exception as e:
            logger.error(f"[ProfessorAgent] Failed to log recommendation: {e}")
            db.rollback()
            return -1
        finally:
            db.close()

    def log_feedback(self, query_log_id: int, rating: int | None, comments: str | None) -> bool:
        """Action Layer: Logs user feedback for the session."""
        if query_log_id == -1:
            return False
        
        db = SessionLocal()
        try:
            fb = Feedback(
                query_log_id=query_log_id,
                rating=rating,
                comments=comments
            )
            db.add(fb)
            db.commit()
            logger.info(f"[ProfessorAgent] Feedback successfully logged for QueryLog ID: {query_log_id}")
            return True
        except Exception as e:
            logger.error(f"[ProfessorAgent] Failed to log feedback: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def generate_collaboration_email(self, project: dict) -> dict:
        """Action Layer: Generates professional email pitch for selected project."""
        faculty = project.get("faculty", [])
        title = project.get("title", "")
        desc = project.get("description", "")
        synergy = project.get("trend_alignment", "")
        
        draft = self.email_gen.generate_draft(
            project_title=title,
            project_description=desc,
            faculty_names=faculty,
            reason=synergy
        )
        return draft.model_dump()
