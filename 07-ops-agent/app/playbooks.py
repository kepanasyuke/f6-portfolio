"""Чек-листы укрепления для Linux и Windows."""

LINUX = (
    {
        "id": "linux-ssh-root",
        "title": "Запретить вход root по SSH",
        "how": "PermitRootLogin no в /etc/ssh/sshd_config",
    },
    {
        "id": "linux-ssh-keys",
        "title": "Только ключевая аутентификация",
        "how": "PasswordAuthentication no, ключи в authorized_keys",
    },
    {
        "id": "linux-fail2ban",
        "title": "Защита от перебора",
        "how": "fail2ban с jail для sshd, maxretry=5, bantime растёт",
    },
    {
        "id": "linux-updates",
        "title": "Автообновления безопасности",
        "how": "unattended-upgrades для security-репозитория",
    },
    {
        "id": "linux-auditd",
        "title": "Аудит процессов и файлов",
        "how": "auditd с правилами на execve и /etc/passwd",
    },
    {
        "id": "linux-sudo",
        "title": "Минимальные права sudo",
        "how": "sudoers по группам, NOPASSWD только для дежурных команд",
    },
    {
        "id": "linux-firewall",
        "title": "Периметр закрыт",
        "how": "nftables: default deny inbound, разрешены 22/443",
    },
)

WINDOWS = (
    {
        "id": "win-laps",
        "title": "Локальные админы под контролем",
        "how": "LAPS для ротации паролей локальных администраторов",
    },
    {
        "id": "win-smbtls",
        "title": "Отключить SMBv1 и NTLMv1",
        "how": "Set-SmbServerConfiguration -EnableSMB1Protocol $false",
    },
    {
        "id": "win-rdp-nla",
        "title": "RDP только с NLA",
        "how": "UserAuthentication=1 и ограничение по подсетям",
    },
    {
        "id": "win-defender",
        "title": "Активная защита",
        "how": "Defender: real-time protection, ASR-правила, cloud-delivered",
    },
    {
        "id": "win-logs",
        "title": "Сбор 4688 и PowerShell 4104",
        "how": "command line в событиях процесса и script block logging",
    },
    {
        "id": "win-patches",
        "title": "Окно обновлений",
        "how": "WSUS/Intune с кольцами и контролем перезагрузок",
    },
    {
        "id": "win-bitlocker",
        "title": "Диски зашифрованы",
        "how": "BitLocker с escrow ключей в AD/Intune",
    },
)

PLAYBOOKS = {"linux": LINUX, "windows": WINDOWS}


def playbook(os_name: str) -> tuple[dict, ...]:
    return PLAYBOOKS.get(os_name.lower(), LINUX)


def os_names() -> tuple[str, ...]:
    return tuple(PLAYBOOKS)
