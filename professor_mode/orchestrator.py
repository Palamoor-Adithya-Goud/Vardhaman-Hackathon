"""
Professor Mode Orchestrator.
Main entry point for running analysis layer features:
1. Retrieval of local expertise context
2. Trend analysis (external)
3. Gap analysis
4. Workload checking for suggested faculty members
5. Project suggestions generation
Does not log to database or trigger emails (pure analysis layer).
"""

from core.logger import logger
from rag.retriever import ChromaRetriever
from professor_mode.trend_analyzer import TrendAnalyzer
from professor_mode.gap_analyzer import GapAnalyzer
from professor_mode.workload_checker import WorkloadChecker
from professor_mode.project_suggester import ProjectSuggester

KNOWN_FACULTY = [
    "shirina samreen",
    "akhil jabbar meerja",
    "jaishree agrawal",
    "nimesh raj",
    "gagandeep"
]

class ProfessorOrchestrator:
    def __init__(self):
        self.retriever = ChromaRetriever()
        self.trend_analyzer = TrendAnalyzer()
        self.gap_analyzer = GapAnalyzer()
        self.workload_checker = WorkloadChecker()
        self.project_suggester = ProjectSuggester()

    def run_analysis(self, topic: str) -> dict:
        logger.info(f"[Orchestrator] Starting analysis pipeline for topic: '{topic}'")

        # 1. Retrieve local faculty chunks matching topic
        local_results = self.retriever.retrieve(topic, n_results=10)
        local_texts = []
        for r in local_results:
            source = r["metadata"].get("source", "Unknown Document")
            local_texts.append(f"[Faculty Source: {source}]\n{r['document']}")
        local_context = "\n\n".join(local_texts) if local_texts else "No local faculty profiles found."

        # 2. Extract allowed faculty names grounded in retrieved profiles
        local_candidates = set()
        for r in local_results:
            doc_lower = r["document"].lower()
            src_lower = r["metadata"].get("source", "").lower()
            for k in KNOWN_FACULTY:
                # Check for full name or first name overlap in doc or filename
                first_name = k.split()[0]
                if k in doc_lower or first_name in doc_lower or k in src_lower or first_name in src_lower:
                    local_candidates.add(k)

        # Fallback to known faculty if none matched (prevents empty lists)
        if not local_candidates:
            # Try to grab the closest name from the source metadata, or fallback to default
            for r in local_results:
                src = r["metadata"].get("source", "")
                if src:
                    stem = src.split("_")[-1].replace(".pdf", "").lower()
                    for k in KNOWN_FACULTY:
                        if stem in k or k.split()[0] in stem:
                            local_candidates.add(k)
            if not local_candidates:
                local_candidates = {KNOWN_FACULTY[0], KNOWN_FACULTY[1]}

        allowed_names = list(local_candidates)
        logger.info(f"[Orchestrator] Grounded faculty candidates: {allowed_names}")

        # 3. Run Trend Analysis (External sources)
        trends = self.trend_analyzer.analyze(topic)

        # 4. Run Gap Analysis
        gaps = self.gap_analyzer.analyze(topic, trends)

        # 5. Suggest Grounded Projects
        suggestions = self.project_suggester.suggest_projects(
            topic=topic,
            trends_output=trends,
            gaps_output=gaps,
            local_faculty_names=allowed_names,
            local_faculty_profiles_context=local_context
        )

        # 6. Evaluate Faculty Workloads and check for overload warnings
        workload_states = {}
        project_list = []

        for project in suggestions.projects:
            assigned_faculty = project.faculty
            checked_faculty = []
            
            for fac in assigned_faculty:
                workload = self.workload_checker.check_workload(fac)
                checked_faculty.append(workload)
                workload_states[workload["faculty_name"]] = workload

            # Create final project output dictionary
            project_dict = {
                "title": project.title,
                "description": project.description,
                "faculty": [w["faculty_name"] for w in checked_faculty],
                "trend_alignment": project.trend_alignment,
                "gap_alignment": project.gap_alignment,
                "impact": project.impact,
                "workload_warnings": []
            }

            # Check for overloaded professors (active >= 3)
            for w in checked_faculty:
                if w["status"] == "HIGH LOAD":
                    alts = self.workload_checker.get_alternatives(w["faculty_name"])
                    warning = {
                        "faculty": w["faculty_name"],
                        "warning": f"Professor {w['faculty_name']} is overloaded with {w['active_projects']} active projects.",
                        "suggested_alternatives": alts[:3]
                    }
                    project_dict["workload_warnings"].append(warning)
            
            project_list.append(project_dict)

        # 7. Package structured analysis output
        analysis_report = {
            "topic": topic,
            "trend_analysis": trends.model_dump(),
            "gap_analysis": gaps.model_dump(),
            "workload_analysis": workload_states,
            "project_suggestions": project_list
        }
        
        logger.info("[Orchestrator] Analysis pipeline executed successfully.")
        return analysis_report
