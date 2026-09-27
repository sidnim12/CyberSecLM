# Report identity review

All cross-split report pairs were compared using normalized, distinct sentence text.
Shown below: pairs sharing labeled sentences or substantial full-text overlap.
Substantial overlap means at least 10 shared sentences and at least 80% coverage of each report.
This is a review heuristic, not confirmation of source identity. No datasets were changed.

## Pair 1

A: train / Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester
B: validation / AA22320A Iranian GovernmentSponsored APT Actors Compromise Federal Network Deploy Crypto Miner Credential Harvester

- Shared sentences: 166
- Coverage of A: 86.0% (193 distinct sentences)
- Coverage of B: 86.5% (192 distinct sentences)
- Assessment: substantial text overlap; source review needed

Shared labeled text:

- [ds0002]. scheduled task/job: scheduled task t1053.005
- [ds0003]. valid accounts: default accounts t1078.001
- [ds0017]. credentials from password stores t1555 the actors used mimikatz to harvest credentials.
- [ds0029]. ingress tool transfer t1105
- [t1078.001] to move laterally [ta0008] to a vmware vdi-kms host.
- additionally, the threat actor was observed attempting to dump the local security authority subsystem service (lsass) process [t1003.001] with task manager but this was stopped by additional anti-virus the fceb organization had installed. mitre att&ck tactics and techniques see table 1 for all referenced threat actor tactics and techniques in this advisory, as well as corresponding detection and/or mitigation recommendations.
- develop rules to monitor logon behavior across default accounts that have been activated or logged into [ds0028]. defense evasion technique title id use recommendations impair defenses: disable or modify tools t1562.001
- indicator removal on host: file deletion t1070.004
- mimikatz – a credential theft tool.
- ngrok is known to be used for malicious purposes.[1] the threat actors then executed mimikatz on vdi-kms to harvest credentials and created a rogue domain administrator account
- other factors, such as access patterns (ex: multiple systems over a relatively short period of time) and activity that occurs after a remote login, may indicate suspicious or malicious behavior with rdp [ds0028]. command and control technique title id use recommendations proxy t1090 the actors used ngrok to proxy rdp connections and to perform command and control.
- remote desktop protocol t1021.001 the actors used rdp to move laterally to multiple hosts on the network.
- table 1: cyber threat actors att&ck techniques for enterprise initial access technique title id use recommendations exploit public-facing application t1190 the actors exploited log4shell for initial access to the organization’s vmware horizon server.
- the actors added an exclusion rule to windows defender.
- the actors downloaded malware and multiple tools to the network, including psexec, mimikatz, and ngrok.
- the actors downloaded the following tools: psexec – a microsoft signed tool for system administrators.
- the actors manually disabled windows defender via the gui.
- the actors removed malicious file mde.ps1 from the dis. detection:
- the actors used built-in windows user account defaultaccount.
- the actors were observed trying to dump lsass process.
- the actors’ exploit payload created scheduled task runtimebrokerservice.exe, which executed runtimebroker.exe daily as system.
- the actors’ exploit payload ran the following powershell command [t1059.001] that added an exclusion rule to
- the exploit payload created a scheduled task
- the threat actors also moved laterally to the domain controller, compromised credentials, and implanted ngrok reverse proxies.
- the tool allowlisted the entire c:\drive, enabling the actors to bypass virus scans for tools they downloaded to the c:\drive.
- threat actor activity in february 2022, the threat actors exploited log4shell [t1190] for initial access [ta0001] to the organization’s unpatched vmware horizon server.
- upon logging into each host, the actors manually disabled windows defender via the graphical user interface (gui) and implanted ngrok executables and configuration files.
- using the newly created account, the actors leveraged rdp to propagate to several hosts within the network.
- windows defender

## Pair 2

A: train / Malicious ISO File Leads to Domain Wide Ransomware  The DFIR Report
B: validation / Conti Ransomware

- Shared sentences: 2
- Coverage of A: 0.6% (318 distinct sentences)
- Coverage of B: 1.7% (117 distinct sentences)
- Assessment: limited overlap; insufficient evidence to group reports

Shared labeled text:

- cmd.exe /c

## Pair 3

A: train / Dead or Alive An Emotet Story
B: validation / Analyzing Solorigate the compromised DLL file that started a sophisticated cyberattack and how Microsoft Defender helps protect customers

- Shared sentences: 1
- Coverage of A: 0.7% (150 distinct sentences)
- Coverage of B: 0.7% (152 distinct sentences)
- Assessment: limited overlap; insufficient evidence to group reports

Shared labeled text:

- c:\windows\system32\cmd.exe /c

## Pair 4

A: train / Vice Society leverages PrintNightmare in ransomware attacks
B: validation / Operation Harvest A Deep Dive into a Longterm Campaign

- Shared sentences: 1
- Coverage of A: 0.7% (137 distinct sentences)
- Coverage of B: 0.5% (190 distinct sentences)
- Assessment: limited overlap; insufficient evidence to group reports

Shared labeled text:

- cmd /c

## Pair 5

A: train / Malicious ISO File Leads to Domain Wide Ransomware  The DFIR Report
B: validation / Analyzing Solorigate the compromised DLL file that started a sophisticated cyberattack and how Microsoft Defender helps protect customers

- Shared sentences: 1
- Coverage of A: 0.3% (318 distinct sentences)
- Coverage of B: 0.7% (152 distinct sentences)
- Assessment: limited overlap; insufficient evidence to group reports

Shared labeled text:

- c:\windows\system32\cmd.exe /c

## Decision guidance

Review substantial-overlap pairs against the original source. Confirmed copies should share a document group in a future split.
A command such as cmd.exe /c appearing in unrelated reports is not enough to merge their document identities.
Preserve the original experiment. Record source evidence before creating a versioned split or changing annotations.
