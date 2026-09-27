# TRAM dataset review

Review queue only: source data and labels have not been changed.
All record indices below start at zero.

## 1. Report pairs sharing labeled sentences

- **29 shared labeled sentences**: train / Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester ↔ validation / AA22320A Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester
- **1 shared labeled sentences**: train / Dead or Alive An Emotet Story ↔ validation / Analyzing Solorigate the compromised DLL file that started a sophisticated cyberattack and how Microsoft Defender helps protect customers
- **1 shared labeled sentences**: train / Malicious ISO File Leads to Domain Wide Ransomware  The DFIR Report ↔ validation / Analyzing Solorigate the compromised DLL file that started a sophisticated cyberattack and how Microsoft Defender helps protect customers
- **1 shared labeled sentences**: train / Vice Society leverages PrintNightmare in ransomware attacks ↔ validation / Operation Harvest A Deep Dive into a Longterm Campaign
- **1 shared labeled sentences**: train / Malicious ISO File Leads to Domain Wide Ransomware  The DFIR Report ↔ validation / Conti Ransomware

Check whether these are copies of the same original report. Different titles alone do not prove independence.
For a future dataset version, group confirmed report copies before splitting; preserve the original benchmark.

## 2. Conflicting annotations

### Conflict 1

the threat actors also moved laterally to the domain controller, compromised credentials, and implanted ngrok reverse proxies.

**train, raw index 6146 — Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1078, T1090

- Raw index 6145: As trusted-third party reporting associated Log4Shell activity from 51.89.181[.]64 with lateral movement and targeting of DCs, CISA suspected the threat actors had moved laterally and compromised the organization’s DC. From mid-June through mid-July 2022, CISA conducted an onsite incident response engagement and determined that the organization was compromised as early as February 2022, by likely Iranian government-sponsored APT actors who installed XMRig crypto mining software.
- Raw index 6146: The threat actors also moved laterally to the domain controller, compromised credentials, and implanted Ngrok reverse proxies.
- Raw index 6147: Threat Actor Activity In February 2022, the threat actors exploited Log4Shell [T1190] for initial access [TA0001] to the organization’s unpatched VMware Horizon server.

**validation, raw index 2167 — AA22320A Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1078

- Raw index 2166: As trusted-third party reporting associated Log4Shell activity from with lateral movement and targeting of DCs, CISA suspected the threat actors had moved laterally and compromised the organization’s DC. From mid-June through mid-July 2022, CISA conducted an onsite incident response engagement and determined that the organization was compromised as early as February 2022, by likely Iranian government-sponsored APT actors who installed XMRig crypto mining software.
- Raw index 2167: The threat actors also moved laterally to the domain controller, compromised credentials, and implanted Ngrok reverse proxies.
- Raw index 2168: Threat Actor Activity In February 2022, the threat actors exploited Log4Shell [T1190] for initial access [TA0001] to the organization’s unpatched VMware Horizon server.

Decision: pending source review. Do not merge label lists automatically.

### Conflict 2

the actors downloaded the following tools: psexec – a microsoft signed tool for system administrators.

**train, raw index 6167 — Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1003.001, T1105

- Raw index 6166: Once the threat actor established themselves on the VDI-KMS host, CISA observed the actors download around 30 megabytes of files from transfer[.]sh server associated with 144.76.136[.]153.
- Raw index 6167: The actors downloaded the following tools: PsExec – a Microsoft signed tool for system administrators.
- Raw index 6168: Mimikatz – a credential theft tool.

**validation, raw index 2187 — AA22320A Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1003.001

- Raw index 2186: Once the threat actor established themselves on the VDI-KMS host, CISA observed the actors download around 30 megabytes of files from server associated with .
- Raw index 2187: The actors downloaded the following tools: PsExec – a Microsoft signed tool for system administrators.
- Raw index 2188: Mimikatz – a credential theft tool.

Decision: pending source review. Do not merge label lists automatically.

### Conflict 3

mimikatz – a credential theft tool.

**train, raw index 6168 — Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1003.001, T1090

- Raw index 6167: The actors downloaded the following tools: PsExec – a Microsoft signed tool for system administrators.
- Raw index 6168: Mimikatz – a credential theft tool.
- Raw index 6169: Ngrok – a reverse proxy tool for proxying an internal service out onto an Ngrok domain, which the user can then access at a randomly generated subdomain at *.ngrok[.]io.

**validation, raw index 2188 — AA22320A Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1003.001

- Raw index 2187: The actors downloaded the following tools: PsExec – a Microsoft signed tool for system administrators.
- Raw index 2188: Mimikatz – a credential theft tool.
- Raw index 2189: Ngrok – a reverse proxy tool for proxying an internal service out onto an Ngrok domain, which the user can then access at a randomly generated subdomain at .

Decision: pending source review. Do not merge label lists automatically.

### Conflict 4

indicator removal on host: file deletion t1070.004

**train, raw index 6224 — Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1070.004

- Raw index 6223: Monitor processes for unexpected termination related to security tools/services [DS0009].
- Raw index 6224: Indicator Removal on Host: File Deletion T1070.004
- Raw index 6225: The actors removed malicious file mde.ps1 from the dis. Detection:

**validation, raw index 2243 — AA22320A Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1027

- Raw index 2242: Monitor processes for unexpected termination related to security tools/services [DS0009].
- Raw index 2243: Indicator Removal on Host: File Deletion T1070.004
- Raw index 2244: The actors removed malicious file mde.ps1 from the dis. Detection:

Decision: pending source review. Do not merge label lists automatically.

### Conflict 5

the actors removed malicious file mde.ps1 from the dis. detection:

**train, raw index 6225 — Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1070.004

- Raw index 6224: Indicator Removal on Host: File Deletion T1070.004
- Raw index 6225: The actors removed malicious file mde.ps1 from the dis. Detection:
- Raw index 6226: Monitor executed commands and arguments for actions that could be utilized to unlink, rename, or delete files [DS0017]. Detection:

**validation, raw index 2244 — AA22320A Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester**
Labels: T1027

- Raw index 2243: Indicator Removal on Host: File Deletion T1070.004
- Raw index 2244: The actors removed malicious file mde.ps1 from the dis. Detection:
- Raw index 2245: Monitor executed commands and arguments for actions that could be utilized to unlink, rename, or delete files [DS0017]. Detection:

Decision: pending source review. Do not merge label lists automatically.

### Conflict 6

cmd.exe /c

**train, raw index 7752 — Malicious ISO File Leads to Domain Wide Ransomware  The DFIR Report**
Labels: T1059.003

- Raw index 7751: As seen in the screenshot below, GetSystem creates a service and connects to a pipe.
- Raw index 7752: cmd.exe /c
- Raw index 7753: echo nbproc > \\.\pipe\nbproc cmd.exe /c

**train, raw index 11540 — Vice Society leverages PrintNightmare in ransomware attacks**
Labels: Unknown / unannotated

- Raw index 11539: In this case, PSExec remotely authenticated and executed PowerShell on remote systems within the environment.
- Raw index 11540: cmd.exe /c
- Raw index 11541: C:\s$\0.bat PsExec.exe -d \\[HOSTNAME] -u

**validation, raw index 961 — Conti Ransomware**
Labels: T1059.003, T1112

- Raw index 960: Additional discovery commands were executed by Cobalt Strike.
- Raw index 961: cmd.exe /C
- Raw index 962: whoami /groupscmd.exe /C query sessioncmd.exe /C

Decision: pending source review. Do not merge label lists automatically.

## 3. Examples exceeding the token limit

### train: prepared index 1739, raw index 7919

Document: Malicious ISO File Leads to Domain Wide Ransomware  The DFIR Report
Tokens: 2538 / limit 1024
Labels: T1027, T1219

Text preview (first 700 characters):

Once the file was unpacked and the Cobalt Strike beacon binary carved, the Cobalt Strike configuration could be determined as follows: { "beacontype": [ "HTTPS" ], "sleeptime": 5000, "jitter": 28, "maxgetsize": 1865903, "spawnto": "AAAAAAAAAAAAAAAAAAAAAA==", "license_id": 0, "cfg_caution": false, "kill_date": null, "server": { "hostname": "fazehotafa.com", "port": 443, "publickey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC1nAS8+PqMnQs3hynG2JDgMQK6ZqLkIoDXWnqaOS/dQsdKBHE0Ify/HIZ2ntSpyMtvomDHCA98pCEi1L7mT0mvfiYapP9Aj776rDpzXMYNiRk1BWrAzJqzLcfwzxJx26hL1VSu1C5mWEl7JsVT/9l/kHcNYAALgNQuI0uZAqM7YQIDAQABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

Decision: inspect full raw record. Preserve evidence and the complete target answer; do not blindly truncate.

### train: prepared index 1948, raw index 8848

Document: Dead or Alive An Emotet Story
Tokens: 1138 / limit 1024
Labels: T1219

Text preview (first 700 characters):

72a589da586844d7f0818ce684948eea JA3S: f176ba63b4d68e576b5ba345bec2c7b7 Certificate: [66:f7:4c:f9:56:5d:fe:15:a6:8c:62:b9:3d:72:cb:8e:c9:e9:89:02] Not Before: 2022/05/19 12:22:46 UTC Not After: 2023/05/19 12:22:46 (UTC) Issuer Org: jQuery Subject Common: jquery.com { "beacontype": [ "HTTP" ], "sleeptime": 45000, "jitter": 37, "maxgetsize": 1403644, "spawnto": "AAAAAAAAAAAAAAAAAAAAAA==", "license_id": 206546002, "cfg_caution": false, "kill_date": null, "server": { "hostname": "59.95.98.204", "port": 8080, "publickey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCfWiK6EPk2D2Ho7CBgdUfK2kqa/1x2L0Tt0R4Pl/Sof+7skIOqclxG1PeQTbc0VYagoqiuCJCn/QQd8pJBzci5GMTtdrzcKqZXQBy3Rv7Sfv9v8MZQfU2UVrRgVChdAetwPDdSMAa5

Decision: inspect full raw record. Preserve evidence and the complete target answer; do not blindly truncate.

### train: prepared index 2450, raw index 11174

Document: Unwrapping Ursnifs Gifts  The DFIR Report
Tokens: 1169 / limit 1024
Labels: T1090, T1021.001

Text preview (first 700 characters):

RDP was also used by the threat actor on the final two days of the intrusion to connect to various hosts from a domain controller proxying the traffic via the firefox.exe Cobalt Strike beacon. Command and Control Ursnif Ursnif was seen using the following domains and IPs: 5.42.199.83superliner.top 62.173.149.7 internetlines.in 31.41.44.97 superstarts.top 31.41.44.27 superlinez.top 31.41.44.27 internetlined.com 208.91.197.91 denterdrigx.com: 187.190.48.135 210.92.250.133 189.143.170.233 201.103.222.246 151.251.24.5 190.147.189.122 115.88.24.202 211.40.39.251 187.195.146.2 186.182.55.44 222.232.238.243 211.119.84.111 51.211.212.188 203.91.116.53 115.88.24.203 190.117.75.91 181.197.121.228 190.

Decision: inspect full raw record. Preserve evidence and the complete target answer; do not blindly truncate.

### validation: prepared index 109, raw index 588

Document: Emotet Strikes Again  LNK File Leads to Domain Wide Ransomware  The DFIR Report
Tokens: 1439 / limit 1024
Labels: T1219

Text preview (first 700 characters):

Indicators Atomic Emotet Deployment Domains descontador[.]com[.]br www.elaboro[.]pl el-energiaki[.]gr drechslerstammtisch[.]de dhnconstrucciones[.]com[.]ar dilsrl[.]com Emotet C2 Servers 103.159.224.46 103.75.201.2 119.193.124.41 128.199.225.17 131.100.24.231 139.59.60.88 144.217.88.125 146.59.226.45 149.56.131.28 159.89.202.34 165.22.211.113 165.227.166.238 178.128.82.218 209.126.98.206 213.32.75.32 37.187.115.122 45.226.53.34 45.55.134.126 46.55.222.11 51.210.176.76 51.254.140.238 54.37.70.105 82.223.82.69 91.207.181.106 92.114.18.20 94.23.45.86 96.125.171.165 Cobalt Strike 139.60.161.167 (survefuz[.]com) 139.60.160.18 (juanjik[.]com) Tactical RMM Agent api.floppasoftware[.]com mesh.floppa

Decision: inspect full raw record. Preserve evidence and the complete target answer; do not blindly truncate.

## Recommended next step

Resolve report identity first. Then review label conflicts against the original source, recording each decision.
For long records, inspect token masks before choosing a larger context limit or an evidence-preserving transformation.
An IOC list or configuration block should not be split into chunks that all inherit the full record's labels.
