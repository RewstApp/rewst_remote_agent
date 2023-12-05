# To-Do List

## Features
- [x] Automated Sign-up
- [x] Run as a service
- [x] Sign binaries during build process
- [ ] Automated Updates
- [ ] Encrypt commands sent to the agent via IoT Hub
  - [ ] Generate a signing key to be stored on the agent and within Rewst
  - [ ] Consider implementing database storage for key management

## Bugs
- [ ] Ensure agent processes exit cleanly without manual intervention
  - Investigate and fix the issue causing agent processes to require manual termination

## Documentation
- [ ] Fully document the setup and operation of the system
  - Include detailed instructions for initial setup
  - Document operational procedures and common use cases

## Improvements
- [ ] Implement online status tracking in IoT Hub
  - Develop a mechanism to track and report the online status of agents
- [ ] Finish and test Linux Agent
- [ ] Finish and test MacOS Agent
- [ ] Clean up unused bits
- [ ] Allow for flag for powershell commands to RunAsUser

## Testing
- [ ] Test limits of "Free" IoT Hub tier to see if it is enough

## Rewst Workflows
- [ ] Provisioning Agent Infrastructure
- [ ] Generate and display Agent Installation Commands
- [ ] App Platform Agent Status Dashboard