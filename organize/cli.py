"""
organize

The file management automation tool.
"""
import os
import sys

import click
from fs import appfs, osfs

from . import output
from .__version__ import __version__
from .output import console

DOCS_URL = "https://organize.readthedocs.io"
DEFAULT_CONFIG = """# organize configuration file
# {docs}

rules:
  locations:
    -
  filters:
    -
  actions:
    -
""".format(
    docs=DOCS_URL
)

try:
    config_filename = "config.yaml"
    if os.getenv("ORGANIZE_CONFIG"):
        dirname, config_filename = os.path.split(os.getenv("ORGANIZE_CONFIG"))
        config_fs = osfs.OSFS(dirname, create=False)
    else:
        config_fs = appfs.UserConfigFS("organize", create=True)

    if not config_fs.exists(config_filename):
        config_fs.writetext(config_filename, DEFAULT_CONFIG)
    CONFIG_PATH = config_fs.getsyspath(config_filename)
except Exception as e:
    output.error(str(e), title="Config file")
    sys.exit(1)


class NaturalOrderGroup(click.Group):
    def list_commands(self, ctx):
        return self.commands.keys()


CLI_CONFIG = click.argument(
    "config",
    required=False,
    default=CONFIG_PATH,
    type=click.Path(exists=True),
)
CLI_WORKING_DIR_OPTION = click.option(
    "--working-dir",
    default=".",
    type=click.Path(exists=True),
    help="The working directory",
)
# for CLI backwards compatibility with organize v1.x
CLI_CONFIG_FILE_OPTION = click.option(
    "--config-file",
    default=None,
    hidden=True,
    type=click.Path(exists=True),
)


@click.group(
    help=__doc__,
    cls=NaturalOrderGroup,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.version_option(__version__)
def cli():
    pass


@cli.command()
@CLI_CONFIG
@CLI_WORKING_DIR_OPTION
@CLI_CONFIG_FILE_OPTION
def run(config, working_dir, config_file):
    """Organizes your files according to your rules."""
    from .core import run_file

    if config_file:
        config = config_file
        output.deprecated(
            "The --config-file option can now be omitted. See organize --help."
        )
    run_file(config_file=config, working_dir=working_dir, simulate=False)


@cli.command()
@CLI_CONFIG
@CLI_WORKING_DIR_OPTION
@CLI_CONFIG_FILE_OPTION
def sim(config, working_dir, config_file):
    """Simulates a run (does not touch your files)."""
    from .core import run_file

    if config_file:
        config = config_file
        output.deprecated(
            "The --config-file option can now be omitted. See organize --help."
        )
    run_file(config_file=config, working_dir=working_dir, simulate=True)


@cli.command()
@click.argument(
    "config",
    required=False,
    default=CONFIG_PATH,
    type=click.Path(),
)
@click.option(
    "--editor",
    envvar="EDITOR",
    help="The editor to use. (Default: $EDITOR)",
)
def edit(config, editor):
    """Edit the rules.

    If called without arguments it will open the default config file in $EDITOR.
    """
    click.edit(filename=config, editor=editor)


@cli.command()
@CLI_CONFIG
def check(config):
    """Checks whether a given config file is valid.

    If called without arguments it will check the default config file.
    """
    print(config)


@cli.command()
@click.option("--path", is_flag=True, help="Print the path instead of revealing it.")
def reveal(path):
    """Reveals the default config file."""
    if path:
        click.echo(CONFIG_PATH)
    else:
        click.launch(str(CONFIG_PATH), locate=True)


@cli.command()
def schema():
    """Prints the json schema for config files."""
    import json

    from .config import CONFIG_SCHEMA

    js = json.dumps(
        CONFIG_SCHEMA.json_schema(
            schema_id="https://tfeldmann.de/organize.schema.json",
        )
    )
    console.print_json(js)


@cli.command()
def docs():
    """Opens the documentation."""
    click.launch(DOCS_URL)


# deprecated - only here for backwards compatibility
@cli.command(hidden=True)
@click.option("--path", is_flag=True, help="Print the default config file path")
@click.option("--debug", is_flag=True, help="Debug the default config file")
@click.option("--open-folder", is_flag=True)
@click.pass_context
def config(ctx, path, debug, open_folder):
    """Edit the default configuration file."""
    if open_folder:
        ctx.invoke(reveal)
    elif path:
        ctx.invoke(reveal, path=True)
        return
    elif debug:
        ctx.invoke(check)
    else:
        ctx.invoke(edit)
    output.deprecated("`organize config` is deprecated.")
    output.deprecated("Please see `organize --help` for all available commands.")


if __name__ == "__main__":
    cli()


# def config_debug(config_path: Path) -> None:
#     """prints the config with resolved yaml aliases, checks rules syntax and checks
#     whether the given folders exist
#     """
#     print(str(config_path))
#     haserr = False
#     # check config syntax
#     try:
#         print(Style.BRIGHT + "Your configuration as seen by the parser:")
#         config = Config.from_file(config_path)
#         if not config.config:
#             print_error("Config file is empty")
#             return
#         print(config.yaml())
#         rules = config.rules
#         print("Config file syntax seems fine!")
#     except Config.Error as e:
#         haserr = True
#         print_error(e)
#     else:
#         # check whether all folders exists:
#         allfolders = set(flatten([rule.folders for rule in rules]))
#         for f in allfolders:
#             if not fullpath(f).exists():
#                 haserr = True
#                 print(Fore.YELLOW + 'Warning: "%s" does not exist!' % f)

#     if not haserr:
#         print(Fore.GREEN + Style.BRIGHT + "No config problems found.")


# def list_actions_and_filters() -> None:
#     """Prints a list of available actions and filters"""
#     import inspect  # pylint: disable=import-outside-toplevel

#     from organize import actions, filters  # pylint: disable=import-outside-toplevel

#     print(Style.BRIGHT + "Filters:")
#     for name, _ in inspect.getmembers(filters, inspect.isclass):
#         print("  " + name)
#     print()
#     print(Style.BRIGHT + "Actions:")
#     for name, _ in inspect.getmembers(actions, inspect.isclass):
#         print("  " + name)
