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

def store_secure_config(ACCOUNT_NAME, SERVICE_NAME, filename):
    try:
        with open(filename, "r") as f:
            config_json_str = f.read()

        encoded_config = base64.b64encode(config_json_str.encode()).decode().strip()
        result = subprocess.run(
            ["security", "add-generic-password", "-a", ACCOUNT_NAME, "-s", f"SC-{SERVICE_NAME}", "-w", encoded_config, "-U"],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info("Secrets updated: %s -> %s/%s", filename, ACCOUNT_NAME, SERVICE_NAME)
        # Ensure 0 apps are trusted by setting an empty partition list
        subprocess.run(
            ["security", "set-generic-password-partition-list", "-S", "", "-a", ACCOUNT_NAME, "-s", f"SC-{SERVICE_NAME}"],
            capture_output=True,
            text=True,
            check=True
        )

    except subprocess.CalledProcessError as e:
        logging.error("Failed to store configuration: %s", e.stderr.strip())
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error("Invalid JSON retrieved from Keychain: %s", e)
        sys.exit(1)

def delete_secure_config(ACCOUNT_NAME, SERVICE_NAME):
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["security", "delete-generic-password", "-a", ACCOUNT_NAME, "-s", f"SC-{SERVICE_NAME}"],
                capture_output=True,
                text=True,
                check=True
            )
            logging.info("Secret deleted: %s/%s", ACCOUNT_NAME, SERVICE_NAME)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to delete secret: %s", e.stderr.strip())
            sys.exit(1)
    else:
        logging.error("Deleting secrets is only supported on macOS.")
        sys.exit(1)

def list_generic_passwords(service_filter=None):
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-a", getpass.getuser(), "-g"],
                capture_output=True,
                text=True,
                check=False  # -g returns non-zero exit status even on success
            )

            keychain_dump = subprocess.run(
                ["security", "dump-keychain"],
                capture_output=True,
                text=True,
                check=True
            )

            passwords = []
            current_service = None
            current_account = None

            for line in keychain_dump.stdout.splitlines():
                line = line.strip()
                if line.startswith('"svce"'):
                    current_service = line.split('<blob>=')[1].strip(' "')
                elif line.startswith('"acct"'):
                    current_account = line.split('<blob>=')[1].strip(' "')

                if current_service and current_account:
                    if (current_service.startswith("SC-")):
                        passwords.append({"service": current_service.replace("SC-",""), "account": current_account})
                    current_service, current_account = None, None

            logging.info("Found %d matching generic passwords", len(passwords))
            for password in passwords:
                logging.info("Service: %s, Account: %s", password["service"], password["account"])

            return passwords
        except subprocess.CalledProcessError as e:
            logging.error("Failed to list generic passwords: %s", e.stderr.strip())
            sys.exit(1)
    else:
        logging.error("Listing generic passwords is only supported on macOS.")
        sys.exit(1)

def version():
    return "Secure Config Tool v1.0.0"

def main():
    parser = argparse.ArgumentParser(description="Tool to manage config files in OSX Keychain or from file in Linux.\nWARNING: Overwrite or delete operations do not require authentication!")
    
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser.add_argument("-v", "--version", action="version", version=version(), help="Show version information")

    list_parser = subparsers.add_parser('list', help="List all generic passwords")
    list_parser.add_argument("-a", "--account", default=getpass.getuser(), help="Account name (default: current user)")  # updated: optional, default=current user

    load_parser = subparsers.add_parser('load', help="Load configuration")
    load_parser.add_argument("-a", "--account", default=getpass.getuser(), help="Account name (default: current user)")  # updated: optional, default=current user
    load_parser.add_argument("-s", "--service", required=True, help="Service name")
    load_parser.add_argument("-f", "--file", default="config.json", help="Configuration file (Linux only)")
    load_parser.add_argument("--store", action="store_true", help="If set on macOS, saves loaded secret to config.json")

    store_parser = subparsers.add_parser('store', help="Store configuration into keychain (macOS only)")
    store_parser.add_argument("-a", "--account", default=getpass.getuser(), help="Account name (default: current user)")  # updated: optional, default=current user
    store_parser.add_argument("-s", "--service", required=True, help="Service name")
    store_parser.add_argument("-f", "--file", required=True, help="Configuration file to store")

    delete_parser = subparsers.add_parser('delete', help="Delete a secret from keychain (macOS only)")
    delete_parser.add_argument("-a", "--account", default=getpass.getuser(), help="Account name (default: current user)")
    delete_parser.add_argument("-s", "--service", required=True, help="Service name")

    args = parser.parse_args()

    if args.command == "load":
        config = load_secure_config(args.account, args.service, store=args.store, filename=args.file)
        logging.info("Configuration loaded successfully")
        print(json.dumps(config, indent=2))
    elif args.command == "store":
        store_secure_config(args.account, args.service, args.file)
        logging.info("Configuration stored successfully")
    elif args.command == "list":
        list_generic_passwords()
        # logging.info("Configuration stored successfully")
    elif args.command == "delete":
        delete_secure_config(args.account, args.service)
        logging.info("Secret deleted successfully")

if __name__ == "__main__":
    main()
