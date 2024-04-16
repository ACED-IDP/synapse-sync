import contextlib
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime

import gen3_util
import requests
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
    _ = {
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
        ],
        "admin_users": []
    }
    _['admin_users'] = """
beckmanl@ohsu.edu
ellrott@ohsu.edu
leejor@ohsu.edu
peterkor@ohsu.edu
walsbr@ohsu.edu
wongq@ohsu.edu
""".strip().split('\n')
    return _


def get_gen3_users():
    """Get gen3 users."""
    arborist_service_port = os.environ.get('ARBORIST_SERVICE_PORT', None)
    assert arborist_service_port, "ARBORIST_SERVICE_PORT not set, are you running on a gen3 commons POD?"
    url = arborist_service_port.replace('tcp', 'http')
    url = f"{url}/user"
    response = requests.get(url)
    assert response.status_code == 200, f"Failed to get users {response.status_code} {response.text}"
    return response.json()


def get_gen3_users_mock():
    """Get gen3 users."""
    with open('users.json') as f:
        return json.load(f)


@click.group()
@click.option('--config', type=click.Path(exists=True), default=None, help="path to config file", envvar="SYNAPSE_SYNC_CONFIG" )
@click.pass_context
def cli(ctx, config):
    """Sync synapse teams with gen3."""
    ctx.ensure_object(dict)
    if config:
        with open(config) as f:
            ctx.obj['config'] = yaml.safe_load(f)
            click.secho(f"Using config file {config}", fg="yellow", file=sys.stderr)
    else:
        ctx.obj['config'] = default_config()
        click.secho(f"Using default config", fg="yellow", file=sys.stderr)


def run_cmd(cmd: str, dry_run: bool):
    """Run a command."""
    try:
        if dry_run:
            click.secho(f"DRY RUN: {cmd}", fg="yellow", file=sys.stderr)
            return None
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            click.secho(f"Command '{cmd}' failed with error: {result.stderr.decode('utf-8')}", fg="red", file=sys.stderr)
            return None
        output = result.stdout.decode('utf-8')
        return output
    except subprocess.CalledProcessError as e:
        click.secho(f"Command '{cmd}' failed with error: {e}, {result.stdout.decode('utf-8')}", fg="red", file=sys.stderr)
        return None


def get_current_requests(project):
    """Get Gen3 current requests."""
    # run cmd, return stdout

    # click.secho(f"Getting current gen3 users", fg="yellow", file=sys.stderr)
    try:
        cmd = "g3t --format json utilities access ls --all"
        output = run_cmd(cmd, dry_run=False)
        json_output = json.loads(output)
        assert 'requests' in json_output, f"Expected 'requests' in {json_output}"
        return {
            'requests': [_ for _ in json_output['requests'] if
                         _['status'] == 'SIGNED' and project in _['policy_id'] and not _['revoke']]
        }

        return json_output
    except json.JSONDecodeError as e:
        click.secho(f"Failed to parse JSON output from command '{cmd}': {e}", fg="red", file=sys.stderr)
        return None


@cli.command()
@click.pass_context
def config(ctx):
    """Print current config."""
    print(yaml.dump(ctx.obj['config']))


@cli.group()
@click.pass_context
def teams(ctx):
    """Teams commands."""
    pass


@teams.command("sync")
@click.option('--debug', is_flag=True, default=False, help="Show debug output.")
@click.option('--dry_run', is_flag=True, default=False, help="List cmds, don't run them")
@click.pass_context
def teams_sync(ctx, debug: bool, dry_run: bool):
    """List commands to add users (and current status) of a team to gen3.

    \b
TEAM_ID one of:
* AI_READI: https://www.synapse.org/#!Team:3499899
* CHoRUS: https://www.synapse.org/#!Team:3499900
* CM4AI: https://www.synapse.org/#!Team:3499897
* Voice: https://www.synapse.org/#!Team:3499898
    """

    try:
        g3t_config = gen3_util.config.default()
        assert g3t_config.gen3.project_id, "Not in a gen3 project directory, expected .g3t"
        click.secho(f"gen3 project_id: {g3t_config.gen3.project_id}", fg="yellow", file=sys.stderr)

        program, project = g3t_config.gen3.project_id.split('-')
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

        gen3_users = get_gen3_users()
        current_users = {}
        for _ in gen3_users['users']:
            for p in _['policies']:
                if project in p['policy']:
                    if _['name'] not in current_users:
                        current_users[_['name']] = {'policies': []}
                    current_users[_['name']]['policies'].append(p['policy'])

        team = syn.getTeam(team_id)
        click.secho(f"Syncing team: {team.name}", fg="yellow", file=sys.stderr)
        cmds = []
        new_users = []
        for _ in syn.getTeamMembers(team):
            username = f'{_.member.ownerId}@synapse.org'
            cmd = f"g3t utilities users add --username"
            user_name_msg = f' # {_.member.userName}'
            if username in current_users:
                usr = current_users[username]
                user_name_msg += f" STATUS {usr['policies']} "
                click.secho(f"# '{username}'{user_name_msg}", fg="green", file=sys.stderr)
                continue
            else:
                user_name_msg += f" STATUS NONE"
                cmds.append(f"{cmd} '{username}'{user_name_msg}")
                new_users.append(username)

        if cmds:
            click.secho(f"Adding {len(cmds)} users to gen3", fg="yellow", file=sys.stderr)
            for cmd in cmds:
                click.secho(cmd, fg="yellow", file=sys.stderr)
                run_cmd(cmd, dry_run=dry_run)
            run_cmd("g3t utilities access sign", dry_run=dry_run)
        else:
            click.secho(f"No new users to add to {project}", fg="yellow", file=sys.stderr)

        # remove users not in synapse
        cmds = []
        expected_users = [f'{_.member.ownerId}@synapse.org' for _ in syn.getTeamMembers(team)]
        for user_name, user in current_users.items():
            if user_name in ctx.obj['config']['admin_users']:
                click.secho(f"Skipping admin user {user_name}", fg="green", file=sys.stderr)
                continue
            if user_name not in expected_users:
                cmd = f"g3t utilities users rm --username"
                cmds.append(f"{cmd} '{user_name}' --project_id {program}-{project} # {user['policies']}")
        if cmds:
            click.secho(f"Removing {len(cmds)} users from gen3", fg="yellow", file=sys.stderr)
            for cmd in cmds:
                click.secho(cmd, fg="yellow", file=sys.stderr)
                run_cmd(cmd, dry_run=dry_run)
            run_cmd("g3t utilities access sign", dry_run=dry_run)
        else:
            click.secho(f"No users to remove from {project}", fg="yellow", file=sys.stderr)

    except Exception as e:
        click.secho(f"{e.__class__.__name__} {e}", fg="red", file=sys.stderr)
        if debug:
            raise e


@teams.command("sync-all")
@click.option('--program', default="bridge2ai", help="gen3 program")
@click.option('--projects_dir', default="projects", help="root directory holding <program>-<project>")
@click.option('--debug', is_flag=True, default=False, help="Show debug output.")
@click.pass_context
def teams_sync_all(ctx, program, projects_dir, debug: bool):
    """Sync teams with gen3."""
    try:
        path = pathlib.Path(projects_dir)
        start_dir = os.getcwd()
        start_dir = pathlib.Path(start_dir)
        team_names = [_['name'] for _ in ctx.obj['config']['synapse_teams']]

        for team_name in team_names:
            project_dir = path / f"{program}-{team_name}"
            assert project_dir.exists(), f"Missing expected directory: {path / f'{program}-{team_name}'}"
            project_id = project_dir.name
            timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_file = pathlib.Path('logs') / f'synapse-sync-{team_name}-{timestamp_str}.log'
            click.secho(f"Syncing project {project_id}, log {log_file}", fg="yellow", file=sys.stderr)
            with open(log_file, 'w') as f:
                with contextlib.redirect_stdout(f):
                    with contextlib.redirect_stderr(f):
                        os.chdir(project_dir.absolute())
                        ctx.invoke(teams_sync)
                        os.chdir(start_dir.absolute())
    except Exception as e:
        click.secho(f"{e.__class__.__name__} {e}", fg="red", file=sys.stderr)
        if debug:
            raise e
