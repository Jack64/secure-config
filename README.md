# Secure Config

A tool to manage configuration files in the OSX Keychain or from a file in Linux.

## Installation

Ensure you have Python 3.6+ installed.  
Install dependencies (if any) and setup the project:
```bash
pip install -e .
```

### Installing pipx

If you don't have pipx installed, install it by running:
```bash
python3 -m pip install pipx
python3 -m pipx ensurepath
```
Restart your terminal after running the above commands.

### Installation via pipx

For an isolated installation using pipx, run:
```bash
pipx install .
```

### Uninstallation via pipx

To remove the application, run:
```bash
pipx uninstall secure-config
```

## Usage

### Load Configuration
```bash
python main.py load -s <SERVICE_NAME> [--account <ACCOUNT_NAME>] [--file <CONFIG_FILE>] [--store]
```
- `--account`: Optional, defaults to the current user.
- `--file`: Optional, specifies the configuration file (Linux only).
- `--store`: If set on macOS, saves the loaded secret to `config.json`.

Example (macOS):
```bash
python main.py load -s myService --store
```
Example (Linux):
```bash
python main.py load -s myService --file config.json
```

### Store Configuration (macOS only)
```bash
python main.py store -s <SERVICE_NAME> [--account <ACCOUNT_NAME>] -f <CONFIG_FILE>
```
- `--account`: Optional, defaults to the current user.
- `-f`: Specifies the configuration file to store.

Example:
```bash
python main.py store -s myService -f config.json
```

### List Generic Passwords (macOS only)
```bash
python main.py list [--account <ACCOUNT_NAME>]
```
- `--account`: Optional, defaults to the current user.

Example:
```bash
python main.py list
```

### Delete a Secret (macOS only)
```bash
python main.py delete -s <SERVICE_NAME> [--account <ACCOUNT_NAME>]
```
- `--account`: Optional, defaults to the current user.

Example:
```bash
python main.py delete -s myService
```


## Code Samples

Use this code to retrieve secrets from keychain in multiple programming languages:

### Python

```python
import subprocess
import json, base64
import sys
import argparse
import logging
import getpass  # new import for default user

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_secure_config(ACCOUNT_NAME, SERVICE_NAME, store=False, filename="config.json"):
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-a", ACCOUNT_NAME, "-s", f"SC-{SERVICE_NAME}", "-w"],
                capture_output=True,
                text=True,
                check=True
            )
            config_json_str = base64.b64decode(result.stdout.strip())
            if store:
                with open("config.json", "w") as f:
                    f.write(config_json_str.decode())
                logging.info("Secrets stored in config.json")
            return json.loads(config_json_str)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to retrieve configuration: %s", e.stderr.strip())
            sys.exit(1)
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON retrieved from Keychain: %s", e)
            sys.exit(1)
    else:
        try:
            if not filename:
                raise ValueError("Filename parameter must be provided for Linux environment.")
            with open(filename, "r") as f:
                config_json_str = f.read()
            return json.loads(config_json_str)
        except Exception as e:
            logging.error("Error loading configuration: %s", e)
            sys.exit(1)
```

### Go

```golang
package main

import (
    "os"
    "os/exec"
    "encoding/base64"
    "io/ioutil"
    "log"
    "strings"
    "encoding/json"
)

func loadSecureConfig(ACCOUNT_NAME, SERVICE_NAME string, store bool, filename string) (map[string]interface{}, error) {
    if os.Getenv("GOOS") == "darwin" {
        // macOS-specific code
        cmd := exec.Command("security", "find-generic-password", "-a", ACCOUNT_NAME, "-s", "SC-"+SERVICE_NAME, "-w")
        result, err := cmd.Output()
        if err != nil {
            log.Printf("Failed to run security command: %v", err)
            os.Exit(1)
        }

        configJSONBytes := result

        configJSONStr, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(configJSONBytes)))
        if err != nil {
            log.Printf("Failed to decode configuration: %v", err)
            os.Exit(1)
        }

        var config map[string]interface{}
        err = json.Unmarshal(configJSONStr, &config)
        if err != nil {
            log.Printf("Invalid JSON retrieved from Keychain: %v", err)
            os.Exit(1)
        }

        if store {
            // Write to config.json if store is true
            fw, err := os.Create("config.json")
            if err != nil {
                log.Printf("Error creating config file: %v", err)
                os.Exit(1)
            }
            defer fw.Close()

            _, err = fw.Write(configJSONStr)
            if err != nil {
                log.Printf("Error writing to config.json: %v", err)
                os.Exit(1)
            }
            log.Println("Secrets stored in config.json")
        }

        return config, nil
    } else {
        // Linux-specific code
        if filename == "" {
            log.Println("Filename parameter must be provided for Linux environment.")
            os.Exit(1)
        }

        content, err := ioutil.ReadFile(filename)
        if err != nil {
            log.Printf("Error reading file: %v", err)
            os.Exit(1)
        }

        var config map[string]interface{}
        err = json.Unmarshal(content, &config)
        if err != nil {
            log.Printf("Error loading configuration: %v", err)
            os.Exit(1)
        }

        return config, nil
    }
}

func main() {
    ACCOUNT_NAME := "jack"
    SERVICE_NAME := "llm"
    store := false // Set to true if you want to store the config in a file
    filename := "a" // Default filename for Linux

    config, err := loadSecureConfig(ACCOUNT_NAME, SERVICE_NAME, store, filename)
    if err != nil {
        log.Fatalf("Error loading secure config: %v", err)
    }

    // Do something with the config
    log.Printf("Loaded config: %v", config)
}
```

## License

[Add license information here]
