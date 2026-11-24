# Uji native
```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_phase1.py
.venv/bin/python tests/browser_editor.py
```
`test_phase1.py` mengunggah video hitam tanpa audio, B-roll merah dan nada musik. Sesudah render, tes membaca piksel dan sampel audio dari MP4 pada saat sebelum dan selama layer aktif. Uji browser melakukan unggah, edit waktu layer, simpan, buka ulang dan unduh MP4. Fixture pendek tidak membuktikan performa pada 2 GB. Uji internet opsional: `WHISPER_MODEL=tiny .venv/bin/python tests/live_check.py`.
