# Menjalankan DiscoveryBrief di Windows lokal

Diverifikasi 10 November 2026. Direktori aplikasi:
`C:\Projects\DiscoveryBrief`.
Mesin ini menggunakan Podman 6.1.4, WSL dan Docker Compose v5.7.0; perintah `docker`
tidak terpasang. Dockerfile yang sama berhasil dibangun/dijalankan oleh Podman.

## Pilihan utama: container untuk aplikasi dan Bifrost

Buka PowerShell dan jalankan:

```powershell
Set-Location C:\Projects\DiscoveryBrief
podman machine list
# Hanya bila machine belum Running:
# podman machine start
podman info

# Konfigurasi gateway dari .env, tanpa menulis API key ke config.json.
.\.venv\Scripts\python.exe scripts/start_bifrost.py --prepare-only
$env:DISCOVERYBRIEF_MODE = 'local'
$env:RESEARCH_MODE = 'live'
$env:ENABLE_LIVE_RUNS = '1'
podman build --format docker -t discoverybrief-app .
podman compose --profile live up -d --no-build
podman compose --profile live ps
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Buka **http://127.0.0.1:8000/**. Health harus menunjukkan `live_enabled: true`.
Pilih perusahaan nyata dan domain resminya, waktu meeting yang akan datang, tujuan, bahasa,
serta RFP opsional. Buat brief, periksa bukti, kemudian unduh hasil. Membuat run live dapat
memakai kredit Tavily dan model berbayar. Contoh sintetis/replay tidak membuat panggilan baru.
Hasil `limited` atau `context_only` sah ketika bukti tidak cukup.

`.env` yang sudah ada berisi konfigurasi provider, primary dan fallback. Jangan menimpanya
dengan `.env.example`. MODEL_FALLBACK opsional; model `beam-1.0` pada konfigurasi saat ini
lulus tes routing terstruktur. Keduanya memakai provider yang sama, sehingga tidak menjamin
layanan tetap hidup jika provider mati. Sesudah mengubah `.env`, buat ulang konfigurasi
`--prepare-only` dan jalankan kembali perintah `compose up` di atas dengan `--force-recreate`.
Jangan menjalankan gateway native pada 8080 atau API native pada 8000 bersamaan dengan Compose.

Menghentikan layanan tanpa menghapus hasil:

```powershell
podman compose --profile live stop
```

Memulai kembali dengan konfigurasi live yang sama: ulangi tiga variabel `$env:` dan
`podman compose --profile live up -d --no-build` dari atas. Variabel tersebut hanya berlaku di terminal
PowerShell saat ini. Pada host ini builder Compose Windows gagal membaca direktori cache lokal; karena itu
gunakan `podman build` lalu Compose `--no-build` seperti di atas.
Hasil disimpan dalam named volume `discoverybrief_app_data`.
Hindari `down -v` bila ingin mempertahankan hasil. UI dan gateway hanya dibuka pada loopback.

## Demo tanpa API berbayar

```powershell
$env:DISCOVERYBRIEF_MODE = 'public_demo'
$env:RESEARCH_MODE = 'fixture'
$env:ENABLE_LIVE_RUNS = '0'
podman build --format docker -t discoverybrief-app .
podman compose up -d --no-build app
```

Buka alamat yang sama dan jalankan contoh sintetis. Mode ini hanya menyajikan replay yang
diizinkan. Untuk beralih ke live, ulangi perintah pada pilihan utama.

## Alternatif: Python dan Node native

Hentikan layanan Compose dahulu agar port tidak bentrok. Instalasi awal:

```powershell
uv sync --extra dev --extra pdf --frozen
uv run playwright install chromium
npm --prefix web ci
npm --prefix web run build
# Launcher sudah tersedia pada mesin ini; diperlukan untuk checkout baru:
# npm install --no-save --prefix data/bifrost-runtime @maximhq/bifrost@1.6.3
```

Terminal pertama, dari direktori aplikasi:

```powershell
.\.venv\Scripts\python.exe scripts/start_bifrost.py
```

Terminal kedua, dari direktori aplikasi:

```powershell
$env:DISCOVERYBRIEF_MODE = 'local'
$env:RESEARCH_MODE = 'live'
$env:ENABLE_LIVE_RUNS = '1'
$env:BIFROST_BASE_URL = 'http://127.0.0.1:8080/v1'
.\.venv\Scripts\python.exe -m uvicorn discoverybrief.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Buka http://127.0.0.1:8000/. Ctrl+C menghentikan masing-masing terminal. Konfigurasi
APP_DATA_DIR dari `.env` menyimpan run native; data ini terpisah dari named volume container.

## Diagnostik

- `podman info` harus berhasil sebelum menjalankan Compose.
- Port terpakai: `Get-NetTCPConnection -State Listen -LocalPort 8000,8080`.
- Log aplikasi: `podman compose logs --tail 100 app`; log gateway: layanan `bifrost`.
  Jangan membagikan konfigurasi/kredensial atau log konteks privat.
- Health live false: pastikan ketiga variabel live diatur sebelum `compose up`; kredensial
  provider/Tavily dan MODEL_PRIMARY harus tersedia dalam `.env`.
- Menjalankan pengujian fallback berbayar: set `$env:ENABLE_LIVE_TESTS='1'`, lalu
  `podman compose exec -e ENABLE_LIVE_TESTS=1 app python scripts/spike_fallback.py`.
- Uji container read-only otomatis: `python scripts/verify_container.py --base-url URL`;
  memerlukan Python dev dependencies, Chromium, dan server mode public_demo.
