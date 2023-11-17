from typing import List
import os

import click

from . import all_servers_option
from .parseServerConfig import Server


def check_run_with_root():
    if os.getuid() != 0:  # Check if the script is executed with root rights
        click.secho("Please execute the script with root rights!", fg="red", err=True, bold=True)
        raise PermissionError("Executed without root priveleges.")


def filter_server_config_by_target(target: str, server_config: List[Server]) -> List[Server]:
    if target == all_servers_option:
        return server_config

    for server in server_config:
        if server["name"] == target and len(server["containers"]) > 0:
            return [server]

    click.secho(f"Could not find a target server '{target}' in the provided server config.", err=True, fg='red',
                bold=True)
    raise ValueError(f"Target server {target} could not be found in the server config")
