# Product Requirements Document (PRD): ClipFlow Web

**Versi Dokumen:** 2.0  
**Status:** Siap Pengembangan (Ready for Development)  
**Target Platform:** Web Browser (Desktop & Mobile Responsive)  
**Fokus Utama:** Pembuat Klip Video Otomatis (AI), Editor Video Gaya CapCut Web, & Ekspor Kualitas Tinggi

---

## 1. Ringkasan Produk (Product Overview)
**ClipFlow Web** adalah platform pembuatan klip video pendek (*short-form video*) dan editor video berbasis *web browser* yang dirancang semudah dan selengkap **CapCut Web**. Pengguna dapat mengunggah video panjang, memotong momen terbaik secara otomatis dengan bantuan AI, mengedit video secara mendalam menggunakan antarmuka *multi-track timeline* ala CapCut, menerapkan template subtitle dinamis, serta mengekspor video dengan kualitas jernih hingga resolusi **4K 60fps** tanpa *watermark* yang mengganggu.

### Sasaran Utama & KPI Produk
* **Kualitas Ekspor Maksimal:** Mendukung resolusi 720p, 1080p (Full HD), hingga 4K dengan opsi pengaturan *bitrate* tinggi dan *frame rate* 30fps / 60fps.
* **Kemudahan Editor:** Pengguna baru dapat memahami alur *timeline* ala CapCut dan menyelesaikan video pertama dalam waktu < 5 menit.
* **Kecepatan Rendering:** Proses ekspor video berdurasi 1 menit pada resolusi 1080p selesai dalam waktu < 30 detik.

---

## 2. Arsitektur AI & Keamanan API Key
Sistem mengintegrasikan layanan AI pihak ketiga untuk mengotomatiskan pembuatan teks dan pemotongan klip, dengan standar keamanan ketat agar biaya operasional tetap terkendali.

### 2.1 Layanan AI yang Digunakan
1. **Speech-to-Text (Auto-Subtitle):** Menggunakan **OpenAI Whisper API** atau **Deepgram API** untuk transkripsi suara ke teks dengan akurasi stempel waktu (*word-level timestamp*) per kata.
2. **Analisis Momen Viral (Smart Clipping):** Menggunakan **Google Gemini API** atau **OpenAI GPT-4o-mini** untuk menganalisis transkrip dan memberi skor (*Viral Score*) pada segmen paling menarik.
3. **Deteksi Wajah (Auto-Reframe):** Menggunakan **MediaPipe** (berjalan di *client/server* tanpa biaya API) untuk melacak wajah pembicara agar tetap berada di tengah saat rasio layar diubah menjadi vertikal (9:16).

### 2.2 Standar Keamanan Penyimpanan API Key
* **Penyimpanan Backend Eksklusif:** Seluruh API Key (`OPENAI_API_KEY`, `GEMINI_API_KEY`) **wajib** disimpan di sisi *server* (*Backend*) menggunakan **Environment Variables (`.env`)** atau *Secret Manager* milik layanan *cloud hosting*.
* **Larangan Keras di Frontend:** API Key dilarang keras diletakkan pada kode *Frontend* (React/Next.js/Vue) atau dikirimkan ke *browser* pengguna.
* **Rate Limiting & Kuota:** *Backend* wajib menerapkan pembatasan jumlah permintaan (*rate limit*) dan pengecekan kuota kredit pengguna sebelum meneruskan permintaan ke server AI untuk mencegah penyalahgunaan/spam saldo.

---

## 3. Fitur Utama (Core Features)

### 3.1 Modul Pembuat Klip Video Otomatis (AI Clipper)
* **Impor Multi-Sumber:** Mendukung unggah file lokal (MP4, MOV, MKV, WebM hingga 2GB) dan impor langsung via tautan YouTube / Google Drive.
* **Pemotongan Momen Otomatis:** AI membagi video panjang menjadi 3–10 klip pendek berdurasi 15–60 detik lengkap dengan judul dan skor potensi viral.
* **Auto-Reframe Cerdas:** Mengubah rasio aspek secara otomatis antara **9:16** (TikTok/Reels/Shorts), **1:1** (Instagram Feed), dan **16:9** (YouTube) dengan pelacakan posisi pembicara.

---

### 3.2 Modul Editor Video Lengkap (Gaya CapCut Web)
Antarmuka editor dirancang menyerupai **CapCut Web** agar intuitif bagi kreator konten modern:

#### A. Tata Letak Ruang Kerja (Workspace Layout)
1. **Panel Aset (Kiri):** Tab navigasi untuk *Media/Upload*, *Audio & Musik*, *Teks & Subtitle*, *Stiker & Elemen*, *Transisi*, dan *Filter/Efek*.
2. **Canvas Pratinjau (Tengah):** Layar pratinjau *real-time* lengkap dengan panduan garis aman (*Safe Zone* untuk ikon TikTok/Reels), kontrol *zoom canvas*, serta manipulasi objek langsung (*drag, resize, rotate*).
3. **Panel Properti (Kanan):** Pengaturan detail untuk elemen yang sedang dipilih (posisi, skala, opasitas, kecepatan klip, kurva warna, dan gaya font subtitle).
4. **Multi-Track Timeline (Bawah):** Lini masa berlapis (*layer-based*) di bagian bawah layar.

#### B. Fitur Editing Timeline ala CapCut
* **Multi-Layer Track:** Mendukung banyak lapisan secara bersamaan (Track Video Utama, Track Overlay/B-Roll/Gambar, Track Subtitle, Track Teks Judul, dan Track Audio/SFX).
* **Alat Potong Presisi:** Fitur *Split* (Ctrl+B / ikon gunting), *Trim* (tarik ujung klip), *Ripple Delete* (hapus celah kosong otomatis), dan *Undo/Redo* tanpa batas.
* **Pengaturan Kecepatan (Speed Control):** Ubah kecepatan video dari 0.1x (*slow motion*) hingga 10x (*timelapse*) dengan opsi *Pitch Correction* agar suara tidak melengking.
* **Animasi & Transisi:**
  * *Transisi antar klip:* Dissolve, Slide, Zoom In/Out, Whip Pan, Glitch.
  * *Animasi masuk/keluar elemen:* Fade, Pop, Bounce, Slide Up/Down.
* **Audio & Efek Suara (SFX):**
  * Pustaka musik latar bebas royalti dan efek suara populer (*whoosh, pop, ding, bass drop*).
  * Pengaturan volume per trek, *Fade In / Fade Out* audio, serta fitur *Noise Reduction* (peredam bising latar).
* **Penyesuaian Warna & Filter (Color Adjustment):** Pengaturan *Brightness*, *Contrast*, *Saturation*, *Exposure*, *Sharpen*, serta filter sinematik siap pakai.

---

### 3.3 Template Gaya Subtitle Dinamis (6 Preset Bawaan)
Pengguna dapat mengganti tampilan subtitle secara instan dengan satu klik, serta mengedit teks maupun posisi per kata secara langsung:

| No | Nama Template | Karakteristik Visual & Gaya Desain | Cocok Untuk Konten |
| :--- | :--- | :--- | :--- |
| **1** | **Bold Viral (Gaya Hormozi)** | Font tebal sans-serif kapital (*Montserrat ExtraBold*), warna putih dengan sorotan kata aktif kuning/hijau neon, garis tepi (*stroke*) hitam tebal, dan efek membesar (*pop*) per kata. | Podcast, motivasi, edukasi bisnis, TikTok/Reels cepat. |
| **2** | **Karaoke Highlight Box** | Teks putih bersih dengan kotak latar belakang persegi panjang membulat (*rounded pill*) berwarna ungu/biru elektrik yang berpindah mengikuti kata yang sedang diucapkan. | Storytelling, ulasan produk (*review*), tutorial. |
| **3** | **Minimalist Clean** | Font modern ramping (*Inter / Plus Jakarta Sans*), latar belakang kotak hitam transparan (*opacity* 65%), tanpa animasi berlebihan, posisi rapi di bagian bawah. | Dokumenter, wawancara formal, LinkedIn, YouTube. |
| **4** | **Neon Glow Cyber** | Font futuristik dengan efek pendar cahaya (*outer glow*) biru cyan dan merah muda (*magenta*) yang kontras pada latar gelap. | Konten *gaming*, teknologi, musik, hiburan malam. |
| **5** | **News Headline Banner** | Teks rata kiri di dalam bilah berita (*lower-third banner*) merah-putih khas siaran televisi, dilengkapi label kategori kecil di bagian atasnya. | Berita terkini, opini publik, analisis isu viral. |
| **6** | **Comic Pop Bubble** | Font bergaya komik membulat dengan bayangan keras (*hard drop shadow*) hitam di sisi kanan bawah dan efek memantul (*bounce*). | Komedi, vlog harian, konten anak muda, sketsa. |

---

## 4. Sistem Ekspor Video Berkualitas Tinggi (High-Quality Export Engine)
Untuk menjamin hasil video tajam, tidak pecah saat diunggah ke media sosial, dan memiliki pergerakan mulus, sistem rendering dibangun menggunakan **FFmpeg** di sisi *server* (dan akselerasi GPU/WebCodecs bila tersedia).

### 4.1 Spesifikasi & Opsi Pengaturan Ekspor
Pengguna dapat memilih kualitas ekspor sebelum mengunduh file:

1. **Resolusi Video:**
   * **720p (HD):** 1280x720 (atau 720x1280 untuk vertikal) — Cepat untuk draf.
   * **1080p (Full HD - Rekomendasi):** 1920x1080 (atau 1080x1920) — Standar jernih untuk TikTok, Reels, dan Shorts.
   * **2K (QHD) & 4K (Ultra HD):** 2560x1440 dan 3840x2160 — Ketajaman maksimal tanpa kompresi berlebih.
2. **Frame Rate (FPS):**
   * **30 fps** (Standar sinematik & hemat ukuran file).
   * **60 fps** (Pergerakan super mulus untuk video *gaming*, olahraga, dan transisi cepat).
3. **Bitrate & Kualitas Encoding:**
   * **Tinggi (High Bitrate):** 15–25 Mbps (1080p) hingga 45–60 Mbps (4K) menggunakan profil encoding `H.264 High Profile` (`CRF 18`) agar detail teks subtitle dan tekstur wajah tetap tajam setelah dikompresi ulang oleh algoritma TikTok/Instagram.
   * **Audio Jernih:** Codec **AAC Stereo 320 kbps, 48 kHz** untuk memastikan suara vokal dan musik terdengar bulat dan jernih.
4. **Format File:**
   * **MP4 (H.264 / H.265 HEVC)** — Kompatibel di semua perangkat dan media sosial.
   * **MOV** — Opsi profesional untuk kebutuhan pascaproduksi lanjutan.

---

## 5. Alur Pengguna Utama (User Flow)
1. **Unggah / Impor:** Pengguna mengunggah video atau menempelkan tautan video.
2. **Proses AI:** *Backend* mengekstrak audio, mengirimkannya ke API Speech-to-Text (menggunakan API Key di `.env`), lalu menampilkan daftar rekomendasi klip pendek lengkap dengan subtitle otomatis.
3. **Masuk ke Mode Editor (Gaya CapCut):** Pengguna memilih salah satu klip dan masuk ke tampilan editor *multi-track timeline*.
4. **Kustomisasi:** Pengguna memilih salah satu dari 6 template subtitle, memperbaiki ejaan jika perlu, menambahkan B-Roll/gambar, stiker, transisi, atau musik latar.
5. **Pengaturan Ekspor Berkualitas:** Pengguna menekan tombol **Export**, memilih resolusi **1080p / 4K**, **60fps**, dan *bitrate* tinggi.
6. **Rendering & Unduh:** *Server* memproses video dengan FFmpeg dan menyediakan tautan unduhan file MP4 siap unggah.

---

## 6. Rekomendasi Teknologi (Tech Stack) untuk Tim Developer
* **Frontend (Antarmuka Editor):** Next.js / React, TypeScript, Tailwind CSS, Canvas API / WebGL (untuk pratinjau *timeline* yang mulus tanpa *lag*).
* **Backend & Keamanan API:** Node.js (Express/NestJS) atau Python (FastAPI) dengan manajemen rahasia via `.env`.
* **Video Rendering Engine:** **FFmpeg** (dengan dukungan *hardware acceleration* NVENC/GPU pada server) + **Remotion** (opsional untuk merender animasi subtitle kompleks menjadi video tajam).
* **Penyimpanan File Sementara:** AWS S3 / Cloudflare R2 (dengan penghapusan otomatis file mentah setelah 24 jam untuk menghemat biaya penyimpanan).
