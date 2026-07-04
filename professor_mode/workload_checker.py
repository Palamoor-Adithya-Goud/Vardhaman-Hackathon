"""
Workload Checker Service.
Queries database for faculty active project count and flags overloaded candidates (>= 3 projects).
Provides candidate alternatives with lower workloads.
"""

from db.database import CacheSessionLocal
from db.models import FacultyWorkload
from utils.helpers import clean_professor_name
from core.logger import logger

class WorkloadChecker:
    def check_workload(self, faculty_name: str) -> dict:
        """
        Queries DB to check if a faculty member is overloaded (>= 3 projects).
        Returns status dictionary.
        """
        clean_name = clean_professor_name(faculty_name)
        logger.info(f"[WorkloadChecker] Checking workload for: '{faculty_name}' (clean: '{clean_name}')")

        db = CacheSessionLocal()
        try:
            # Query workload using exact or fuzzy name match
            record = (
                db.query(FacultyWorkload)
                .filter(FacultyWorkload.faculty_name.ilike(f"%{clean_name}%"))
                .first()
            )
            
            if record:
                active = record.active_projects or 0
                titles = record.project_titles or []
                status = "HIGH LOAD" if active >= 3 else "NORMAL"
                return {
                    "faculty_name": record.faculty_name,
                    "active_projects": active,
                    "project_titles": titles,
                    "status": status
                }
            else:
                logger.warning(f"[WorkloadChecker] No workload record found for faculty: '{faculty_name}'")
                return {
                    "faculty_name": faculty_name,
                    "active_projects": 0,
                    "project_titles": [],
                    "status": "NORMAL"
                }
        except Exception as e:
            logger.error(f"[WorkloadChecker] Database query error: {e}")
            return {
                "faculty_name": faculty_name,
                "active_projects": 0,
                "project_titles": [],
                "status": "NORMAL"
            }
        finally:
            db.close()

    def get_alternatives(self, overloaded_name: str) -> list[str]:
        """
        Queries database for alternative faculty members who are NOT overloaded (< 3 projects).
        Returns a list of names.
        """
        clean_overloaded = clean_professor_name(overloaded_name)
        db = CacheSessionLocal()
        alternatives = []
        try:
            records = (
                db.query(FacultyWorkload)
                .filter(FacultyWorkload.active_projects < 3)
                .filter(~FacultyWorkload.faculty_name.ilike(f"%{clean_overloaded}%"))
                .order_by(FacultyWorkload.active_projects.asc())
                .all()
            )
            alternatives = [r.faculty_name for r in records]
        except Exception as e:
            logger.error(f"[WorkloadChecker] Failed to retrieve workload alternatives: {e}")
        finally:
            db.close()
        return alternatives
