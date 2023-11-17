import os
from typing import TypedDict, Optional, List

from schema import Schema, SchemaError, Optional as OptionalSchema
import click
import yaml


class ContainerSecrets(TypedDict):
    public: Optional[List[str]]
    private: Optional[List[str]]
    fixed: Optional[List[str]]


class Container(TypedDict):
    name: str
    secrets: ContainerSecrets


class Server(TypedDict):
    name: str
    containers: List[Container]


# Define the schema for a single block
block_schema = {
    OptionalSchema("public"): [str],
    OptionalSchema("private"): [str],
    OptionalSchema("fixed"): [str]
}

# Define the schema for the entire YAML file
yaml_schema = {
    "env_files": {str: block_schema}
}


# Function to process the 'needed-secrets.yaml' file in a subdirectory
def process_secrets_yaml_file(directory: str, debug: bool):
    yaml_file_path = os.path.join(directory, 'needed-secrets.yaml')

    if not os.path.exists(yaml_file_path):
        click.secho(f"\n'needed-secrets.yaml' file does not exist in {directory}. Skipping.", fg='cyan',
                    bold=True)
        return None

    try:
        with open(yaml_file_path, 'r') as yaml_file:
            loaded_data = yaml.safe_load(yaml_file)

            # Validate yaml file with schema
            schema = Schema(yaml_schema)
            schema.validate(loaded_data)

            if debug:
                click.echo(f"Successfully loaded secrets yaml file {yaml_file_path}.")

            # Return the validated data
            return loaded_data

    except SchemaError as e:
        click.secho(f"Warning: 'needed-secrets.yaml' validation failed in {directory}. Skipping.", fg='yellow',
                    bold=True)
        click.secho(str(e), fg='yellow', bold=True)
    except Exception as e:
        click.secho(f"Warning: Error while processing 'needed-secrets.yaml' in {directory}. Skipping.", fg='yellow',
                    bold=True)
        click.secho(f"Error details: {str(e)}", fg='yellow', bold=True)
    return None


def parse_server_config(directory: str, dirname: str, debug: bool) -> Server:
    server_secrets = process_secrets_yaml_file(directory, debug)
    containers = []

    if server_secrets is not None:
        for container, container_data in server_secrets["env_files"].items():
            container_secrets_dict: ContainerSecrets = container_data
            container_dict: Container = {
                "name": container,
                "secrets": container_secrets_dict
            }
            containers.append(container_dict)

    server: Server = {
        "name": dirname,
        "containers": containers
    }

    return server


def find_servers(root_dir: str, debug: bool) -> List[Server]:
    """
    Finds all Subdirectories in the root dir and assumes they are servers
    Fetches the configuration files (e.g. secrets) for the server and adds the information into the typed dict
    Returns a list of servers and their retrieved configuration
    """
    directory_items = os.listdir(root_dir)
    subdirectories = [item for item in directory_items if os.path.isdir(os.path.join(root_dir, item))]
    server_info = []

    if debug:
        click.secho(f"Scanning the following directories for config items: {subdirectories}")

    with click.progressbar(subdirectories, label="Listing servers and fetching their configuration...",
                           show_eta=True, show_pos=True) as bar:
        for dirname in bar:
            current_dir = os.path.join(root_dir, dirname)

            if debug:
                click.secho(f"\nFetching data for server {dirname}", fg='cyan')
            server = parse_server_config(current_dir, dirname, debug)
            if not server:
                click.secho(f"Could not fetch info for directory {current_dir}.", fg='yellow', bold=True)
            else:
                server_info.append(server)
    return server_info
