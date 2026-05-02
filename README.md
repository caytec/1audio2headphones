# 1Audio2Headphones

**Słuchaj jednego dźwięku z komputera na dwóch parach słuchawek jednocześnie.**
Bez instalacji wirtualnych kabli, bez Voicemeeter, bez sterowników, bez konfiguracji.

[![Pobierz najnowszą wersję](https://img.shields.io/badge/Pobierz-1Audio2Headphones.exe-4a9eff?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/caytec/1audio2headphones/releases/latest/download/1Audio2Headphones.exe)
[![Landing page](https://img.shields.io/badge/Landing-caytec.github.io%2F1audio2headphones-c084fc?style=for-the-badge)](https://caytec.github.io/1audio2headphones/)

## Czym jest

Lekka aplikacja Windows (jeden plik `.exe`, ~28 MB) która kopiuje dźwięk z jednej pary słuchawek do drugiej w czasie rzeczywistym. Idealna do wspólnego oglądania filmu, słuchania muzyki we dwoje albo grania couch co-op.

## Jak to działa

Aplikacja korzysta z wbudowanego w Windows mechanizmu **WASAPI Loopback**. YouTube, Spotify, gra czy cokolwiek innego gra normalnie do Twoich głównych słuchawek (np. C27 przez Bluetooth). Aplikacja w tle przechwytuje ten sygnał i wysyła kopię do drugiej pary (np. NCX po kablu).

## Użycie

1. Pobierz `1Audio2Headphones.exe` z [najnowszego release](https://github.com/caytec/1audio2headphones/releases/latest)
2. W Windows ustaw domyślne wyjście dźwięku na pierwszą parę słuchawek
3. Uruchom aplikację, wybierz **Pierwsze słuchawki** (te z Windows default) i **Drugie słuchawki** (kopia)
4. Kliknij URUCHOM

## Wymagania

- Windows 10 lub 11
- Co najmniej dwa urządzenia odtwarzające audio podłączone do komputera

## Pobieranie

Pobierz skompilowany plik `.exe` bezpośrednio z sekcji [Releases](https://github.com/caytec/1audio2headphones/releases/latest).

**Uwaga:** To repozytorium zawiera wyłącznie skompilowane pliki binarne. Kod źródłowy nie jest publicznie dostępny.

## Wspomóż projekt

Jeśli aplikacja Ci się podoba i chciałbyś wesprzeć jej rozwój, możesz wnieść dowolną wpłatę:

- **[Ko-Fi ☕](https://ko-fi.com/F1F51O3A4A)** — szybka donacja bez konfiguracji
- **PayPal** — dostępne bezpośrednio w aplikacji

Wszystkie wpłaty pomagają finansować rozwój nowych funkcji, poprawki błędów i wsparcie dla użytkowników. Dziękujemy! 💙

## Architektura

- **Język:** Python 3.12
- **GUI:** customtkinter (ciemny motyw)
- **Audio:** soundcard (WASAPI Loopback)
- **Build:** PyInstaller (one-file)

## Licencja

MIT

## Autor

[Kajetan Kupaj](https://caytec.github.io)
