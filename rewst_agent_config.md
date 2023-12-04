This component of the application is the piece that is directly run by the end user or existing RMM script. 

It should perform the following functions:

* Make an HTTP call to Rewst using the config-url and config-secret parameters to receive configuration data to write to the configuration JSON
* Using the information, establish a connection to IoT Hub to await a 'command' message that will contain powershell (or Bash if Linux or MacOS) for continued configuration
  * The powershell will initiate the download of the service manager and service agent executables, and write them into the correct locations
* Await all of the files to be written (poll the operating system). Once the files have been fully written, perform these functions:
  * End the IoT Hub connection
  * use the service manager to Install and Start the Service and wait for a return that the service has successfully started
* Exit the program with a success message