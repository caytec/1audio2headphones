# 📦 Lista rejestracji na portale z oprogramowaniem

Ten dokument zawiera instrukcje krok po kroku do zarejestrowania **1Audio2Headphones** na największych polskich i międzynarodowych portalach z darmowym oprogramowaniem.

---

## 🌟 Priorytet 1 — Automatyczne package managery (najlepsze!)

### 1. **Chocolatey** (Windows Package Manager)
- **URL:** https://chocolatey.org/packages/1audio2headphones
- **Dlaczego:** Miliony użytkowników, automatyczne aktualizacje
- **Status:** ❌ Wymaga ręcznej rejestracji

**Instrukcja:**
1. Zajetrz na https://chocolatey.org/account/register
2. Stwórz konto (możesz użyć GitHuba)
3. Przejdź do https://chocolatey.org/packages/upload
4. Zaloguj się
5. **Plik:** Pobierz niezależny `1Audio2Headphones.exe` z Releases
6. Wgraj do Chocolatey

---

### 2. **Winget** (Microsoft Store — rekomendowany!)
- **URL:** https://github.com/microsoft/winget-pkgs
- **Dlaczego:** Oficjalny Windows package manager od Microsoftu
- **Status:** ✅ Można zrobić automatycznie przez GitHub Actions

**Instrukcja:**
1. Przejdź do https://github.com/microsoft/winget-pkgs
2. Kliknij **Fork**
3. W swoim forku stwórz PR z nowym plikiem:
   ```
   manifests/c/caytec/1Audio2Headphones/1.0.0/caytec.1Audio2Headphones.yaml
   ```
4. Zawartość:
   ```yaml
   PackageIdentifier: caytec.1Audio2Headphones
   PackageVersion: 1.0.0
   DisplayName: 1Audio2Headphones
   Publisher: Kajetan Kupaj
   License: MIT
   ShortDescription: Stream one audio source to two headphone outputs simultaneously
   Description: One-file Windows app that copies audio from one pair of headphones to another in real-time. Zero installation, zero virtual cables, zero drivers.
   Installers:
   - Architecture: x64
     InstallerUrl: https://github.com/caytec/1audio2headphones/releases/download/v1.0.0/1Audio2Headphones.exe
     InstallerSha256: [WYLICZ SKRYPTEM PONIŻEJ]
     InstallerType: portable
   ManifestVersion: 1.4.0
   ```

**Wylicz SHA256 pliku .exe:**
```powershell
$file = "C:\path\to\1Audio2Headphones.exe"
(Get-FileHash -Path $file -Algorithm SHA256).Hash
```

---

## ⭐ Priorytet 2 — Wielkie portale międzynarodowe

### 3. **Softpedia** (wielomilionowa baza)
- **URL:** https://softpedia.com
- **Status:** ❌ Wymaga formularza

**Instrukcja:**
1. Przejdź do https://softpedia.com/submit-software
2. Wypełnij formularz:
   - **Nazwa:** 1Audio2Headphones
   - **Wersja:** 1.0.0
   - **Kategoria:** Audio
   - **Podkategoria:** Audio Utilities
   - **Opis:** Stream one audio source to two headphone outputs simultaneously. Zero installation, zero virtual cables, zero configuration.
   - **URL pobierania:** https://github.com/caytec/1audio2headphones/releases/latest/download/1Audio2Headphones.exe
   - **Licencja:** MIT
   - **OS:** Windows 10, Windows 11
   - **Autor:** Kajetan Kupaj
   - **Email:** coopaisolutions@gmail.com
   - **Website:** https://caytec.github.io/1audio2headphones

---

### 4. **FileHippo** (popularne)
- **URL:** https://filehippo.com
- **Status:** ❌ Wymaga formularza

**Instrukcja:**
1. Przejdź do https://filehippo.com/submit-software/
2. Wypełnij dane (analogicznie jak Softpedia)
3. Paczekaj na zatwierdzenie (24-48h)

---

### 5. **Major Geeks** (duże społeczności)
- **URL:** https://majorgeeks.com
- **Status:** ❌ Wymaga maila

**Instrukcja:**
1. Wyślij email na: submissions@majorgeeks.com
2. Temat: `New Software Submission: 1Audio2Headphones`
3. Zawartość:
   ```
   Software Name: 1Audio2Headphones
   Version: 1.0.0
   Description: Stream one audio source to two headphone outputs simultaneously. 
   Zero installation, zero virtual cables, zero configuration.
   
   Download URL: https://github.com/caytec/1audio2headphones/releases/latest/download/1Audio2Headphones.exe
   Website: https://caytec.github.io/1audio2headphones
   License: MIT
   
   Author: Kajetan Kupaj
   Contact: coopaisolutions@gmail.com
   ```

---

### 6. **SourceForge** (popularne wśród użytkowników)
- **URL:** https://sourceforge.net
- **Status:** ❌ Wymaga rejestracji i konfiguracji

**Instrukcja:**
1. Zarejestruj się na https://sourceforge.net
2. Przejdź do https://sourceforge.net/user/registration/
3. Stwórz nowy projekt: https://sourceforge.net/user/caytec/admin/
4. Wgraj `.exe` do "Files" sekcji
5. Ustaw jako default download

---

## 🇵🇱 Priorytet 3 — Portale polskie

### 7. **Programy.pl** (polski katalog)
- **URL:** https://www.programy.pl
- **Status:** ❌ Wymaga formularza

**Instrukcja:**
1. Przejdź do https://www.programy.pl/dodaj-program.html
2. Wypełnij dane:
   - **Nazwa programu:** 1Audio2Headphones
   - **Opis:** Aplikacja do słuchania jednego strumienia audio na dwóch parach słuchawek jednocześnie. Bez instalacji, bez wirtualnych kabli, bez konfiguracji.
   - **Link do pobrania:** https://github.com/caytec/1audio2headphones/releases/latest/download/1Audio2Headphones.exe
   - **Kategoria:** Audio
   - **Licencja:** MIT
   - **Wymagania:** Windows 10, Windows 11

---

### 8. **AlternativeTo.net**
- **URL:** https://alternativeto.net
- **Status:** ❌ Wymaga zalogowania

**Instrukcja:**
1. Zarejestruj się na https://alternativeto.net/register/
2. Przejdź do https://alternativeto.net/add/software/
3. Dodaj wpis:
   - **Nazwa:** 1Audio2Headphones
   - **Opis:** Stream one audio source to two headphone outputs simultaneously
   - **Kategoria:** Voicemeeter alternatives
   - **Link:** https://caytec.github.io/1audio2headphones

---

## 📊 Stan rejestracji

| Portal | Status | Trudność | Priorytet |
|--------|--------|----------|-----------|
| Winget | ⏳ Do zrobienia | Średnia | 🌟🌟🌟 |
| Chocolatey | ⏳ Do zrobienia | Łatwa | 🌟🌟🌟 |
| Softpedia | ⏳ Do zrobienia | Łatwa | 🌟🌟 |
| FileHippo | ⏳ Do zrobienia | Łatwa | 🌟🌟 |
| Major Geeks | ⏳ Do zrobienia | Łatwa | 🌟🌟 |
| SourceForge | ⏳ Do zrobienia | Średnia | 🌟 |
| Programy.pl | ⏳ Do zrobienia | Łatwa | 🌟🌟 |
| AlternativeTo | ⏳ Do zrobienia | Łatwa | 🌟 |

---

## 📝 Dane do użytku

**Dane aplikacji (kopiuj-wklej):**
```
Nazwa: 1Audio2Headphones
Wersja: 1.0.0
Licencja: MIT
OS: Windows 10, 11 (64-bit)
Rozmiar: ~28 MB
URL: https://github.com/caytec/1audio2headphones
Pobieranie: https://github.com/caytec/1audio2headphones/releases/latest/download/1Audio2Headphones.exe
Autor: Kajetan Kupaj
Email: coopaisolutions@gmail.com
Landing Page: https://caytec.github.io/1audio2headphones
```

**Opis długi (angielski):**
```
1Audio2Headphones is a lightweight Windows application that streams one audio source to two headphone outputs simultaneously. Perfect for watching movies together, couch co-op gaming, or sharing music without speakers.

Key Features:
- Zero installation — single .exe file
- Zero configuration — works immediately
- Works with any combination: Bluetooth + cable, two USB, headphones + speakers
- Low latency (10 ms) using native Windows WASAPI Loopback
- Independent volume controls for each pair
- Real-time audio level indicator
- Saves your device settings

No virtual cables, no Voicemeeter, no drivers needed.
```

**Opis krótki (polski):**
```
Aplikacja Windows do słuchania jednego strumienia audio na dwóch parach słuchawek jednocześnie. Bez instalacji, bez wirtualnych kabli, bez konfiguracji.
```

---

## ✅ Po rejestracji

1. Dodaj do README.md sekcję "Available on" z logami portali
2. Wyślij update PR z informacją o rejestracjach
3. Monitoruj strony w ciągu 24-48h czy aplikacja się pojawiła
4. Dodaj nowe portale do routine check-upów (co miesiąc)

---

**Ostatnia aktualizacja:** 2 maja 2026
**Status:** Czekam na Twoją działalność! 🚀
