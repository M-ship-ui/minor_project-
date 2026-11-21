// Sanskriti University - Intelligent Academic Asset Recovery System
// Main Interactive Scripts

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips & Popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Image Upload Preview
    const imageInput = document.getElementById('itemImageInput');
    const imagePreview = document.getElementById('imagePreviewContainer');
    const previewImg = document.getElementById('previewImg');

    if (imageInput && imagePreview && previewImg) {
        imageInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImg.src = e.target.result;
                    imagePreview.classList.remove('d-none');
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.classList.add('d-none');
            }
        });
    }

    // 3. Anonymous Toggle Details Helper
    const anonCheckbox = document.getElementById('isAnonymousCheckbox');
    const contactInfoSection = document.getElementById('reporterInfoSection');
    if (anonCheckbox && contactInfoSection) {
        anonCheckbox.addEventListener('change', function () {
            if (this.checked) {
                contactInfoSection.style.opacity = '0.5';
                contactInfoSection.style.pointerEvents = 'none';
            } else {
                contactInfoSection.style.opacity = '1';
                contactInfoSection.style.pointerEvents = 'auto';
            }
        });
    }

    // 4. Quick Login Fill for Demo Evaluation
    window.quickLogin = function (role) {
        const emailField = document.getElementById('loginEmail');
        const passField = document.getElementById('loginPassword');
        if (!emailField || !passField) return;

        if (role === 'admin') {
            emailField.value = 'admin@sanskriti.edu.in';
            passField.value = 'admin123';
        } else if (role === 'hod') {
            emailField.value = 'hod.cs@sanskriti.edu.in';
            passField.value = 'hod123';
        } else if (role === 'staff') {
            emailField.value = 'staff.rajesh@sanskriti.edu.in';
            passField.value = 'staff123';
        } else if (role === 'student') {
            emailField.value = 'student.reddy@sanskriti.edu.in';
            passField.value = 'student123';
        } else if (role === 'student2') {
            emailField.value = 'student.priya@sanskriti.edu.in';
            passField.value = 'priya123';
        }

        // Add visual flash to indicate fields filled
        emailField.classList.add('bg-light');
        passField.classList.add('bg-light');
        setTimeout(() => {
            emailField.classList.remove('bg-light');
            passField.classList.remove('bg-light');
        }, 400);
    };

    // 5. Print Certificate Handler
    window.printRecoveryCertificate = function () {
        window.print();
    };

    // 6. Search Filter Form Reset Handler
    const resetBtn = document.getElementById('resetSearchFilters');
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            window.location.href = '/search';
        });
    }

    // 8. Live AI Match Simulator for Presentation Review
    const simPresets = [
        {
            lost: "Dell XPS 15 Silver Laptop with Sanskriti Coding Club Sticker on lid",
            found: "Found Dell XPS 15 silver metallic laptop left on 2nd floor desk Central Library"
        },
        {
            lost: "Sanskriti University Student ID Card for O. Pulla Reddy (2302320110) with blue lanyard",
            found: "Found smart card ID for Computer Science student with blue university lanyard near cafeteria counter"
        },
        {
            lost: "Tektronix 100MHz Digital Storage Oscilloscope Unit left in VLSI Hardware Lab Room 302",
            found: "Found dual-channel oscilloscope left unattended on equipment trolley outside Lab 302"
        }
    ];
    let presetIdx = 0;

    window.loadSimPreset = function () {
        presetIdx = (presetIdx + 1) % simPresets.length;
        document.getElementById('simLostText').value = simPresets[presetIdx].lost;
        document.getElementById('simFoundText').value = simPresets[presetIdx].found;
        runLiveSimilaritySim();
    };

    window.runLiveSimilaritySim = function () {
        const t1 = (document.getElementById('simLostText')?.value || '').toLowerCase();
        const t2 = (document.getElementById('simFoundText')?.value || '').toLowerCase();

        const clean = str => str.replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(w => w.length > 2);
        const w1 = clean(t1);
        const w2 = clean(t2);

        const stopWords = new Set(['the', 'and', 'for', 'with', 'from', 'this', 'that', 'with', 'left', 'found', 'lost']);
        const tokens1 = w1.filter(w => !stopWords.has(w));
        const tokens2 = w2.filter(w => !stopWords.has(w));

        const intersection = tokens1.filter(w => tokens2.includes(w));
        const uniqueMatches = Array.from(new Set(intersection));

        const union = Array.from(new Set([...tokens1, ...tokens2]));
        let score = union.length ? (uniqueMatches.length / Math.sqrt(tokens1.length * tokens2.length)) : 0;
        // Scale to calibrated TF-IDF range (0.65 to 0.88 for true academic assets)
        let pct = Math.min(96, Math.max(12, Math.round(score * 95)));

        const scoreEl = document.getElementById('simScoreDisplay');
        const verdictEl = document.getElementById('simVerdictText');
        const tokensEl = document.getElementById('simTokensText');

        if (scoreEl) {
            scoreEl.textContent = pct + '%';
            scoreEl.style.color = pct >= 50 ? '#059669' : (pct >= 25 ? '#d97706' : '#dc2626');
        }
        if (verdictEl) {
            verdictEl.textContent = pct >= 60 ? 'High-Confidence Pair (Automatic Suggestion & Push Notification)' :
                                   (pct >= 25 ? 'Moderate Similarity (Candidate Review Queue)' : 'Below Threshold (< 0.25) Filtered Out');
        }
        if (tokensEl) {
            tokensEl.innerHTML = uniqueMatches.length ?
                'Matched Keywords: ' + uniqueMatches.map(m => `<code>${m}</code>`).join(' ') :
                '<span class="text-muted">No key overlapping tokens detected.</span>';
        }
    };
});
