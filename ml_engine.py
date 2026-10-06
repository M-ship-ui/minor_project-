import os
import re
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image

# Attempt to import OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    OPENCV_AVAILABLE = False


def clean_text(text):
    """Normalize text by lowercasing and trimming non-essential characters."""
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def build_item_text_profile(item):
    """
    Construct a dense, rich descriptive profile for an item dictionary or row
    to feed into the TF-IDF vectorizer.
    """
    parts = [
        item.get('title', ''),
        item.get('category', ''),
        item.get('department', ''),
        item.get('building_zone', ''),
        item.get('location', ''),
        item.get('description', ''),
        item.get('identifying_marks', ''),
        item.get('serial_number_hint', ''),
        item.get('storage_location', '')
    ]
    # Weight title and category by repeating them
    title = item.get('title', '')
    category = item.get('category', '')
    weighted_text = f"{title} {title} {category} {category} " + " ".join([p for p in parts if p])
    return clean_text(weighted_text)


def compute_text_similarity(item_a, item_b):
    """
    Compute semantic similarity between two items using TF-IDF and Cosine Similarity.
    """
    text_a = build_item_text_profile(item_a)
    text_b = build_item_text_profile(item_b)

    if not text_a or not text_b:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(np.clip(sim, 0.0, 1.0))
    except Exception as e:
        # Fallback to Jaccard similarity if vectorizer fails
        words_a = set(text_a.split())
        words_b = set(text_b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return float(intersection / union) if union > 0 else 0.0


def compute_category_score(cat_a, cat_b):
    """
    Score categorical alignment between two items.
    """
    if not cat_a or not cat_b:
        return 0.0
    cat_a = cat_a.strip().lower()
    cat_b = cat_b.strip().lower()

    if cat_a == cat_b:
        return 1.0

    # Related category semantic cross-mappings
    related_groups = [
        {'laptops', 'electronic devices', 'project equipment'},
        {'projectors', 'electronic devices', 'laboratory equipment'},
        {'books', 'other university assets'},
        {'id cards', 'other university assets'}
    ]

    for group in related_groups:
        if cat_a in group and cat_b in group:
            return 0.45

    return 0.0


def compute_location_score(item_a, item_b):
    """
    Evaluate spatial and departmental proximity.
    """
    score = 0.0
    zone_a = (item_a.get('building_zone') or '').strip().lower()
    zone_b = (item_b.get('building_zone') or '').strip().lower()
    loc_a = clean_text(item_a.get('location') or '')
    loc_b = clean_text(item_b.get('location') or '')
    dept_a = (item_a.get('department') or '').strip().lower()
    dept_b = (item_b.get('department') or '').strip().lower()

    # Exact building zone match
    if zone_a and zone_b and zone_a == zone_b:
        score += 0.55
    elif zone_a and zone_b and (zone_a in zone_b or zone_b in zone_a):
        score += 0.35

    # Specific room / text overlap
    if loc_a and loc_b:
        words_a = set(loc_a.split())
        words_b = set(loc_b.split())
        overlap = len(words_a & words_b)
        if overlap > 0:
            score += min(0.30, overlap * 0.15)

    # Department alignment
    if dept_a and dept_b and dept_a == dept_b:
        score += 0.15

    return min(1.0, score)


def compute_date_proximity_score(date_str_a, date_str_b):
    """
    Evaluate temporal plausibility. Typically, found date occurs on or shortly after lost date.
    """
    if not date_str_a or not date_str_b:
        return 0.5

    try:
        dt_a = datetime.strptime(date_str_a.strip()[:10], '%Y-%m-%d')
        dt_b = datetime.strptime(date_str_b.strip()[:10], '%Y-%m-%d')
        diff_days = abs((dt_b - dt_a).days)

        if diff_days == 0:
            return 1.0
        elif diff_days <= 2:
            return 0.90
        elif diff_days <= 5:
            return 0.75
        elif diff_days <= 10:
            return 0.60
        elif diff_days <= 30:
            return 0.35
        else:
            return 0.15
    except Exception:
        return 0.5


def extract_image_color_histogram(image_path):
    """
    Extract normalized 3D color histogram from an image using OpenCV or Pillow.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    if OPENCV_AVAILABLE:
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            img = cv2.resize(img, (128, 128))
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # 8 bins for Hue, 8 for Saturation, 8 for Value
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
            cv2.normalize(hist, hist)
            return hist
        except Exception:
            pass

    # Pillow fallback
    try:
        with Image.open(image_path) as pil_img:
            pil_img = pil_img.convert('RGB').resize((64, 64))
            hist = pil_img.histogram()
            # Normalize
            total = sum(hist) or 1
            return np.array(hist, dtype=np.float32) / total
    except Exception:
        return None


def compute_visual_similarity(img_path_a, img_path_b):
    """
    Compare visual appearance of two item images.
    Returns score between 0.0 and 1.0, or None if images unavailable.
    """
    if not img_path_a or not img_path_b:
        return None

    hist_a = extract_image_color_histogram(img_path_a)
    hist_b = extract_image_color_histogram(img_path_b)

    if hist_a is None or hist_b is None:
        return None

    if OPENCV_AVAILABLE and isinstance(hist_a, np.ndarray) and hist_a.shape == (8, 8, 8):
        try:
            # Correlation comparison (-1 to 1) -> scaled to 0 to 1
            corr = cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)
            return float(np.clip((corr + 1.0) / 2.0, 0.0, 1.0))
        except Exception:
            pass

    # Flattened array comparison
    try:
        a_flat = hist_a.flatten().reshape(1, -1)
        b_flat = hist_b.flatten().reshape(1, -1)
        sim = cosine_similarity(a_flat, b_flat)[0][0]
        return float(np.clip(sim, 0.0, 1.0))
    except Exception:
        return 0.5


def calculate_match_score(lost_item, found_item, base_upload_folder=None):
    """
    Compute comprehensive multi-factor similarity between a lost item and a found item.
    Returns a dict with all component scores and the composite percentage.
    """
    text_score = compute_text_similarity(lost_item, found_item)
    cat_score = compute_category_score(lost_item.get('category'), found_item.get('category'))
    loc_score = compute_location_score(lost_item, found_item)
    date_score = compute_date_proximity_score(lost_item.get('date_event'), found_item.get('date_event'))

    # Visual scoring
    img_a_path = None
    img_b_path = None
    if base_upload_folder:
        if lost_item.get('image_path'):
            img_a_path = os.path.join(base_upload_folder, lost_item['image_path'])
        if found_item.get('image_path'):
            img_b_path = os.path.join(base_upload_folder, found_item['image_path'])

    vis_score = compute_visual_similarity(img_a_path, img_b_path)

    # Weighted calculation
    if vis_score is not None:
        # Image present on both items
        composite = (
            text_score * 0.45 +
            cat_score * 0.25 +
            loc_score * 0.15 +
            date_score * 0.05 +
            vis_score * 0.10
        )
    else:
        # No image on one or both
        composite = (
            text_score * 0.50 +
            cat_score * 0.25 +
            loc_score * 0.18 +
            date_score * 0.07
        )
        vis_score = 0.0

    composite_pct = round(min(100.0, max(0.0, composite * 100.0)), 1)

    if composite_pct >= 75.0:
        confidence = "High"
        badge_color = "success"
    elif composite_pct >= 50.0:
        confidence = "Moderate"
        badge_color = "warning"
    else:
        confidence = "Low"
        badge_color = "secondary"

    return {
        'lost_item_id': lost_item.get('id'),
        'found_item_id': found_item.get('id'),
        'text_similarity_score': round(text_score, 3),
        'category_score': round(cat_score, 3),
        'location_score': round(loc_score, 3),
        'date_score': round(date_score, 3),
        'visual_score': round(vis_score, 3),
        'composite_score': composite_pct,
        'confidence_tier': confidence,
        'badge_color': badge_color
    }


def detect_spam_or_duplicate(new_item, recent_items):
    """
    Detect spam text or duplicate submissions.
    Returns (is_flagged: bool, reason: str)
    """
    title = (new_item.get('title') or '').strip()
    description = (new_item.get('description') or '').strip()

    # Rule 1: Very short gibberish or empty
    if len(title) < 3 or len(description) < 6:
        return True, "Title or description is too brief to be authentic."

    # Rule 2: Repeated single character spam (e.g., 'aaaaaaa', 'xxxxx')
    if re.search(r'(.)\1{5,}', title) or re.search(r'(.)\1{7,}', description):
        return True, "Repetitive character pattern detected (anti-spam flag)."

    # Rule 3: Cosine similarity against recent items submitted within the last 7 days
    new_profile = build_item_text_profile(new_item)
    for existing in recent_items:
        # Check against items submitted by the same user or identical content
        if existing.get('id') == new_item.get('id'):
            continue
        existing_profile = build_item_text_profile(existing)
        if not existing_profile:
            continue
        try:
            vec = TfidfVectorizer(stop_words='english')
            mat = vec.fit_transform([new_profile, existing_profile])
            sim = cosine_similarity(mat[0:1], mat[1:2])[0][0]
            if sim > 0.90 and existing.get('type') == new_item.get('type'):
                return True, f"High similarity (>90%) with existing ticket #{existing.get('ticket_number')}. Possible duplicate submission."
        except Exception:
            pass

    return False, "Passed"
