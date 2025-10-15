# prep-pi: Server für Offline Informationen

prep-pi ist ein Raspberry-Pi (Zero) Webserver, der über einen WLAN-Hotspot Informationen lokal bereitstellt. Die Informationen sind auch bei ausgefallenem Internet noch verfügbar und mithilfe eines Solarpanels sogar bei Stromausfall.

## Einleitung
Netzwerke sind im urbanen Leben notwendig, aber auch fehleranfällig. Wenn große infrastrukturelle Netzwerke wie Strom, Wasser, Internet ausfallen, merken wir das sofort:  nichts geht mehr.
Mit dem prep-pi lassen sich in einem solchen Fall Informationen bereitstellen. Das Projekt ist zum Nachmachen und Nachbauen konzipiert.

## Features
Der prep-pi ist eine Sammlung an Skripten die dabei helfen einen Offline-Server zur Verfügung zu stellen. Das Projekt besteht aus zwei Teilen:
1. Setup-Skripte für den Pi

    Mithilfe diser Skripte wird der Pi ganz automatisch aufgesetzt um einen WLAN-Hotspot zur Verfügung zu stellen. Wird eine Verbindung zu diesem WLAN-Hotspot hergestellt öffnet das verbundene Gerät automatisch die "Login-Seite" (Captive Portal). Statt einer Seite zum Login kann hier aber jede beliebige lokale Seite angezeigt werden.

2. Statische Website mittels Hugo

    Teil 1 stellt die Infrastruktur zum Anzeigen einer Website zur Verfügung. In diesem Projekt haben wir eine einfache Website mit Hugo kreiert, diese kann Bilder, PDFs, Videos und andere Formate zur Verfügung stellen und unterstützt deutsche und englische Beschreibungstexte, auch in einfacher Sprache. 
    Neben unserer Seite mit eigenem Content kann aber auch eine gänzlich andere Seite angezeigt werden.

## Was du brauchst
    Um mit den notwendigen Tools zu arbeiten musst du eventuell einige Programme installieren und wissen was ein SSH-Key ist.

- Raspberry Pi Zero (W) + Zubehör

  - microSD
  - Micro-USB zu Ethernet Adapter
  - (optional) _mini_-HDMI

    *Die Installation und Konfiguration ist nur auf einem Pi Zero W getestet, kann grundsätztlich aber auch auf anderen Modellen funktionieren. Der Pi Zero ist aber sehr stromsparend.*


- Solarpanel (optional)

    *Du musst den Pi natürlich nicht an einem Solar Panel verwenden, nur dann ist er aber dauerhaft ohne Stromnetz nutzbar. Für kurze Zeiten kann aber auch eine Powerbank ausreichen.*


## Installation

1. Clone dieses git-repo auf deinen Computer
2. Dietpi auf microSD Karte flashen

    Lade das aktuelle [dietpi](https://dietpi.com) Image für den Raspberry Pi Zero herunter. Dises musst du nun auf die SD Karte flashen, hierfür kannst du z.B. balenaEtcher nutzen.

3. Setup Dateien anpassen
   1. SSH-Key hinzufügen: Öffne `install/dietpi.txt` und füge bei `AUTO_SETUP_SSH_PUBKEY` deinen Public Key ein. Nur so kannst du später auf den Pi zugreifen.
   2. Passwort ändern: Öffne `install/dietpi.txt` und ändere bei `AUTO_SETUP_GLOBAL_PASSWORD` das Passwort.
   3. WLAN Namen ändern: Öffne `install/Automation_Custom_Script.sh` und bearbeite bei `SSID` den Namen.

4. Setup Dateien auf microSD austauschen

    Im Unterordner `install` dieses Projekts findest du drei Dateien `dietpi.txt`, `Automation_Custom_Script.sh` und `Automation_Custom_PreScript.sh`. Diese Dateien musst du auf die microSD Karte in den Ordner `boot` kopieren, bzw. ersetzen. Es kann sein das die microSD als zwei Geräte auftaucht, wähle einfach das in dem der `boot` Ordner existiert. Es kann sein, dass du hierfür Administrator-Rechte brauchst.

5. Pi starten
    
    Stecke die microSD in den Pi, schließe Ethernet (unbedingt notwendig, ein Setup über WLAN ist nicht möglich da dieses als Hotspot konfiguriert wird) und falls du hast HDMI Kabel an, *dann* den Strom. Der Pi startet automatisch die Installation, das dauert ungefähr 20 Minuten.

6. Pi neustarten. Verbinde dich über ssh und starte den Pi neu mit `sudo reboot`.
7. Website deployen

## Website mit Hugo

[Hugo](https://gohugo.io/) ist ein Tool das einfache Templates benutzt um statische Webseiten zu erzeugen. Wir haben ein einfaches Template zur Verwendung erstellt.

### Content erstellen oder aktualisieren
    Du musst Hugo installiert haben.
#### Automatisch
Du musst Python installiert haben um die automatischen Skripte zu benutzen.

Das automatische Skript erstellt für deine zu teilenden Daten automatisch die notwendigen Dateien in die du Beschreibungen hinzufügen kannst. Für gängige Dateitypen versucht das Skript außerdem automatisch Vorschaubilder zu erzeugen. Die Dateien werden am Ende automatisch aus dem Ordner entfernt.

1. Kopiere Dateien die du Teilen möchtest in `new-content`
2. Führe `new_resources.py` durch doppelklicken oder im Terminal aus
3. In `hugo-page/content` wurden automatisch `*.md` Dateien für jede Datei aus `new-content` erstellt. Du kannst die Dateien in einem Texteditor öffnen und an den vorgesehenen Stellen Beschreibungstexte einfügen. Du kannst dort auch den Titel oder das Vorschaubild (Dateien dafür müssen in `hugo-page/static/images` liegen) ändern. Du kannst auch den Dateinamen ändern.
4. Nun müssen diese Dateien noch auf den Pi um dort als Website angezeigt werden zu können. Verbinde dich dazu mit dem WLAN des Pi und führe dann `deploy.py` aus.

#### Manuell

Im Terminal kannst du auch selbst neue Dateien erstellen mit `hugo new --kind [blog|resource] content/<lang>/[blog|resources]/<filename.md>`, oder du duplizierst einfach eine der existierenden Dateien und änderst Namen und Inhalt.

Dateien zum herunterladen müssen in `hugo-page/content/static/downloads` und Bilder für die Vorschau in `hugo-page/content/static/images`.

Content auf Pi aktualisieren:
1. Wechsle in `hugo-page`
2. Lösche eventuell existierenden `public` Ordner. (Hugo überschreibt nur Dateien, veraltete könnten sonst liegen bleiben)
3. Führe hugo [--minify] aus um die statischen Dateien zu generieren.
4. Schalte das Dateisystem des PIs auf read-write indem du auf dem pi `dietpi-drive_manager` ausführst 
5. Ersetze auf dem Pi `/var/www/public` mit dem vorher generierten `public` Ordner.
6. Schalte das Dateisystem des PIs wieder auf read-only indem du auf dem pi `dietpi-drive_manager` ausführst. Wähle als directory `/` dann die option für read-only. Der drive_manager fragt nach erfolgreichem umschalten ob du das Dateisystem in den read-write Modus setzen willst, breche dies ab.


## Einige Details

- Wir nutzen dietpi weil es ein System optimiert auf Performance und somit auch Akkulaufzeit ist. Es laufen nur die nötigsten Dienste. Außerdem erlaubt dietpi in einem automatischen Setup das aufsetzen benötigter Software.
- Das Setup setzt mithilfe von hostapd einen WLAN Hotspot auf, mit dnsmasq als dhcp Server. 
- IPV6 ist deaktiviert um jegliche Weiterleitungen zu vereinfachen.
- iptables sind eingestellt um jeden http traffic auf den Pi umzuleiten. Dieser traffic wird von lighttpd beantwortet. Dieser erwartet eine `index.html` in `/var/www/public`. In diesem Projekt legen wir dort eine mit Hugo erstellte Seite ab, jegliche andere statische Seite würde aber auch funktionieren. 
- Um als Captive-Portal zu funktionieren werden anfragen auf die lokale Domain weitergeleitet. Für Apple Geräte wird bei einer Anfrage für das Captive Portal keine Weiterleitung sondern einfach direkt die Webseite zurückgegeben.

## Lizenz

Copyright © 2025 Hugo Dünger -  ZKM | Zentrum für Kunst und Medien Karlsruhe

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für weitere Informationen.

### Ausnahmen

Die Schriftarten im Ordner `hugo-page/static/fonts` unterliegen eigenen Lizenzen:
- **IBMPlexMono**: SIL Open Font License - siehe `hugo-page/static/fonts/OFL.txt