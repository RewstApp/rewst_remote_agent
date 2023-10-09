# rewst_remote_agent

Beginning phases of building an RMM-agnostic remote agent using the Azure IoT Hub

Goals:
* Run as an service on Windows / Linux / Mac
* Provisioning:
    * 
* Operation:
    * Stays resident and connected to the IoT Hub
    * Rewst workflows can send an object to IoT hub that contains a list of `commands`
    * When the list arrives, the script will spawn shell process and process these commands sequentially within the _same_ environment
    * Each command will have its output collected and returned back in a list of `command_results` that is in the same index as the command from `commands`
    * Handle disconnects gracefully and restart



Current phase: POC

Plan:


Todo:
- [ ] All the things
- [ ] Add cross-platform support
- [ ] _Future:_ Watchdog service?