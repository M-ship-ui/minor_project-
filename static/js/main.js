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

    // 7. Auto-dismiss flash alerts after 6 seconds
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-auto-dismiss');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 6000);
});
