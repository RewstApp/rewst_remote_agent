package main

import (
    "encoding/json"
    "os"
    "log"
    "os/signal"
    "syscall"
    "time"

    "github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/iothub/armiothub"
)

type Config struct {
    AzureIoTHubHost string `json:"azure_iot_hub_host"`
    DeviceId        string `json:"device_id"`
    SharedAccessKey string `json:"shared_access_key"`
}

func main() {
    // Load configuration
    config, err := load_config("config.json")
    if err != nil {
        log.Fatalf("Failed to load config: %s\n", err)
    }

    // Build connection string
    connection_string := build_connection_string(config)

    // Create client
    client, err := device.NewFromConnectionString(connection_string, device.WithTransport(device.HTTP))
    if err != nil {
        log.Fatalf("Failed to create client: %s\n", err)
    }
    defer client.Close()

    // Set up signal handling to gracefully shutdown
    terminate := make(chan os.Signal, 1)
    signal.Notify(terminate, syscall.SIGINT, syscall.SIGTERM)

    // Send messages in a loop
    go func() {
        for {
            err := client.SendEvent([]byte("Hello, IoT Hub!"))
            if err != nil {
                log.Printf("Failed to send message: %s\n", err)
            } else {
                log.Println("Message sent!")
            }
            time.Sleep(10 * time.Second)
        }
    }()

    // Wait for termination
    <-terminate
    log.Println("Terminating...")
}

func load_config(filename string) (Config, error) {
    var config Config
    data, err := ioutil.ReadFile(filename)
    if err != nil {
        return config, err
    }
    err = json.Unmarshal(data, &config)
    return config, err
}

func build_connection_string(config Config) string {
    return "HostName=" + config.AzureIoTHubHost + ";DeviceId=" + config.DeviceId + ";SharedAccessKey=" + config.SharedAccessKey
}