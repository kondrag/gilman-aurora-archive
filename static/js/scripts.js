/**
 * Aurora Archive - JavaScript functionality
 * Handles image modal pop-ups for space weather images
 */

// Modal functionality
class ImageModal {
    constructor() {
        this.modal = null;
        this.modalImg = null;
        this.modalVideo = null;
        this.modalCaption = null;
        this.closeBtn = null;
        this.currentMediaType = null; // 'image' or 'video'

        this.init();
    }

    init() {
        // Get modal elements
        this.modal = document.getElementById('imageModal');
        this.modalImg = this.modal.querySelector('.modal-image');
        this.modalCaption = this.modal.querySelector('.modal-caption');
        this.closeBtn = this.modal.querySelector('.modal-close');

        // Create video element (hidden by default)
        this.modalVideo = document.createElement('video');
        this.modalVideo.id = 'modal-video';
        this.modalVideo.className = 'modal-video';
        this.modalVideo.controls = true;
        this.modalVideo.style.display = 'none';

        // Insert video element before the image
        this.modalImg.parentNode.insertBefore(this.modalVideo, this.modalImg);

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
        const mediaType = trigger.getAttribute('data-type') || 'image';
        const mediaSrc = trigger.getAttribute('data-src');
        const mediaAlt = trigger.getAttribute('data-alt') || trigger.getAttribute('data-title') || '';
        const mediaTitle = trigger.getAttribute('data-title') || mediaAlt;

        this.currentMediaType = mediaType;

        // Hide both media elements first
        this.modalImg.style.display = 'none';
        this.modalVideo.style.display = 'none';

        if (mediaType === 'video') {
            // Setup video modal
            this.modalVideo.src = mediaSrc;
            this.modalVideo.alt = mediaAlt;
            this.modalCaption.textContent = mediaTitle;
            this.modalVideo.style.display = 'block';

            // Pause video when modal closes
            this.modalVideo.addEventListener('ended', () => {
                this.modalVideo.currentTime = 0;
            });
        } else {
            // Setup image modal
            this.modalImg.src = mediaSrc;
            this.modalImg.alt = mediaAlt;
            this.modalCaption.textContent = mediaTitle;
            this.modalImg.style.display = 'block';
        }

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
        // Stop video if playing
        if (this.currentMediaType === 'video' && this.modalVideo) {
            this.modalVideo.pause();
            this.modalVideo.currentTime = 0;
        }

        // Remove animation class
        this.modal.classList.remove('modal-active');

        // Hide modal after animation
        setTimeout(() => {
            this.modal.style.display = 'none';
            // Restore body scroll
            document.body.style.overflow = '';
            // Clear media sources
            this.modalImg.src = '';
            this.modalVideo.src = '';
            this.currentMediaType = null;
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