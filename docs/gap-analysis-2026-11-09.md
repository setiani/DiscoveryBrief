# DiscoveryBrief — gap analysis implementasi

Tanggal audit: 9 November 2026, Asia/Jakarta. Audit terhadap snapshot lokal, bukan sertifikasi release.

## Kesimpulan

DiscoveryBrief sudah memiliki fondasi aplikasi yang berjalan offline dan jalur integrasi live eksperimental. Implementasi **belum memenuhi implementation plan**, terutama pada kontrak keluaran, kelengkapan evidence ledger, aturan waktu, kualitas hasil, evaluasi independen, dan reproduksi paket submission. Melanjutkan kode yang ada lebih tepat daripada membangun ulang.

Tidak ada persentase penyelesaian yang dapat dipertanggungjawabkan hanya dari jumlah file atau tes. Tidak ada milestone yang dinyatakan diterima oleh progress note. M0/M4/M5 sudah memiliki banyak implementasi; M2/M3 masih mengandung gap inti, sedangkan M6–M8 belum memiliki bukti acceptance lengkap.

## Ruang lingkup dan batas bukti

- Membaca AGENTS.md, MEMORY.md, README.md, spesifikasi 00–15 beserta contoh, progress/spike/evaluation notes, dan menelusuri modul backend, frontend, pengujian, runner evaluasi serta artefak hasil yang relevan.
- Menginventarisasi workspace dan memeriksa salinan plan: seluruh file pada `discoverybrief-plan/` identik secara byte dengan `discoverybrief/docs/plan/` pada audit ini. Perbedaan perilaku berasal dari implementasi, bukan dua versi plan yang berbeda.
- Dependency terpasang, cache, bytecode, database gateway, dan kredensial bukan dokumen rancangan yang perlu dibaca seluruh isinya. Tidak melakukan audit isi `.env` atau membongkar log privat gateway. Profil/proyek hackathon lama yang dirujuk memory tidak tersedia pada workspace ini; bukan dependency implementasi DiscoveryBrief.
- Tidak mengubah kode aplikasi atau menyalakan live mode. Tidak menjalankan panggilan Tavily/Bifrost berbayar. Bukti live dan frozen-research merupakan artefak tersimpan, bukan hasil panggilan baru atau pemeriksaan kebenaran web terkini.
- Audit ini membandingkan terhadap spesifikasi lokal; aturan kompetisi/deadline/harga eksternal tidak diverifikasi ulang dan tidak dinyatakan mutakhir.

## Verifikasi yang dijalankan ulang

Direktori kerja: `discoverybrief/`.

| Pemeriksaan | Hasil aktual |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q` | **63 passed**, 1 warning deprecation FastAPI/Starlette TestClient; 22,27 detik. Termasuk browser/PDF yang tersedia, tanpa skipped test pada run ini. |
| `npm --prefix web run build` | **Lulus**: pemeriksaan TypeScript dan Vite build. |
| `.\.venv\Scripts\ruff.exe check .` | **Lulus**. |
| `.\.venv\Scripts\ruff.exe format --check .` | **Gagal**: satu Python code block di `docs/plan/06-integrations-and-spikes.md`; 100 file lain sudah formatted. Ini gap housekeeping, bukan cacat runtime. |
| `npm --prefix web run test` | **Gagal**: Vitest tidak menemukan test file. Browser test Python tetap ada dan lulus; kegagalan ini tidak berarti seluruh frontend tidak diuji. |
| Fixture API, clock disimulasikan `2026-11-15T03:00:00Z` | **422 VALIDATION_ERROR**, meeting di luar horizon. |
| Registrasi route evidence | `/api/runs/{run_id}/evidence` **tidak ada**. |
| Missing Tavily usage, model usage tersedia | `tavily_credits_reported=null`, tetapi `usage_complete=true`; flag hanya mencakup model saat ini. |
| Planner memilih partnership + leadership dengan domain terisi | Kedua query tidak memiliki filter domain dan tidak ada official-news query. |

Perintah `uv run` awal tertahan akses cache global di luar sandbox. Pemeriksaan dilakukan menggunakan interpreter/tool pada `.venv` yang sudah ada. Ini tidak membuktikan fresh install atau `uv sync` gagal di lingkungan pengguna biasa. Tidak ada metadata Git pada root workspace; keberadaan repository publik di layanan eksternal tidak diperiksa.

## Yang sudah ada dan layak dipertahankan

- RunRequest Pydantic: batas input, aware datetime, offset versus IANA timezone, normalisasi Unicode/newline, public-context allowlist.
- Tavily Search/Extract adapter: pembatas panggilan, retry terbatas, normalisasi URL, pencocokan hasil Extract berdasarkan URL.
- Gateway-only Bifrost client dan structured submissions dengan satu schema repair; tidak ada direct-provider fallback tersembunyi.
- Lima konteks peran, pemeriksaan hash/quote literal, entailment requirement melalui Verifier, filtering premise melalui Auditor, neutral-question fallback.
- Ranking dan event clustering deterministik serta bounded selection.
- FastAPI, SQLite WAL, idempotency backend, bounded queue, cancel dan restart interruption tanpa paid auto-resume.
- Artifact manifest, validasi path/hash, HTML escaping, Markdown/JSON/PDF, PDF page-count check dan pruning.
- UI formulir, progress polling, evidence quotes, unduhan, fixture serta replay; browser smoke 390 px.
- Sepuluh kasus sintetis dan 20 output baseline/candidate frozen-research tersimpan; worksheet human review tersedia.
- Draft PPTX delapan slide dan demo script. Keberadaan file bukan acceptance presentasi final.

## Temuan terprioritas

### GAP-01 — Tinggi: fixture API bergantung pada tanggal kalender eksekusi

**Rencana:** fixture deterministik dapat direproduksi tanpa keys; replay mempertahankan tanggal asal. R13/G4, TC40–TC41, M8.

**Aktual:** `api/main.py` memberikan clock tetap 8 November hanya setelah job mulai; sebelumnya `RunStore.create()` tetap menjalankan `request.validate_horizon(now)` untuk fixture. Request kanonik memiliki meeting 12 November. Pada simulasi 15 November, POST fixture ditolak 422 sebelum workflow dimulai. CLI fixture/display sample/replay merupakan jalur berbeda dan tidak otomatis mengalami penolakan yang sama.

**Dampak:** tombol “Jalankan contoh offline” pada konfigurasi fixture dapat gagal saat demo/reproduksi setelah horizon meeting contoh berlalu, walaupun tes dengan FrozenClock 8 November lulus.

**Perbaikan:** pisahkan horizon live dari clock fixture yang repository-controlled; pertahankan label tanggal fixture. Tambahkan regression test API fixture pada tanggal jauh setelah tanggal contoh.

### GAP-02 — Tinggi: jalur pipeline tidak dapat menghasilkan ready

**Rencana:** >=3 event cluster eligible tanpa konflik/fallback material dapat `ready`; TC05 dan E01.

**Aktual:** `pipeline.py` baris 494 menetapkan `context_only` jika nol cluster, selain itu selalu `limited`. Komentar kode menyebut date precision/conflict/release gates belum lengkap. E01 tersimpan menghasilkan satu claim dan `limited`, sementara target `ready`.

**Dampak:** ada dua gap terpisah: quality derivation belum lengkap, dan E01 belum menghasilkan cakupan tiga event. Mengizinkan string `ready` saja tidak menyelesaikan recall atau correctness.

**Perbaikan:** selesaikan eligibility/uncertainty/conflict/fallback gates terlebih dahulu, lalu quality derivation. Uji tiga event valid serta tiga event dengan boundary ambiguity/konflik/auditor failure. Periksa alasan dua atom E01 tidak tampil melalui ledger lengkap.

### GAP-03 — Tinggi: temporal policy baru subset dari kontrak

**Rencana:** explicit event, original publication, provider-estimated basis, timestamp instan, partial boundary day, old-updated precedence, unknown/conflict; 03/04, TC06–TC09.

**Aktual:** `approve_claim()` memerlukan exact `date_quote` yang parse ke event date; `recent_date()` hanya membandingkan tanggal lokal. Belum ada jalur original-publication/provider-estimate sesuai kontrak, `published_at`/precision tidak dipertahankan, dan boundary warning tidak dibuat. Semua approved claim diberi `temporal_basis=explicit_event` oleh pipeline. Konflik membuat claim ditolak tetapi belum otomatis diubah menjadi unknown yang dapat diperiksa.

**Dampak:** bukti yang sebenarnya layak bisa terlalu banyak ditolak, sementara batas pengetahuan pada hari parsial belum diungkap. Tidak dapat membuktikan exact-instant filtering dari date-only implementation. Pembatasan quality saat ini konservatif, tetapi tidak menggantikan policy tersebut.

**Perbaikan:** typed date evidence/basis dan precision; deterministic predicate untuk instant/day; warning boundary; fallback publication/estimate sesuai plan; persist alasan konflik dan coverage notes. Jangan melonggarkan exact-quote gate untuk mengejar lebih banyak hasil.

### GAP-04 — Tinggi: evidence ledger dan penjelasan penolakan tidak lengkap

**Rencana:** R10, M2/M3/M4: sumber immutable, candidates/reviews/evidence/rejections, endpoint evidence, excluded findings, dan bukti yang sudah terkumpul tetap tersedia saat tahap berikut gagal.

**Aktual:** route evidence tidak terdaftar. Pipeline mengembalikan approved claims dan aggregate rejection counters, bukan seluruh candidates/reviews/item-level rejection reasons. `publish.py` membentuk `evidence.json` dari **bundle yang telah dipilih untuk satu halaman**; sources hanya metadata dan quotes dari item terpilih. Source text lengkap hanya ada dalam result sukses lokal, bukan ledger terstruktur yang dapat diinspeksi. Pada Analyst/provider failure, runner menyimpan safe error tetapi research/evidence in-memory tidak dicatat sebagai stage checkpoint.

**Dampak:** pengguna tidak dapat menjelaskan mengapa finding hilang atau memastikan hasil penolakan. Isi yang dipangkas PDF tidak tersedia lengkap pada evidence export walaupun overflow note mengarahkan pengguna ke detail lengkap. Pada run gagal, panggilan berbayar bisa terjadi tanpa evidence/usage record lengkap.

**Perbaikan:** persist source/candidate/review/approval/rejection per tahap, terpisah dari selected brief; endpoint evidence dan excluded findings; sanitasi download; checkpoint pada failed/cancelled runs. Detail lengkap tidak perlu dimasukkan ke halaman utama.

### GAP-05 — Tinggi: output contract berbeda dari spesifikasi normatif

**Rencana:** canonical Pydantic models `RunRecord`, `SourceRecord`, `ApprovedClaim`, `Brief`, `BriefBundle`, `RunEvent`, `Warning`, `RunError`, `RunMetrics`; kontrak 03 dan API 07.

**Aktual:** `schemas.py` terutama mendefinisikan input; banyak keluaran internal berupa dict. `build_bundle()` mengembalikan struktur datar, bukan `brief: Brief` plus ledger. Field seperti run_id, company_domain, meeting_timezone, window_start/end serta event date/basis/eligibility claim tidak terdapat pada bundle. Question/hypothesis/unknown IDs belum ditetapkan. Requirements kehilangan category/unspecified pada bundle. RunView hanya subset field dan `error_code`, warnings berupa string. Events tidak memiliki event_id/stage/metadata sesuai kontrak.

**Dampak:** UI dan API dapat saling cocok secara internal tetapi tetap tidak memenuhi rancangan; consumers/export kehilangan informasi attribution/time/grounding penting. Tes saat ini menerima struktur implementasi, sehingga tidak mendeteksi seluruh penyimpangan kontrak.

**Perbaikan:** implementasikan canonical output models dan validasi hasil lintas pipeline/API/export; jika kontrak memang ingin disederhanakan, perlukan keputusan eksplisit dan pembaruan semua dokumen terkait. Jangan menganggap struktur folder yang berbeda sebagai bug; masalahnya ialah field/invariant yang hilang.

### GAP-06 — Tinggi: Verifier masih menerima reasoning dari Analyst

**Rencana:** Verifier fresh-context tidak menerima Analyst reasoning; 03/05 dan M3.

**Aktual:** pipeline mengirim kandidat penuh melalui `"claims": candidates`; ClaimCandidate memuat `relevance_reason`. Field itu merupakan alasan dari Analyst, bukan bukti sumber. Pemisahan message context sudah ada, pemisahan input reasoning belum tuntas.

**Dampak:** berpotensi membias penilaian Verifier dan mengurangi independensi yang menjadi diferensiasi produk. Ini pelanggaran input boundary; bukan bukti bahwa suatu claim tertentu pasti salah.

**Perbaikan:** verifier-input allowlist berisi statement/ID/proposed evidence/date metadata yang diperlukan, tanpa relevance_reason atau desired answer. Assert boundary pada test payload.

### GAP-07 — Sedang–tinggi: research coverage belum sesuai strategi

**Rencana:** wajib satu official-domain query ketika domain diisi; supplemental query jika <3 usable extracted sources setelah dedup; dedup URL/content sebelum pemilihan; 04, M2.

**Aktual:** Planner dapat memilih dua enum tanpa `official_news`, dan kode tidak menambahkannya. Hanya query awal yang dijalankan; tidak ada supplemental pass. URL didedup, tetapi content duplicate baru ditandai sesudah ekstraksi dan tetap masuk daftar/prompt. Pemilihan ekstraksi mengambil sepuluh URL pertama, bukan hasil seleksi usable-source yang terjelaskan. Evidence prompt mengisi sumber awal sampai 24.000 karakter; dengan sumber 12.000 karakter, dua sumber panjang dapat menghabiskan seluruh konteks.

**Dampak:** coverage sempit dan budget/context dapat habis pada halaman duplikat atau sumber awal. Mekanisme ini konsisten dengan risiko recall rendah, tetapi belum terbukti sebagai satu-satunya penyebab E01 gagal.

**Perbaikan:** enforce official query di code; dedup/extract selection; bounded supplemental pass; pembagian evidence passages yang menjaga cakupan source; persist alasan seleksi/truncation. Tetap patuhi hard caps.

### GAP-08 — Tinggi: quality evaluation belum selesai

**Rencana:** R14/G2/M7: human-supported precision, entity/time/reference validity, RFP grounding, recall, question ratings, baseline overhead.

**Aktual:** 20 record `data/eval-v2/evaluation/` ada dengan satu implementation fingerprint. Sepuluh baseline parsed; candidate sesuai status/quality pada 9/10 kasus. Worksheet masih kosong. **9/10 bukan semantic accuracy.** Baseline/candidate belum memiliki independent judgments atau aggregate comparison. Raw outputs berada di ignored data, belum menjadi paket evaluasi publik yang sanitized.

**Dampak:** belum ada bukti pipeline lebih berguna/akurat dibanding satu summarization call; lebih banyak role juga berpotensi lebih mahal/lambat. Artefak live empat claims dari satu source bukan empat sumber independen dan bukan validasi kualitas.

**Perbaikan:** review kedua sistem terhadap labels yang telah disiapkan, catat denominator dan N/A; hitung usefulness/recall/precision dan overhead. Periksa fairness temporal: candidate menerima explicit historical cutoff/window, sedangkan baseline menerima request/evidence tanpa explicit clock_at/cutoff yang setara. Koreksi dan versioning sebelum perbandingan final bila berdampak. Jangan mengubah label agar E01 terlihat lulus.

### GAP-09 — Sedang–tinggi: observability, usage dan failure taxonomy belum lengkap

**Rencana:** per-call usage/correlation, prompt/schema/model versions, duration, error codes stabil, unknown coverage, ledgers; 03/05/06/07/12.

**Aktual:** ledger usage terutama in-memory aggregate; belum menyimpan per-role request ID, prompt hash, resolved model, latency dan usage durable. Failed pipeline tidak menyimpan ledger ke result. `usage_complete` hanya memeriksa model tokens: missing Tavily usage dapat tetap true. Normal API result belum mengisi duration_ms/fallbacks_observed. Banyak ValueError/RuntimeError termasuk budget/timeout dipetakan menjadi `PIPELINE_FAILED`, bukan error spesifik. Correlation header dan Retry-After antrean belum ada.

**Dampak:** sulit mendiagnosis kegagalan dan membandingkan operational cost; flag “complete” dapat disalahartikan. `estimated_model_cost=null` saat harga tidak tersedia **sudah benar**, bukan gap yang harus diisi angka tebakan.

**Perbaikan:** durable per-call ledger dan failure snapshot, pisahkan model/Tavily coverage, ukur duration, stable typed error mapping; null tetap dipertahankan untuk data yang tidak diketahui.

### GAP-10 — Sedang: lifecycle/storage dan deadline belum memenuhi kontrak penuh

**Aktual:** store sudah WAL/foreign keys/lock, transaksi state-event, cancel/restart/idempotency. Namun belum ada `PRAGMA user_version`, penolakan schema DB lebih baru, started_at/finished_at, dan ledger tables/ekuivalen checkpoint. Artifact manifest ditulis per file sebelum terminal transaction, bukan satu publication unit lengkap. Timeout 300 detik berada di `run_live()`, sedangkan rendering/PDF di `publish_artifacts()` berjalan setelah fungsi itu selesai; belum ada deadline yang meliputi keseluruhan worker run.

**Dampak:** recovery/schema compatibility dan batas waktu end-to-end belum terjamin sesuai 03/07/12. Tidak menyatakan artefak parsial saat ini terbuka: download tetap memeriksa completed status.

**Perbaikan:** schema versioning, lifecycle timestamps, stage checkpoints dan publication semantics; timeout mencakup rendering tanpa menghilangkan JSON/HTML fallback yang aman.

### GAP-11 — Sedang–tinggi: UX P0 masih belum lengkap

**Aktual:** UI memiliki pilihan bahasa laporan tetapi seluruh interface hardcoded Indonesia; timezone hardcoded Asia/Jakarta/+07:00. `needs_input` hanya generic error, tidak menampilkan candidate companies dari API. Evidence drawer tidak menampilkan tanggal event/basis, entity assessment, conflicts atau excluded findings. Tidak ada elapsed run time. Public-demo tetap menampilkan form pembuatan yang disabled, belum diganti sample-only view. Setiap submit menghasilkan UUID baru, tanpa mekanisme retry jaringan menggunakan ID yang sama. Tidak ada browser test yang membuktikan semua state/keyboard/error associations.

**Dampak:** R12 serta G3 belum lengkap. Backend idempotency yang benar belum otomatis melindungi retry pengguna pada frontend. Mode demo perlu penjelasan rekaman yang lebih eksplisit.

**Perbaikan:** static ID/EN dictionary dan UI language switch; timezone input atau scope yang disepakati; actionable ambiguity state; drawer berisi metadata lengkap; retained submission ID untuk retry; keyboard/error-state checks.

### GAP-12 — Sedang: ekspor dan layout perlu acceptance lebih luas

**Aktual:** JSON/MD/HTML/PDF ada dan tes tiga PDF sintetis lulus. Namun belum mencakup maximum-length ID+EN, nama/peran panjang, zero-news, long source URL/title dan error Chromium sebagai satu matrix acceptance. Pruning dapat membuang semua claims bila perlu; retained ledger lengkap pada detail export belum ada (GAP-04). Output HTML/MD/PDF belum membawa semua window/date precision/coverage metadata. Browser dan report menggunakan renderer berbeda, meskipun selected bundle dipakai bersama.

**Perbaikan:** regression matrix TC27–TC30; persist full accepted ledger terpisah; pastikan PDF/HTML/JSON selected content konsisten dan tidak kehilangan evidence detail. Tidak perlu mengganti renderer yang sudah aman hanya untuk menyeragamkan organisasi file.

### GAP-13 — Sedang: CLI dan clean setup belum sesuai paket rencana

**Aktual:** CLI hanya doctor offline dan run fixture yang mencetak `sample()`; bukan workflow terpersistensi yang sama dengan API. Belum ada run live, evaluate, build-demo sanitizer atau doctor --live. Script evaluasi terpisah sudah ada, tetapi tidak menggantikan seluruh kontrak CLI. Compose hanya service Bifrost dan mengandalkan config generated; Dockerfile/app service dan `scripts/dev.ps1` belum ada. Fresh environment belum diuji. README quickstart memakai extra dev, sementara Playwright/pypdf berada di extra pdf dan petunjuk install Chromium belum menjadi jalur lengkap reproduksi ekspor. Bifrost wrapper npm dan gateway transport memiliki nomor versi berbeda; hubungan versi perlu dijelaskan, bukan diasumsikan salah.

**Perbaikan:** satu service workflow untuk API/CLI, CLI equivalents atau documented deviation; fixture no-key setup dan optional PDF install yang lengkap; Compose app+Bifrost bila tetap bagian deliverable; fresh environment smoke. Docker/deployment publik bukan pengganti bukti aplikasi lokal yang benar.

### GAP-14 — Sedang: coverage acceptance belum dapat ditelusuri dari 63 tests

**Aktual:** tidak ada mapping eksekusi TC01–TC54 ke tes/assertion/artifact. Sejumlah helper dan happy path diuji baik, tetapi TC05, instant boundary, wrong-name/domain, auditor omissions, all outage paths, max input, queue across boundary, keyboard/i18n dan global offline socket enforcement belum memiliki bukti lengkap. Vitest tidak punya test files. Satu code-block formatting check gagal. Test browser menggunakan intercepted HTTP, sehingga bukan real API-to-browser live acceptance.

**Perbaikan:** traceability matrix actual pass/partial/missing; tambah tes untuk gap perilaku yang nyata dan boundary penting, lalu jalankan P0 release checks. Jangan menyamakan 63 pytest cases dengan 54 scenario acceptance atau menulis tes yang hanya mengabadikan hardcoded `limited`.

### GAP-15 — Tinggi untuk submission: paket final belum siap ditinjau sebagai release

**Aktual:** draft PPTX delapan slide ada dan struktur paket dapat dibaca; visual/final review belum terbukti. Demo hanya satu saved synthetic case, belum tiga ready/context_only/failure samples. LICENSE dan dependency attribution final belum ada. README belum mencakup seluruh architecture/setup/mode/retention/removal/limitations sesuai 13. Root README masih berkata aplikasi belum ada; plan/progress berisi snapshot historis sehingga mudah disalahbaca. Tidak ada bukti local Git metadata, URL public repo terverifikasi, clean checkout, final deck/screenshots, atau submission receipt pada workspace.

**Perbaikan:** selesaikan correctness dan evaluation lebih dahulu, lalu curate sanitized outputs/demo samples, license/attribution, README dan deck final. Verifikasi fresh checkout. Publication/submission dilakukan pada scope otorisasi yang sesuai; deployment/video bersifat opsional menurut plan lokal, sehingga ketiadaannya sendiri bukan alasan menyebut MVP gagal.

## Pemetaan milestone saat audit

| Milestone | Penilaian dari bukti |
|---|---|
| M0 Bootstrap/contracts | Scaffold dan input ada; canonical output contract belum lengkap. |
| M1 Spikes | Banyak limited live checks tersimpan; fallback disabled secara jujur; logging/usage dan target environment masih memiliki batas verifikasi. |
| M2 Research/evidence | Partial: official/supplemental/temporal/full ledger belum selesai. |
| M3 Role pipeline | Lima role terhubung; verifier input boundary, output schemas, quality/coverage belum memenuhi acceptance. |
| M4 API/storage/CLI | Banyak jalur dasar lulus; evidence endpoint/checkpoints/schema versioning/CLI equivalents belum lengkap. |
| M5 UI/exports | Form/brief/download/PDF berfungsi; i18n, ambiguity/evidence states, full layout acceptance belum selesai. |
| M6 Live/freeze | Live completed/limited tersimpan; semantic inspection dan release evidence belum lengkap. |
| M7 Evaluation/presentation | 20 outputs dan deck draft ada; human judging, baseline comparison dan presentasi final belum selesai. |
| M8 Reproduction/submission | Belum diterima; fixture-date regression menjadi blocker reproduksi nyata. |

## Urutan penyelesaian yang disarankan

1. **Reproduksi offline dan kontrak:** perbaiki fixture clock; tetapkan output models/invariants; buat acceptance traceability yang menyebut actual evidence.
2. **Evidence dan correctness:** durable stage ledger/detail endpoint, temporal policy, verifier input allowlist, identity/failure paths. Selesaikan uncertainty/conflict sebelum mengizinkan ready.
3. **Coverage dan quality:** official query/supplemental/dedup/passage allocation, periksa E01 recall, lalu quality derivation dengan regression tests.
4. **Product workflow:** i18n/timezone/ambiguity/evidence UX, usage/error trace, end-to-end deadline, konsistensi ekspor serta full-layout matrix.
5. **Evaluation:** review output yang ada; setelah perubahan perilaku material, gunakan dataset/version/fingerprint dan run terpisah yang tidak menimpa artefak lama. Laporkan hasil buruk sekalipun; jangan klaim target tercapai tanpa denominator.
6. **Release package:** fresh setup, sanitized samples/results, license/README, final PPT dan tindakan publikasi/submission yang memang diotorisasi.

Fallback provider yang belum terbukti boleh tetap disabled dan diungkap sebagai keterbatasan. CRM, calendar, PDF upload parser, benchmark platform tambahan dan deployment live publik tidak diperlukan untuk menutup gap MVP ini.
