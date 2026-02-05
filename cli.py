import click
import main
import json
import sys
from typing import Optional


class CliContext:
    """Context object to store CLI state."""
    
    def __init__(self):
        self.token: Optional[str] = None


pass_context = click.make_pass_decorator(CliContext, ensure=True)


@click.group()
@click.pass_context
def cli(ctx):
    """Unofficial CAME Connect CLI."""
    # Initialize context
    ctx.obj = CliContext()
    
    # Validate environment variables before proceeding
    try:
        main.validate_env_vars()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
@pass_context
def devices(ctx: CliContext):
    """Manage Devices."""
    # Fetch token when needed
    if ctx.token is None:
        try:
            ctx.token = main.fetch_token()
        except Exception as e:
            click.echo(f"Error fetching token: {e}", err=True)
            sys.exit(1)


@cli.group()
@pass_context
def site(ctx: CliContext):
    """Manages Sites."""
    # Fetch token when needed
    if ctx.token is None:
        try:
            ctx.token = main.fetch_token()
        except Exception as e:
            click.echo(f"Error fetching token: {e}", err=True)
            sys.exit(1)


@site.command("read")
@pass_context
def sites_read(ctx: CliContext):
    """Read sites"""
    try:
        sites = main.fetch_sites(ctx.token)
        click.echo(json.dumps(sites, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@devices.command("read")
@pass_context
def devices_read(ctx: CliContext):
    """Read Devices"""
    try:
        devices_list = main.fetch_devices(ctx.token)
        click.echo(json.dumps(devices_list, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@devices.command("status")
@pass_context
def devices_status(ctx: CliContext):
    """Read Device Statuses"""
    try:
        statuses = main.fetch_device_statuses(ctx.token)
        click.echo(json.dumps(statuses, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@devices.command("commands")
@click.argument("device_id", type=int)
@pass_context
def device_commands(ctx: CliContext, device_id: int):
    """Read Device Commands"""
    try:
        commands = main.fetch_commands_for_device(ctx.token, str(device_id))
        click.echo(json.dumps(commands, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@devices.command("run_command")
@click.argument("device_id", type=int)
@click.argument("command_id", type=int)
@pass_context
def device_run_command(ctx: CliContext, device_id: int, command_id: int):
    """Run a Device Command"""
    try:
        run = main.run_command_for_device(ctx.token, str(device_id), str(command_id))
        click.echo(json.dumps(run, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
