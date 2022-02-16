"""RLlib integration in beobench."""

import ray.tune
import ray.tune.integration.wandb
import ray.tune.integration.mlflow

import beobench.utils


def run_in_tune(
    problem_def: dict,
    method_def: dict,
    rllib_setup: dict,
    wandb_project: str = None,
    wandb_entity: str = None,
    mlflow_name: str = None,
    use_gpu: bool = False,
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
    if wandb_project and wandb_entity:
        callbacks = [_create_wandb_callback(wandb_project, wandb_entity)]
    elif wandb_project or wandb_entity:
        raise ValueError(
            "Only one of wandb_project or wandb_entity given, but both required."
        )
    elif mlflow_name:
        callbacks = [_create_mlflow_callback(mlflow_name)]
    else:
        callbacks = []

    # change RLlib setup if GPU used
    if use_gpu:
        rllib_setup["rllib_experiment_config"]["config"]["num_gpus"] = 1

    # combine the three incomplete ray tune experiment
    # definitions into a single complete one.
    exp_config = beobench.experiment.definitions.utils.get_experiment_config(
        problem_def, method_def, rllib_setup
    )

    # register the problem environment with ray tune
    # env_creator is a module available in experiment containers
    import env_creator  # pylint: disable=import-outside-toplevel,import-error

    ray.tune.registry.register_env(
        problem_def["rllib_experiment_config"]["config"]["env"],
        env_creator.create_env,
    )

    # if run in notebook, change the output reported throughout experiment.
    if beobench.utils.check_if_in_notebook():
        reporter = ray.tune.JupyterNotebookReporter(overwrite=True)
    else:
        reporter = None

    # running the experiment
    analysis = ray.tune.run(
        progress_reporter=reporter,
        callbacks=callbacks,
        **exp_config,
    )

    return analysis


def _create_wandb_callback(
    wandb_project: str,
    wandb_entity: str,
):
    """Create an RLlib weights and biases (wandb) callback.

    Args:
        wandb_project (str): name of wandb project.
        wandb_entity (str): name of wandb entity that owns project.

    Returns:
        : a wandb callback
    """
    wandb_callback = ray.tune.integration.wandb.WandbLoggerCallback(
        project=wandb_project, log_config=True, entity=wandb_entity
    )
    return wandb_callback


def _create_mlflow_callback(
    mlflow_name: str,
):
    """Create an RLlib MLflow callback.

    Args:
        mlflow_name (str, optional): name of MLflow experiment.

    Returns:
        : a wandb callback
    """
    mlflow_callback = ray.tune.integration.mlflow.MLflowLoggerCallback(
        experiment_name=mlflow_name, tracking_uri="file:/root/ray_results/mlflow"
    )
    return mlflow_callback
