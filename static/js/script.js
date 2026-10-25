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

    // -------------------------------------------------------------
    // 6. Llama Brain Interactive Chat Widget
    // -------------------------------------------------------------
    initLlamaChat();

    function initLlamaChat() {
        const triggerBtn = document.getElementById('llama-chat-trigger');
        const chatWindow = document.getElementById('llama-chat-window');
        const closeBtn = document.getElementById('llama-chat-close');
        const clearBtn = document.getElementById('llama-chat-clear');
        const chatForm = document.getElementById('llama-chat-form');
        const chatInput = document.getElementById('llama-chat-input');
        const sendBtn = document.getElementById('llama-chat-send');
        const messagesContainer = document.getElementById('llama-chat-messages');
        const statusText = document.getElementById('llama-status-text');
        const modelBadge = document.getElementById('llama-model-badge');
        const suggestionBtns = document.querySelectorAll('.llama-suggest-btn');

        if (!triggerBtn || !chatWindow) return;

        let conversationHistory = [];
        let isGenerating = false;
        let activeModel = 'my-brain';

        // Load persisted conversation or show initial greeting
        const savedChat = sessionStorage.getItem('llama_chat_history');
        if (savedChat) {
            try {
                conversationHistory = JSON.parse(savedChat);
                renderAllMessages();
            } catch (e) {
                conversationHistory = [];
                renderWelcomeMessage();
            }
        } else {
            renderWelcomeMessage();
        }

        // Fetch engine status
        checkEngineStatus();

        // Toggle Chat Window
        triggerBtn.addEventListener('click', () => {
            const isHidden = chatWindow.classList.contains('hidden');
            if (isHidden) {
                chatWindow.classList.remove('hidden');
                chatWindow.classList.add('flex');
                setTimeout(() => chatInput && chatInput.focus(), 100);
            } else {
                chatWindow.classList.add('hidden');
                chatWindow.classList.remove('flex');
            }
        });

        closeBtn.addEventListener('click', () => {
            chatWindow.classList.add('hidden');
            chatWindow.classList.remove('flex');
        });

        clearBtn.addEventListener('click', () => {
            if (isGenerating) return;
            conversationHistory = [];
            sessionStorage.removeItem('llama_chat_history');
            renderWelcomeMessage();
        });

        // Textarea auto-resize & input events
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
            sendBtn.disabled = !chatInput.value.trim() || isGenerating;
        });

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.disabled) {
                    chatForm.dispatchEvent(new Event('submit'));
                }
            }
        });

        // Quick Suggestions
        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                if (isGenerating) return;
                const prompt = btn.textContent.replace(/^[^a-zA-Z0-9]+/, '').trim();
                chatInput.value = prompt;
                chatInput.style.height = 'auto';
                sendBtn.disabled = false;
                chatForm.dispatchEvent(new Event('submit'));
            });
        });

        // Submit message
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (!text || isGenerating) return;

            // Append User Message
            const userMsg = { role: 'user', content: text };
            conversationHistory.push(userMsg);
            saveHistory();

            appendMessageUI('user', text);
            chatInput.value = '';
            chatInput.style.height = 'auto';
            sendBtn.disabled = true;

            // Prepare Assistant Placeholder Bubble
            const assistantBubble = appendMessageUI('assistant', '', true);
            const contentDiv = assistantBubble.querySelector('.chat-content');

            isGenerating = true;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: conversationHistory,
                        model: activeModel,
                        stream: true
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }

                // Stream response handling
                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let fullReply = '';
                let isFirstChunk = true;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const rawJson = line.substring(6).trim();
                            if (!rawJson) continue;
                            try {
                                const parsed = JSON.parse(rawJson);
                                if (parsed.content) {
                                    if (isFirstChunk) {
                                        // Remove typing indicator on first word
                                        contentDiv.innerHTML = '';
                                        isFirstChunk = false;
                                    }
                                    fullReply += parsed.content;
                                    contentDiv.innerHTML = formatMarkdown(fullReply);
                                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                                }
                            } catch (err) {
                                // non-json line or partial
                            }
                        }
                    }
                }

                if (!fullReply) {
                    fullReply = 'I apologize, but no response was generated. Please verify that Ollama is running locally.';
                    contentDiv.innerHTML = formatMarkdown(fullReply);
                }

                conversationHistory.push({ role: 'assistant', content: fullReply });
                saveHistory();

            } catch (err) {
                console.error('Chat error:', err);
                contentDiv.innerHTML = `
                    <div class="text-red-400 text-xs">
                        <p class="font-bold">⚠️ Connection Issue</p>
                        <p class="mt-1">Unable to communicate with local Llama Brain. Please verify that Ollama is running (<code>ollama serve</code>) with model <code>${activeModel}</code>.</p>
                    </div>
                `;
            } finally {
                isGenerating = false;
                sendBtn.disabled = !chatInput.value.trim();
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                if (window.lucide) window.lucide.createIcons();
            }
        });

        // ----------------- Helpers -----------------
        async function checkEngineStatus() {
            try {
                const res = await fetch('/api/chat/status');
                if (res.ok) {
                    const data = await res.json();
                    if (data.online) {
                        activeModel = data.active_model || 'my-brain';
                        if (modelBadge) modelBadge.textContent = activeModel;
                        if (statusText) statusText.textContent = data.status_label || (data.hardware ? data.hardware + ' Online' : 'AI Online');
                    } else {
                        if (statusText) statusText.textContent = data.status_label || 'Offline';
                    }
                }
            } catch (e) {
                if (statusText) statusText.textContent = 'Connecting...';
            }
        }

        function saveHistory() {
            sessionStorage.setItem('llama_chat_history', JSON.stringify(conversationHistory));
        }

        function renderWelcomeMessage() {
            messagesContainer.innerHTML = '';
            const welcomeHtml = `
                <div class="chat-bubble-assistant p-4 text-sm">
                    <div class="flex items-center gap-2 mb-2 pb-2 border-b border-ink-700/50">
                        <div class="h-6 w-6 rounded-md bg-accent-600/30 flex items-center justify-center text-accent-300">
                            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                        </div>
                        <span class="font-bold text-white text-xs">Jarvis • AI Architecture Brain</span>
                    </div>
                    <div class="chat-content text-gray-200">
                        <p>Hello! I am <strong>Jarvis</strong>, your AI Architecture & Integration Assistant for <strong>EverythingWithAI</strong>.</p>
                        <p class="mt-2 text-xs text-gray-400">Ask me about:</p>
                        <ul class="text-xs text-gray-300 mt-1 space-y-1">
                            <li>• Integrating ChatGPT & LLMs with existing .NET apps</li>
                            <li>• Building RAG pipelines with SQL Server or vector DBs</li>
                            <li>• Developing autonomous AI Agents with API tool-calling</li>
                            <li>• Estimating project feasibility and timelines</li>
                        </ul>
                    </div>
                </div>
            `;
            messagesContainer.innerHTML = welcomeHtml;
            if (window.lucide) window.lucide.createIcons();
        }

        function renderAllMessages() {
            messagesContainer.innerHTML = '';
            renderWelcomeMessage();
            conversationHistory.forEach(msg => {
                if (msg.role !== 'system') {
                    appendMessageUI(msg.role, msg.content, false);
                }
            });
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function appendMessageUI(role, content, isStreaming = false) {
            const isUser = role === 'user';
            const wrapper = document.createElement('div');
            wrapper.className = `flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`;

            const bubble = document.createElement('div');
            bubble.className = `${isUser ? 'chat-bubble-user ml-12' : 'chat-bubble-assistant mr-6'} p-3.5 max-w-[85%]`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'chat-content';

            if (isStreaming) {
                contentDiv.innerHTML = `
                    <div class="chat-typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                `;
            } else {
                contentDiv.innerHTML = formatMarkdown(content);
            }

            bubble.appendChild(contentDiv);
            wrapper.appendChild(bubble);
            messagesContainer.appendChild(wrapper);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            if (window.lucide) window.lucide.createIcons();
            return bubble;
        }

        function formatMarkdown(text) {
            if (!text) return '';

            // Escape HTML tags to prevent XSS
            let safe = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');

            // Code blocks with syntax highlighting & copy button
            safe = safe.replace(/```([a-zA-Z0-9_\-\.]*)\n([\s\S]*?)```/g, (match, lang, code) => {
                return `
                    <div class="relative my-2">
                        <button type="button" class="chat-copy-code-btn" onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText); this.textContent='Copied!'; setTimeout(()=>this.textContent='Copy', 1500)">Copy</button>
                        <pre><code>${code.trim()}</code></pre>
                    </div>
                `;
            });

            // Inline code
            safe = safe.replace(/`([^`]+)`/g, '<code>$1</code>');

            // Bold
            safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

            // Italic
            safe = safe.replace(/\*([^*]+)\*/g, '<em>$1</em>');

            // Linebreaks to paragraphs
            const paragraphs = safe.split(/\n\n+/);
            return paragraphs.map(p => {
                p = p.trim();
                if (!p) return '';
                if (p.startsWith('<div class="relative') || p.startsWith('<pre')) {
                    return p;
                }
                // Bullet points
                if (p.includes('\n- ') || p.startsWith('- ')) {
                    const items = p.split('\n- ').map(item => item.replace(/^- /, ''));
                    return `<ul>${items.map(it => `<li>${it.replace(/\n/g, '<br>')}</li>`).join('')}</ul>`;
                }
                return `<p>${p.replace(/\n/g, '<br>')}</p>`;
            }).join('');
        }
    }

    // Initialize Lucide icons if available
    if (window.lucide) {
        window.lucide.createIcons();
    }
});
