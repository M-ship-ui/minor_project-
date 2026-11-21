# Intelligent Academic Asset Recovery and Management System

**Institution:** Sanskriti University  
**Student Name:** O. Pulla Reddy (Enrollment No: `2302320110`)  
**Faculty Guide:** Dr. Sakuldeep Singh  
**Project Start Date:** 25-08-2026 | **Checkpoint Date:** 05-10-2026  

---

## 🏛️ Project Overview

The **Intelligent Academic Asset Recovery and Management System** is a production-ready, centralized web portal designed for university campuses. It replaces fragmented, unreliable communication channels (such as WhatsApp groups, social media posts, and physical notice boards) with a standardized, secure platform for reporting, searching, AI-matching, adjudicating, and recovering lost and found belongings and university institutional assets.

The platform handles campus assets such as:
- **Laptops** (personal and department issue)
- **Projectors & A/V Remotes**
- **Textbooks & Academic Courseware**
- **Student & Staff Smart ID Cards**
- **Laboratory Equipment** (oscilloscopes, multimeters, microscopes)
- **Electronic Devices** (calculators, audio gear, tablets)
- **Project Kits** (Arduino/Raspberry Pi robotics equipment)
- **Other University Belongings**

---

## 🌟 Key Features & Architectural Capabilities

1. **Multi-Factor AI/ML Recommendation Engine:**
   - **TF-IDF Semantic Vectorization & Cosine Similarity (`scikit-learn`):** Extracts textual features from item titles, categories, departments, and descriptions.
   - **Computer Vision Feature Extraction (`OpenCV` & `Pillow`):** Preprocesses asset images into normalized HSV color spaces to compute color histogram correlations.
   - **Composite Match Scoring:** Weighted combination of:
     - 45% TF-IDF Text Cosine Similarity
     - 25% Category Taxonomy Alignment
     - 15% Spatial & Departmental Proximity
     - 10% Visual Color Histogram Similarity
     - 5% Temporal Proximity
   - Automatic background triggers scan new reports and dispatch notifications.

2. **Standard & Anonymous Complaint Submission:**
   - Privacy-preserving reporting options for sensitive or high-value assets.

3. **Anti-Spam & Duplicate Detection:**
   - Algorithmic filters scan incoming reports for repetitive text patterns and high textual similarity (>88%) against recent submissions to protect database integrity.

4. **Structured Ownership Claim Lifecycle:**
   - Full state progression: `Lost` / `Found` ➔ `Under Claim` ➔ `Verified` ➔ `Returned` ➔ `Closed`.
   - Claimants provide purchase invoices, secret serial numbers, or distinctive identifying marks.
   - Authorities conduct physical verification and issue an official **Certificate of Asset Restoration**.

5. **Multi-Role Security Architecture:**
   - Role-Based Access Control (RBAC) supporting **Student**, **Staff**, **Department Head (HOD)**, and **Admin**.
   - Password encryption using PBKDF2 with SHA-256 hashing.

6. **Authority Oversight, Escalation & Auditing:**
   - **Authority Dashboard:** Live monitoring of active items, recovery rate, dispute counts.
   - **Auto-Escalation Engine:** Automatically flags tickets unresolved for over 7 days or contested claims.
   - **Immutable Audit Trails:** Logs every status change, claim action, and authentication event with timestamps.

7. **Analytics & Visual Reporting:**
   - Interactive Chart.js graphs: Monthly recovery trends, category distributions, campus loss hotspots, and turnaround duration.
   - One-click CSV incident report export.

---

## 📂 Project Directory Structure

```
academic_asset_system/
├── app.py                     # Main Flask Application & Route Controllers (all 17 modules)
├── auth_helper.py             # Authentication helpers, session verification & RBAC decorators
├── database.py                # SQLite database connection, schema setup & audit utilities
├── ml_engine.py               # AI/ML TF-IDF, OpenCV histogram extraction & composite matching
├── seed_data.py               # Database seeder with realistic campus data & test accounts
├── test_app.py                # Automated unit test suite verifying all modules
├── requirements.txt           # Python dependency specifications
├── academic_assets.db         # SQLite database file (created on init)
├── static/
│   ├── css/
│   │   └── style.css          # Sanskriti University custom palette & responsive styling
│   ├── js/
│   │   ├── main.js            # Image upload preview, quick-login handlers, form validations
│   │   └── charts.js          # Chart.js visualization configurations
│   ├── img/
│   │   └── sample_items/      # Pre-generated sample images for seeded items
│   └── uploads/               # Upload directory for item photos & claim proofs
└── templates/
    ├── base.html              # University master layout (Navbar, Notifications, Topbar, Footer)
    ├── index.html             # Module 1: Home Dashboard & Live Counters
    ├── auth/
    │   ├── login.html         # Module 3: Login with 1-click Demo Fill Buttons
    │   └── register.html      # Module 2: User Registration Form
    ├── user/
    │   └── profile.html       # Module 4: User Profile & Personal Tickets
    ├── assets/
    │   ├── list.html          # Lost / Found item listings with category filters
    │   ├── report_lost.html   # Module 6: Report Lost Asset (with photo & spam filter)
    │   ├── report_found.html  # Module 7: Report Found Asset (with storage custody desk)
    │   ├── item_detail.html   # Detailed Asset Dossier & Lifecycle Progress Bar
    │   └── institutional.html # Module 5: Campus Inventory / Departmental Equipment
    ├── search/
    │   └── search.html        # Module 8: Multi-Parameter Search & Filter
    ├── ai/
    │   ├── matching_center.html # Module 9: AI Asset Matching Hub
    │   └── item_matches.html  # Ranked Candidate Matches Side-by-Side Comparison
    ├── claims/
    │   ├── manage_claims.html # Module 10: Recovery Management & Claim Queue
    │   ├── submit_claim.html  # Ownership Claim Submission with Proof
    │   └── claim_detail.html  # Authority Adjudication & Handover Verification
    ├── notifications/
    │   └── notifications.html # Module 11: In-Portal Notifications & Campus Email Logs
    ├── admin/
    │   ├── dashboard.html     # Module 12: Authority Oversight Command Center
    │   ├── items_management.html # Module 14: Lost & Found Inventory Moderation
    │   ├── match_verification.html # Module 15: Admin AI Match Verification
    │   ├── institutional_assets.html # Module 13: Admin Equipment Registry Management
    │   ├── escalation_queue.html # Auto-Escalation Priority Queue
    │   └── audit_logs.html    # Immutable System Audit Trails
    ├── recovery/
    │   ├── history.html       # Module 16: Permanent Recovery History Ledger
    │   └── certificate.html   # Official Printable Handover Certificate
    └── reports/
        └── statistics.html    # Module 17: Reports, Visual Analytics & CSV Export
```

---

## 🚀 How to Run the Project Locally

### Step 1: Open Terminal in Project Directory
```powershell
cd "c:\Users\bandi\OneDrive\Desktop\academic_asset_system"
```

### Step 2: Install Python Dependencies (if not already installed)
```powershell
pip install -r requirements.txt
```
*(Dependencies: `Flask`, `scikit-learn`, `numpy`, `Pillow`, `opencv-python`)*

### Step 3: Seed Database (Fresh Demo Data)
To ensure all sample accounts, pre-matched items, and historical records are ready:
```powershell
python seed_data.py
```

### Step 4: Run the Flask Web Application
```powershell
python app.py
```

### Step 5: Open in Your Web Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Evaluation Accounts (Ready to Test)

For your college presentation, quick-fill buttons are provided on the login page:

| Role | Name | Email | Password |
|---|---|---|---|
| **Admin / Guide** | Dr. Sakuldeep Singh | `admin@sanskriti.edu.in` | `admin123` |
| **Dept Head (HOD)** | Prof. Amit Sharma | `hod.cs@sanskriti.edu.in` | `hod123` |
| **Staff / Security** | Rajesh Kumar (Library) | `staff.rajesh@sanskriti.edu.in` | `staff123` |
| **Student (Presenter)** | O. Pulla Reddy | `student.reddy@sanskriti.edu.in` | `student123` |
| **Student 2** | Priya Verma | `student.priya@sanskriti.edu.in` | `priya123` |

---

## 🧪 Running Automated Unit Tests

Run the comprehensive test suite verifying all 17 modules:
```powershell
python test_app.py
```
*(Output: `Ran 10 tests ... OK`)*

---

## 🎤 College Presentation Demonstration Flow (For Tomorrow)

Follow this step-by-step walkthrough to present the project to your faculty panel:

1. **Introduction & Motivation (Home Screen):**
   - Open `http://127.0.0.1:5000`.
   - Point out the Sanskriti University branding, live recovery rate counter (e.g. `83.3%`), and recent items feed.
   - Explain the problem: campus lost property is traditionally lost in informal WhatsApp groups or ignored notice boards.

2. **The AI Asset Matching Engine in Action:**
   - Click on the **AI Matcher** tab in the top navigation bar.
   - Explain the formula card (TF-IDF vectorizer + OpenCV color histograms).
   - Show the top match: **Dell XPS 15 Silver Laptop** lost by student O. Pulla Reddy vs found by Library Officer Rajesh Kumar.
   - Click **Deep Inspection** to showcase the side-by-side feature comparison:
     - TF-IDF Text Cosine Similarity: `~93%`
     - Category Alignment: `100%`
     - Location Proximity: `100%`
     - Overall Composite Score: `~84%`

3. **Report Lost / Found with Instant Duplicate Checking:**
   - Log in as **O. Pulla Reddy** (use the 1-click button on `/login`).
   - Click **Report Lost Item**. Show the form validation, room selection, anonymous toggle, and photo upload.
   - Explain how submitting automatically triggers the AI background scan.

4. **Ownership Verification & Claim Workflow:**
   - Navigate to the found Dell XPS laptop or an oscilloscope.
   - Click **Submit Claim**.
   - Show how the claimant enters confidential details (matching serial number, distinguishing marks) and uploads proof.
   - The status dynamically updates from `Found` to `Under Claim`.

5. **Authority Console & Adjudication:**
   - Sign in as **Admin / Faculty Guide (Dr. Sakuldeep Singh)**.
   - Open **Authority Dashboard**: show the escalation queue, active status distribution chart, and audit logs.
   - Navigate to **Claims & Ownership** -> click **Review & Adjudicate**.
   - Verify the serial number against the confidential escrow record.
   - Click **Complete Physical Handover & Close**.

6. **Official Certificate of Asset Restoration:**
   - Click **Recovery Ledger** -> view the newly closed record.
   - Click **Certificate**: show the university-crested certificate complete with serial verification stamp, officer signatures, and Print/PDF capability.

7. **Analytics & Campus Facilities Planning:**
   - Navigate to **Analytics** (`/reports/statistics`).
   - Present the Chart.js visual graphs:
     - Lost vs Found by Category
     - High-Loss Campus Hotspots (Central Library, SAC, Science Complex)
     - Average turnaround speed
   - Click **Export Incident Report (CSV)** to demonstrate administrative export.

---

## 🛡️ Academic References & Credits

- **Pedregosa et al. (2011)** — *Scikit-learn: Machine Learning in Python*, JMLR 12, pp. 2825-2830.
- **OpenCV Computer Vision Library** — HSV Histogram Extraction and Bhattacharyya Metric.
- **Sanskriti University** — Department of Computer Science & Engineering, Academic Year 2026-27.
