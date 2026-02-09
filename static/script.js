/**
 * SariKidung - Main JavaScript
 * Tema: Bali Heritage Bronze
 */

document.addEventListener("DOMContentLoaded", function() {
    
    // 1. ANIMASI MUNCUL (FADE-IN UP)
    // Mencari semua elemen dengan class 'animate'
    const animateElements = document.querySelectorAll('.animate');
    
    const observerOptions = {
        threshold: 0.1 // Animasi jalan saat 10% elemen terlihat di layar
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, observerOptions);

    animateElements.forEach(el => {
        // Set kondisi awal (tersembunyi)
        el.style.opacity = "0";
        el.style.transform = "translateY(30px)";
        el.style.transition = "all 0.8s cubic-bezier(0.165, 0.84, 0.44, 1)";
        observer.observe(el);
    });


    // 2. EFEK NAVBAR SAAT SCROLL
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('shadow-sm'); // Tambah bayangan saat scroll
            navbar.style.padding = "10px 0";  // Navbar jadi lebih ramping
            navbar.style.backgroundColor = "rgba(255, 255, 255, 0.98)";
        } else {
            navbar.classList.remove('shadow-sm');
            navbar.style.padding = "15px 0";  // Navbar kembali normal
        }
    });


    // 3. INISIALISASI BOOTSTRAP TOOLTIP (Optional)
    // Jika Anda ingin menggunakan fitur penjelasan saat kursor diarahkan ke tombol
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

});

/**
 * 4. FUNGSI PENCARIAN TABEL (Library)
 * Diletakkan di luar agar bisa dipanggil oleh onkeyup="searchTable()"
 */
function searchTable() {
    let input = document.getElementById("searchInput");
    if (!input) return; // Keluar jika bukan di halaman library

    let filter = input.value.toUpperCase();
    let table = document.getElementById("kidungTable");
    let tr = table.getElementsByTagName("tr");
    let noResult = document.getElementById("noResult");
    let visibleCount = 0;

    // Loop semua baris tabel (lewati header index 0)
    for (let i = 1; i < tr.length; i++) {
        let textContent = tr[i].textContent || tr[i].innerText;
        if (textContent.toUpperCase().indexOf(filter) > -1) {
            tr[i].classList.remove("d-none"); // Tampilkan
            visibleCount++;
        } else {
            tr[i].classList.add("d-none");    // Sembunyikan
        }
    }

    // Tampilkan pesan "Data tidak ditemukan" jika hasil kosong
    if (noResult) {
        if (visibleCount === 0) {
            noResult.classList.remove("d-none");
        } else {
            noResult.classList.add("d-none");
        }
    }
}
