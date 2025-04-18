# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Run ephemeral Docker Swarm services."""

from __future__ import annotations

import re
import shlex
from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Literal

from docker import types
from docker.errors import APIError

from airflow.exceptions import AirflowException
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.strings import get_random_string

if TYPE_CHECKING:
    try:
        from airflow.sdk.definitions.context import Context
    except ImportError:
        # TODO: Remove once provider drops support for Airflow 2
        from airflow.utils.context import Context


class DockerSwarmOperator(DockerOperator):
    """
    Execute a command as an ephemeral docker swarm service.

    Example use-case - Using Docker Swarm orchestration to make one-time
    scripts highly available.

    A temporary directory is created on the host and
    mounted into a container to allow storing files
    that together exceed the default disk size of 10GB in a container.
    The path to the mounted directory can be accessed
    via the environment variable ``AIRFLOW_TMP_DIR``.

    If a login to a private registry is required prior to pulling the image, a
    Docker connection needs to be configured in Airflow and the connection ID
    be provided with the parameter ``docker_conn_id``.

    :param image: Docker image from which to create the container.
        If image tag is omitted, "latest" will be used.
    :param api_version: Remote API version. Set to ``auto`` to automatically
        detect the server's version.
    :param auto_remove: Enable removal of the service when the service has terminated. Possible values:

        - ``never``: (default) do not remove service
        - ``success``: remove on success
        - ``force``: always remove service
    :param command: Command to be run in the container. (templated)
    :param args: Arguments to the command.
    :param docker_url: URL of the host running the docker daemon.
        Default is the value of the ``DOCKER_HOST`` environment variable or unix://var/run/docker.sock
        if it is unset.
    :param environment: Environment variables to set in the container. (templated)
    :param force_pull: Pull the docker image on every run. Default is False.
    :param mem_limit: Maximum amount of memory the container can use.
        Either a float value, which represents the limit in bytes,
        or a string like ``128m`` or ``1g``.
    :param tls_ca_cert: Path to a PEM-encoded certificate authority
        to secure the docker connection.
    :param tls_client_cert: Path to the PEM-encoded certificate
        used to authenticate docker client.
    :param tls_client_key: Path to the PEM-encoded key used to authenticate docker client.
    :param tls_hostname: Hostname to match against
        the docker server certificate or False to disable the check.
    :param tls_ssl_version: Version of SSL to use when communicating with docker daemon.
    :param tmp_dir: Mount point inside the container to
        a temporary directory created on the host by the operator.
        The path is also made available via the environment variable
        ``AIRFLOW_TMP_DIR`` inside the container.
    :param user: Default user inside the docker container.
    :param docker_conn_id: The :ref:`Docker connection id <howto/connection:docker>`
    :param tty: Allocate pseudo-TTY to the container of this service
        This needs to be set see logs of the Docker container / service.
    :param enable_logging: Show the application's logs in operator's logs.
        Supported only if the Docker engine is using json-file or journald logging drivers.
        The `tty` parameter should be set to use this with Python applications.
    :param retrieve_output: Should this docker image consistently attempt to pull from and output
        file before manually shutting down the image. Useful for cases where users want a pickle serialized
        output that is not posted to logs
    :param retrieve_output_path: path for output file that will be retrieved and passed to xcom
    :param configs: List of docker configs to be exposed to the containers of the swarm service.
        The configs are ConfigReference objects as per the docker api
        [https://docker-py.readthedocs.io/en/stable/services.html#docker.models.services.ServiceCollection.create]_
    :param secrets: List of docker secrets to be exposed to the containers of the swarm service.
        The secrets are SecretReference objects as per the docker create_service api.
        [https://docker-py.readthedocs.io/en/stable/services.html#docker.models.services.ServiceCollection.create]_
    :param mode: Indicate whether a service should be deployed as a replicated or global service,
        and associated parameters
    :param networks: List of network names or IDs or NetworkAttachmentConfig to attach the service to.
    :param placement: Placement instructions for the scheduler. If a list is passed instead,
        it is assumed to be a list of constraints as part of a Placement object.
    :param container_resources: Resources for the launched container.
        The resources are Resources as per the docker api
        [https://docker-py.readthedocs.io/en/stable/api.html#docker.types.Resources]_
        This parameter has precedence on the mem_limit parameter.
    :param service_prefix: Prefix for the service name. The service name will be generated as
        ``{service_prefix}-{random_string}``. Default is 'airflow'.
    :param logging_driver: The logging driver to use for container logs. Docker by default uses 'json-file'.
        For more information on Docker logging drivers: https://docs.docker.com/engine/logging/configure/
        NOTE: Only drivers 'json-file' and 'gelf' are currently supported. If left empty, 'json-file' will be used.
    :param logging_driver_opts: Dictionary of logging options to use with the associated logging driver chosen.
        Depending on the logging driver, some options are required.
        Failure to include them, will result in the operator failing.
        All option values must be strings and wrapped in double quotes.
        For information on 'json-file' options: https://docs.docker.com/engine/logging/drivers/json-file/
        For information on 'gelf' options: https://docs.docker.com/engine/logging/drivers/gelf/
        NOTE: 'gelf' driver requires the 'gelf-address' option to be set.
    """

    def __init__(
        self,
        *,
        image: str,
        args: str | list[str] | None = None,
        enable_logging: bool = True,
        configs: list[types.ConfigReference] | None = None,
        secrets: list[types.SecretReference] | None = None,
        mode: types.ServiceMode | None = None,
        networks: list[str | types.NetworkAttachmentConfig] | None = None,
        placement: types.Placement | list[types.Placement] | None = None,
        container_resources: types.Resources | None = None,
        service_prefix: str = "airflow",
        logging_driver: Literal["json-path", "gelf"] | None = None,
        logging_driver_opts: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(image=image, **kwargs)
        self.args = args
        self.enable_logging = enable_logging
        self.service = None
        self.tasks: list[dict] = []
        self.containers: list[dict] = []
        self.configs = configs
        self.secrets = secrets
        self.mode = mode
        self.networks = networks
        self.placement = placement
        self.container_resources = container_resources or types.Resources(mem_limit=self.mem_limit)
        self.service_prefix = service_prefix
        self.logging_driver = logging_driver
        self.logging_driver_opts = logging_driver_opts

        if self.logging_driver:
            supported_logging_drivers = ("json-file", "gelf")
            if self.logging_driver not in supported_logging_drivers:
                raise AirflowException(
                    f"Invalid logging driver provided: {self.logging_driver}. Must be one of: [{', '.join(supported_logging_drivers)}]"
                )
            self.log_driver_config = types.DriverConfig(self.logging_driver, self.logging_driver_opts)
        else:
            self.log_driver_config = None

    def execute(self, context: Context) -> None:
        self.environment["AIRFLOW_TMP_DIR"] = self.tmp_dir
        return self._run_service()

    def _run_service(self) -> None:
        self.log.info("Starting docker service from image %s", self.image)
        self.service = self.cli.create_service(
            types.TaskTemplate(
                container_spec=types.ContainerSpec(
                    image=self.image,
                    command=self.format_command(self.command),
                    args=self.format_args(self.args),
                    mounts=self.mounts,
                    env=self.environment,
                    user=self.user,
                    tty=self.tty,
                    configs=self.configs,
                    secrets=self.secrets,
                ),
                restart_policy=types.RestartPolicy(condition="none"),
                resources=self.container_resources,
                networks=self.networks,
                placement=self.placement,
                log_driver=self.log_driver_config,
            ),
            name=f"{self.service_prefix}-{get_random_string()}",
            labels={"name": f"airflow__{self.dag_id}__{self.task_id}"},
            mode=self.mode,
        )
        if self.service is None:
            raise RuntimeError("Service should be set here")
        self.log.info("Service started: %s", self.service)

        # wait for the service to start the task
        while not self.cli.tasks(filters={"service": self.service["ID"]}):
            continue

        if self.enable_logging:
            self._stream_logs_to_output()

        while True:
            if self._has_service_terminated():
                self.log.info("Service status before exiting: %s", self._service_status())
                break

        if self.service and self._service_status() == "complete":
            self.tasks = self.cli.tasks(filters={"service": self.service["ID"]})
            for task in self.tasks:
                container_id = task["Status"]["ContainerStatus"]["ContainerID"]
                container = self.cli.inspect_container(container_id)
                self.containers.append(container)

        if self.retrieve_output:
            return self._attempt_to_retrieve_results()

        self.log.info("auto_remove: %s", str(self.auto_remove))
        if self.service and self._service_status() != "complete":
            if self.auto_remove == "force":
                self.cli.remove_service(self.service["ID"])
            raise AirflowException(f"Service did not complete: {self.service!r}")
        if self.auto_remove in ["success", "force"]:
            if not self.service:
                raise RuntimeError("The 'service' should be initialized before!")
            self.cli.remove_service(self.service["ID"])

    def _service_status(self) -> str | None:
        if not self.service:
            raise RuntimeError("The 'service' should be initialized before!")
        return self.cli.tasks(filters={"service": self.service["ID"]})[0]["Status"]["State"]

    def _has_service_terminated(self) -> bool:
        status = self._service_status()
        return status in ["complete", "failed", "shutdown", "rejected", "orphaned", "remove"]

    def _stream_logs_to_output(self) -> None:
        if not self.service:
            raise RuntimeError("The 'service' should be initialized before!")
        last_line_logged, last_timestamp = "", 0

        def stream_new_logs(last_line_logged, since=0):
            logs = self.cli.service_logs(
                self.service["ID"],
                follow=False,
                stdout=True,
                stderr=True,
                is_tty=self.tty,
                since=since,
                timestamps=True,
            )
            logs = list(map(lambda line: line.decode("utf-8"), logs))
            if last_line_logged in logs:
                logs = logs[logs.index(last_line_logged) + 1 :]
            for line in logs:
                match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6,}Z) (.*)", line)
                timestamp, message = match.groups()
                self.log.info(message)

            if len(logs) == 0:
                return last_line_logged, since

            last_line_logged = line

            # Floor nanoseconds to microseconds
            last_timestamp = re.sub(r"(\.\d{6})\d+Z", r"\1Z", timestamp)
            last_timestamp = datetime.strptime(last_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            last_timestamp = last_timestamp.timestamp()
            return last_line_logged, last_timestamp

        while not self._has_service_terminated():
            sleep(2)
            last_line_logged, last_timestamp = stream_new_logs(last_line_logged, since=last_timestamp)

    def _attempt_to_retrieve_results(self):
        """
        Attempt to pull the result from the expected file for each containers.

        This uses Docker's ``get_archive`` function. If the file is not yet
        ready, *None* is returned.
        """
        try:
            file_contents = []
            for container in self.containers:
                file_content = self._copy_from_docker(container["Id"], self.retrieve_output_path)
                file_contents.append(file_content)
            if len(file_contents) == 1:
                return file_contents[0]
            return file_contents
        except APIError:
            return None

    @staticmethod
    def format_args(args: list[str] | str | None) -> list[str] | None:
        """
        Retrieve args.

        The args string is parsed to a list.

        :param args: args to the docker service

        :return: the args as list
        """
        if isinstance(args, str):
            return shlex.split(args)
        return args

    def on_kill(self) -> None:
        if self.hook.client_created and self.service is not None:
            self.log.info("Removing docker service: %s", self.service["ID"])
            self.cli.remove_service(self.service["ID"])
