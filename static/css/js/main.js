// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navMenu = document.getElementById('navMenu');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            const icon = this.querySelector('i');
            if (icon.classList.contains('fa-bars')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.navbar') && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            const icon = mobileMenuBtn.querySelector('i');
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    });
    
    // Form validation
    const birthForm = document.getElementById('birthForm');
    if (birthForm) {
        birthForm.addEventListener('submit', function(e) {
            const year = document.getElementById('year').value;
            const month = document.getElementById('month').value;
            const day = document.getElementById('day').value;
            const hour = document.getElementById('hour').value;
            const minute = document.getElementById('minute').value;
            const second = document.getElementById('second').value;
            
            // Basic validation
            if (year < 1900 || year > 2100) {
                e.preventDefault();
                alert('Please enter a valid year between 1900 and 2100');
                return;
            }
            
            if (month < 1 || month > 12) {
                e.preventDefault();
                alert('Please enter a valid month (1-12)');
                return;
            }
            
            if (day < 1 || day > 31) {
                e.preventDefault();
                alert('Please enter a valid day (1-31)');
                return;
            }
            
            if (hour < 0 || hour > 23) {
                e.preventDefault();
                alert('Please enter a valid hour (0-23)');
                return;
            }
            
            if (minute < 0 || minute > 59) {
                e.preventDefault();
                alert('Please enter a valid minute (0-59)');
                return;
            }
            
            if (second < 0 || second > 59) {
                e.preventDefault();
                alert('Please enter a valid second (0-59)');
                return;
            }
        });
    }
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .planet-card, .house-card, .panchanga-card, .stat-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Navbar background change on scroll
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(255, 255, 255, 0.98)';
            navbar.style.boxShadow = '0 2px 20px rgba(44, 95, 45, 0.15)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.boxShadow = '0 2px 20px rgba(44, 95, 45, 0.1)';
        }
    });
    
    // Tooltips for planet symbols
    const planetSymbols = document.querySelectorAll('.planet-symbol');
    planetSymbols.forEach(symbol => {
        symbol.setAttribute('title', 'Vedic planet symbol');
    });
});

// Function to download chart as JSON
function downloadChart() {
    const chartData = {
        ascendant: window.ascendantData,
        planets: window.planetData,
        houses: window.houseData,
        panchanga: window.panchangaData
    };
    
    const dataStr = JSON.stringify(chartData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'vedic-chart.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}

// Make chart data available globally if on chart page
if (document.querySelector('.chart-content')) {
    window.ascendantData = {{ chart.Ascendant | tojson }};
    window.planetData = {{ chart.Planets | tojson }};
    window.houseData = {{ chart.Houses | tojson }};
    window.panchangaData = {{ chart.Panchanga | tojson }};
}
