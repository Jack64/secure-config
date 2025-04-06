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

# OR

brew install pipx
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
secure-config load -s <SERVICE_NAME> [--account <ACCOUNT_NAME>] [--file <CONFIG_FILE>] [--store]
```
- `--account`: Optional, defaults to the current user.
- `--file`: Optional, specifies the configuration file (Linux only).
- `--store`: If set on macOS, saves the loaded secret to `config.json`.

Example (macOS):
```bash
secure-config load -s myService --store
```
Example (Linux):
```bash
secure-config load -s myService --file config.json
```

### Store Configuration (macOS only)
```bash
secure-config store -s <SERVICE_NAME> [--account <ACCOUNT_NAME>] -f <CONFIG_FILE>
```
- `--account`: Optional, defaults to the current user.
- `-f`: Specifies the configuration file to store.

Example:
```bash
secure-config store -s myService -f config.json
```

### List Generic Passwords (macOS only)
```bash
secure-config list [--account <ACCOUNT_NAME>]
```
- `--account`: Optional, defaults to the current user.

Example:
```bash
secure-config list
```

### Delete a Secret (macOS only)
```bash
secure-config delete -s <SERVICE_NAME> [--account <ACCOUNT_NAME>]
```
- `--account`: Optional, defaults to the current user.

Example:
```bash
secure-config delete -s myService
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
	"encoding/base64"
	"encoding/json"
	"errors"
	"io/ioutil"
	"log"
	"os/exec"
	"runtime"
	"strings"
)

func loadSecureConfig(accountName, serviceName string, store bool, filename string) (map[string]interface{}, error) {
	var config map[string]interface{}

	if runtime.GOOS == "darwin" {
		// macOS-specific code
		cmd := exec.Command("security", "find-generic-password", "-a", accountName, "-s", "SC-"+serviceName, "-w")
		result, err := cmd.Output()
		if err != nil {
			return nil, errors.New("failed to run security command: " + err.Error())
		}

		decodedBytes, err := base64.StdEncoding.DecodeString(strings.TrimSpace(string(result)))
		if err != nil {
			return nil, errors.New("failed to decode base64 configuration: " + err.Error())
		}

		if err := json.Unmarshal(decodedBytes, &config); err != nil {
			return nil, errors.New("invalid JSON retrieved from Keychain: " + err.Error())
		}

		if store {
			if err := ioutil.WriteFile("config.json", decodedBytes, 0600); err != nil {
				return nil, errors.New("error writing to config.json: " + err.Error())
			}
			log.Println("Secrets stored in config.json")
		}
	} else {
		// Linux-specific code
		if filename == "" {
			return nil, errors.New("filename parameter must be provided for Linux environment")
		}

		content, err := ioutil.ReadFile(filename)
		if err != nil {
			return nil, errors.New("error reading file: " + err.Error())
		}

		if err := json.Unmarshal(content, &config); err != nil {
			return nil, errors.New("error loading configuration: " + err.Error())
		}
	}

	return config, nil
}

func main() {
	accountName := "jack"
	serviceName := "llm"
	store := false
	filename := "a"

	config, err := loadSecureConfig(accountName, serviceName, store, filename)
	if err != nil {
		log.Fatalf("Error loading secure config: %v", err)
	}

	log.Printf("Loaded config: %v", config)
}
```

## License

[Add license information here]
