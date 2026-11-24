# Kliper v2 · ClipFlow Web

**Tahap 1:** unggah video, susun B-roll/gambar dan musik pada timeline, simpan perubahan dan unduh MP4. Ini aplikasi privat untuk satu operator. Tidak memerlukan Docker, Node, kunci API, atau basis data terpisah. Arsitektur: Python 3.12, FastAPI/Uvicorn, HTML/CSS/JavaScript dan FFmpeg.

### Instalasi sekali · Ubuntu 24.04
```sh
git clone https://github.com/saidabdillah/kliper-v2.git
cd kliper-v2
sudo apt update && sudo apt install -y python3.12-venv ffmpeg fonts-dejavu-core
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```
### Menjalankan web
```sh
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8765
```
Buka `http://localhost:8765`. Jika aplikasi berjalan di VPS, dari **laptop** jalankan `ssh -N -L 8765:127.0.0.1:8765 user@IP_VPS` sebelum membuka browser. Jangan buka port aplikasi ke publik tanpa autentikasi. Ctrl+C menghentikan server tanpa menghapus proyek.

### Coba alurnya
1. Pilih MP4, MOV, MKV atau WebM (batas 2 GB), lalu **Unggah video**. Impor URL publik juga tersedia.
2. Klik **Buat klip dengan AI**. Whisper membuat transkrip per kata, lalu model semantik multilingual E5 menilai kandidat dan memilih hingga 10 momen. Saat pertama dipakai server mengunduh kedua model; tidak perlu API key. Skor menunjukkan kecocokan isi, bukan peluang viral. Pilih **Edit klip** pada hasil AI sebelum ekspor. Untuk video tanpa ucapan saja, tersedia alternatif **Edit manual**.
3. Pada **Timeline klip**, pilih jenis aset, unggah B-roll/gambar atau audio. Atur waktu mulai/akhir dan volume musik. Waktu trek relatif terhadap hasil trim, bukan terhadap sumber asli. B-roll menutup kanvas; audio sumber tetap terdengar. Item visual terakhir tampil di atas.
4. **Simpan** lalu **Ekspor MP4**. Render 1080p H.264 menyatukan gambar, subtitle dan musik. Unduh hasil atau simpan SRT/VTT jika ada transkrip.

Data disimpan di `data/` (lokasi lain: `CLIP_DATA`). Tombol **Hapus** menghapus proyek dan media terkait. Simpan salinan asli; tidak ada pembersihan otomatis 24 jam di tahap ini. Maksimal 12 item tambahan per klip; panjang tiap aset B-roll/audio yang disiapkan maksimal 10 menit.

[PRD lengkap](PRD.md) adalah sasaran produk, bukan daftar fitur yang seluruhnya sudah aktif. 4K/HEVC/MOV, AI cloud berkuota, transisi lanjutan, kanvas drag/resize, dan penyimpanan cloud belum termasuk tahap 1. [Pengujian](HASIL-UJI.md).
