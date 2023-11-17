from typing import List
import os
import subprocess
import secrets as secrets_lib

import click

from . import SecretHandler, KV_Server, KV_Container, KV_ContainerSecrets, KeyValuePair
from ...parseServerConfig import Server
from ... import all_servers_option

public_secrets_file_name = "publicSecrets.txt"


class FileSecretHandler(SecretHandler):
    @staticmethod
    def get_hander_name() -> str:
        return 'file'

    @staticmethod
    def _read_fixed_secrets(root_directory: str, server_name: str, container_name: str, fixed_secrets: [str],
                            debug: bool) -> List[KeyValuePair]:
        if len(fixed_secrets) < 1:
            if debug:
                click.secho(f"Skipping fixed secrets. No fixed secrets necessary for {server_name} - {container_name}")
            return []
        
        fixed_secret_file_path = os.path.join(root_directory, 'fixed_secrets.txt')

        # Ensure the file exists and can be opened
        try:
            with open(fixed_secret_file_path, 'r'):
                pass
        except Exception as e:
            click.secho(f"Could not open file {fixed_secret_file_path} from cwd {os.getcwd()}", fg='red', bold=True,
                        err=True)
            click.echo(e, err=True)
            raise FileNotFoundError('Could not open fixed secrets file.')

        # Make sure the fixed_secrets.txt file is protected with required root access
        subprocess.check_call(['sudo', 'chmod', '700', fixed_secret_file_path])
        if debug:
            click.secho(f"Restricting rights of {fixed_secret_file_path} to root access just to make sure its safe.")

        # Reads a fixed_secrets.txt file
        # Assumes a structure of headline (server_name - container_name) and key value pairs
        kv_fixed_secrets = []
        headline_reached = False
        with open(fixed_secret_file_path, 'r') as fixed_secrets_file:
            for line in fixed_secrets_file:
                stripped_line = line.strip()
                expected_headline = f"# {server_name} - {container_name}"

                if stripped_line == expected_headline:
                    print("Headline detected")
                    headline_reached = True
                elif headline_reached and stripped_line.startswith('#'):
                    click.secho(f"Could not find all fixed secrets for {server_name}-{container_name}: {fixed_secrets}",
                                fg="yellow", bold=True)
                    break
                elif headline_reached:
                    split_secret = [kv.strip() for kv in stripped_line.split('=')]
                    secret_name = split_secret[0]
                    secret_value = split_secret[1]

                    if secret_name not in fixed_secrets:
                        click.secho(
                            f"Fixed secret {secret_name} is present in the fixed_secrets file but not listed as requirement for {server_name}-{container_name}",
                            fg='yellow', bold=True)
                    else:
                        secret: KeyValuePair = {"key": secret_name, "value": secret_value}
                        kv_fixed_secrets.append(secret)

                        if len(kv_fixed_secrets) == len(fixed_secrets):
                            if debug:
                                click.secho(f"Finished reading all secrets for {server_name}-{container_name}")
                            return kv_fixed_secrets
            click.secho(f"Could not find necessary secret headline for {server_name}{container_name}", fg='yellow', bold=True)

    def generate_secrets(self, server_config: List[Server], root_directory: str, debug: bool) -> List[KV_Server]:
        generated_secrets = []

        for server in server_config:
            kv_containers: List[KV_Container] = []
            for container in server['containers']:
                secrets: KV_ContainerSecrets = {
                    "public": list(map(lambda x: {"key": x, "value": secrets_lib.token_hex(32)},
                                       container['secrets'].get('public', []))),
                    "private": list(map(lambda x: {"key": x, "value": secrets_lib.token_hex(32)},
                                        container['secrets'].get('private', []))),
                    "fixed": FileSecretHandler._read_fixed_secrets(root_directory, server["name"], container["name"],
                                                                   container['secrets'].get('fixed', []), debug)
                }

                kv_container: KV_Container = {
                    "name": container["name"],
                    "secrets": secrets
                }
                kv_containers.append(kv_container)
            server: KV_Server = {
                "name": server["name"],
                "containers": kv_containers
            }
            generated_secrets.append(server)
        return generated_secrets

    def publish_public_secrets(self, kv_server_config: List[KV_Server], root_directory: str, debug: bool) -> None:
        # Clean befor publishing
        self.clean(all_servers_option, root_directory,
                   debug)  # TODO adjust to clean call per KV_Server in List after clean supports cleanup by target

        public_secrets_file_path = os.path.join(root_directory, public_secrets_file_name)

        # Create public secret file if it not exists already
        open(public_secrets_file_path, 'a').close()

        # Apply chmod 700 to the publicSecrets.txt file
        subprocess.check_call(['sudo', 'chmod', '700', public_secrets_file_path])

        if debug:
            click.secho(
                "Updated permissions of public secrets file to make sure only root privilege users can access it.")

        with click.progressbar(length=0, label="Publishing public secrets to public secrets file") as spinner:
            try:
                with open(public_secrets_file_path, 'a') as public_secrets_file:
                    for server in kv_server_config:
                        for container in server["containers"]:
                            public_secrets = container["secrets"]["public"]
                            if public_secrets and len(public_secrets) > 0:
                                # Write headline
                                public_secrets_file.write(f'# {server["name"]} - {container["name"]}\n')

                                # Write secrets
                                for secret in public_secrets:
                                    public_secrets_file.write(f'{secret["key"]}={secret["value"]}\n')
                                public_secrets_file.write('\n')
                            elif debug:
                                click.secho(
                                    f'Skipping public secret publishing for {server["name"]}-{container["name"]}. No public secrets available/needed')
            except Exception as e:
                click.secho("Could not publish public secrets into public secrets file. Some error occurred.", fg='red',
                            err=True, bold=True)
                click.secho(e, err=True)
                raise e
            finally:
                spinner.update(1)

    # TODO: Enable this to be target specific; (will currently only enable you to clean all public secrets)
    def clean(self, target: str, root_directory: str, debug: bool) -> None:
        click.secho(
            'Currently only all public secrets can be deleted by the File SecretHandler.\nPlease confirm that you really want to delete all public secrets',
            fg='yellow', bold=True)
        click.confirm(
            'Are you sure you want to delete all public secrets? All servers will continue to work but you will not have easy access to the public passwords anymore.',
            abort=True)

        public_secrets_file_path = os.path.join(root_directory, public_secrets_file_name)

        if debug:
            click.secho(
                f"Attempting to delete public secrets file with path {public_secrets_file_path} at cwd {os.getcwd()}")
        try:
            os.remove(public_secrets_file_path)
            click.secho('Public Secrets File secrets file has been successfully deleted', fg='green')
        except FileNotFoundError:
            click.secho(f"Could not delete public secrets file as there is none at {public_secrets_file_path}",
                        fg='cyan')
        except Exception as e:
            click.secho(f"Could not delete public secrets file at {public_secrets_file_path}", err=True, fg='red',
                        bold=True)
            click.secho(e, fg='red', err=True)
