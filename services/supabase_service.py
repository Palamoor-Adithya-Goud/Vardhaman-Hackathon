"""
Supabase Service.
Handles storage of student-teacher research paper discussions.
Stores messages directly in Supabase using the PostgREST API when configured,
otherwise falls back to using the local database engine via SQLAlchemy.
"""

import httpx
from datetime import datetime, timezone
from core.config import settings
from core.logger import logger
from db.database import SessionLocal
from db.models import PaperChat, FacultyChat

class SupabaseService:
    @staticmethod
    def is_configured() -> bool:
        """Checks if Supabase configurations are present."""
        return settings.has_supabase

    @staticmethod
    def get_headers() -> dict:
        """Returns standard Supabase headers."""
        return {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    @staticmethod
    def get_messages(paper_title: str) -> list[dict]:
        """
        Retrieves all chat messages for a specific research paper.
        Tries Supabase first, falls back to SQLAlchemy.
        """
        if SupabaseService.is_configured():
            try:
                # Query paper_chats table on Supabase filtering by paper_title, sorted by timestamp ascending
                url = f"{settings.SUPABASE_URL}/rest/v1/paper_chats"
                params = {
                    "paper_title": f"eq.{paper_title}",
                    "order": "timestamp.asc"
                }
                
                logger.info(f"Fetching chat messages for '{paper_title}' from Supabase...")
                response = httpx.get(
                    url,
                    headers=SupabaseService.get_headers(),
                    params=params,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        f"Supabase REST query failed with status {response.status_code}: {response.text}. "
                        "Falling back to local database..."
                    )
            except Exception as e:
                logger.error(f"Error querying Supabase, falling back to local: {e}")

        # Fallback to SQLAlchemy
        db = SessionLocal()
        try:
            logger.info(f"Fetching chat messages for '{paper_title}' from main DB...")
            records = (
                db.query(PaperChat)
                .filter(PaperChat.paper_title == paper_title)
                .order_by(PaperChat.timestamp.asc())
                .all()
            )
            return [
                {
                    "id": r.id,
                    "paper_title": r.paper_title,
                    "sender_name": r.sender_name,
                    "sender_role": r.sender_role,
                    "message": r.message,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to fetch paper chats from local database: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def save_message(paper_title: str, sender_name: str, sender_role: str, message: str) -> dict:
        """
        Saves a new chat message to the paper_chats table.
        Saves to Supabase if configured, and always ensures it is written locally/primary DB.
        """
        # Save to local database (always keep in sync / fallback)
        local_success = False
        db_record_id = None
        db = SessionLocal()
        try:
            db_chat = PaperChat(
                paper_title=paper_title,
                sender_name=sender_name,
                sender_role=sender_role,
                message=message
            )
            db.add(db_chat)
            db.commit()
            db.refresh(db_chat)
            db_record_id = db_chat.id
            local_success = True
            logger.info(f"Successfully saved chat message locally with ID {db_record_id}.")
        except Exception as e:
            logger.error(f"Failed to save paper chat locally: {e}")
            db.rollback()
        finally:
            db.close()

        # Try to save to Supabase
        if SupabaseService.is_configured():
            try:
                url = f"{settings.SUPABASE_URL}/rest/v1/paper_chats"
                payload = {
                    "paper_title": paper_title,
                    "sender_name": sender_name,
                    "sender_role": sender_role,
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Saving chat message to Supabase...")
                response = httpx.post(
                    url,
                    headers=SupabaseService.get_headers(),
                    json=payload,
                    timeout=5.0
                )
                if response.status_code in (200, 201):
                    logger.info("Successfully saved chat message in Supabase.")
                    return response.json()[0] if response.json() else payload
                else:
                    logger.warning(
                        f"Supabase REST insert failed with status {response.status_code}: {response.text}."
                    )
            except Exception as e:
                logger.error(f"Error saving chat to Supabase: {e}")

        # If Supabase was failed or not configured, return standard payload/db record
        return {
            "id": db_record_id,
            "paper_title": paper_title,
            "sender_name": sender_name,
            "sender_role": sender_role,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ─────────────────────────────────────────────────────────────────
    # Faculty Direct Chat (student → faculty DMs)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_faculty_messages(faculty_name: str) -> list[dict]:
        """Return all messages for a specific faculty thread (from Supabase or local DB)."""
        if SupabaseService.is_configured():
            try:
                url = f"{settings.SUPABASE_URL}/rest/v1/faculty_chats"
                params = {
                    "faculty_name": f"eq.{faculty_name}",
                    "order": "timestamp.asc"
                }
                response = httpx.get(
                    url, headers=SupabaseService.get_headers(), params=params, timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"Supabase faculty chat query failed {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Supabase error, falling back to local: {e}")

        db = SessionLocal()
        try:
            records = (
                db.query(FacultyChat)
                .filter(FacultyChat.faculty_name == faculty_name)
                .order_by(FacultyChat.timestamp.asc())
                .all()
            )
            return [
                {
                    "id": r.id,
                    "faculty_name": r.faculty_name,
                    "sender_name": r.sender_name,
                    "sender_role": r.sender_role,
                    "message": r.message,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to fetch faculty chats from local: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def save_faculty_message(
        faculty_name: str, sender_name: str, sender_role: str, message: str
    ) -> dict:
        """Save a direct faculty chat message (to Supabase + local fallback)."""
        db_record_id = None
        db = SessionLocal()
        try:
            rec = FacultyChat(
                faculty_name=faculty_name,
                sender_name=sender_name,
                sender_role=sender_role,
                message=message
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            db_record_id = rec.id
            logger.info(f"Faculty chat saved locally (ID {db_record_id}).")
        except Exception as e:
            logger.error(f"Failed to save faculty chat locally: {e}")
            db.rollback()
        finally:
            db.close()

        if SupabaseService.is_configured():
            try:
                url = f"{settings.SUPABASE_URL}/rest/v1/faculty_chats"
                payload = {
                    "faculty_name": faculty_name,
                    "sender_name": sender_name,
                    "sender_role": sender_role,
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                response = httpx.post(
                    url, headers=SupabaseService.get_headers(), json=payload, timeout=5.0
                )
                if response.status_code in (200, 201):
                    logger.info("Faculty chat saved to Supabase.")
                    return response.json()[0] if response.json() else payload
                logger.warning(f"Supabase insert failed {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Supabase error: {e}")

        return {
            "id": db_record_id,
            "faculty_name": faculty_name,
            "sender_name": sender_name,
            "sender_role": sender_role,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
