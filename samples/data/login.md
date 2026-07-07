# Module: Login - OrangeHRM Demo
URL Target: https://opensource-demo.orangehrmlive.com/web/index.php/auth/login
Modul: Authentication / Login
Tanggal Dibuat: 01 Juli 2026
Author: Markrow
Tiket Story Dev: BSMPD-2694
Tiket Test Case: BSMPD-2814
Platform: Web
Env: Staging
Username: Admin
Password: admin123

## Scenario: 1-User berhasil login dengan username dan password yang benar
**Priority**: P1
**TC Type**: Positive
**Test Data**: role=admin; hasil=berhasil

**Precondition**:
- Halaman login terbuka
- User memiliki akun valid (username: Admin, password: admin123)

**Test Steps**:
1. Buka halaman [Login OrangeHRM](https://opensource-demo.orangehrmlive.com/web/index.php/auth/login)
2. Masukkan username: "Admin" pada field Username
3. Masukkan password: "admin123" pada field Password
4. Klik tombol "Login"

**Expected Result**:
1. User berhasil login dan diarahkan ke halaman Dashboard
2. Muncul notifikasi atau header yang menyapa user (misal: "PIM" menu muncul di sidebar)

## Scenario: 2-User gagal login karena field username tidak diisi
**Priority**: P2
**TC Type**: Negative


**Test Steps**:
Buka halaman login
Biarkan field username kosong
Masukkan password: "admin123" pada field Password
Klik tombol "Login"

**Expected Result**:
Login gagal dan user tetap di halaman login
Muncul pesan error validasi "Required" tepat di bawah field Username

## Scenario: User gagal login karena field password tidak diisi
**Priority**: P2
**TC Type**: Negative


**Test Steps**:
1. Buka halaman login
2. Masukkan username: "Admin" pada field Username
3. Biarkan field password kosong
4. Klik tombol "Login"

**Expected Result**:
- Login gagal dan user tetap di halaman login
- Muncul pesan error validasi "Required" tepat di bawah field Password

## Scenario: User gagal login karena kedua field tidak diisi sama sekali
**Priority**: P2
**TC Type**: Negative

**Precondition**:
Halaman login terbuka

**Test Steps**:
1. Buka halaman login
2. Biarkan field username kosong
3. Biarkan field password kosong
4. Klik tombol "Login"

**Expected Result**:
Login gagal dan user tetap di halaman login
Muncul pesan error "Required" pada field Username dan "Required" pada field Password

## Scenario: User gagal login karena memasukkan username yang salah
**Priority**: P2
**TC Type**: Negative

**Precondition**:
- Halaman login terbuka
- User mengetahui username yang invalid

**Test Steps**:
1. Buka halaman login
2. Masukkan username: "InvalidUser123" pada field Username
3. Masukkan password: "admin123" pada field Password
4. Klik tombol "Login"

**Expected Result**:
Login gagal dan user tetap di halaman login
Muncul pesan error di bagian atas form: "Invalid credentials"