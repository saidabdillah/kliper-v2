import os,tempfile,unittest
from pathlib import Path
from fastapi.testclient import TestClient
from app import app
class Web(unittest.TestCase):
 def test_guard(self):
  c=TestClient(app,base_url="http://localhost:8765");self.assertEqual(c.post("/api/projects",json={"url":"http://127.0.0.1"}).status_code,403);self.assertEqual(c.post("/api/projects",json={"url":"http://127.0.0.1"},headers={"X-Studio":"1"}).status_code,400); self.assertIn("ClipStudio",c.get("/").text)
