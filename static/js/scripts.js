/**
 * Aurora Archive - JavaScript functionality
 * Handles image modal pop-ups for space weather images
 */

// Modal functionality
class ImageModal {
    constructor() {
        this.modal = null;
        this.modalImg = null;
        this.modalCaption = null;
        this.closeBtn = null;

        this.init();
    }

    init() {
        // Get modal elements
        this.modal = document.getElementById('imageModal');
        this.modalImg = this.modal.querySelector('.modal-image');
        this.modalCaption = this.modal.querySelector('.modal-caption');
        this.closeBtn = this.modal.querySelector('.modal-close');

        // Add event listeners
        this.addEventListeners();
    }

    addEventListeners() {
        // Add click event to all modal trigger images
        const modalTriggers = document.querySelectorAll('.modal-trigger');
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                this.openModal(trigger);
            });
        });

        // Close modal when clicking the X button
        this.closeBtn.addEventListener('click', () => {
            this.closeModal();
        });

        // Close modal when clicking outside the image
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.closeModal();
            }
        });
    }

    openModal(trigger) {
        const imgSrc = trigger.getAttribute('data-src');
        const imgAlt = trigger.getAttribute('data-alt');

        // Set modal content
        this.modalImg.src = imgSrc;
        this.modalImg.alt = imgAlt;
        this.modalCaption.textContent = imgAlt;

        // Show modal
        this.modal.style.display = 'block';

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        // Add animation class
        setTimeout(() => {
            this.modal.classList.add('modal-active');
        }, 10);
    }

    closeModal() {
        // Remove animation class
        this.modal.classList.remove('modal-active');

        // Hide modal after animation
        setTimeout(() => {
            this.modal.style.display = 'none';
            // Restore body scroll
            document.body.style.overflow = '';
        }, 200);
    }
}

// Initialize modal when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ImageModal();
});

// Add smooth scroll behavior for internal links
document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});