-- SQLite schema untuk Sistem Informasi Absensi Guru
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS admins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nama TEXT NOT NULL,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS guru (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nip TEXT NOT NULL UNIQUE,
  nama TEXT NOT NULL,
  jenis_kelamin TEXT,
  tempat_lahir TEXT,
  tanggal_lahir TEXT,
  pendidikan TEXT,
  jabatan TEXT,
  mata_pelajaran TEXT,
  no_hp TEXT,
  email TEXT,
  alamat TEXT,
  status_kepegawaian TEXT,
  foto TEXT,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS absensi (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guru_id INTEGER NOT NULL,
  tanggal TEXT NOT NULL,
  jam_masuk TEXT,
  jam_pulang TEXT,
  status TEXT NOT NULL,
  terlambat INTEGER DEFAULT 0,
  keterangan TEXT,
  validated INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (guru_id) REFERENCES guru (id) ON DELETE CASCADE,
  UNIQUE (guru_id, tanggal)
);

CREATE TABLE IF NOT EXISTS profil_madrasah (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nama_madrasah TEXT NOT NULL,
  nsm TEXT,
  npsn TEXT,
  alamat TEXT,
  telepon TEXT,
  email TEXT,
  kepala_madrasah TEXT,
  logo_madrasah TEXT,
  logo_kemenag TEXT,
  ttd_kepala TEXT,
  tahun_ajaran TEXT DEFAULT '2025/2026',
  semester_aktif TEXT DEFAULT 'Genap',
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Seed: pastikan ada 1 profil madrasah (id=1)
INSERT INTO profil_madrasah (
  id, nama_madrasah, alamat, kepala_madrasah, logo_madrasah, logo_kemenag
) VALUES (
  1,
  'MI AL-KHAIRIYAH BADAMUSALAM',
  'Badamusalam, Sawah Luhur, Kec. Kasemen, Kota Serang, Banten 42191',
  'Sugiarto S.E.',
  'logo/logo_madrasah.png',
  'logo/logo_kemenag.png'
)
ON CONFLICT(id) DO NOTHING;

-- Seed: admin default (username: admin, password: admin123)
-- Password hash dibuat oleh aplikasi saat pertama kali dijalankan bila belum ada.
