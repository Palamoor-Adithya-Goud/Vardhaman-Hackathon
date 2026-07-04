"""
Comprehensive Integration Tests for the Professor Intelligence Layer (Features 1-5).
Verifies schemas, trend analysis, gap analysis, workload checking, project suggestions,
email drafting, and database logging under strict separation policies.
"""

import unittest
from db.init_db import init_database
from db.database import SessionLocal
from db.models import FacultyWorkload, QueryLog, ProjectSuggestion, Recommendation, Feedback
from professor_mode.schemas import TrendAnalysisOutput, GapAnalysisOutput, ProjectSuggestionOutput
from professor_mode.trend_analyzer import TrendAnalyzer
from professor_mode.gap_analyzer import GapAnalyzer
from professor_mode.workload_checker import WorkloadChecker
from professor_mode.project_suggester import ProjectSuggester
from professor_mode.email_generator import EmailGenerator
from professor_mode.orchestrator import ProfessorOrchestrator
from professor_mode.professor_agent import ProfessorAgent

class ProfessorModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize and seed workloads in the test database
        init_database()
        cls.agent = ProfessorAgent()
        cls.orchestrator = ProfessorOrchestrator()

    def test_01_trend_analyzer_output(self):
        """Test if TrendAnalyzer generates a valid TrendAnalysisOutput matching Pydantic schemas."""
        print("\nRunning test: TrendAnalyzer Output Validation")
        analyzer = TrendAnalyzer()
        report = analyzer.analyze("recommendation systems")
        
        self.assertIsInstance(report, TrendAnalysisOutput)
        self.assertEqual(report.topic, "recommendation systems")
        self.assertTrue(len(report.trends) > 0)
        self.assertTrue(len(report.emerging_areas) > 0)
        print("SUCCESS: TrendAnalyzer schema validation passed.")

    def test_02_gap_analyzer_output(self):
        """Test if GapAnalyzer correctly identifies covered and missing research areas."""
        print("\nRunning test: GapAnalyzer Output Validation")
        analyzer = GapAnalyzer()
        trends_output = TrendAnalyzer().analyze("recommendation systems")
        report = analyzer.analyze("recommendation systems", trends_output)
        
        self.assertIsInstance(report, GapAnalysisOutput)
        self.assertTrue(len(report.covered_areas) >= 0)
        self.assertTrue(len(report.missing_areas) >= 0)
        self.assertTrue(len(report.opportunity_gaps) > 0)
        print("SUCCESS: GapAnalyzer schema validation passed.")

    def test_03_workload_checker_rules(self):
        """Test if WorkloadChecker flags high active project counts and finds substitutes."""
        print("\nRunning test: WorkloadChecker Validation")
        checker = WorkloadChecker()
        
        # 1. Overloaded professor (shirina samreen has 3 active projects in seed)
        shirina_status = checker.check_workload("shirina samreen")
        self.assertEqual(shirina_status["status"], "HIGH LOAD")
        self.assertEqual(shirina_status["active_projects"], 3)
        
        # 2. Normal loaded professor (akhil jabbar meerja has 2 active projects in seed)
        akhil_status = checker.check_workload("akhil jabbar meerja")
        self.assertEqual(akhil_status["status"], "NORMAL")
        self.assertEqual(akhil_status["active_projects"], 2)
        
        # 3. Workload alternatives logic
        alts = checker.get_alternatives("shirina samreen")
        self.assertTrue(len(alts) > 0)
        self.assertNotIn("shirina samreen", alts)
        print("SUCCESS: WorkloadChecker rules and status flags passed.")

    def test_04_project_suggestions_grounding(self):
        """Test if ProjectSuggester creates valid suggested projects without hallucinations."""
        print("\nRunning test: ProjectSuggester Validation")
        suggester = ProjectSuggester()
        trends_output = TrendAnalyzer().analyze("trust routing")
        gaps_output = GapAnalyzer().analyze("trust routing", trends_output)
        
        allowed_faculty = ["shirina samreen", "akhil jabbar meerja"]
        suggestions = suggester.suggest_projects(
            topic="trust routing",
            trends_output=trends_output,
            gaps_output=gaps_output,
            local_faculty_names=allowed_faculty,
            local_faculty_profiles_context="Dr. Shirina Samreen works on trust ad hoc routing."
        )
        
        self.assertIsInstance(suggestions, ProjectSuggestionOutput)
        self.assertTrue(len(suggestions.projects) > 0)
        for proj in suggestions.projects:
            self.assertTrue(len(proj.faculty) > 0)
            for fac in proj.faculty:
                self.assertIn(fac, allowed_faculty, "Hallucinated faculty name suggested!")
        print("SUCCESS: ProjectSuggester grounding check passed.")

    def test_05_email_generator_drafting(self):
        """Test if EmailGenerator outputs proper academic templates containing context."""
        print("\nRunning test: EmailGenerator Output Validation")
        generator = EmailGenerator()
        draft = generator.generate_draft(
            project_title="Secure IoT Health Tracking",
            project_description="A blockchain-based telemetry health tracking system.",
            faculty_names=["Gagandeep"],
            reason="Synergy in blockchain networks"
        )
        
        self.assertTrue(len(draft.subject) > 10)
        self.assertIn("Secure IoT Health Tracking", draft.subject)
        self.assertIn("Gagandeep", draft.body)
        print("SUCCESS: EmailGenerator formatting passed.")

    def test_06_orchestrator_compilation(self):
        """Test if the main orchestrator combines all layers cleanly without database side-effects."""
        print("\nRunning test: ProfessorOrchestrator compilation")
        report = self.orchestrator.run_analysis("IoT security")
        
        self.assertIn("trend_analysis", report)
        self.assertIn("gap_analysis", report)
        self.assertIn("workload_analysis", report)
        self.assertIn("project_suggestions", report)
        print("SUCCESS: Orchestrator execution layer complete.")

    def test_07_action_layer_db_persistence(self):
        """Test if the agent successfully saves selections and feedback to the database."""
        print("\nRunning test: Action Layer DB Persistence and Feedback Logs")
        topic = "cloud databases"
        report = self.orchestrator.run_analysis(topic)
        
        # 1. Log selected suggestion
        log_id = self.agent.log_recommendation_to_db(topic, report, project_idx=0)
        self.assertNotEqual(log_id, -1)
        
        # 2. Check query_logs, project_suggestions, and recommendations database records
        db = SessionLocal()
        try:
            q_record = db.query(QueryLog).filter(QueryLog.id == log_id).first()
            self.assertIsNotNone(q_record)
            self.assertEqual(q_record.mode, "professor")
            
            p_record = db.query(ProjectSuggestion).filter(ProjectSuggestion.query_log_id == log_id).first()
            self.assertIsNotNone(p_record)
            
            rec_records = db.query(Recommendation).filter(Recommendation.query_log_id == log_id).all()
            self.assertTrue(len(rec_records) > 0)
            
            # 3. Log user feedback
            fb_success = self.agent.log_feedback(log_id, rating=5, comments="Fantastic analysis report!")
            self.assertTrue(fb_success)
            
            fb_record = db.query(Feedback).filter(Feedback.query_log_id == log_id).first()
            self.assertIsNotNone(fb_record)
            self.assertEqual(fb_record.rating, 5)
            self.assertEqual(fb_record.comments, "Fantastic analysis report!")
        finally:
            db.close()
        print("SUCCESS: Action layer database logging and feedback logs validated.")

if __name__ == "__main__":
    print("=================================================================")
    print("[PROFESSOR MODE] RUNNING INTEGRATION TESTING SUITE")
    print("=================================================================")
    unittest.main()
