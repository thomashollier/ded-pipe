## In power shell:

Invoke-WebRequest -Uri "https://salsa.debian.org/debian/WSL/-/raw/master/x64/install.tar.gz" -OutFile "$env:USERPROFILE\Downloads\debian-wsl.tar.gz"
New-Item -ItemType Directory -Path "C:\WSL_Ed\Ed_Debian" -Force
wsl --import Ed_Debian C:\WSL_Ed\Ed_Debian "$env:USERPROFILE\Downloads\debian-wsl.tar.gz" --version 2
wsl -d Ed_Debian -u root bash -c "apt update && apt upgrade -y && apt install sudo -y && useradd -m -s /bin/bash dedusr && echo 'dedusr:dedusrpw' | chpasswd && usermod -aG sudo dedusr && echo '[user]' > /etc/wsl.conf && echo 'default=dedusr ' >> /etc/wsl.conf"
wsl --shutdown
wsl -d Ed_Debian

## The above logs you into the debian instance. Username and Password : dedusr:dedusrpw


in Debian:
bash ./debian_wsl_setup.sh
