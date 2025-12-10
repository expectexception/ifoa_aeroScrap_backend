// Collapsible Filters JavaScript
(function() {
    'use strict';
    
    function initCollapsibleFilters() {
        const filterSidebar = document.querySelector('#changelist-filter');
        if (!filterSidebar) return;
        
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'filter-toggle-btn';
        toggleBtn.innerHTML = `
            <span>🔍 Filters</span>
            <span class="icon">▼</span>
        `;
        
        // Wrap filter content
        const filterContent = document.createElement('div');
        filterContent.className = 'filter-content collapsed';
        
        // Move all children except h2 into filterContent
        const children = Array.from(filterSidebar.children);
        children.forEach(child => {
            if (child.tagName !== 'H2') {
                filterContent.appendChild(child);
            }
        });
        
        // Check if filters should be expanded by default (if any filter is active)
        const hasActiveFilter = filterContent.querySelector('li.selected');
        if (hasActiveFilter) {
            filterContent.classList.remove('collapsed');
            toggleBtn.classList.remove('collapsed');
        } else {
            toggleBtn.classList.add('collapsed');
        }
        
        // Insert button and content
        filterSidebar.appendChild(toggleBtn);
        filterSidebar.appendChild(filterContent);
        
        // Toggle main filter panel
        toggleBtn.addEventListener('click', function() {
            filterContent.classList.toggle('collapsed');
            toggleBtn.classList.toggle('collapsed');
            
            // Save state to localStorage
            const isCollapsed = filterContent.classList.contains('collapsed');
            localStorage.setItem('adminFiltersCollapsed', isCollapsed);
        });
        
        // Restore saved state
        const savedState = localStorage.getItem('adminFiltersCollapsed');
        if (savedState === 'false') {
            filterContent.classList.remove('collapsed');
            toggleBtn.classList.remove('collapsed');
        }
        
        // Make individual filter sections collapsible
        const filterHeaders = filterContent.querySelectorAll('h3');
        filterHeaders.forEach(header => {
            // Skip if already has click handler
            if (header.dataset.collapsible) return;
            header.dataset.collapsible = 'true';
            
            const filterList = header.nextElementSibling;
            if (filterList && filterList.tagName === 'UL') {
                // Collapse by default unless it has active selection
                const hasSelection = filterList.querySelector('li.selected');
                if (!hasSelection) {
                    filterList.classList.add('collapsed');
                    header.classList.add('collapsed');
                }
                
                header.addEventListener('click', function() {
                    filterList.classList.toggle('collapsed');
                    header.classList.toggle('collapsed');
                    
                    // Save individual filter states
                    const filterId = header.textContent.trim();
                    const isCollapsed = filterList.classList.contains('collapsed');
                    localStorage.setItem(`filter_${filterId}_collapsed`, isCollapsed);
                });
                
                // Restore individual filter state
                const filterId = header.textContent.trim();
                const savedFilterState = localStorage.getItem(`filter_${filterId}_collapsed`);
                if (savedFilterState === 'true') {
                    filterList.classList.add('collapsed');
                    header.classList.add('collapsed');
                } else if (savedFilterState === 'false') {
                    filterList.classList.remove('collapsed');
                    header.classList.remove('collapsed');
                }
            }
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCollapsibleFilters);
    } else {
        initCollapsibleFilters();
    }
    
    // Re-initialize on AJAX updates (for Django admin's changelist)
    if (window.django && django.jQuery) {
        django.jQuery(document).on('ajaxComplete', function() {
            setTimeout(initCollapsibleFilters, 100);
        });
    }
})();
