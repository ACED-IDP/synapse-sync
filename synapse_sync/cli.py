import json
import pathlib
import subprocess
import sys

import synapseclient
import click
import yaml
from synapseclient import Synapse
import gen3_util.config


def login(debug: bool) -> Synapse:
    """Login to synapse."""
    # click.secho(f"Logging in to synapse", fg="yellow", file=sys.stderr)

    try:

        syn = synapseclient.Synapse(debug=debug)
        syn.login(silent=True)
        return syn

    except Exception as e:
        if not pathlib.Path('~/.synapseConfig').expanduser().exists():
            click.secho(f"Please setup ~/.synapseConfig",
                        fg="red",
                        file=sys.stderr
                        )
        click.secho(
            message=f"{e} see\n" +
                    "https://python-docs.synapse.org/tutorials/authentication/#prerequisites\n" +
                    "https://help.synapse.org/docs/Client-Configuration.1985446156.html#ClientConfiguration-ForDevelopers",
            fg="red",
            file=sys.stderr
        )


def default_config() -> dict:
    """Return the default configuration."""
    return {
        "synapse_teams": [
            {
                "id": "3499899",
                "name": "AI_READI"
            },
            {
                "id": "3499900",
                "name": "CHoRUS"
            },
            {
                "id": "3499897",
                "name": "CM4AI"
            },
            {
                "id": "3499898",
                "name": "Voice"
            }
        ]
    }


@click.group()
@click.option('--config', type=click.Path(exists=True), default=None, help="path to config file")
@click.pass_context
def cli(ctx, config):
    """Sync synapse teams with gen3."""
    ctx.ensure_object(dict)
    if config:
        with open(config) as f:
            ctx.obj['config'] = yaml.safe_load(f)
            # click.secho(f"Using config file {config}", fg="yellow", file=sys.stderr)
    else:
        ctx.obj['config'] = default_config()
        # click.secho(f"Using default config", fg="yellow", file=sys.stderr)


def get_current_requests():
    """Get Gen3 current requests."""
    # run cmd, return stdout

    # click.secho(f"Getting current gen3 users", fg="yellow", file=sys.stderr)
    cmd = "g3t --format json utilities access ls --all"
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        json_output = json.loads(output)
        return json_output
    except subprocess.CalledProcessError as e:
        click.secho(f"Command '{cmd}' failed with error: {e}", fg="red", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        click.secho(f"Failed to parse JSON output from command '{cmd}': {e}", fg="red", file=sys.stderr)
        return None


@cli.group()
@click.pass_context
def teams(ctx):
    """Teams commands."""
    pass


@teams.command("ls")
@click.option('--debug', is_flag=True, default=False, help="log synapse calls")
@click.option('--long', '-l', is_flag=True, default=False, help="show user name")
@click.argument('team_id', required=False, default=None)
@click.pass_context
def teams_ls(ctx, debug: bool, team_id: str, long: bool):
    """List commands to add users (and current status) of a team to gen3.

    \b
TEAM_ID one of:
* AI_READI: https://www.synapse.org/#!Team:3499899
* CHoRUS: https://www.synapse.org/#!Team:3499900
* CM4AI: https://www.synapse.org/#!Team:3499897
* Voice: https://www.synapse.org/#!Team:3499898
    """

    try:
        config = gen3_util.config.default()
        click.secho(f"gen3 project_id: {config.gen3.project_id}", fg="yellow", file=sys.stderr)

        if not team_id:
            program, project = config.gen3.project_id.split('-')
            # click.secho(f"using gen3 project: {project} as team_id", fg="yellow", file=sys.stderr)
            team_id = project

        valid_team_ids = [_['id'] == team_id for _ in ctx.obj['config']['synapse_teams']]
        valid_teams = {_['name']: _['id'] for _ in ctx.obj['config']['synapse_teams']}
        if team_id.isnumeric():
            if team_id not in valid_team_ids:
                click.secho(f"Invalid team id {team_id} should be one of {valid_teams}", fg="red", file=sys.stderr)
                return
        else:
            if team_id not in valid_teams:
                click.secho(f"Invalid team name {team_id} should be one of {valid_teams}", fg="red", file=sys.stderr)
                return
            team_id = valid_teams[team_id]

        syn = login(debug)

        current_requests = get_current_requests()
        if not current_requests:
            current_requests = {'requests': []}
            click.secho(f"Failed to get current requests, proceeding, status may not be accurate.", fg="yellow", file=sys.stderr)
        if 'requests' not in current_requests:
            current_requests['requests'] = []
            click.secho(current_requests['msg'], fg="yellow", file=sys.stderr)
        assert 'requests' in current_requests, f"Expected 'requests' in {current_requests}"

        current_users = {_.get('username'): _ for _ in current_requests['requests'] if project in _['policy_id']}
        # for k, v in current_users.items():
        #     print(k, v['policy_id'], v['username'], v['status'], v['updated_time'])

        team = syn.getTeam(team_id)
        click.secho(f"Syncing team: {team.name}", fg="yellow", file=sys.stderr)
        cmds = []
        for _ in syn.getTeamMembers(team):
            user_name_msg = ''
            username = f'{_.member.ownerId} (Synapse ID)'
            cmd = f"g3t utilities users add --username"
            if long:
                user_name_msg = f' # {_.member.userName}'
                if username in current_users:
                    usr = current_users[username]
                    user_name_msg += f" STATUS {usr['status']} {usr['updated_time']} {usr['policy_id']} "
                    click.secho(f"# '{username}'{user_name_msg}", fg="green", file=sys.stderr)
                    continue
                else:
                    user_name_msg += f" STATUS NONE"
            cmds.append(f"{cmd} '{_.member.ownerId} (Synapse ID)'{user_name_msg}")

        if cmds:
            click.secho("# <cmd> # name status updated_time policy_id", fg="yellow", file=sys.stderr)
            for cmd in cmds:
                print(cmd)

    except Exception as e:
        click.secho(f"{e.__class__.__name__} {e}", fg="red", file=sys.stderr)
        if debug:
            raise e
