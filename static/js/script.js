/**
 * Sujit.dev - Interactive Portfolio Client Logic
 * Handles Mobile Menu, FAQ Accordion, AJAX Contact Form, and AI Architecture Advisor
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. Mobile Menu Toggle
    // -------------------------------------------------------------
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            const isHidden = mobileMenu.classList.contains('hidden');
            if (isHidden) {
                mobileMenu.classList.remove('hidden');
                document.body.style.overflow = 'hidden';
            } else {
                mobileMenu.classList.add('hidden');
                document.body.style.overflow = '';
            }
        });

        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.add('hidden');
                document.body.style.overflow = '';
            });
        });
    }

    // -------------------------------------------------------------
    // 2. Navbar Background Blur on Scroll
    // -------------------------------------------------------------
    const mainNav = document.getElementById('main-nav');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 30) {
            mainNav.classList.add('bg-ink-950/90', 'backdrop-blur-md', 'border-b', 'border-ink-600/60', 'shadow-lg');
            mainNav.classList.remove('bg-transparent');
        } else {
            mainNav.classList.remove('bg-ink-950/90', 'backdrop-blur-md', 'border-b', 'border-ink-600/60', 'shadow-lg');
            mainNav.classList.add('bg-transparent');
        }
    });

    // -------------------------------------------------------------
    // 3. Interactive FAQ Accordion
    // -------------------------------------------------------------
    const faqButtons = document.querySelectorAll('.faq-toggle');

    faqButtons.forEach((btn, index) => {
        btn.addEventListener('click', () => {
            const container = btn.closest('.faq-item');
            const answer = container.querySelector('.faq-answer');
            const icon = container.querySelector('.faq-icon');
            const isOpen = !answer.classList.contains('hidden');

            // Close all other FAQs
            document.querySelectorAll('.faq-item').forEach(other => {
                const otherAnswer = other.querySelector('.faq-answer');
                const otherIcon = other.querySelector('.faq-icon');
                const otherBtn = other.querySelector('.faq-toggle');
                
                otherAnswer.classList.add('hidden');
                otherBtn.setAttribute('aria-expanded', 'false');
                other.classList.remove('border-accent-500/40', 'bg-ink-800/80');
                other.classList.add('border-ink-600/50', 'bg-ink-800/40');
                if (otherIcon) {
                    otherIcon.classList.remove('rotate-180', 'text-accent-400');
                    otherIcon.classList.add('text-gray-400');
                }
            });

            // If it was closed, open it
            if (!isOpen) {
                answer.classList.remove('hidden');
                btn.setAttribute('aria-expanded', 'true');
                container.classList.remove('border-ink-600/50', 'bg-ink-800/40');
                container.classList.add('border-accent-500/40', 'bg-ink-800/80');
                if (icon) {
                    icon.classList.add('rotate-180', 'text-accent-400');
                    icon.classList.remove('text-gray-400');
                }
            }
        });
    });

    // -------------------------------------------------------------
    // 4. AJAX Contact Form Submission
    // -------------------------------------------------------------
    const contactForm = document.getElementById('contact-form');
    const formSuccess = document.getElementById('form-success');
    const formError = document.getElementById('form-error');
    const submitBtn = document.getElementById('contact-submit-btn');
    const submitText = document.getElementById('submit-btn-text');
    const submitSpinner = document.getElementById('submit-btn-spinner');
    const resetFormBtn = document.getElementById('reset-form-btn');

    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Clear previous errors
            clearFormErrors();
            formError.classList.add('hidden');

            // Collect form fields
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const company = document.getElementById('company').value.trim();
            const projectType = document.getElementById('projectType').value;
            const existingTechnology = document.getElementById('existingTechnology').value;
            const projectDescription = document.getElementById('projectDescription').value.trim();

            // Client-side Validation
            let hasErrors = false;

            if (!name) {
                showFieldError('name', 'Please enter your name.');
                hasErrors = true;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!email) {
                showFieldError('email', 'Please enter your email.');
                hasErrors = true;
            } else if (!emailRegex.test(email)) {
                showFieldError('email', 'Please enter a valid email address.');
                hasErrors = true;
            }

            if (!projectType) {
                showFieldError('projectType', 'Please select a project type.');
                hasErrors = true;
            }

            if (!existingTechnology) {
                showFieldError('existingTechnology', 'Please select your technology.');
                hasErrors = true;
            }

            if (!projectDescription) {
                showFieldError('projectDescription', 'Please describe your project.');
                hasErrors = true;
            } else if (projectDescription.length < 20) {
                showFieldError('projectDescription', 'Please provide at least a brief description (20+ characters).');
                hasErrors = true;
            }

            if (hasErrors) return;

            // Submit via API
            try {
                setLoadingState(true);

                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: name,
                        email: email,
                        company: company || null,
                        project_type: projectType,
                        existing_technology: existingTechnology,
                        project_description: projectDescription
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Unable to submit your inquiry. Please try again.');
                }

                // Show success state
                contactForm.classList.add('hidden');
                formSuccess.classList.remove('hidden');
                contactForm.reset();

            } catch (err) {
                console.error('Contact Form Submission Error:', err);
                formError.textContent = err.message || 'An unexpected error occurred. Please try again later.';
                formError.classList.remove('hidden');
            } finally {
                setLoadingState(false);
            }
        });
    }

    if (resetFormBtn) {
        resetFormBtn.addEventListener('click', () => {
            formSuccess.classList.add('hidden');
            contactForm.classList.remove('hidden');
            clearFormErrors();
        });
    }

    function showFieldError(fieldId, errorMsg) {
        const input = document.getElementById(fieldId);
        const errorEl = document.getElementById(`${fieldId}-error`);
        if (input) {
            input.classList.add('border-red-500/80', 'focus:ring-red-500/30');
            input.classList.remove('border-ink-500/50');
        }
        if (errorEl) {
            errorEl.textContent = errorMsg;
            errorEl.classList.remove('hidden');
        }
    }

    function clearFormErrors() {
        ['name', 'email', 'projectType', 'existingTechnology', 'projectDescription'].forEach(id => {
            const input = document.getElementById(id);
            const errorEl = document.getElementById(`${id}-error`);
            if (input) {
                input.classList.remove('border-red-500/80', 'focus:ring-red-500/30');
                input.classList.add('border-ink-500/50');
            }
            if (errorEl) {
                errorEl.textContent = '';
                errorEl.classList.add('hidden');
            }
        });
    }

    function setLoadingState(loading) {
        if (!submitBtn) return;
        submitBtn.disabled = loading;
        if (loading) {
            submitText.textContent = 'Sending Project Request...';
            submitSpinner.classList.remove('hidden');
        } else {
            submitText.textContent = 'Send Project Request';
            submitSpinner.classList.add('hidden');
        }
    }

    // -------------------------------------------------------------
    // 5. Interactive AI Architecture Advisor Demo
    // -------------------------------------------------------------
    const advisorForm = document.getElementById('advisor-form');
    const advisorResult = document.getElementById('advisor-result');
    const advisorLoading = document.getElementById('advisor-loading');

    if (advisorForm) {
        advisorForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const existingTech = document.getElementById('adv-tech').value;
            const useCase = document.getElementById('adv-use-case').value;
            const database = document.getElementById('adv-database').value;

            try {
                advisorLoading.classList.remove('hidden');
                advisorResult.classList.add('hidden');

                const response = await fetch('/api/advisor', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        existing_tech: existingTech,
                        use_case: useCase,
                        database: database,
                        data_privacy_level: "Enterprise / Private"
                    })
                });

                if (!response.ok) throw new Error('Failed to generate recommendation.');

                const data = await response.json();

                // Populate UI
                document.getElementById('res-arch-title').textContent = data.recommended_architecture;
                document.getElementById('res-score').textContent = `${data.feasibility_score}%`;
                document.getElementById('res-score-bar').style.width = `${data.feasibility_score}%`;
                document.getElementById('res-timeline').textContent = data.estimated_timeline;
                document.getElementById('res-protip').textContent = data.pro_tip;

                const compList = document.getElementById('res-components');
                compList.innerHTML = '';
                data.key_components.forEach(comp => {
                    const li = document.createElement('li');
                    li.className = 'flex items-start gap-2 text-sm text-gray-300';
                    li.innerHTML = `<span class="h-1.5 w-1.5 mt-2 rounded-full bg-accent-400 shrink-0"></span><span>${comp}</span>`;
                    compList.appendChild(li);
                });

                const stepList = document.getElementById('res-steps');
                stepList.innerHTML = '';
                data.implementation_steps.forEach(step => {
                    const li = document.createElement('li');
                    li.className = 'text-xs font-mono text-gray-400 bg-ink-700/40 p-2.5 rounded-lg border border-ink-600/40';
                    li.textContent = step;
                    stepList.appendChild(li);
                });

                advisorLoading.classList.add('hidden');
                advisorResult.classList.remove('hidden');

            } catch (err) {
                console.error(err);
                advisorLoading.classList.add('hidden');
                alert('Could not generate recommendation. Please try again.');
            }
        });
    }

    // Initialize Lucide icons if available
    if (window.lucide) {
        window.lucide.createIcons();
    }
});
