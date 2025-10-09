// HygGeo Navbar - Mobile Menu Handler
document.addEventListener('DOMContentLoaded', function() {
    const navbarCollapse = document.querySelector('#navbarNav');

    // Custom mobile dropdown handling
    document.querySelectorAll('.mobile-dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('data-target');
            const targetSubmenu = document.getElementById(targetId);

            // Close other open submenus
            document.querySelectorAll('.mobile-submenu.show').forEach(submenu => {
                if (submenu !== targetSubmenu) {
                    submenu.classList.remove('show');
                    submenu.previousElementSibling.classList.remove('active');
                }
            });

            // Toggle current submenu
            if (targetSubmenu.classList.contains('show')) {
                targetSubmenu.classList.remove('show');
                this.classList.remove('active');
            } else {
                targetSubmenu.classList.add('show');
                this.classList.add('active');
            }
        });
    });

    // Close mobile navbar when clicking submenu items
    document.querySelectorAll('.mobile-submenu a').forEach(link => {
        link.addEventListener('click', function() {
            setTimeout(() => {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse) bsCollapse.hide();
            }, 150);
        });
    });

    // Close mobile navbar when clicking regular nav links
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        if (link.classList.contains('mobile-dropdown-toggle') ||
            link.classList.contains('dropdown-toggle')) {
            return;
        }

        link.addEventListener('click', function() {
            if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
                setTimeout(() => {
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) bsCollapse.hide();
                }, 150);
            }
        });
    });

    // Reset mobile submenus when navbar collapses
    navbarCollapse.addEventListener('hidden.bs.collapse', function() {
        document.querySelectorAll('.mobile-submenu.show').forEach(submenu => {
            submenu.classList.remove('show');
        });
        document.querySelectorAll('.mobile-dropdown-toggle.active').forEach(toggle => {
            toggle.classList.remove('active');
        });
    });
});
