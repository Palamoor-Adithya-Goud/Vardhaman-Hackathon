"""
Research Project Suggester.
Generates 3-5 structured research project suggestions grounded strictly in local faculty expertise,
gap analysis opportunities, and global trends. Enforces zero hallucination of faculty names.
"""

import json
from core.logger import logger
from services.groq_service import GroqService
from professor_mode.schemas import ProjectSuggestionOutput, TrendAnalysisOutput, GapAnalysisOutput

class ProjectSuggester:
    def __init__(self):
        self.llm = GroqService()

    def suggest_projects(
        self,
        topic: str,
        trends_output: TrendAnalysisOutput,
        gaps_output: GapAnalysisOutput,
        local_faculty_names: list[str],
        local_faculty_profiles_context: str
    ) -> ProjectSuggestionOutput:
        logger.info(f"[ProjectSuggester] Suggesting research projects for topic: '{topic}'")

        # 1. Format inputs for Groq context
        trends_str = "\n".join([f"- {t.title}: {t.summary}" for t in trends_output.trends])
        gaps_str = "\n".join([f"- {g.gap}: {g.why_it_matters}" for g in gaps_output.opportunity_gaps])
        faculty_list_str = ", ".join(local_faculty_names) if local_faculty_names else "No specific local faculty list."

        # 2. Call Groq JSON Mode to generate grounded research suggestions
        system_prompt = (
            "You are a Senior University Research Director. Suggest 3 to 5 research projects that bridge the gaps "
            "between our local faculty expertise and global research trends.\n\n"
            "CRITICAL RULES:\n"
            "- The suggested projects MUST be grounded in the provided local faculty profile context.\n"
            "- You MUST suggest only real faculty members listed in the ALLOWED FACULTY NAMES below. "
            "Do NOT hallucinate or invent new faculty names under any circumstances.\n"
            "- Each project must list one or more faculty members from the allowed list.\n"
            "- Output ONLY a valid JSON object matching the schema below. Do not include markdown fencing or surrounding text.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            '  "projects": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "description": "string",\n'
            '      "faculty": ["string"],\n'
            '      "trend_alignment": "string",\n'
            '      "gap_alignment": "string",\n'
            '      "impact": "string"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = f"""Topic: {topic}

ALLOWED FACULTY NAMES (STRICT):
{faculty_list_str}

Local Faculty Profiles Context:
{local_faculty_profiles_context}

Global Research Trends:
{trends_str}

Opportunity Gaps Identified:
{gaps_str}

Suggest 3-5 projects following the critical rules and structure."""

        logger.info("[ProjectSuggester] Calling Groq structured completion...")
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
            # Post-processing: clean and ground faculty suggestions
            for p in parsed.get("projects", []):
                grounded_faculty = []
                for name in p.get("faculty", []):
                    # Check if the name matches or contains any of the allowed names
                    cleaned_name = name.strip().lower()
                    matched = False
                    for allowed in local_faculty_names:
                        if allowed.lower() in cleaned_name or cleaned_name in allowed.lower():
                            grounded_faculty.append(allowed)
                            matched = True
                            break
                    if not matched and local_faculty_names:
                        # Fallback to the first allowed faculty if a hallucinated name is output
                        grounded_faculty.append(local_faculty_names[0])
                # Deduplicate and re-assign
                p["faculty"] = list(set(grounded_faculty)) if grounded_faculty else local_faculty_names[:1]
                
            validated = ProjectSuggestionOutput(**parsed)
            logger.info("[ProjectSuggester] Project suggestions generated and validated successfully.")
            return validated
        except Exception as e:
            logger.error(f"[ProjectSuggester] JSON Validation failed: {e}. Raw response: {raw_json}")
            # Fallback output
            fallback_faculty = local_faculty_names[:1] if local_faculty_names else ["Unassigned"]
            return ProjectSuggestionOutput(
                projects=[
                    {
                        "title": f"Collaborative Research on {topic}",
                        "description": "A cross-disciplinary project leveraging local faculty expertise to target emerging trends.",
                        "faculty": fallback_faculty,
                        "trend_alignment": "Aligns with overall trends in the field.",
                        "gap_alignment": "Addresses specialized skill development gaps.",
                        "impact": "Establishes institutional presence in the topic area."
                    }
                ]
            )
