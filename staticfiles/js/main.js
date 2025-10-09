document.addEventListener('DOMContentLoaded', function () {
    // ===============================
    // Sticky Navbar با gradient ثابت
    // ===============================
    const navbar = document.querySelector('.navbar.fixed-top');
    if (navbar) {
        function setNavbarGradient() {
            navbar.style.background = 'linear-gradient(135deg, #00ff7f, #fff200)';
        }

        setNavbarGradient();
        window.addEventListener('scroll', setNavbarGradient);
        window.addEventListener('resize', setNavbarGradient);
    }

    // ===============================
    // مدیریت منوی موبایل
    // ===============================
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const bsCollapse = document.getElementById('navbarContent');
    const bsCollapseInstance = new bootstrap.Collapse(bsCollapse, { toggle: false });

    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            if (window.innerWidth < 992) {
                bsCollapseInstance.hide();
            }
        });
    });

    // ===============================
    // جلوگیری از overflow در موبایل
    // ===============================
    function fixMobileLayout() {
        if (window.innerWidth < 992) {
            document.body.style.overflowX = 'hidden';
            if (navbar) {
                navbar.style.width = '100%';
                navbar.style.maxWidth = '100%';
            }
        } else {
            document.body.style.overflowX = '';
        }
    }

    fixMobileLayout();
    window.addEventListener('resize', fixMobileLayout);

    // ===============================
    // فعال کردن تب‌های Bootstrap
    // ===============================
    const tabButtons = document.querySelectorAll('#product-tab button');
    tabButtons.forEach(button => {
        const tab = new bootstrap.Tab(button);
        button.addEventListener('click', function (event) {
            event.preventDefault();
            tab.show();
        });
    });
});
