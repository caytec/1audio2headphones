# submit-pad.ps1
# Automatycznie wysyla plik PAD na wszystkie portale z darmowym oprogramowaniem
# Uzycie: .\submit-pad.ps1

$PAD_URL = "https://raw.githubusercontent.com/caytec/1audio2headphones/main/pad/1audio2headphones.xml"
$LOG_FILE = "$PSScriptRoot\submit-log.txt"

# Lista portali akceptujacych PAD file
$PAD_PORTALS = @(
    # Tier 1 - duze portale
    @{ Name="Softpedia";    Url="https://www.softpedia.com/user/submit.shtml" }
    @{ Name="SnapFiles";    Url="https://www.snapfiles.com/submitapp.html" }
    @{ Name="Download3k";   Url="https://www.download3k.com/SubmitSoftware.html" }
    @{ Name="Apponic";      Url="https://apponic.com/submit" }
    @{ Name="SoftSea";      Url="https://www.softsea.com/submit.html" }
    @{ Name="FreewareFiles";Url="https://www.freewarefiles.com/submit.php" }
    @{ Name="SoftLookup";   Url="https://www.softlookup.com/submit.asp" }
    @{ Name="Tucows";       Url="https://www.tucows.com/submit" }
    @{ Name="Softonic";     Url="https://en.softonic.com/about/add-software" }

    # Tier 2
    @{ Name="WinSite";      Url="https://www.winsite.com/submit" }
    @{ Name="Nonags";       Url="https://www.nonags.com/submit.html" }
    @{ Name="SoftArea51";   Url="https://www.softarea51.com/submit.php" }
    @{ Name="Filepuma";     Url="https://www.filepuma.com/upload/" }
    @{ Name="FileBuzz";     Url="https://www.filebuzz.com/submit.html" }
    @{ Name="SharewareOnSale"; Url="https://sharewareonsale.com/submit" }
)

# Lista portali do recznego zgloszenia (nie akceptuja PAD bezposrednio)
$MANUAL_PORTALS = @(
    @{ Name="FileHippo";    Url="https://filehippo.com/submit-software/";     Note="Formularz web, wklej URL do PAD: $PAD_URL" }
    @{ Name="MajorGeeks";   Url="mailto:submissions@majorgeeks.com";          Note="Wyslij email z danymi z PAD" }
    @{ Name="SourceForge";  Url="https://sourceforge.net/user/registration/"; Note="Zaloz konto, stwórz projekt, wgraj exe" }
    @{ Name="AlternativeTo";Url="https://alternativeto.net/add/";             Note="Dodaj wpis jako alternatywa dla Voicemeeter" }
    @{ Name="Programy.pl";  Url="https://www.programy.pl/dodaj-program.html"; Note="Polski portal - wypelnij formularz" }
    @{ Name="Winget";       Url="https://github.com/microsoft/winget-pkgs";   Note="Automatyczny PR - uzyj GitHub Actions (juz skonfigurowane)" }
    @{ Name="Chocolatey";   Url="https://push.chocolatey.org/";               Note="Wymaga konta i paczki NuGet" }
)

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Message"
    Write-Host $line -ForegroundColor $Color
    Add-Content -Path $LOG_FILE -Value $line
}

function Submit-PadToPortal {
    param($Portal)
    Write-Log "Wysylanie do: $($Portal.Name)..." "Cyan"
    try {
        $body = @{ pad_url = $PAD_URL; url = $PAD_URL; padurl = $PAD_URL }
        $response = Invoke-WebRequest -Uri $Portal.Url -Method POST -Body $body `
            -TimeoutSec 15 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -lt 400) {
            Write-Log "  OK: $($Portal.Name) (HTTP $($response.StatusCode))" "Green"
            return $true
        } else {
            Write-Log "  BLAD HTTP: $($Portal.Name) ($($response.StatusCode))" "Yellow"
            return $false
        }
    } catch {
        Write-Log "  NIEUDANE: $($Portal.Name) - $($_.Exception.Message)" "Yellow"
        return $false
    }
}

# --- START ---
Write-Log "=" * 60
Write-Log "  1Audio2Headphones - Automatyczne zgłoszenie do portali"
Write-Log "  PAD URL: $PAD_URL"
Write-Log "=" * 60

$success = 0
$fail = 0

Write-Log "`n[AUTOMATYCZNE - portale PAD]" "Magenta"
foreach ($portal in $PAD_PORTALS) {
    $ok = Submit-PadToPortal -Portal $portal
    if ($ok) { $success++ } else { $fail++ }
    Start-Sleep -Milliseconds 500
}

Write-Log "`n[RECZNE - otwieranie przegladarki]" "Magenta"
foreach ($portal in $MANUAL_PORTALS) {
    Write-Log "  -> $($portal.Name): $($portal.Note)" "Yellow"
    Write-Log "     URL: $($portal.Url)" "DarkYellow"
    Start-Process $portal.Url
    Start-Sleep -Seconds 2
}

Write-Log "`n"
Write-Log "=" * 60
Write-Log "  WYNIKI:"
Write-Log "  Automatyczne wysłanie: $success ok, $fail nieudane" "$(if ($fail -eq 0) { 'Green' } else { 'Yellow' })"
Write-Log "  Reczne (otwarte w przegladarce): $($MANUAL_PORTALS.Count)" "Cyan"
Write-Log "  Log zapisany do: $LOG_FILE"
Write-Log "=" * 60
