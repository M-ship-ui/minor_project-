import unittest
import os
import database
import seed_data
from app import app

class AcademicAssetSystemTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        # Seed database
        seed_data.seed_all()

    def test_01_homepage_renders(self):
        """Test home/dashboard renders properly with statistics."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Intelligent Academic Asset Recovery', response.data)
        self.assertIn(b'SANSKRITI UNIVERSITY', response.data)
        self.assertIn(b'Recovery Rate', response.data)

    def test_02_user_login_success_and_failure(self):
        """Test authentication flow for student and admin."""
        # Valid login as student Mukesh
        res = self.client.post('/login', data={
            'email': 'student.mukesh@sanskriti.edu.in',
            'password': 'student123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back, B. Mukesh', res.data)

        # Invalid password
        res_bad = self.client.post('/login', data={
            'email': 'student.mukesh@sanskriti.edu.in',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res_bad.data)

    def test_03_search_assets(self):
        """Test multi-parameter asset search."""
        # Query for Dell
        res = self.client.get('/search?q=Dell')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dell XPS 15', res.data)

        # Query by category: Laboratory Equipment
        res_cat = self.client.get('/search?category=Laboratory+Equipment')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b'Oscilloscope', res_cat.data)

    def test_04_ai_matching_center(self):
        """Test AI asset matching engine and matrix view."""
        res = self.client.get('/ai/matching-center')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AI Intelligent Asset Matching Hub', res.data)
        self.assertIn(b'Composite Matching Formula', res.data)
        self.assertIn(b'TF-IDF Description Cosine Sim', res.data)

    def test_05_item_specific_ai_matches(self):
        """Test candidate ranking for item #1 (Mukesh Dell XPS)."""
        res = self.client.get('/ai/item/1/matches')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ranked Candidate Matches', res.data)
        self.assertIn(b'Dell XPS 15 Silver Laptop', res.data)

    def test_06_institutional_asset_catalog(self):
        """Test campus inventory management."""
        res = self.client.get('/institutional-assets')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Campus Institutional Asset Registry', res.data)
        self.assertIn(b'SKU-AST-2024-001', res.data)

    def test_07_recovery_history_and_certificate(self):
        """Test permanent recovery ledger and printable certificate."""
        res = self.client.get('/recovery/history')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'REC-2026-001', res.data)

        res_cert = self.client.get('/recovery/certificate/1')
        self.assertEqual(res_cert.status_code, 200)
        self.assertIn(b'OFFICIAL CERTIFICATE OF ASSET RESTORATION', res_cert.data)
        self.assertIn(b'Casio fx-991EX', res_cert.data)

    def test_08_reports_and_statistics(self):
        """Test visual analytics module."""
        res = self.client.get('/reports/statistics')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Institutional Asset Analytics', res.data)
        self.assertIn(b'Central Library', res.data)

    def test_09_admin_dashboard_authorization(self):
        """Test admin role security and authority oversight console."""
        # Login as Admin Dr. Sakuldeep Singh
        self.client.post('/login', data={
            'email': 'admin@sanskriti.edu.in',
            'password': 'admin123'
        }, follow_redirects=True)

        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'University Oversight &amp; Audit Command Center', res.data)
        self.assertIn(b'Escalated Tickets', res.data)

    def test_10_report_lost_item_creation(self):
        """Test standard ticket creation with automatic AI matching."""
        # Login as Priya
        self.client.post('/login', data={
            'email': 'student.priya@sanskriti.edu.in',
            'password': 'priya123'
        }, follow_redirects=True)

        res = self.client.post('/report/lost', data={
            'title': 'Sony Noise Cancelling Headphones WH-1000XM4',
            'category': 'Electronic Devices',
            'description': 'Black over-ear Sony headphones with custom foam pads forgotten in CS lab.',
            'department': 'Computer Science & Engineering',
            'building_zone': 'Academic Block A',
            'location': 'Computer Lab 2 Table 5',
            'date_event': '2026-10-05',
            'time_event': '14:30',
            'serial_number_hint': 'SN: SNY-WH-441',
            'identifying_marks': 'Small scratch on right ear cup',
            'is_anonymous': '0'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Lost item ticket', res.data)

if __name__ == '__main__':
    unittest.main()
