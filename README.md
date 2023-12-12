# rewst_remote_agent

An RMM-agnostic remote agent using the Azure IoT Hub

Goals:
* Run as an service on Windows (Linux / Mac coming later!)
* Provisioning (Windows):
  * `iwr ((irm {{ github_release_url }}).assets|?{$_.name -eq "rewst_agent_config.win.exe"}|select -exp browser_download_url) -OutFile rewst_agent_config.win.exe`
    * Downloads latest release of configuration Utility from GitHub
  * `.\rewst_agent_config.win.exe` `--config-url` _{ Your Trigger URL }_  `--config-secret` _{ Your global config secret }_ `--org-id` _{ customer organization id }_
    * Initiates configuration and installation of the agent
    * `config-url`: The configured workflow trigger from the Crate installation
    * `config-secret`: Stored in an Org variable under your company. If it changes, existing installations will still work, but new commands to install it will need the new secret.
    * `org-id`: The organization's (your customer) Rewst Org ID.
* Operation:
    * Stays resident and connected to the IoT Hub
    * Rewst workflows can send an object to IoT hub that contains a list of `commands`
    * When the list arrives, the script will spawn shell process and process these commands sequentially within the _same_ environment
    * Each command will have its output collected and returned back in a list of `command_results` that is in the same index as the command from `commands`
    * Handle disconnects gracefully and restart


