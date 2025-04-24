document.addEventListener('DOMContentLoaded', function() {
    // Handle all delete confirmation dialogs
    const deleteButtons = document.querySelectorAll('.btn-danger[href*="delete"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const deleteUrl = this.getAttribute('href');
            
            if (confirm('Are you sure you want to delete this item?')) {
                window.location.href = deleteUrl;
            }
        });
    });
});
