"""
Generate high-resolution UI figures for the Sanskriti University Academic Asset Project Report:
Figures 5.1.1 to 5.1.8
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"C:\Users\bandi\OneDrive\Desktop\academic_asset_system\figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors
NAVY = (0, 33, 71)
DARK_NAVY = (0, 21, 46)
GOLD = (201, 151, 0)
WHITE = (255, 255, 255)
LIGHT_GRAY = (248, 250, 252)
BORDER_GRAY = (226, 232, 240)
TEXT_DARK = (30, 41, 59)
TEXT_MUTED = (100, 116, 139)
RED = (239, 68, 68)
GREEN = (16, 185, 129)
YELLOW = (217, 119, 6)
BLUE = (37, 99, 235)

def get_font(name="segoeui.ttf", size=14):
    font_path = os.path.join(r"C:\Windows\Fonts", name)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

font_title = get_font("segoeuib.ttf", 20)
font_h1 = get_font("segoeuib.ttf", 16)
font_h2 = get_font("segoeuib.ttf", 14)
font_body = get_font("segoeui.ttf", 12)
font_small = get_font("segoeui.ttf", 10)
font_mono = get_font("consola.ttf", 11)

def draw_browser_frame(draw, width, height, title_url):
    # Top browser header bar
    draw.rectangle([0, 0, width, 40], fill=(230, 235, 242))
    draw.line([0, 40, width, 40], fill=BORDER_GRAY, width=1)
    # 3 dots
    draw.ellipse([14, 14, 24, 24], fill=(255, 95, 86))
    draw.ellipse([32, 14, 42, 24], fill=(255, 189, 46))
    draw.ellipse([50, 14, 60, 24], fill=(39, 201, 63))
    # URL bar
    draw.rounded_rectangle([75, 8, width - 20, 32], radius=6, fill=WHITE, outline=BORDER_GRAY)
    draw.text((90, 12), f"🔒 {title_url}", fill=TEXT_MUTED, font=font_small)

def draw_topbar_and_nav(draw, width, active_nav="Home"):
    # University topbar
    draw.rectangle([0, 41, width, 66], fill=DARK_NAVY)
    draw.text((20, 46), "🎓 SANSKRITI UNIVERSITY  |  Academic Asset Recovery Cell", fill=GOLD, font=font_small)
    draw.text((width - 320, 46), "● SYSTEM LIVE  |  Session 2026-27  |  Mathura Campus", fill=WHITE, font=font_small)
    # Main Navbar
    draw.rectangle([0, 67, width, 115], fill=NAVY)
    draw.text((20, 77), "🛡️ Sanskriti University", fill=WHITE, font=font_h1)
    draw.text((20, 97), "Intelligent Academic Asset Recovery Portal", fill=GOLD, font=font_small)
    # Nav links
    links = [("Home", 360), ("Lost Items", 440), ("Found Items", 535), ("AI Matcher", 635), ("Search", 735), ("Dashboard", 815)]
    for name, x in links:
        color = GOLD if name == active_nav else (200, 215, 235)
        draw.text((x, 85), name, fill=color, font=font_body)
    # User badge
    draw.rounded_rectangle([width - 200, 78, width - 20, 106], radius=14, fill=(10, 45, 90), outline=GOLD)
    draw.text((width - 190, 84), "👤 O. Pulla Reddy (Student)", fill=WHITE, font=font_small)

# --------------------------------------------------------------------------------------
# 1. FIGURE 5.1.1: REGISTRATION & LOGIN PAGE
# --------------------------------------------------------------------------------------
def make_fig_5_1_1():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/login")
    draw_topbar_and_nav(draw, W, active_nav="")

    # Center card
    card = [260, 135, 740, 530]
    draw.rounded_rectangle(card, radius=12, fill=WHITE, outline=BORDER_GRAY)
    draw.text((370, 155), "Sign In to Sanskriti Portal", fill=NAVY, font=font_title)
    draw.text((345, 185), "Academic Asset Recovery & Management System", fill=TEXT_MUTED, font=font_small)

    # Email field
    draw.text((290, 215), "University Email Address *", fill=TEXT_DARK, font=font_body)
    draw.rounded_rectangle([290, 235, 710, 268], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((305, 244), "student.reddy@sanskriti.edu.in", fill=TEXT_DARK, font=font_body)

    # Password field
    draw.text((290, 280), "Password *", fill=TEXT_DARK, font=font_body)
    draw.rounded_rectangle([290, 300, 710, 333], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((305, 309), "••••••••••••••••••••", fill=TEXT_MUTED, font=font_body)

    # Sign In Button
    draw.rounded_rectangle([290, 348, 710, 385], radius=6, fill=BLUE)
    draw.text((470, 357), "Sign In", fill=WHITE, font=font_h2)

    # 1-Click Evaluation Login Box
    draw.rounded_rectangle([290, 400, 710, 500], radius=8, fill=(255, 251, 235), outline=GOLD)
    draw.text((320, 410), "⚡ Quick 1-Click Evaluation Logins for Faculty Guide Review", fill=NAVY, font=font_small)

    draw.rounded_rectangle([305, 432, 490, 458], radius=4, fill=WHITE, outline=RED)
    draw.text((315, 437), "🛡️ Admin / Guide (Dr. Sakuldeep)", fill=RED, font=font_small)

    draw.rounded_rectangle([510, 432, 695, 458], radius=4, fill=WHITE, outline=BLUE)
    draw.text((535, 437), "👔 HOD (Prof. Amit Sharma)", fill=BLUE, font=font_small)

    draw.rounded_rectangle([305, 465, 490, 491], radius=4, fill=WHITE, outline=GREEN)
    draw.text((325, 470), "📚 Staff (Rajesh Kumar)", fill=GREEN, font=font_small)

    draw.rounded_rectangle([510, 465, 695, 491], radius=4, fill=NAVY, outline=GOLD)
    draw.text((520, 470), "🎓 Student (O. Pulla Reddy)", fill=GOLD, font=font_small)

    draw.text((410, 508), "New student or faculty? Register Account", fill=BLUE, font=font_small)
    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_1.png"), quality=95)

# --------------------------------------------------------------------------------------
# 2. FIGURE 5.1.2: HOME PAGE
# --------------------------------------------------------------------------------------
def make_fig_5_1_2():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/")
    draw_topbar_and_nav(draw, W, active_nav="Home")

    # Hero Banner
    draw.rounded_rectangle([20, 125, W - 20, 245], radius=14, fill=DARK_NAVY, outline=GOLD)
    draw.rounded_rectangle([40, 138, 220, 158], radius=10, fill=(20, 55, 100), outline=GOLD)
    draw.text((50, 142), "⚡ NLP TF-IDF POWERED", fill=GOLD, font=font_small)

    draw.text((40, 165), "Intelligent Academic Asset Recovery & Management System", fill=WHITE, font=font_title)
    draw.text((40, 195), "Centralized Sanskriti University portal to report lost items, verify ownership, and cross-match candidates.", fill=(200, 215, 235), font=font_body)

    # Hero Action Buttons
    draw.rounded_rectangle([40, 215, 170, 240], radius=6, fill=RED)
    draw.text((55, 220), "+ Report Lost", fill=WHITE, font=font_small)
    draw.rounded_rectangle([180, 215, 310, 240], radius=6, fill=GREEN)
    draw.text((195, 220), "+ Report Found", fill=WHITE, font=font_small)
    draw.rounded_rectangle([320, 215, 460, 240], radius=6, fill=GOLD)
    draw.text((335, 220), "✨ Open AI Matcher", fill=DARK_NAVY, font=font_small)

    # 4 KPI Stat Widgets
    kpis = [
        ("5", "Active Lost Reports", RED, 20),
        ("4", "Items Found & Held", GREEN, 265),
        ("3", "AI Match Pairs Detected", YELLOW, 510),
        ("1", "Recovered & Handed Over", NAVY, 755)
    ]
    for val, lbl, color, x in kpis:
        draw.rounded_rectangle([x, 255, x + 225, 325], radius=10, fill=WHITE, outline=BORDER_GRAY)
        draw.rectangle([x, 255, x + 5, 325], fill=color)
        draw.text((x + 20, 265), val, fill=color, font=font_title)
        draw.text((x + 20, 295), lbl, fill=TEXT_DARK, font=font_small)

    # AI Match Highlight Banner
    draw.rounded_rectangle([20, 335, W - 20, 435], radius=10, fill=(255, 251, 235), outline=GOLD)
    draw.text((35, 345), "⚡ Top AI Match Recommendations (Threshold ≥ 0.25)", fill=NAVY, font=font_h2)

    # Match row
    draw.rounded_rectangle([35, 370, W - 35, 425], radius=6, fill=WHITE, outline=BORDER_GRAY)
    draw.text((45, 380), "Dell XPS 15 Silver Laptop with Coding Club Sticker", fill=RED, font=font_h2)
    draw.text((45, 400), "📍 Central Library 2nd Floor Cubicle #14", fill=TEXT_MUTED, font=font_small)
    draw.text((440, 380), "Dell XPS 15 Silver Laptop", fill=GREEN, font=font_h2)
    draw.text((440, 400), "📍 Held at Central Library Desk Locker 3B", fill=TEXT_MUTED, font=font_small)
    # Score meter
    draw.text((750, 380), "Score: 84.5%", fill=GOLD, font=font_h2)
    draw.rounded_rectangle([750, 405, 870, 415], radius=4, fill=BORDER_GRAY)
    draw.rounded_rectangle([750, 405, 850, 415], radius=4, fill=GOLD)
    draw.rounded_rectangle([890, 382, 970, 412], radius=4, fill=NAVY)
    draw.text((905, 390), "Verify", fill=WHITE, font=font_small)

    # Recent Lost & Found Grid preview
    draw.rounded_rectangle([20, 445, 485, 545], radius=10, fill=WHITE, outline=BORDER_GRAY)
    draw.text((35, 455), "Recently Lost on Campus", fill=RED, font=font_h2)
    draw.text((35, 480), "• Lenovo ThinkPad L14 Gen 3 Project Laptop (Block C)", fill=TEXT_DARK, font=font_small)
    draw.text((35, 500), "• Morrison & Boyd Organic Chemistry 7th Ed (Science)", fill=TEXT_DARK, font=font_small)
    draw.text((35, 520), "• Apple AirPods Pro 2nd Gen in Leather Case (SAC)", fill=TEXT_DARK, font=font_small)

    draw.rounded_rectangle([505, 445, W - 20, 545], radius=10, fill=WHITE, outline=BORDER_GRAY)
    draw.text((520, 455), "Recently Found & Handed In", fill=GREEN, font=font_h2)
    draw.text((520, 480), "• Arduino Uno Rev3 Starter Kit (Innovation Lab)", fill=TEXT_DARK, font=font_small)
    draw.text((520, 500), "• Sony 4K Laser Projector Remote Control (Dean Office)", fill=TEXT_DARK, font=font_small)
    draw.text((520, 520), "• Tektronix 100MHz Digital Storage Oscilloscope (Lab 302)", fill=TEXT_DARK, font=font_small)

    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_2.png"), quality=95)

# --------------------------------------------------------------------------------------
# 3. FIGURE 5.1.3: REPORT LOST / FOUND ITEM FORM
# --------------------------------------------------------------------------------------
def make_fig_5_1_3():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/report/lost")
    draw_topbar_and_nav(draw, W, active_nav="Lost Items")

    card = [150, 130, 850, 540]
    draw.rounded_rectangle(card, radius=12, fill=WHITE, outline=BORDER_GRAY)
    # Header bar inside card
    draw.rounded_rectangle([150, 130, 850, 175], radius=12, fill=RED)
    draw.text((170, 142), "📝 Report Lost Academic Asset Form", fill=WHITE, font=font_h1)
    draw.text((170, 160), "Register asset metadata for automated AI cross-referencing", fill=(255, 230, 230), font=font_small)

    # Fields
    draw.text((180, 190), "Item Title / Device Name *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 210, 820, 240], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 218), "Dell XPS 15 Silver Laptop with Sanskriti Coding Club Sticker", fill=TEXT_DARK, font=font_body)

    draw.text((180, 250), "Asset Category *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 270, 480, 300], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 278), "Laptops & Computers ▼", fill=TEXT_DARK, font=font_body)

    draw.text((500, 250), "Campus Facility / Building *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([500, 270, 820, 300], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((515, 278), "Central Library (Academic Block A) ▼", fill=TEXT_DARK, font=font_body)

    draw.text((180, 310), "Specific Room / Hall Location *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 330, 480, 360], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 338), "2nd Floor Silent Reading Cubicle #14", fill=TEXT_DARK, font=font_body)

    draw.text((500, 310), "Date & Time Misplaced *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([500, 330, 820, 360], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((515, 338), "2026-09-28 at 16:30", fill=TEXT_DARK, font=font_body)

    draw.text((180, 370), "Detailed Description (Used by TF-IDF Vectorizer) *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 390, 820, 440], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 398), "Silver Dell XPS 15-inch laptop with black carbon palm rest and Sanskriti Coding Club sticker on lid.", fill=TEXT_DARK, font=font_body)
    draw.text((195, 418), "Blue silicone keyboard protector attached. Lost during study session.", fill=TEXT_MUTED, font=font_small)

    draw.text((180, 450), "Confidential Serial Number (Verification Proof)", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 470, 480, 500], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 478), "SN: DLXPS-99214A", fill=TEXT_DARK, font=font_body)

    draw.text((500, 450), "Identifying Marks", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([500, 470, 820, 500], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((515, 478), "Coding club sticker on top left lid", fill=TEXT_DARK, font=font_body)

    draw.rounded_rectangle([600, 506, 820, 534], radius=6, fill=RED)
    draw.text((640, 513), "Submit Lost Report", fill=WHITE, font=font_h2)

    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_3.png"), quality=95)

# --------------------------------------------------------------------------------------
# 4. FIGURE 5.1.4: SEARCH AND FILTER PAGE
# --------------------------------------------------------------------------------------
def make_fig_5_1_4():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/search")
    draw_topbar_and_nav(draw, W, active_nav="Search")

    # Search filter card
    draw.rounded_rectangle([20, 125, W - 20, 195], radius=10, fill=WHITE, outline=BORDER_GRAY)
    draw.text((35, 135), "🔍 Search & Multi-Parameter Filter Registry", fill=NAVY, font=font_h2)

    draw.rounded_rectangle([35, 155, 340, 185], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((50, 163), "Search keyword: Dell", fill=TEXT_DARK, font=font_body)

    draw.rounded_rectangle([355, 155, 540, 185], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((370, 163), "Category: Laptops ▼", fill=TEXT_DARK, font=font_body)

    draw.rounded_rectangle([555, 155, 720, 185], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((570, 163), "Type: All Types ▼", fill=TEXT_DARK, font=font_body)

    draw.rounded_rectangle([735, 155, 850, 185], radius=6, fill=BLUE)
    draw.text((760, 163), "Apply Filters", fill=WHITE, font=font_body)

    draw.rounded_rectangle([865, 155, 965, 185], radius=6, fill=WHITE, outline=BORDER_GRAY)
    draw.text((895, 163), "Reset", fill=TEXT_DARK, font=font_body)

    # Results Grid (3 items)
    items = [
        ("Dell XPS 15 Silver Laptop with Coding Club Sticker", "Laptops", "Lost", "Central Library 2nd Floor", "2026-09-28", RED, 20),
        ("Dell XPS 15 Silver Laptop", "Laptops", "Found", "Central Library Front Desk", "2026-09-28", GREEN, 345),
        ("Lenovo ThinkPad L14 Gen 3 Project Laptop", "Laptops", "Lost", "Academic Block C Hall", "2026-09-18", RED, 670)
    ]
    for title, cat, st, loc, dt, badge_col, x in items:
        draw.rounded_rectangle([x, 210, x + 310, 530], radius=10, fill=WHITE, outline=BORDER_GRAY)
        # Placeholder thumb
        draw.rectangle([x, 210, x + 310, 330], fill=(240, 245, 250))
        draw.text((x + 90, 260), "💻 [Hardware Asset]", fill=TEXT_MUTED, font=font_body)
        # Badges
        draw.rounded_rectangle([x + 15, 340, x + 90, 360], radius=4, fill=LIGHT_GRAY, outline=BORDER_GRAY)
        draw.text((x + 25, 344), cat, fill=TEXT_DARK, font=font_small)

        draw.rounded_rectangle([x + 100, 340, x + 160, 360], radius=4, fill=badge_col)
        draw.text((x + 115, 344), st, fill=WHITE, font=font_small)

        draw.text((x + 15, 370), title[:32] + "...", fill=TEXT_DARK, font=font_h2)
        draw.text((x + 15, 395), f"📍 {loc}", fill=TEXT_MUTED, font=font_small)
        draw.text((x + 15, 415), f"📅 Date: {dt}", fill=TEXT_MUTED, font=font_small)

        draw.rounded_rectangle([x + 15, 480, x + 150, 512], radius=6, fill=WHITE, outline=NAVY)
        draw.text((x + 55, 490), "Details", fill=NAVY, font=font_body)

        draw.rounded_rectangle([x + 160, 480, x + 295, 512], radius=6, fill=GOLD)
        draw.text((x + 195, 490), "AI Match", fill=DARK_NAVY, font=font_body)

    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_4.png"), quality=95)

# --------------------------------------------------------------------------------------
# 5. FIGURE 5.1.5: MATCH SUGGESTIONS PAGE
# --------------------------------------------------------------------------------------
def make_fig_5_1_5():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/ai/item/1/matches")
    draw_topbar_and_nav(draw, W, active_nav="AI Matcher")

    # Target Item Banner
    draw.rounded_rectangle([20, 125, W - 20, 215], radius=10, fill=DARK_NAVY, outline=GOLD)
    draw.text((35, 135), "TARGET QUERY ASSET (LOST ITEM #TKT-LOST-2026-001)", fill=GOLD, font=font_small)
    draw.text((35, 155), "Dell XPS 15 Silver Laptop with Sanskriti Coding Club Sticker", fill=WHITE, font=font_title)
    draw.text((35, 185), "📍 Central Library 2nd Floor Cubicle #14  |  Reporter: O. Pulla Reddy (2302320110)", fill=(200, 215, 235), font=font_body)

    # Candidate 1 Card
    draw.rounded_rectangle([20, 225, W - 20, 365], radius=10, fill=WHITE, outline=GOLD, width=2)
    draw.rounded_rectangle([35, 240, 180, 260], radius=4, fill=(235, 245, 255), outline=BLUE)
    draw.text((45, 244), "Candidate Match #1", fill=BLUE, font=font_small)
    draw.rounded_rectangle([190, 240, 310, 260], radius=4, fill=(235, 255, 245), outline=GREEN)
    draw.text((200, 244), "Status: Found / Held", fill=GREEN, font=font_small)

    draw.text((35, 270), "Dell XPS 15 Silver Laptop (Found at Central Library Desk)", fill=TEXT_DARK, font=font_title)
    draw.text((35, 298), "Description: Found Dell XPS 15 silver metallic laptop left on 2nd floor desk Central Library with charger.", fill=TEXT_MUTED, font=font_body)
    draw.text((35, 320), "Custody: Central Library Front Desk Locker 3B  |  Finder: Rajesh Kumar (Library Officer)", fill=TEXT_DARK, font=font_small)

    # Confidence Box
    draw.rounded_rectangle([720, 240, 960, 350], radius=8, fill=(255, 251, 235), outline=GOLD)
    draw.text((740, 250), "AI Composite Score", fill=NAVY, font=font_small)
    draw.text((740, 270), "84.5%", fill=GOLD, font=font_title)
    draw.text((740, 300), "• TF-IDF Text Cosine: 72.4%\n• Category Match: 100%\n• Color / HSV Match: 85.0%", fill=TEXT_DARK, font=font_small)

    draw.rounded_rectangle([35, 335, 200, 360], radius=4, fill=BLUE)
    draw.text((50, 342), "Inspect Comparison", fill=WHITE, font=font_small)

    draw.rounded_rectangle([210, 335, 380, 360], radius=4, fill=GREEN)
    draw.text((225, 342), "Initiate Ownership Claim", fill=WHITE, font=font_small)

    # Candidate 2 Card
    draw.rounded_rectangle([20, 380, W - 20, 520], radius=10, fill=WHITE, outline=BORDER_GRAY)
    draw.rounded_rectangle([35, 395, 180, 415], radius=4, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((45, 399), "Candidate Match #2", fill=TEXT_MUTED, font=font_small)

    draw.text((35, 425), "Lenovo ThinkPad Project Laptop (Academic Block C)", fill=TEXT_DARK, font=font_title)
    draw.text((35, 453), "Description: Black matte Lenovo ThinkPad with university barcoded sticker. Found near symposium.", fill=TEXT_MUTED, font=font_body)
    draw.text((35, 475), "Custody: Security Post Main Gate  |  Finder: Security Staff", fill=TEXT_DARK, font=font_small)

    draw.rounded_rectangle([720, 395, 960, 505], radius=8, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((740, 405), "AI Composite Score", fill=NAVY, font=font_small)
    draw.text((740, 425), "28.3%", fill=YELLOW, font=font_title)
    draw.text((740, 455), "• TF-IDF Text Cosine: 18.2%\n• Category Match: 100%\n• Color / HSV Match: 10.0%", fill=TEXT_MUTED, font=font_small)

    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_5.png"), quality=95)

# --------------------------------------------------------------------------------------
# 6. FIGURE 5.1.6: CLAIM FORM AND VERIFICATION SCREEN
# --------------------------------------------------------------------------------------
def make_fig_5_1_6():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/claims/submit/2")
    draw_topbar_and_nav(draw, W, active_nav="")

    card = [150, 130, 850, 540]
    draw.rounded_rectangle(card, radius=12, fill=WHITE, outline=BORDER_GRAY)
    draw.rounded_rectangle([150, 130, 850, 175], radius=12, fill=NAVY)
    draw.text((170, 142), "🛡️ Ownership Claim Submission & Verification Gate", fill=GOLD, font=font_h1)
    draw.text((170, 160), "Two-tier verification protocol &bull; Physical inspection required prior to handover", fill=WHITE, font=font_small)

    # Target info box
    draw.rounded_rectangle([180, 190, 820, 245], radius=8, fill=(245, 250, 255), outline=BLUE)
    draw.text((195, 198), "Claiming Asset: Dell XPS 15 Silver Laptop (Ticket #TKT-FND-2026-001)", fill=NAVY, font=font_h2)
    draw.text((195, 220), "Current Custody: Central Library Front Desk Locker 3B  |  Held by: Rajesh Kumar", fill=TEXT_MUTED, font=font_small)

    draw.text((180, 260), "Hardware Serial Number / Unique Identifier (Confidential) *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 280, 820, 310], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 288), "SN: DLXPS-99214A", fill=TEXT_DARK, font=font_body)

    draw.text((180, 320), "Ownership Evidence & Secret Identifier Description *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 340, 820, 410], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 348), "1. Sanskriti Coding Club oval sticker on top left of metallic display lid.", fill=TEXT_DARK, font=font_body)
    draw.text((195, 368), "2. Blue silicone keyboard dust protector with worn 'Enter' key.", fill=TEXT_DARK, font=font_body)
    draw.text((195, 388), "3. Purchase tax invoice uploaded under O. Pulla Reddy (Enrollment: 2302320110).", fill=TEXT_MUTED, font=font_small)

    draw.text((180, 420), "Claimant Contact Phone *", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([180, 440, 480, 470], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((195, 448), "+91 98765 43213", fill=TEXT_DARK, font=font_body)

    draw.text((500, 420), "Proof of Purchase / Student ID Document", fill=TEXT_DARK, font=font_h2)
    draw.rounded_rectangle([500, 440, 820, 470], radius=6, fill=LIGHT_GRAY, outline=BORDER_GRAY)
    draw.text((515, 448), "📎 invoice_dell_xps_reddy.pdf (Uploaded)", fill=BLUE, font=font_body)

    draw.rounded_rectangle([580, 485, 820, 520], radius=6, fill=GREEN)
    draw.text((610, 495), "Submit Verification Claim", fill=WHITE, font=font_h2)

    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_6.png"), quality=95)

# --------------------------------------------------------------------------------------
# 7. FIGURE 5.1.7: AUTHORITY DASHBOARD
# --------------------------------------------------------------------------------------
def make_fig_5_1_7():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/dashboard")
    draw_topbar_and_nav(draw, W, active_nav="Dashboard")

    # Admin Header Banner
    draw.rounded_rectangle([20, 125, W - 20, 185], radius=10, fill=DARK_NAVY, outline=BORDER_GRAY)
    draw.text((35, 135), "AUTHORITY OPERATIONAL DASHBOARD (EXECUTIVE VIEW)", fill=GOLD, font=font_small)
    draw.text((35, 155), "Campus Security & Asset Recovery Monitoring Console", fill=WHITE, font=font_title)
    draw.rounded_rectangle([W - 270, 140, W - 35, 170], radius=15, fill=RED)
    draw.text((W - 255, 148), "🛡️ Dr. Sakuldeep Singh (Director/Admin)", fill=WHITE, font=font_small)

    # 4 KPI Cards
    cards = [
        ("12", "Total Campus Assets", BLUE, 20),
        ("1", "Pending Claims to Verify", YELLOW, 265),
        ("2", "Verified Handover Certificates", GREEN, 510),
        ("8", "Registered Campus Users", NAVY, 755)
    ]
    for val, lbl, col, x in cards:
        draw.rounded_rectangle([x, 195, x + 225, 265], radius=10, fill=WHITE, outline=BORDER_GRAY)
        draw.rectangle([x, 195, x + 5, 265], fill=col)
        draw.text((x + 20, 205), val, fill=col, font=font_title)
        draw.text((x + 20, 235), lbl, fill=TEXT_DARK, font=font_small)

    # Verification Queue
    draw.rounded_rectangle([20, 275, 620, 545], radius=10, fill=WHITE, outline=BORDER_GRAY)
    draw.text((35, 285), "Claims Verification Queue", fill=NAVY, font=font_h2)

    # Row 1 (Pending)
    draw.rounded_rectangle([35, 310, 605, 415], radius=6, fill=LIGHT_GRAY, outline=YELLOW)
    draw.text((45, 320), "Dell XPS 15 Silver Laptop (#TKT-FND-2026-001)", fill=NAVY, font=font_h2)
    draw.text((45, 342), "Claimant: O. Pulla Reddy (student.reddy@sanskriti.edu.in)", fill=TEXT_DARK, font=font_small)
    draw.text((45, 360), "Proof: Serial match verified (DLXPS-99214A) & coding sticker", fill=TEXT_MUTED, font=font_small)

    draw.rounded_rectangle([420, 375, 500, 405], radius=4, fill=GREEN)
    draw.text((435, 384), "Approve", fill=WHITE, font=font_small)
    draw.rounded_rectangle([515, 375, 595, 405], radius=4, fill=WHITE, outline=RED)
    draw.text((535, 384), "Reject", fill=RED, font=font_small)

    # Row 2 (Verified)
    draw.rounded_rectangle([35, 425, 605, 530], radius=6, fill=LIGHT_GRAY, outline=GREEN)
    draw.text((45, 435), "Tektronix 100MHz Digital Oscilloscope (#TKT-FND-2026-003)", fill=NAVY, font=font_h2)
    draw.text((45, 457), "Claimant: Prof. Amit Sharma (HOD CSE)", fill=TEXT_DARK, font=font_small)
    draw.text((45, 475), "Status: Verified & Handover Certificate Generated", fill=GREEN, font=font_small)
    draw.rounded_rectangle([450, 490, 595, 520], radius=4, fill=NAVY)
    draw.text((465, 498), "View Certificate", fill=GOLD, font=font_small)

    # Activity Stream
    draw.rounded_rectangle([640, 275, W - 20, 545], radius=10, fill=WHITE, outline=BORDER_GRAY)
    draw.text((655, 285), "Recent Security Audit Events", fill=NAVY, font=font_h2)
    events = [
        ("CLAIM_APPROVED", "Oscilloscope handed to Prof. Amit", "10:14 AM"),
        ("CLAIM_SUBMITTED", "Claim by O. Pulla Reddy on Dell XPS", "09:30 AM"),
        ("MATCH_DETECTED", "AI Engine score 84.5% on Dell XPS", "09:15 AM"),
        ("ITEM_REPORTED", "Rajesh Kumar reported found laptop", "08:45 AM"),
        ("ITEM_REPORTED", "O. Pulla Reddy reported lost laptop", "08:00 AM")
    ]
    ey = 315
    for act, desc, tm in events:
        draw.rounded_rectangle([655, ey, 770, ey + 20], radius=4, fill=DARK_NAVY)
        draw.text((662, ey + 4), act, fill=GOLD, font=font_small)
        draw.text((780, ey + 4), tm, fill=TEXT_MUTED, font=font_small)
        draw.text((655, ey + 23), desc, fill=TEXT_DARK, font=font_small)
        draw.line([655, ey + 40, W - 35, ey + 40], fill=BORDER_GRAY, width=1)
        ey += 44

    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_7.png"), quality=95)

# --------------------------------------------------------------------------------------
# 8. FIGURE 5.1.8: NOTIFICATIONS AND AUDIT LOG
# --------------------------------------------------------------------------------------
def make_fig_5_1_8():
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    draw_browser_frame(draw, W, H, "http://127.0.0.1:5000/audit-logs")
    draw_topbar_and_nav(draw, W, active_nav="")

    # Audit log container
    draw.rounded_rectangle([20, 125, W - 20, 545], radius=10, fill=WHITE, outline=BORDER_GRAY)
    draw.text((35, 135), "📜 Sanskriti University System Audit Log & Security Trail", fill=NAVY, font=font_title)
    draw.text((35, 165), "Immutable tamper-evident record of all system state transitions & actor actions (Figure 5.1.8)", fill=TEXT_MUTED, font=font_small)

    # Table header
    draw.rectangle([35, 190, W - 35, 220], fill=(235, 240, 248))
    headers = [("ID", 45), ("Timestamp", 90), ("Actor / Role", 240), ("Action", 450), ("Entity", 590), ("Details & Verification Notes", 670)]
    for h, x in headers:
        draw.text((x, 198), h, fill=NAVY, font=font_h2)

    rows = [
        ("#105", "2026-10-06 11:30:00", "Dr. Sakuldeep Singh (Admin)", "CLAIM_APPROVED", "Claim #1", "Approved claim for Tektronix Oscilloscope & generated handover certificate", GREEN),
        ("#104", "2026-10-06 10:00:00", "Prof. Amit Sharma (HOD)", "CLAIM_SUBMITTED", "Claim #1", "Submitted verified departmental claim with property register #AST-VLSI-402", BLUE),
        ("#103", "2026-10-05 14:30:00", "AI Matching Engine", "MATCH_DETECTED", "Match #1", "High-confidence composite match score (84.5%) discovered between #1 and #2", GOLD),
        ("#102", "2026-10-01 14:00:00", "Rajesh Kumar (Staff)", "ITEM_REPORTED", "Item #2", "Reported found Dell XPS 15 laptop at Central Library Reading Room Counter", TEXT_DARK),
        ("#101", "2026-09-28 16:30:00", "O. Pulla Reddy (Student)", "ITEM_REPORTED", "Item #1", "Reported lost Dell XPS 15 laptop with Sanskriti Coding Club Sticker", RED),
        ("#100", "2026-09-28 09:00:00", "System Daemon", "SYSTEM_INIT", "Database", "Initialised relational schema and pre-seeded Sanskriti academic inventory", TEXT_MUTED)
    ]
    ry = 225
    for id_val, tm, actor, act, ent, det, col in rows:
        draw.rectangle([35, ry, W - 35, ry + 48], fill=WHITE if ry % 2 == 0 else (250, 252, 255))
        draw.text((45, ry + 12), id_val, fill=TEXT_MUTED, font=font_mono)
        draw.text((90, ry + 12), tm, fill=TEXT_DARK, font=font_small)
        draw.text((240, ry + 12), actor, fill=NAVY, font=font_body)

        draw.rounded_rectangle([445, ry + 8, 570, ry + 32], radius=4, fill=DARK_NAVY)
        draw.text((455, ry + 12), act, fill=col, font=font_small)

        draw.text((590, ry + 12), ent, fill=TEXT_DARK, font=font_small)
        draw.text((670, ry + 12), det[:45] + "...", fill=TEXT_MUTED, font=font_small)

        draw.line([35, ry + 48, W - 35, ry + 48], fill=BORDER_GRAY, width=1)
        ry += 50

    img.save(os.path.join(OUTPUT_DIR, "fig_5_1_8.png"), quality=95)

if __name__ == "__main__":
    make_fig_5_1_1()
    make_fig_5_1_2()
    make_fig_5_1_3()
    make_fig_5_1_4()
    make_fig_5_1_5()
    make_fig_5_1_6()
    make_fig_5_1_7()
    make_fig_5_1_8()
    print("All 8 figures generated successfully in:", OUTPUT_DIR)
