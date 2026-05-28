/* ==================== Toast System ==================== */
class Toast {
    static container = null;

    static init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    static show(options = {}) {
        this.init();

        const { type = 'info', title = '', message = '', duration = 4000 } = options;

        const icons = {
            success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type]}</div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" aria-label="关闭">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;

        this.container.appendChild(toast);

        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.dismiss(toast));

        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }

        return toast;
    }

    static dismiss(toast) {
        if (!toast || !toast.parentNode) return;
        toast.classList.add('toast-exit');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    static success(message, title = '成功') {
        return this.show({ type: 'success', title, message });
    }

    static error(message, title = '错误') {
        return this.show({ type: 'error', title, message });
    }

    static warning(message, title = '警告') {
        return this.show({ type: 'warning', title, message });
    }

    static info(message, title = '提示') {
        return this.show({ type: 'info', title, message });
    }
}

/* ==================== Modal System ==================== */
class Modal {
    static show(options = {}) {
        const { title = '', content = '', confirmText = '确认', cancelText = '取消', onConfirm = null, onCancel = null, type = 'default' } = options;

        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    <button class="modal-close" aria-label="关闭">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="modal-body">${content}</div>
                <div class="modal-footer">
                    <button class="btn btn-secondary modal-cancel">${cancelText}</button>
                    <button class="btn ${type === 'danger' ? 'btn-danger' : 'btn-primary'} modal-confirm">${confirmText}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Show animation
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });

        // Event handlers
        const close = () => {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
        };

        overlay.querySelector('.modal-close').addEventListener('click', () => {
            if (onCancel) onCancel();
            close();
        });

        overlay.querySelector('.modal-cancel').addEventListener('click', () => {
            if (onCancel) onCancel();
            close();
        });

        overlay.querySelector('.modal-confirm').addEventListener('click', () => {
            if (onConfirm) onConfirm();
            close();
        });

        // Close on backdrop click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                if (onCancel) onCancel();
                close();
            }
        });

        // Close on Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                if (onCancel) onCancel();
                close();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        return { close };
    }

    static confirm(message, options = {}) {
        return new Promise((resolve) => {
            this.show({
                title: options.title || '确认操作',
                content: message,
                confirmText: options.confirmText || '确认',
                cancelText: options.cancelText || '取消',
                type: options.type || 'default',
                onConfirm: () => resolve(true),
                onCancel: () => resolve(false)
            });
        });
    }

    static alert(message, options = {}) {
        return new Promise((resolve) => {
            this.show({
                title: options.title || '提示',
                content: message,
                confirmText: options.confirmText || '知道了',
                onConfirm: () => resolve()
            });
        });
    }
}

/* ==================== Fullscreen Viewer ==================== */
class FullscreenViewer {
    static show(imageUrl) {
        const viewer = document.createElement('div');
        viewer.className = 'fullscreen-viewer';
        viewer.innerHTML = `
            <button class="close-btn" aria-label="关闭">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
            <img src="${imageUrl}" alt="全屏查看">
        `;

        document.body.appendChild(viewer);

        requestAnimationFrame(() => {
            viewer.classList.add('active');
        });

        const close = () => {
            viewer.classList.remove('active');
            setTimeout(() => viewer.remove(), 300);
        };

        viewer.querySelector('.close-btn').addEventListener('click', close);
        viewer.addEventListener('click', (e) => {
            if (e.target === viewer) close();
        });

        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                close();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }
}

/* ==================== Cookie Helper ==================== */
function getCookie(name) {
    let v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : null;
}

/* ==================== Password Strength Checker ==================== */
function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    const levels = ['weak', 'medium', 'strong'];
    return levels[Math.min(strength - 1, 2)] || 'weak';
}

/* ==================== Password Toggle ==================== */
function initPasswordToggle(inputId, toggleId) {
    const input = document.getElementById(inputId);
    const toggle = document.getElementById(toggleId);

    if (!input || !toggle) return;

    toggle.addEventListener('click', () => {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        toggle.innerHTML = isPassword
            ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
            : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
    });
}

/* ==================== Number Animation ==================== */
function animateNumber(element, targetValue, duration = 500) {
    const startValue = parseInt(element.textContent) || 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.round(startValue + (targetValue - startValue) * easeProgress);

        element.textContent = currentValue;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/* ==================== Form Validation ==================== */
class FormValidator {
    constructor(form) {
        this.form = form;
        this.rules = {};
        this.errors = {};
    }

    addRule(fieldName, validator) {
        this.rules[fieldName] = validator;
        return this;
    }

    validate() {
        this.errors = {};
        let isValid = true;

        for (const [fieldName, validator] of Object.entries(this.rules)) {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (!field) continue;

            const error = validator(field.value, this.form);
            const errorElement = this.form.querySelector(`#${fieldName}-error`);

            if (error) {
                isValid = false;
                this.errors[fieldName] = error;
                field.classList.add('error');
                if (errorElement) {
                    errorElement.textContent = error;
                    errorElement.style.display = 'block';
                }
            } else {
                field.classList.remove('error');
                field.classList.add('success');
                if (errorElement) {
                    errorElement.style.display = 'none';
                }
            }
        }

        return isValid;
    }

    clear() {
        this.errors = {};
        this.form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
        this.form.querySelectorAll('.form-error').forEach(el => el.style.display = 'none');
    }
}

/* ==================== File Upload Progress ==================== */
async function uploadFileWithProgress(url, file, options = {}) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append(options.fieldName || 'file', file);

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable && options.onProgress) {
                const percent = Math.round((e.loaded / e.total) * 100);
                options.onProgress(percent);
            }
        });

        xhr.addEventListener('load', () => {
            try {
                const data = JSON.parse(xhr.responseText);
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(data);
                } else {
                    reject(new Error(data.error || '上传失败'));
                }
            } catch (e) {
                reject(new Error('解析响应失败'));
            }
        });

        xhr.addEventListener('error', () => reject(new Error('网络错误')));

        xhr.open('POST', url);
        xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        xhr.send(formData);
    });
}

/* ==================== Keyboard Shortcuts ==================== */
const KeyboardShortcuts = {
    shortcuts: {},

    register(key, callback, options = {}) {
        const { ctrl = false, alt = false, shift = false, meta = false } = options;

        const id = `${ctrl ? 'ctrl+' : ''}${alt ? 'alt+' : ''}${shift ? 'shift+' : ''}${meta ? 'meta+' : ''}${key}`;

        this.shortcuts[id] = callback;
    },

    init() {
        document.addEventListener('keydown', (e) => {
            const id = `${e.ctrlKey ? 'ctrl+' : ''}${e.altKey ? 'alt+' : ''}${e.shiftKey ? 'shift+' : ''}${e.metaKey ? 'meta+' : ''}${e.key}`;

            if (this.shortcuts[id]) {
                e.preventDefault();
                this.shortcuts[id](e);
            }
        });
    }
};

// Initialize keyboard shortcuts
KeyboardShortcuts.init();

// Escape to close modals
KeyboardShortcuts.register('Escape', () => {
    const activeModal = document.querySelector('.modal-overlay.active');
    if (activeModal) {
        activeModal.click();
    }
});

// ==================== Mobile Menu ====================
function initMobileMenu() {
    const toggle = document.querySelector('.mobile-menu-toggle');
    const menu = document.querySelector('.mobile-menu');

    if (!toggle || !menu) return;

    toggle.addEventListener('click', () => {
        menu.classList.toggle('active');
        const isOpen = menu.classList.contains('active');
        toggle.setAttribute('aria-expanded', isOpen);
    });

    // Close menu when clicking a link
    menu.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            menu.classList.remove('active');
            toggle.setAttribute('aria-expanded', false);
        });
    });
}

// ==================== Drag and Drop ====================
function initDragAndDrop(element, options = {}) {
    const { onDrop = () => {}, onDragOver = () => {}, onDragLeave = () => {} } = options;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        element.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        element.addEventListener(eventName, (e) => {
            onDragOver(e, element);
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        element.addEventListener(eventName, (e) => {
            onDragLeave(e, element);
        });
    });

    element.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) {
            onDrop(files, element);
        }
    });
}

// ==================== Export ====================
window.Toast = Toast;
window.Modal = Modal;
window.FullscreenViewer = FullscreenViewer;
window.FormValidator = FormValidator;
window.KeyboardShortcuts = KeyboardShortcuts;
window.animateNumber = animateNumber;
window.checkPasswordStrength = checkPasswordStrength;
window.initPasswordToggle = initPasswordToggle;
window.uploadFileWithProgress = uploadFileWithProgress;
window.initMobileMenu = initMobileMenu;
window.initDragAndDrop = initDragAndDrop;
