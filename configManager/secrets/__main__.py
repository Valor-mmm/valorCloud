import click

from .. import default_root_directory, all_servers_option
from ..parseServerConfig import find_servers
from ..utils import check_run_with_root

from .clean import clean as clean_command
from .generate import generate as generate_command
from .statistics import statistics as statistics_command

from .handlers.handlerManager import handler_names, get_hander_by_name


def get_server_names(servers):
    server_names = [server['name'] for server in servers]
    server_names.append(all_servers_option)
    return server_names

def filter_servers(servers):
    """Filters the servers and excludes all servers without a secrets config"""
    return [server for server in servers if len(server["containers"]) > 0]


server_config = find_servers(default_root_directory, False)
relevant_server_config = filter_servers(server_config)


# Click command to clean before starting
@click.command()
@click.option('--target', required=True, prompt=True, prompt_required=True,
              type=click.Choice(get_server_names(relevant_server_config)))
@click.option('--handler', default=handler_names[0], type=click.Choice(handler_names))
@click.option('--debug', default=False, type=bool)
def clean(target, handler, debug):
    click.echo("\n")
    check_run_with_root()
    handler_instance = get_hander_by_name(handler)
    clean_command(target, handler_instance, relevant_server_config, default_root_directory, debug)


# Click command to generate secrets
@click.command()
@click.option('--target', required=True, prompt=True, prompt_required=True,
              type=click.Choice(get_server_names(relevant_server_config)))
@click.option('--handler', default=handler_names[0], type=click.Choice(handler_names))
@click.option('--debug', default=False, type=bool)
def generate(target, handler, debug):
    click.echo("\n")
    check_run_with_root()
    handler_instance = get_hander_by_name(handler)
    generate_command(target, handler_instance, relevant_server_config, default_root_directory, debug)


@click.command()
@click.option('--target', default="all", required=True, prompt=True, prompt_required=True,
              type=click.Choice(get_server_names(relevant_server_config)))
@click.option('--handler', default=handler_names[0], type=click.Choice(handler_names))
@click.option('--debug', default=False, type=bool)
def stats(target, handler, debug):
    """Display statistics for generated secrets."""
    click.echo("\n")
    check_run_with_root()
    handler_instance = get_hander_by_name(handler)
    statistics_command(target, handler_instance, relevant_server_config, default_root_directory, debug)


# Define the CLI group
@click.group()
def cli():
    pass


# Add the Click commands to the CLI group
cli.add_command(clean)
cli.add_command(generate)
cli.add_command(stats)

if __name__ == '__main__':
    cli()
