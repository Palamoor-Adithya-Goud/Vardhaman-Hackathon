"""
FastAPI Integration Test Suite.
Verifies routes and responses using FastAPI's built-in TestClient.
"""

import json
import unittest
import os

# IMPORTANT: Must set env vars before importing app modules that read settings at import time
os.environ["VERCEL"] = "1"  # Force Vercel mode so DB uses /tmp; must be before import

from fastapi.testclient import TestClient
from server import app

class FastAPITestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Set up FastAPI test client
        from db.init_db import init_database
        init_database()
        cls.client = TestClient(app)

    def test_01_index_page(self):
        """Test serving index.html."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<!DOCTYPE html>", response.content)

    def test_02_stats_endpoint(self):
        """Test GET /api/stats."""
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("chunk_count", data)
        self.assertIn("paper_count", data)
        self.assertIn("total_queries", data)

    def test_03_chat_endpoint(self):
        """Test POST /api/chat."""
        payload = {
            "query": "Who works on plant disease detection?",
            "role": "student"
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("intent", data)
        self.assertIn("response_text", data)
        self.assertIn("data", data)

    def test_04_recommend_endpoint(self):
        """Test POST /api/recommend."""
        payload = {
            "query": "IoT healthcare",
            "role": "faculty"
        }
        response = self.client.post("/api/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "recommend")
        self.assertIn("response_text", data)

    def test_05_collaborate_endpoint(self):
        """Test POST /api/collaborate."""
        payload = {
            "faculty_a": "Shirina Samreen",
            "faculty_b": "Akhil Jabbar Meerja"
        }
        response = self.client.post("/api/collaborate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["faculty_a"], "Shirina Samreen")
        self.assertEqual(data["faculty_b"], "Akhil Jabbar Meerja")
        self.assertIn("synergy_reason", data)

    def test_06_logs_endpoint(self):
        """Test GET /api/logs."""
        response = self.client.get("/api/logs?role=student")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_07_invalid_json_payload(self):
        """Test validation error with incomplete payload on POST /api/chat."""
        payload = {
            "query_wrong_key": "test"
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_08_post_paper_chat(self):
        """Test POST /api/paper-chat: message is created and a timestamp is returned."""
        payload = {
            "paper_title": "Agri-Ai-Intelligent-Plant-Disease-Surveillance-and-Predictive-Forecasting_PADMAJA.pdf",
            "sender_name": "Test User",
            "sender_role": "student",
            "message": "Hello, this is a test message."
        }
        response = self.client.post("/api/paper-chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["paper_title"], payload["paper_title"])
        self.assertEqual(data["sender_name"], payload["sender_name"])
        self.assertEqual(data["sender_role"], payload["sender_role"])
        self.assertEqual(data["message"], payload["message"])
        self.assertIn("timestamp", data)

    def test_09_get_paper_chats(self):
        """Test GET /api/paper-chat: endpoint returns a list (may be empty in offline/network-blocked env)."""
        paper = "Agri-Ai-Intelligent-Plant-Disease-Surveillance-and-Predictive-Forecasting_PADMAJA.pdf"
        response = self.client.get(f"/api/paper-chat?paper_title={paper}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # Verify the structure of any returned messages
        for msg in data:
            self.assertIn("paper_title", msg)
            self.assertIn("sender_name", msg)
            self.assertIn("sender_role", msg)
            self.assertIn("message", msg)
            self.assertIn("timestamp", msg)


    def test_10_post_faculty_chat(self):
        """Test POST /api/faculty-chat: message is created and a timestamp is returned."""
        payload = {
            "faculty_name": "Dr. Padmaja",
            "sender_name": "Student Alice",
            "sender_role": "student",
            "message": "Hello Professor Padmaja, I have a question about crop diseases."
        }
        response = self.client.post("/api/faculty-chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["faculty_name"], payload["faculty_name"])
        self.assertEqual(data["sender_name"], payload["sender_name"])
        self.assertEqual(data["sender_role"], payload["sender_role"])
        self.assertEqual(data["message"], payload["message"])
        self.assertIn("timestamp", data)

    def test_11_get_faculty_chats(self):
        """Test GET /api/faculty-chat: endpoint returns a list of messages for the faculty."""
        faculty = "Dr. Padmaja"
        response = self.client.get(f"/api/faculty-chat?faculty_name={faculty}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) >= 1)
        for msg in data:
            self.assertEqual(msg["faculty_name"], faculty)
            self.assertIn("sender_name", msg)
            self.assertIn("sender_role", msg)
            self.assertIn("message", msg)
            self.assertIn("timestamp", msg)

    def test_12_get_all_faculty_chats(self):
        """Test GET /api/faculty-chat/all: returns active threads."""
        response = self.client.get("/api/faculty-chat/all")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # We should have at least the thread we created for Dr. Padmaja
        self.assertTrue(len(data) >= 1)
        found = False
        for thread in data:
            self.assertIn("faculty_name", thread)
            self.assertIn("message_count", thread)
            self.assertIn("last_message_at", thread)
            if thread["faculty_name"] == "Dr. Padmaja":
                found = True
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
