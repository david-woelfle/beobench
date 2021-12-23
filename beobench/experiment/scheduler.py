"""Module to schedule experiments."""

import ray.tune
import ray.tune.integration.wandb
import click
import uuid
import subprocess

import beobench.experiment.definitions
import beobench.experiment.containers
import beobench.utils
import beobench.integrations.boptest
from beobench.experiment.definitions import (
    PROBLEM_001_BOPTEST_HEATPUMP,
    METHOD_001_PPO,
    RLLIB_SETUP,
)


@click.command()
@click.option(
    "--name",
    default="standard",
    help="Name of experiment collection to run.",
)
@click.option(
    "--use-wandb",
    is_flag=True,
    help=(
        "Use weights and biases (wandb) to log experiments. "
        "Requires being logged into wandb."
    ),
)
@click.option(
    "--wandb-project",
    default="initial_experiments",
    help="Weights and biases project name to log runs to.",
)
@click.option(
    "--wandb-entity",
    default="beobench",
    help="Weights and biases entity name to log runs under.",
)
@click.option(
    "--wandb-api-key",
    default="beobench",
    help="Weights and biases API key.",
)
@click.option(
    "--no-additional-container",
    is_flag=True,
    help="Do not run another container to do experiments in.",
)
def run_experiments_from_cli(
    name: str = "standard",
    use_wandb: bool = True,
    wandb_project: str = "initial_experiments",
    wandb_entity: str = "beobench",
    wandb_api_key: str = None,
    no_additional_container: bool = False,
) -> None:
    if no_additional_container:
        if name == "standard":
            run_standard_experiments(
                use_wandb,
                wandb_project,
                wandb_entity,
            )
    else:
        # Building and running experiments in docker container
        beobench.experiment.containers.build_experiment_container()
        beobench.experiment.containers.create_docker_network("beobench-net")

        unique_id = uuid.uuid4().hex[:6]
        container_name = f"auto_beobench_experiment_{unique_id}"

        flags = []
        if name:
            flags.append(f"--name {name}")
        if use_wandb:
            flags.append("--use-wandb")
        if wandb_project:
            flags.append(f"--wandb-project {wandb_project}")
        if wandb_entity:
            flags.append(f"--wandb-entity {wandb_entity}")

        flag_str = " ".join(flags)

        args = [
            "docker",
            "run",
            "-v",
            "/var/run/docker.sock:/var/run/docker.sock",
            "--name",
            container_name,
            "beobench-experiment",
            "/bin/bash",
            "-c",
            (
                f"export WANDB_API_KEY={wandb_api_key} && python -m "
                f"beobench.experiment.scheduler {flag_str} "
                "--no-additional-container && bash"
            ),
        ]
        subprocess.check_call(args)


def run_standard_experiments(
    use_wandb: bool = True,
    wandb_project: str = "initial_experiments",
    wandb_entity: str = "beobench",
):
    if use_wandb:
        wandb_callback = ray.tune.integration.wandb.WandbLoggerCallback(
            project=wandb_project, log_config=True, entity=wandb_entity
        )
        callbacks = [wandb_callback]
    else:
        callbacks = None

    run_experiment(
        problem_def=PROBLEM_001_BOPTEST_HEATPUMP,
        method_def=METHOD_001_PPO,
        rllib_setup=RLLIB_SETUP,
        rllib_callbacks=callbacks,
    )


def restart() -> None:
    """Clean up remaining beobench processes before running
    new experiments.

    This stops all docker containers still running. This
    function is not called by other scheduler functions
    to enable the parrallel running of experiments.
    """

    beobench.integrations.boptest.shutdown()


def run_experiment(
    problem_def: dict, method_def: dict, rllib_setup: dict, rllib_callbacks: list = None
) -> ray.tune.ExperimentAnalysis:
    """Run beobench experiment.

    Additional info: note that RLlib is a submodule of the ray package, i.e. it is
    imported as `ray.rllib`. For experiment definitions it uses the `ray.tune`
    submodule. Therefore ray tune experiment definition means the same as ray rllib
    experiment defintions. To avoid confusion all variable/argument names use rllib
    instead of ray tune but strictly speaking these are ray tune experiment
    definitions.

    Args:
        problem_def (dict): definition of problem. This is an incomplete
            ray tune experiment defintion that only defines the problem side.
        method_def (dict): definition of method. This is an incomplete
            ray tune experiment defintion that only defines the method side.
        rllib_setup (dict): rllib setup. This is an incomplete
            ray tune experiment defintion that only defines the ray tune/rllib setup
            (e.g. number of workers, etc.).
        rllib_callbacks (list, optional): callbacks to add to ray.tune.run command.
            Defaults to None.

    Returns:
        ray.tune.ExperimentAnalysis: analysis object of completed experiment.
    """
    if rllib_callbacks is None:
        rllib_callbacks = []

    # combine the three incomplete ray tune experiment
    # definitions into a single complete one.
    exp_config = beobench.experiment.definitions.get_experiment_config(
        problem_def, method_def, rllib_setup
    )

    # register the problem environment with ray tune
    ray.tune.registry.register_env(
        problem_def["rllib_experiment_config"]["config"]["env"],
        problem_def["env_creator_to_register"],
    )

    # if run in notebook, change the output reported throughout experiment.
    if beobench.utils.check_if_in_notebook():
        reporter = ray.tune.JupyterNotebookReporter(overwrite=True)
    else:
        reporter = None

    # running the experiment
    analysis = ray.tune.run(
        progress_reporter=reporter,
        callbacks=rllib_callbacks,
        **exp_config,
    )

    return analysis


def run_experiment_in_container():
    # TODO: create function that creates exp container
    # and runs experiment in it.
    pass


if __name__ == "__main__":
    run_experiments_from_cli()