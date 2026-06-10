// Sidebar mobile toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show');
}

// Fermer sidebar en cliquant en dehors (mobile)
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    if (sidebar && sidebar.classList.contains('show')) {
        if (!sidebar.contains(e.target) && !e.target.closest('[onclick="toggleSidebar()"]')) {
            sidebar.classList.remove('show');
        }
    }
});

// Auto-disparition des messages toast
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toast-msg').forEach((el, i) => {
        setTimeout(() => {
            if (el) {
                el.style.opacity = '0';
                el.style.transform = 'translateX(100%)';
                el.style.transition = 'all 0.4s ease';
                setTimeout(() => el.remove(), 400);
            }
        }, 5000 + i * 500);
    });
});
