## In power shell:
```
Invoke-WebRequest -Uri "https://salsa.debian.org/debian/WSL/-/raw/master/x64/install.tar.gz" -OutFile "$env:USERPROFILE\Downloads\debian-wsl.tar.gz"
New-Item -ItemType Directory -Path "C:\WSL_Ed\Ed_Debian" -Force
wsl --import Ed_Debian C:\WSL_Ed\Ed_Debian "$env:USERPROFILE\Downloads\debian-wsl.tar.gz" --version 2
wsl -d Ed_Debian -u root bash -c "apt update && apt upgrade -y && apt install sudo -y && useradd -m -s /bin/bash dedusr && echo 'dedusr:dedusrpw' | chpasswd && usermod -aG sudo dedusr && echo '[user]' > /etc/wsl.conf && echo 'default=dedusr ' >> /etc/wsl.conf"
wsl --shutdown
wsl -d Ed_Debian
```

The above creates a debian instance named Ed_Debian, sets up main user and logs you into it. Username and Password : dedusr:dedusrpw

Once you're in Debian:

```
git clone https://github.com/thomashollier/ded-pipe.git
cd ded-pipe/WSL_setup
bash ./debian_wsl_setup.sh
```

Since basic Debian doesn't have git, you may need to manually download the debian_wsl_setup.sh file manually since that is where git gets installed.



