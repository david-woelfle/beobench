"""Command line interface for beobench."""

import click
import ast

import beobench.experiment.scheduler
import beobench.utils


@click.group()
def cli():
    """Command line interface for Beobench."""


@cli.command()
@click.option(
    "--config",
    "-c",
    default=None,
    help="Json or filepath with yaml that defines beobench experiment configuration.",
    type=str,
)
@click.option(
    "--experiment-file",
    default=None,
    help="File that defines beobench experiment.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "--agent-file",
    default=None,
    help="File that defines custom agent.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "--method",
    default="",
    help="Name of RL method to use in experiment.",
)
@click.option(
    "--env",
    default="",
    help="Name of RL environment to use in experiment.",
)
@click.option(
    "--local-dir",
    default="./beobench_results/ray_results",
    help="Local directory to write results to.",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
)
@click.option(
    "--wandb-project",
    default="",
    help="Weights and biases project name to log runs to.",
)
@click.option(
    "--wandb-entity",
    default="",
    help="Weights and biases entity name to log runs under.",
)
@click.option(
    "--wandb-api-key",
    default="",
    help="Weights and biases API key.",
)
@click.option(
    "--mlflow-name",
    default=None,
    help="Name of MLflow experiment.",
)
@click.option(
    "--use-gpu",
    is_flag=True,
    help="Whether to use GPUs from the host system in experiment container.",
)
@click.option(
    "--docker-shm-size",
    default="2gb",
    help="Size of shared memory available to experiment container.",
)
@click.option(
    "--no-additional-container",
    is_flag=True,
    help="Do not run another container to do experiments in.",
)
@click.option(
    "--use-no-cache",
    is_flag=True,
    help="Whether to use cache to build experiment container.",
)
@click.option(
    "--dev-beobench-location",
    default=None,
    help="For developer use only: location of custom beobench package version.",
)
def run(
    config: str,
    experiment_file: str,
    agent_file: str,
    method: str,
    env: str,
    local_dir: str,
    wandb_project: str,
    wandb_entity: str,
    wandb_api_key: str,
    mlflow_name: str,
    use_gpu: bool,
    docker_shm_size: str,
    no_additional_container: bool,
    use_no_cache: bool,
    dev_beobench_location: str,
) -> None:
    """Run beobench experiment from command line.

    Command line version of beobench.run() function.
    """

    # This appears to be the best (but not great) way to have a parallel python
    # and command line interface.
    #
    # See https://stackoverflow.com/a/40094408.

    # Parse config str to dict if
    if config and config[0] == "{":
        config = ast.literal_eval(config)

    beobench.experiment.scheduler.run(
        config=config,
        experiment_file=experiment_file,
        agent_file=agent_file,
        method=method,
        env=env,
        local_dir=local_dir,
        wandb_project=wandb_project,
        wandb_entity=wandb_entity,
        wandb_api_key=wandb_api_key,
        mlflow_name=mlflow_name,
        use_gpu=use_gpu,
        docker_shm_size=docker_shm_size,
        no_additional_container=no_additional_container,
        use_no_cache=use_no_cache,
        dev_beobench_location=dev_beobench_location,
    )


@cli.command()
def restart():
    """Restart beobench. This will stop any remaining running beobench containers."""
    beobench.utils.restart()
