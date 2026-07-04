"""
Academic Email Generator.
Drafts professional emails for collaboration pitches.
"""

import json
from core.logger import logger
from services.groq_service import GroqService
from professor_mode.schemas import EmailDraft

class EmailGenerator:
    def __init__(self):
        self.llm = GroqService()

    def generate_draft(self, project_title: str, project_description: str, faculty_names: list[str], reason: str) -> EmailDraft:
        logger.info(f"[EmailGenerator] Generating email draft for project: '{project_title}'")
        
        system_prompt = (
            "You are a professional academic coordinator. Draft a formal academic email pitch requesting collaboration on a research project.\n\n"
            "CRITICAL: You must output ONLY a valid JSON object matching the schema below. Do not include markdown fencing or surrounding text.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            '  "subject": "string",\n'
            '  "body": "string"\n'
            "}"
        )

        user_prompt = f"""Project Title: {project_title}
Project Description: {project_description}
Faculty Candidates: {", ".join(faculty_names)}
Collaboration Reason: {reason}

Draft a formal, polite academic collaboration email inviting the specified faculty members to participate in this project. Reference the project summary and the specific synergy reason in the body."""

        logger.info("[EmailGenerator] Calling Groq structured completion...")
        raw_json = self.llm.generate_json(user_prompt=user_prompt, system_prompt=system_prompt)

        # Clean JSON in case LLM added markdown backticks
        clean_json = raw_json.strip()
        if clean_json.startswith("```"):
            lines = clean_json.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:-1]
            clean_json = "\n".join(lines).strip()

        # Parse and validate with Pydantic
        try:
            parsed = json.loads(clean_json)
            validated = EmailDraft(**parsed)
            logger.info("[EmailGenerator] Email draft generated and validated successfully.")
            return validated
        except Exception as e:
            logger.error(f"[EmailGenerator] JSON Validation failed: {e}. Raw response: {raw_json}")
            # Fallback output
            return EmailDraft(
                subject=f"Proposal for Collaborative Research: {project_title}",
                body=(
                    f"Dear Professor,\n\n"
                    f"I hope this email finds you well.\n\n"
                    f"I would like to propose a collaborative research project titled '{project_title}'. "
                    f"Based on your background and expertise, I believe this project aligns closely with your research interests. "
                    f"Summary: {project_description}\n\n"
                    f"Please let me know if you would be open to discussing this opportunity further.\n\n"
                    f"Sincerely,\nAcademic Research Director"
                )
            )
