import os
import subprocess
import yaml
import shutil
from schema import Schema, SchemaError, Optional
import secrets

# ANSI color escape codes
RESET = "\033[0m"
INFO_COLOR = "\033[36m"  # Cyan
WARNING_COLOR = "\033[93m"  # Yellow
ERROR_COLOR = "\033[91m"  # Red
HIGHLIGHT_COLOR = "\033[95m"  # Magenta

# Define the schema for a single block
block_schema = {
    Optional("public"): [str],
    Optional("private"): [str]
}

# Define the schema for the entire YAML file
yaml_schema = {
    "env_files": {str: block_schema}
}


# Function to process the 'needed-secrets.yaml' file in a subdirectory
def process_yaml_file(directory):
    yaml_file_path = os.path.join(directory, 'needed-secrets.yaml')

    if not os.path.exists(yaml_file_path):
        print(f"\t\t{WARNING_COLOR}Warning: 'needed-secrets.yaml' file does not exist in {directory}. Skipping.{RESET}")
        return None

    try:
        with open(yaml_file_path, 'r') as yaml_file:
            loaded_data = yaml.safe_load(yaml_file)

            # Validate yaml file with schema
            schema = Schema(yaml_schema)
            schema.validate(loaded_data)

            # Return the parsed data
            return loaded_data

    except SchemaError as e:
        print(f"\t\t{WARNING_COLOR}Warning: 'needed-secrets.yaml' validation failed in {directory}. Skipping.{RESET}")
        print(e)
    except Exception as e:
        print(f"\t\t{WARNING_COLOR}Warning: Error while processing 'needed-secrets.yaml' in {directory}. Skipping.{RESET}")
        print(f"\t\tError details: {ERROR_COLOR}{str(e)}{RESET}")

    return None


# Function to check if a directory has the 'secrets' folder and 'needed-secrets.txt' file
def restrict_secrets_directory(directory):
    secrets_folder = os.path.join(directory, 'secrets')

    if not os.path.exists(secrets_folder):
        print(f"\t\t{WARNING_COLOR}Skipping {directory}: 'secrets' folder does not exist.{RESET}")
        return False

    if not os.path.isdir(secrets_folder):
        print(f"\t\t{WARNING_COLOR}Skipping {directory}: 'secrets' is not a directory.{RESET}")
        return False

    subprocess.check_call(['sudo', 'chmod', '700', secrets_folder])
    print(f"\t\tModified permissions for '{HIGHLIGHT_COLOR}{secrets_folder}{RESET}' with chmod 700")
    return True


# Function to create secret values for private and public keys
def create_secrets(parsed_data):
    secret_data = {}

    for key, data in parsed_data.items():
        secret_data[key] = {
            "private": {k: secrets.token_hex(32) for k in data.get("private", [])},
            "public": {k: secrets.token_hex(32) for k in data.get("public", [])}
        }

    return secret_data


# Function to generate secret files based on the provided dictionary
def generate_secret_files(secret_data, root_dir):
    for directory, data in secret_data.items():
        if not os.path.exists(directory) or not os.path.isdir(directory):
            print(f"{WARNING_COLOR}Warning: '{directory}' is not a valid directory. Skipping.{RESET}")
            continue

        secrets_folder = os.path.join(directory, 'secrets')

        for container, container_data in data.items():
            print(f"Storing secrets for {directory} - {container}")
            env_file_path = os.path.join(secrets_folder, container + ".env")

            with open(env_file_path, 'w') as env_file:
                if container_data["private"]:
                    env_file.write("# Private\n")
                    for k, v in container_data["private"].items():
                        env_file.write(f"{k}={v}\n")
                else:
                    print("\tSkipping private secret generation. No secrets neccessary.")

                if container_data["public"]:
                    env_file.write("\n# Public\n")
                    for k, v in container_data["public"].items():
                        env_file.write(f"{k}={v}\n")
                else:
                    print("\tSkipping public secret generation. No secrets necessary.")

            print(f"Successfully stored secrets")


# Function to create a publicSecrets.txt file in the root directory
def create_public_secrets_file(env_secret_data, root_dir, public_secrets_name):
    public_secrets_file_path = os.path.join(root_dir, public_secrets_name)

    # Create the empty file
    open(public_secrets_file_path, 'a').close()

    # Apply chmod 700 to the publicSecrets.txt file
    subprocess.check_call(['sudo', 'chmod', '700', public_secrets_file_path])
    print(f"Modified permissions for '{HIGHLIGHT_COLOR}{public_secrets_file_path}{RESET}' with chmod 700")

    with open(public_secrets_file_path, 'w') as public_secrets_file:
        for directory, data in env_secret_data.items():
            for container, container_data in data.items():
                if container_data["public"]:
                    public_secrets_file.write(f"# {directory} - {container}\n")
                    for key, value in container_data['public'].items():
                        public_secrets_file.write(f"{key}={value}\n")
                    public_secrets_file.write('\n')
                else:
                    print(f"\tSkipping public secrets for {directory} - {container}. No public secrets necessary.")

    print("Successfully created public secrets file")


# Function to traverse subdirectories and store parsed and secret data in a dictionary
def process_directories(root_dir):
    print(f"{INFO_COLOR}Processing subdirectories of {root_dir}{RESET}")
    env_secret_data = {}

    for dirname in os.listdir(root_dir):
        current_dir = os.path.join(root_dir, dirname)
        if os.path.isdir(current_dir):
            print(f"\t{INFO_COLOR}Validating {current_dir}{RESET}")
            if restrict_secrets_directory(current_dir):
                print(f"\t{INFO_COLOR}Processing {current_dir}{RESET}")
                parsed_data = process_yaml_file(current_dir)
                if parsed_data is not None:
                    env_secret_data[current_dir] = create_secrets(parsed_data['env_files'])
                    print(f"\tSuccessfully processed {current_dir}")

    return env_secret_data

def print_statistics(env_secret_data):
    print(f"{HIGHLIGHT_COLOR}Finished Execution.{RESET}")

    container_number = 0
    public_secrets_number = 0
    private_secrets_number = 0
    for directory, data in env_secret_data:
        for container, container_data in data:
            container_number += 1
            public_secrets_number += len(container_data['public'])
            private_secrets_number += len(container_data['private'])

    print(f"Created secrets for {HIGHLIGHT_COLOR}{len(env_secret_data)}{RESET} servers and {HIGHLIGHT_COLOR}{container_number}{RESET} containers")
    print(f"Created {HIGHLIGHT_COLOR}{public_secrets_number}{RESET} public secrets")
    print(f"And {HIGHLIGHT_COLOR}{private_secrets_number}{RESET} private secrets")

def clean_before_start(root_dir, public_secrets_name):
    print("Cleaning up before generation")
    public_secrets_file = os.path.join(root_dir, public_secrets_name)
    if os.path.exists(public_secrets_file):
        os.remove(public_secrets_file)
        print("\tRemoved old public secrets file")

    for dirname in os.listdir(root_dir):
        current_dir = os.path.join(root_dir, dirname)
        if os.path.isdir(current_dir):
            print(f"\tCleaning up service {dirname}")
            secrets_dir = os.path.join(current_dir, 'secrets')
            if os.path.isdir(secrets_dir):
                shutil.rmtree(secrets_dir)
                print("\t\tRemoved old secrets dir")
            os.mkdir(secrets_dir)
            subprocess.check_call(["sudo", "chmod", "700", secrets_dir])
            print("\t\tCreated new secrets directory and made it owned by root.")
        


# Specify the root directory to start the search
root_directory = "./servers"
public_secrets_file_name="publicSecrets.txt"

if os.getuid() == 0:  # Check if the script is executed with root rights
    clean_before_start(root_directory, public_secrets_file_name)
    env_secret_data = process_directories(root_directory)
    generate_secret_files(env_secret_data, root_directory)
    create_public_secrets_file(env_secret_data, root_directory, public_secrets_file_name)
else:
    print(f"{ERROR_COLOR}Please execute the script with root rights.{RESET}")
