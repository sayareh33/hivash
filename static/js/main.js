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
    const bsCollapseInstance = new bootstrap.Collapse(bsCollapse, {toggle: false});

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



    document.addEventListener('DOMContentLoaded', () => {
    const cartButtons = document.querySelectorAll('.btn');

    cartButtons.forEach(btn => {
    btn.addEventListener('click', () => {
    if (btn.textContent.includes('افزودن به سبد')) {
    btn.classList.add('shine');
    setTimeout(() => btn.classList.remove('shine'), 1000);
}
});
});
});
// __________________________اگر کاربر لاگین نباشه و روی سبد خرید بزنه هشدار بده

// در فایل main.js یا base.html
document.addEventListener('DOMContentLoaded', function() {
    // مدیریت خطای 401 در تمام درخواست‌های fetch
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            if (response.status === 401) {
                return response.json().then(data => {
                    if (data.login_required) {
                        if (confirm(data.message + '\n\nآیا می‌خواهید به صفحه ورود بروید؟')) {
                            window.location.href = data.login_url + '?next=' + encodeURIComponent(window.location.pathname);
                        }
                        throw new Error('login_required');
                    }
                    return response;
                });
            }
            return response;
        });
    };

// مدیریت فرم‌های سبد خرید در تمام صفحات
function initializeCartForms() {
    const cartForms = document.querySelectorAll('form[data-add-to-cart], .js-add-to-cart-form');

    cartForms.forEach(form => {
        if (form.dataset.authHandler) return;
        form.dataset.authHandler = 'true';

        form.addEventListener('submit', function(e) {
            if (!window.USER_IS_AUTHENTICATED) {
                e.preventDefault();
                e.stopPropagation();

                if (confirm('برای افزودن به سبد خرید باید وارد حساب کاربری خود شوید.\n\nآیا می‌خواهید به صفحه ورود بروید؟')) {
                    window.location.href = window.LOGIN_URL + '?next=' + encodeURIComponent(window.location.pathname);
                }
                return false;
            }
        });
    });
}

// اجرای اولیه
document.addEventListener('DOMContentLoaded', initializeCartForms);
    // اجرای اولیه و همچنین برای محتوای داینامیک
    initializeCartForms();

    // مشاهده تغییرات DOM برای صفحاتی با محتوای داینامیک
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initializeCartForms();
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});