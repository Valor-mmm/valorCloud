from typing import List
import os
import shutil
import subprocess

import click

from ..parseServerConfig import Server
from ..utils import filter_server_config_by_target
from .handlers import SecretHandler, KV_Server


def create_env_files(server_secrets: List[KV_Server], root_directory: str, debug: bool) -> None:
    with click.progressbar(server_secrets, label="Creating env files for target secrets", show_pos=True):
        for server in server_secrets:
            server_path = os.path.join(root_directory, server["name"])

            if not os.path.exists(server_path) or not os.path.isdir(server_path):
                click.secho(f'Skipping env generation for {server["name"]}. Could not find directory of server.',
                            fg='yellow', bold=True)
                continue

            # Create secrets folder and modify the permissions (assumes secrets folder has been removed beforehand)
            secrets_folder = os.path.join(server_path, 'secrets')
            os.makedirs(secrets_folder)
            subprocess.check_call(['sudo', 'chmod', '700', secrets_folder])

            for container in server["containers"]:
                env_file_path = os.path.join(secrets_folder, container["name"] + ".env")

                with open(env_file_path, 'w') as env_file:
                    if container["secrets"]["private"] and len(container["secrets"]["private"]) > 0:
                        env_file.write("# Private\n")
                        for secret in container["secrets"]["private"]:
                            env_file.write(f"{secret['key']}={secret['value']}\n")
                            env_file.write("\n")
                    elif debug:
                        click.secho(
                            f"Skipping private secrets for {server['name']}-{container['name']}. No private secrets to write")

                    if container["secrets"]["public"] and len(container["secrets"]["public"]) > 0:
                        env_file.write("# Public\n")
                        for secret in container["secrets"]["public"]:
                            env_file.write(f"{secret['key']}={secret['value']}\n")
                            env_file.write("\n")
                    elif debug:
                        click.secho(
                            f"Skipping public secrets for {server['name']}-{container['name']}. No public secrets to write")
   
                    if container["secrets"]["fixed"] and len(container["secrets"]["fixed"]) > 0:
                        env_file.write("# Fixed\n")
                        for secret in container["secrets"]["fixed"]:
                            env_file.write(f"{secret['key']}={secret['value']}\n")
                        env_file.write("\n")
                    elif debug:
                        click.secho(
                            f"Skipping fixed secrets for {server['name']}-{container['name']}. No fixed secrets to write")
   

def remove_env_files(servers: List[str], root_directory: str, debug: bool) -> None:
    for server in servers:
        try:
            server_secrets_path = os.path.join(root_directory, server, 'secrets')
            shutil.rmtree(server_secrets_path)
        except FileNotFoundError:
            if debug:
                click.secho(f"Could not delete secret env directory for server {server} as it does not exist")
        except Exception as e:
            click.secho(f"Could not delete secret env directory for server {server}", fg='red', err=True, bold=True)
            click.secho(e, fg='red', err=True)


def generate(target: str, handler: SecretHandler, server_config: List[Server], root_directory: str,
             debug: bool) -> None:
    target_servers = filter_server_config_by_target(target, server_config)

    # Cleanup handler and secrets folder 
    handler.clean(target, root_directory, debug)
    remove_env_files([server["name"] for server in target_servers], root_directory, debug)
    click.echo("\n")

    # Generate all secrets
    secrets = handler.generate_secrets(target_servers, root_directory, debug)
    click.echo("\n")

    # Create env files for the target servers
    create_env_files(secrets, root_directory, debug)
    click.echo("\n")

    # Publish the public secrets
    handler.publish_public_secrets(secrets, root_directory, debug)
    click.echo("\n")
    
    click.secho(f"Successfully generated secrets for {target} with handler '{handler.get_hander_name()}'", fg='bright_green', blink=True, bold=True, underline=True)
