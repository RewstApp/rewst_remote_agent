# To-Do List

## Features
- [x] Automated Sign-up
- [x] Run as a service
- [x] Sign binaries during build process
- [ ] Automated Updates
- [ ] Encrypt commands sent to the agent via IoT Hub
  - [ ] Generate a signing key to be stored on the agent and within Rewst
  - [ ] Consider implementing database storage for key management
- [ ] Optional Logging commands to logfile
- [ ] Optional logging to SIEM?

## Bugs
- [x] Ensure agent processes exit cleanly without manual intervention
  - Investigate and fix the issue causing agent processes to require manual termination

## Documentation
- [ ] Fully document the setup and operation of the system
  - Include detailed instructions for initial setup
  - Document operational procedures and common use cases
  - Videos!

## Improvements
- [ ] Implement online status tracking in IoT Hub
  - Develop a mechanism to track and report the online status of agents
- [ ] Periodic refresh agent info tags
- [ ] Finish and test Linux Operation
- [ ] Finish and test MacOS Operation
  - [ ] Make it actually process commands
- [ ] Clean up unused bits
- [ ] Allow for flag for powershell commands to [RunAsUser](https://github.com/KelvinTegelaar/RunAsUser)

## Testing
- [ ] Test limits of "Free" IoT Hub tier to ballpark agent count

## Rewst Workflows
- [x] Provisioning Agent Infrastructure
- [x] Generate and display Agent Installation Commands
- [x] App Platform Agent Status Dashboard