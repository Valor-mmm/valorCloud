import click

from .fileHandler import FileSecretHandler

handler_names = [FileSecretHandler.get_hander_name()]


def get_hander_by_name(handler_name):
    if handler_name == FileSecretHandler.get_hander_name():
        return FileSecretHandler()
    else:
        click.secho(f"There is no hander for {handler_name} in the handerManager", err=True, bold=True, fg='red')
        raise NotImplementedError(f"No handler for {handler_name} has been implemented")
