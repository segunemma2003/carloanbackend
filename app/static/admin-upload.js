/**
 * Admin Panel Image Upload Helper
 * Automatically handles file uploads and populates image_url fields
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        // Find all image_url input fields
        const imageUrlInputs = document.querySelectorAll('input[name*="image_url"], input[name*="logo_url"]');
        
        imageUrlInputs.forEach(input => {
            // Create upload button next to the input
            const uploadBtn = createUploadButton(input);
            input.parentNode.insertBefore(uploadBtn, input.nextSibling);
        });
    }

    function createUploadButton(input) {
        const container = document.createElement('div');
        container.style.marginTop = '5px';
        
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-primary';
        btn.textContent = '📤 Upload Image';
        btn.style.marginRight = '10px';
        
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.style.display = 'none';
        
        const preview = document.createElement('img');
        preview.style.maxWidth = '200px';
        preview.style.maxHeight = '200px';
        preview.style.marginTop = '10px';
        preview.style.display = 'none';
        preview.style.border = '1px solid #ddd';
        preview.style.borderRadius = '4px';
        preview.style.padding = '5px';
        
        btn.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            // Validate file type
            if (!file.type.startsWith('image/')) {
                alert('Please select an image file');
                return;
            }
            
            // Validate file size (5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert('File size must be less than 5MB');
                return;
            }
            
            btn.disabled = true;
            btn.textContent = '⏳ Uploading...';
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                // Determine folder based on field name
                let folder = 'general';
                if (input.name.includes('logo')) {
                    folder = 'brands';
                } else if (input.name.includes('banner')) {
                    folder = 'banners';
                } else if (input.name.includes('category')) {
                    folder = 'categories';
                }
                
                formData.append('folder', folder);
                
                // Get CSRF token if available
                const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';
                if (csrfToken) {
                    formData.append('csrf_token', csrfToken);
                }
                
                const response = await fetch('/api/v1/uploads/image', {
                    method: 'POST',
                    body: formData,
                    credentials: 'include',
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Upload failed');
                }
                
                const data = await response.json();
                
                // Set the URL in the input field
                input.value = data.url;
                
                // Show preview
                preview.src = data.url;
                preview.style.display = 'block';
                
                // Trigger change event
                input.dispatchEvent(new Event('change', { bubbles: true }));
                
                alert('✅ Image uploaded successfully!');
                
            } catch (error) {
                console.error('Upload error:', error);
                alert('❌ Upload failed: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '📤 Upload Image';
            }
        });
        
        container.appendChild(btn);
        container.appendChild(fileInput);
        container.appendChild(preview);
        
        return container;
    }
})();

