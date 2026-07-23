"""
bridge to docker-compose using subprocess docker-compose CLI
"""

import logging
import os
import subprocess
from typing import Dict, List, Optional, Any

import yaml
from docker.models.containers import Container as DockerContainer

from vulfocus.settings import client


logger = logging.getLogger(__name__)


class ComposeContainer:
    def __init__(self, container: DockerContainer, service_name: str = ""):
        self.container = container
        self.service = service_name

    @property
    def id(self) -> str:
        return self.container.id

    @property
    def name(self) -> str:
        return self.container.name

    @property
    def name_without_project(self) -> str:
        return self.container.name.replace("/", "")

    @property
    def human_readable_command(self) -> List[str]:
        return self.container.attrs.get('Config', {}).get('Cmd', [])

    @property
    def human_readable_state(self) -> str:
        return self.container.status

    @property
    def labels(self) -> Dict[str, str]:
        return self.container.labels

    @property
    def ports(self) -> Dict[str, List[Dict[str, str]]]:
        return self.container.attrs.get('NetworkSettings', {}).get('Ports', {})

    @property
    def is_running(self) -> bool:
        return self.container.status == 'running'


class ComposeProject:
    def __init__(self, path: str, config: Dict[str, Any]):
        self.path = path
        self.config = config
        self.name = os.path.basename(os.path.normpath(path))
        self.client = client
        self._compose_file = os.path.join(path, "docker-compose.yml")

    def _compose_cmd(self, *args: str) -> subprocess.CompletedProcess:
        """Run docker-compose with the given arguments"""
        cmd = [
            "docker-compose",
            "-H", "unix:///var/run/docker.sock",
            "-p", self.name,
            "-f", self._compose_file,
        ] + list(args)
        return subprocess.run(
            cmd,
            capture_output=True, text=True,
            cwd=self.path,
        )

    def up(self) -> List[ComposeContainer]:
        """Start all services using real docker-compose CLI"""
        container_list = []
        services = self.config.get('services', {})

        if not os.path.exists(self._compose_file):
            logger.error(f"Compose file not found: {self._compose_file}")
            return container_list

        # ① 调用真实的 docker-compose up -d（--pull missing 跳过已存在的镜像减少网络超时）
        result = self._compose_cmd("up", "-d", "--pull", "missing")
        if result.returncode != 0:
            raise RuntimeError(
                f"docker-compose up 失败: {result.stderr.strip()}"
            )

        # ② 通过 Docker SDK 按 compose 标签查找容器
        for service_name in services:
            filters = {"label": f"com.docker.compose.service={service_name}"}
            containers = self.client.containers.list(all=True, filters=filters)
            if containers:
                container_list.append(
                    ComposeContainer(containers[0], service_name)
                )
            else:
                logger.warning(
                    f"Service {service_name}: no container found after compose up"
                )

        return container_list

    def stop(self) -> List[ComposeContainer]:
        """Stop all services using real docker-compose CLI"""
        if not os.path.exists(self._compose_file):
            return []
        self._compose_cmd("stop")
        return []


def get_project(path: str) -> ComposeProject:
    """Get docker project given file path"""
    logger.debug(f'get project {path}')

    compose_files = ['docker-compose.yml', 'docker-compose.yaml']
    config_path = None

    for filename in compose_files:
        full_path = os.path.join(path, filename)
        if os.path.exists(full_path):
            config_path = full_path
            break

    if not config_path:
        raise FileNotFoundError(f"No docker-compose file found in {path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return ComposeProject(path, config)
