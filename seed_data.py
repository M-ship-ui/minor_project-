import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from PIL import Image, ImageDraw, ImageFont
import database
import ml_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
SAMPLE_DIR = os.path.join(BASE_DIR, 'static', 'img', 'sample_items')

def generate_sample_item_images():
    """Generate realistic placeholder images for seeded academic items."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    items_to_render = [
        ("dell_xps_lost.jpg", (40, 50, 70), (200, 210, 225), "Dell XPS 15", "Lost Item - Serial: DLXPS"),
        ("dell_xps_found.jpg", (45, 55, 75), (195, 205, 220), "Dell XPS 15", "Found at Central Library"),
        ("id_card_lost.jpg", (11, 37, 69), (212, 175, 55), "Sanskriti ID", "O. Pulla Reddy - 2302320110"),
        ("id_card_found.jpg", (15, 42, 75), (210, 170, 50), "Found Student ID", "SAC Cafeteria Counter"),
        ("oscilloscope.jpg", (25, 40, 45), (100, 200, 160), "Tektronix 100MHz", "VLSI Hardware Lab"),
        ("projector_remote.jpg", (30, 30, 35), (220, 220, 220), "Sony Remote", "Seminar Hall A"),
        ("calculator.jpg", (20, 30, 50), (230, 230, 230), "Casio fx-991EX", "Exam Hall 3 Desk"),
        ("airpods.jpg", (240, 240, 245), (30, 30, 30), "AirPods Pro", "Sports Complex Gym"),
        ("chemistry_book.jpg", (80, 25, 30), (255, 255, 255), "Organic Chem", "Morrison & Boyd 7th Ed"),
        ("arduino_kit.jpg", (0, 120, 130), (255, 255, 255), "Arduino Starter Kit", "Innovation Robotics Lab")
    ]

    for filename, bg_color, fg_color, text_title, text_sub in items_to_render:
        out_path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.exists(out_path):
            img = Image.new('RGB', (400, 300), color=bg_color)
            draw = ImageDraw.Draw(img)
            # Draw decorative border & box
            draw.rectangle([15, 15, 385, 285], outline=fg_color, width=3)
            draw.rectangle([25, 25, 375, 80], fill=(20, 25, 35))
            
            # Draw text
            draw.text((35, 40), f"SANSKRITI UNIVERSITY - ASSET", fill=(212, 175, 55))
            draw.text((40, 110), text_title, fill=fg_color)
            draw.text((40, 145), text_sub, fill=(180, 180, 190))
            draw.text((40, 240), f"Captured: {datetime.now().strftime('%Y-%m-%d')}", fill=(140, 140, 150))
            
            img.save(out_path, format='JPEG', quality=85)
            # Also copy to sample dir
            img.save(os.path.join(SAMPLE_DIR, filename), format='JPEG', quality=85)

def seed_all():
    """Populate database with rich initial academic data."""
    print("Initializing database...")
    database.init_db()
    generate_sample_item_images()
    
    conn = database.get_raw_connection()
    cursor = conn.cursor()

    # Clear previous seed data cleanly
    for table in ['recovery_history', 'email_logs', 'notifications', 'audit_logs', 'ai_matches', 'claims', 'institutional_assets', 'items', 'users']:
        cursor.execute(f"DELETE FROM {table}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

    print("Seeding Users...")
    users = [
        (
            1, "Dr. Sakuldeep Singh (Director/Admin)", "admin@sanskriti.edu.in",
            generate_password_hash("admin123"), "admin",
            "Campus Administration & Security", "ADM-001", "+91 98765 43210", "default_avatar.png"
        ),
        (
            2, "Prof. Amit Sharma (HOD CSE)", "hod.cs@sanskriti.edu.in",
            generate_password_hash("hod123"), "dept_head",
            "Computer Science & Engineering", "HOD-CSE-01", "+91 98765 43211", "default_avatar.png"
        ),
        (
            3, "Rajesh Kumar (Library Officer)", "staff.rajesh@sanskriti.edu.in",
            generate_password_hash("staff123"), "staff",
            "Central Library", "STF-LIB-102", "+91 98765 43212", "default_avatar.png"
        ),
        (
            4, "O. Pulla Reddy (Student)", "student.reddy@sanskriti.edu.in",
            generate_password_hash("student123"), "student",
            "Computer Science & Engineering", "2302320110", "+91 98765 43213", "default_avatar.png"
        ),
        (
            7, "O. Pulla Reddy (Alias)", "student.pulla@sanskriti.edu.in",
            generate_password_hash("student123"), "student",
            "Computer Science & Engineering", "2302320110", "+91 98765 43213", "default_avatar.png"
        ),
        (
            8, "O. Pulla Reddy (Mukesh Alias)", "student.mukesh@sanskriti.edu.in",
            generate_password_hash("student123"), "student",
            "Computer Science & Engineering", "2302320110", "+91 98765 43213", "default_avatar.png"
        ),
        (
            5, "Priya Verma (Student)", "student.priya@sanskriti.edu.in",
            generate_password_hash("priya123"), "student",
            "Electronics & Communication", "2023-BTEC-019", "+91 98765 43214", "default_avatar.png"
        ),
        (
            6, "Arjun Nair (Student)", "student.arjun@sanskriti.edu.in",
            generate_password_hash("arjun123"), "student",
            "Mechanical Engineering", "2022-BTME-088", "+91 98765 43215", "default_avatar.png"
        )
    ]
    cursor.executemany("""
        INSERT INTO users (id, name, email, password_hash, role, department, id_number, phone, avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users)

    print("Seeding Institutional Assets...")
    inst_assets = [
        (
            "SKU-AST-2024-001", "Dell Latitude 5430 Core i7 Laptop", "Laptops",
            "16GB RAM, 512GB SSD, Intel i7-1265U", "SN-DLL-883109",
            "Computer Science & Engineering", "CS Lab 3 Incharge", "Academic Block A - Room 204",
            "Active", "2024-01-15", 72000.0
        ),
        (
            "SKU-AST-2024-042", "Epson PowerLite Cinema Projector", "Projectors",
            "4000 Lumens Full HD Laser Projector", "SN-EPS-991204",
            "Campus Administration & Security", "Audi Tech Support", "Main Auditorium Hall",
            "Active", "2024-02-20", 115000.0
        ),
        (
            "SKU-AST-2023-119", "Tektronix TBS1102B Digital Oscilloscope", "Laboratory Equipment",
            "100MHz 2-Channel 2GS/s", "SN-TEK-441029",
            "Electronics & Communication", "Prof. R. Sengupta", "Science Complex - Lab 302",
            "Active", "2023-08-10", 68000.0
        ),
        (
            "SKU-AST-2024-205", "Sony VPL-FHZ85 Laser Projector", "Projectors",
            "8000 Lumens WUXGA", "SN-SNY-330198",
            "Mechanical Engineering", "Dept Coordinator", "Seminar Hall B",
            "Under Maintenance", "2024-03-05", 185000.0
        ),
        (
            "SKU-AST-2025-088", "HP Z2 Tower G9 Workstation", "Electronic Devices",
            "Intel i9-13900K, RTX A4000, 64GB RAM", "SN-HPZ-771230",
            "Computer Science & Engineering", "AI Research Lab", "Block C - Room 402",
            "Active", "2025-01-18", 165000.0
        ),
        (
            "SKU-AST-2025-301", "Keysight 34461A 6½ Digit Multimeter", "Laboratory Equipment",
            "Truevolt DMM with bench probes", "SN-KEY-551092",
            "Electronics & Communication", "Instrumentation Custodian", "Science Complex - Lab 104",
            "Active", "2025-02-12", 89000.0
        )
    ]
    cursor.executemany("""
        INSERT INTO institutional_assets (asset_tag, name, category, model_specs, serial_number, department, assigned_to, current_location, status, registered_date, value_estimate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inst_assets)

    print("Seeding Items (Lost & Found)...")
    items = [
        # 1. Lost Dell XPS by Mukesh
        (
            1, "TKT-LOST-2026-001", "lost",
            "Dell XPS 15 Silver Laptop with Sanskriti Coding Club Sticker",
            "Laptops",
            "Silver Dell XPS 15 (9520 model) with carbon fiber palm rest, university WiFi registered. Has Sanskriti University Coding Club sticker on top shell and tiny scratch on bottom right bezel.",
            "Computer Science & Engineering",
            "2nd Floor Silent Reading Cubicle #14", "Central Library",
            "2026-09-28", "16:30", "dell_xps_lost.jpg",
            4, "O. Pulla Reddy", "student.reddy@sanskriti.edu.in", 0,
            "Lost", "SN: DLXPS-99214A", "Coding club sticker, blue silicone keyboard protector",
            None, 0, None, None
        ),
        # 2. Found Dell XPS by Rajesh (Library Officer) -> High match with item #1
        (
            2, "TKT-FND-2026-001", "found",
            "Dell XPS 15 Silver Laptop",
            "Laptops",
            "Found a silver Dell laptop left behind on table 14 near the window. Carbon fiber keyboard area with student tech sticker. Handed over to library security counter.",
            "Central Library",
            "2nd Floor study desk near window cubicle 14", "Central Library",
            "2026-09-29", "09:15", "dell_xps_found.jpg",
            3, "Rajesh Kumar (Library Officer)", "staff.rajesh@sanskriti.edu.in", 0,
            "Found", "DLXPS-*****", "Tech sticker on outer lid, dark gray interior",
            "Central Library Front Desk Locker 3B", 0, None, None
        ),
        # 3. Lost ID Card by Mukesh
        (
            3, "TKT-LOST-2026-002", "lost",
            "Sanskriti University Student ID Card - O. Pulla Reddy",
            "ID Cards",
            "Sanskriti University official smart ID card for Computer Science student O. Pulla Reddy (ID: 2302320110). Blue university lanyard attached with library RFID chip.",
            "Computer Science & Engineering",
            "Cafeteria dining hall table 8", "Student Activity Center",
            "2026-10-01", "13:15", "id_card_lost.jpg",
            4, "O. Pulla Reddy", "student.reddy@sanskriti.edu.in", 0,
            "Lost", "2302320110", "Blue university lanyard, transparent card holder",
            None, 0, None, None
        ),
        # 4. Found ID Card by Security -> High match with item #3
        (
            4, "TKT-FND-2026-002", "found",
            "Student Smart ID Card with Blue Sanskriti Lanyard",
            "ID Cards",
            "Found smart card ID for Computer Science student with blue university lanyard and library barcode near cafeteria counter.",
            "Campus Security",
            "Near cafeteria payment counter", "Student Activity Center",
            "2026-10-01", "14:00", "id_card_found.jpg",
            1, "Campus Security Desk", "security@sanskriti.edu.in", 0,
            "Found", "Ends with -042", "Blue lanyard with university emblem",
            "Campus Main Gate Security Booth", 0, None, None
        ),
        # 5. Tektronix Oscilloscope (Under Claim)
        (
            5, "TKT-LOST-2026-003", "lost",
            "Tektronix 100MHz Digital Storage Oscilloscope Unit",
            "Laboratory Equipment",
            "Dual-channel 100MHz digital storage oscilloscope with two probe leads and power adapter. Used for VLSI analog measurement experiments.",
            "Electronics & Communication",
            "VLSI & Hardware Lab Room 302", "Science Complex",
            "2026-09-20", "17:45", "oscilloscope.jpg",
            5, "Priya Verma", "student.priya@sanskriti.edu.in", 0,
            "Under Claim", "SN: TEK-1002-B", "Department yellow asset label partially peeled",
            None, 0, None, None
        ),
        # 6. Tektronix Oscilloscope Found
        (
            6, "TKT-FND-2026-003", "found",
            "Tektronix Digital Oscilloscope Unit with Probes",
            "Laboratory Equipment",
            "Found dual-channel oscilloscope left unattended on equipment trolley in the corridor outside Lab 302.",
            "Electronics & Communication",
            "Corridor outside Lab 302", "Science Complex",
            "2026-09-21", "08:30", "oscilloscope.jpg",
            1, "Lab Technician Staff", "lab.tech@sanskriti.edu.in", 0,
            "Under Claim", "TEK-****", "Yellow label residue on side handle",
            "Science Complex Room 301 Store", 0, None, None
        ),
        # 7. Projector Remote
        (
            7, "TKT-FND-2026-004", "found",
            "Sony 4K Laser Projector Remote Control",
            "Projectors",
            "Black Sony projector remote commander unit RM-PJ28 found on podium desk after guest lecture.",
            "Mechanical Engineering",
            "Podium Desk, Seminar Hall A", "Academic Block B",
            "2026-10-02", "16:45", "projector_remote.jpg",
            1, "Audi Support", "support@sanskriti.edu.in", 0,
            "Found", "Model RM-PJ28", "White sticker label 'HALL-A' on rear battery flap",
            "Dean Office Media Storage Box 1", 0, None, None
        ),
        # 8. Casio Calculator (Closed / Recovered)
        (
            8, "TKT-LOST-2026-004", "lost",
            "Casio fx-991EX ClassWiz Scientific Calculator",
            "Electronic Devices",
            "Black and white Casio ClassWiz fx-991EX calculator with slide-on protective hard case. Name 'Arjun' written in silver marker inside cover.",
            "Mechanical Engineering",
            "Desk 24, Examination Hall 3", "Academic Block A",
            "2026-09-15", "12:00", "calculator.jpg",
            6, "Arjun Nair", "student.arjun@sanskriti.edu.in", 0,
            "Returned", "fx-991EX", "Silver marker 'Arjun' inside slide cover",
            None, 0, None, None
        ),
        # 9. Apple AirPods Pro
        (
            9, "TKT-LOST-2026-005", "lost",
            "Apple AirPods Pro 2nd Gen in Black Leather Case",
            "Electronic Devices",
            "White AirPods Pro (2nd Generation, MagSafe USB-C) enclosed in a Nomad black horween leather protective case with small lanyard strap.",
            "Computer Science & Engineering",
            "Locker area bench", "Sports Complex",
            "2026-10-03", "18:00", "airpods.jpg",
            4, "O. Pulla Reddy", "student.reddy@sanskriti.edu.in", 0,
            "Lost", "SN: H***72K", "Black leather case, faint scuff on lower lip",
            None, 0, None, None
        ),
        # 10. Organic Chemistry Book
        (
            10, "TKT-LOST-2026-006", "lost",
            "Morrison & Boyd Organic Chemistry 7th Edition Textbook",
            "Books",
            "Hardcover Pearson international edition textbook. Contains handwritten notes and bookmarks in Chapter 14 on Reaction Mechanisms.",
            "Pharmacy & Chemical Sciences",
            "Chemistry Reading Room Table 4", "Science Complex",
            "2026-09-24", "15:10", "chemistry_book.jpg",
            5, "Priya Verma", "student.priya@sanskriti.edu.in", 0,
            "Lost", "ISBN: 978-0136436690", "Green sticky tabs on page 412 and 580",
            None, 0, None, None
        ),
        # 11. Arduino Kit
        (
            11, "TKT-FND-2026-005", "found",
            "Arduino Uno Rev3 Starter Kit with Clear Component Box",
            "Project Equipment",
            "Clear plastic tackle box containing Arduino Uno microcontroller board, breadboard, jumper cables, and ultrasonic sensor module.",
            "Computer Science & Engineering",
            "Robotics Club Workstation 2", "Innovation Center",
            "2026-10-04", "17:30", "arduino_kit.jpg",
            2, "Prof. Amit Sharma", "hod.cs@sanskriti.edu.in", 0,
            "Found", "Arduino Uno R3 SMD", "Label 'Team Rover 2026' on box lid",
            "Innovation Lab Cabinet 4", 0, None, None
        ),
        # 12. Lenovo ThinkPad (Escalated item overdue > 7 days)
        (
            12, "TKT-LOST-2026-007", "lost",
            "Lenovo ThinkPad L14 Gen 3 University Project Laptop",
            "Laptops",
            "Black matte Lenovo ThinkPad with university barcoded sticker. Lost during evening project review symposium.",
            "Computer Science & Engineering",
            "Symposium Hall Ground Floor", "Academic Block C",
            "2026-09-18", "19:00", None,
            4, "O. Pulla Reddy", "student.reddy@sanskriti.edu.in", 0,
            "Lost", "SN: TP-L14-991", "University barcode label AST-CS-2024",
            None, 1, "Unresolved for over 18 days with high institutional value. Auto-escalated to Campus Security Head.", "2026-09-26 10:00:00"
        )
    ]

    cursor.executemany("""
        INSERT INTO items (
            id, ticket_number, type, title, category, description, department, location,
            building_zone, date_event, time_event, image_path, user_id, reporter_name,
            reporter_contact, is_anonymous, status, serial_number_hint, identifying_marks,
            storage_location, escalated, escalation_reason, escalated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, items)

    print("Seeding Claims...")
    claims = [
        # Claim 1: Priya Verma claiming oscilloscope #6
        (
            1, "CLM-2026-001", 6, 5,
            "Department lab custody requisition voucher #EC-VLSI-889 signed by Prof. Sengupta. Serial number matches TEK-1002-B.",
            "TEK-1002-B", "Yellow sticker residue on side handle, custom calibration certificate copy attached",
            "oscilloscope.jpg", "Under Claim", "Awaiting physical verification at Science Complex room 301.",
            1, None, None, None
        )
    ]
    cursor.executemany("""
        INSERT INTO claims (
            id, claim_number, item_id, claimant_id, proof_description, proof_serial_number,
            unique_identifiers, proof_image_path, status, admin_notes, verified_by,
            verified_at, handover_officer, handover_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, claims)

    print("Running AI Matching on Seeded Items...")
    # Run the real ML engine to calculate matches between lost and found items
    cursor.execute("SELECT * FROM items WHERE type='lost'")
    lost_rows = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM items WHERE type='found'")
    found_rows = [dict(row) for row in cursor.fetchall()]

    for l_item in lost_rows:
        for f_item in found_rows:
            score_data = ml_engine.calculate_match_score(l_item, f_item, base_upload_folder=UPLOADS_DIR)
            if score_data['composite_score'] >= 35.0:
                status = "Suggested"
                if score_data['composite_score'] >= 75.0:
                    status = "Suggested"
                cursor.execute("""
                    INSERT OR REPLACE INTO ai_matches (
                        lost_item_id, found_item_id, text_similarity_score, category_score,
                        location_score, visual_score, composite_score, status, match_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    l_item['id'], f_item['id'],
                    score_data['text_similarity_score'], score_data['category_score'],
                    score_data['location_score'], score_data['visual_score'],
                    score_data['composite_score'], status,
                    f"AI Match Confidence: {score_data['confidence_tier']} ({score_data['composite_score']}%)"
                ))

    print("Seeding Recovery History...")
    recoveries = [
        (
            1, "REC-2026-001", 8, 8, None,
            "Casio fx-991EX ClassWiz Scientific Calculator", "Electronic Devices",
            "Arjun Nair", "student.arjun@sanskriti.edu.in", "Exam Invigilator Desk",
            "Security Officer Ramesh Chand", "Main Gate Security Desk #1", 3,
            "Identity verified with Student Card #2022-BTME-088. Silver marker signature confirmed."
        )
    ]
    cursor.executemany("""
        INSERT INTO recovery_history (
            id, recovery_number, lost_item_id, found_item_id, claim_id, item_title,
            category, owner_name, owner_email, finder_name, handover_officer,
            handover_desk, resolution_days, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, recoveries)

    print("Seeding Notifications...")
    notifs = [
        (
            1, 4, "High AI Match Detected! [84.5%]",
            "An item matching your lost 'Dell XPS 15 Silver Laptop' was registered by Central Library staff.",
            "match", "/ai/matches", 0
        ),
        (
            2, 4, "High AI Match Detected! [82.0%]",
            "A found 'Student Smart ID Card' closely matches your reported lost ID card.",
            "match", "/ai/matches", 0
        ),
        (
            3, 1, "Item Auto-Escalated to Security Authority",
            "Ticket #TKT-LOST-2026-007 (Lenovo ThinkPad) has been unresolved for >7 days. Immediate action recommended.",
            "escalation", "/admin/escalations", 0
        ),
        (
            4, 5, "Ownership Claim Under Review",
            "Your claim #CLM-2026-001 for Tektronix Digital Oscilloscope is currently under review by authorities.",
            "claim", "/claims/manage", 1
        )
    ]
    cursor.executemany("""
        INSERT INTO notifications (id, user_id, title, message, type, link, is_read)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, notifs)

    print("Seeding Audit Logs...")
    logs = [
        (1, 4, "O. Pulla Reddy", "ITEM_REPORTED", "Item", 1, "Reported lost Dell XPS 15 laptop in Central Library"),
        (2, 3, "Rajesh Kumar", "ITEM_REPORTED", "Item", 2, "Reported found Dell XPS 15 laptop at Library Counter"),
        (3, None, "AI ML Engine", "MATCH_DETECTED", "Match", 1, "High-confidence composite match score (84.5%) discovered between tickets #1 and #2"),
        (4, 5, "Priya Verma", "CLAIM_SUBMITTED", "Claim", 1, "Submitted ownership claim #CLM-2026-001 with lab voucher proof"),
        (5, 1, "Dr. Sakuldeep Singh", "ESCALATION_TRIGGERED", "Item", 12, "Auto-escalated high-value Lenovo ThinkPad laptop to Security Authority queue")
    ]
    cursor.executemany("""
        INSERT INTO audit_logs (id, user_id, user_name, action, target_type, target_id, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, logs)

    print("Seeding Simulated Email Logs...")
    emails = [
        (
            1, "student.reddy@sanskriti.edu.in", "O. Pulla Reddy",
            "[Sanskriti Recovery Portal] Potential Match Found for Lost Item #TKT-LOST-2026-001",
            "Dear O. Pulla Reddy,\n\nOur AI matching engine has detected an 84.5% match for your Dell XPS 15 laptop reported lost on 2026-09-28. Please visit the portal to review candidate photos and initiate verification.\n\nRegards,\nSanskriti University Asset Recovery Cell"
        ),
        (
            2, "security@sanskriti.edu.in", "Campus Security Control",
            "[URGENT] Asset Escalation Alert: Unresolved Ticket #TKT-LOST-2026-007",
            "Attention Security Office,\n\nTicket #TKT-LOST-2026-007 has remained open without resolution for over 7 days. Institutional value exceeds threshold. Please initiate physical verification at Academic Block C.\n\nAutomated Security System"
        )
    ]
    cursor.executemany("""
        INSERT INTO email_logs (id, recipient_email, recipient_name, subject, body)
        VALUES (?, ?, ?, ?, ?)
    """, emails)

    conn.commit()
    conn.close()
    print("All seed data created successfully!")

if __name__ == '__main__':
    seed_all()
