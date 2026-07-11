"""
bridge to docker-compose using docker SDK and pyyaml
"""

import logging
import os
from typing import Dict, List, Optional, Any

import yaml
from docker.models.containers import Container as DockerContainer
from docker.models.networks import Network as DockerNetwork

from vulfocus.settings import client, api_docker_client


logger = logging.getLogger(__name__)


class ComposeContainer:
    def __init__(self, container: DockerContainer):
        self.container = container

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

    def _create_network(self, net_name: str, net_config: Dict[str, Any]) -> Optional[DockerNetwork]:
        """Create network if it doesn't exist"""
        try:
            existing_nets = {n.name for n in self.client.networks.list()}
            if net_name in existing_nets:
                return self.client.networks.get(net_name)

            ipam_pool = None
            ipam_config = net_config.get('ipam')
            if ipam_config and 'config' in ipam_config:
                for pool_config in ipam_config['config']:
                    ipam_pool = {
                        'subnet': pool_config.get('subnet'),
                        'gateway': pool_config.get('gateway')
                    }

            return self.client.networks.create(
                name=net_name,
                driver=net_config.get('driver', 'bridge'),
                ipam_pool=ipam_pool,
                attachable=True
            )
        except Exception as e:
            logger.error(f"Error creating network {net_name}: {e}")
            return None

    def _parse_ports(self, ports_config: List[str]) -> Dict[str, int]:
        """Parse ports configuration"""
        ports = {}
        for port_mapping in ports_config:
            if isinstance(port_mapping, str):
                parts = port_mapping.split(':')
                if len(parts) == 2:
                    try:
                        host_port = int(parts[0])
                        container_port = parts[1]
                        if '/' in container_port:
                            container_port, _ = container_port.split('/')
                        ports[f"{container_port}/tcp"] = host_port
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid port mapping: {port_mapping}")
        return ports

    def up(self) -> List[ComposeContainer]:
        """Start all services defined in docker-compose.yml"""
        container_list = []
        services = self.config.get('services', {})
        networks = self.config.get('networks', {})

        for net_name, net_config in networks.items():
            if not net_config.get('external'):
                self._create_network(net_name, net_config)

        for service_name, service_config in services.items():
            try:
                image = service_config.get('image')
                if not image:
                    logger.warning(f"Service {service_name} has no image defined")
                    continue

                container_name = f"{self.name}_{service_name}_1"

                existing_containers = self.client.containers.list(
                    all=True, filters={'name': container_name}
                )
                if existing_containers:
                    container = existing_containers[0]
                    if container.status != 'running':
                        container.start()
                    container_list.append(ComposeContainer(container))
                    continue

                ports = self._parse_ports(service_config.get('ports', []))
                environment = service_config.get('environment', {})
                volumes = service_config.get('volumes', [])

                network_name = networks.get('default', {}).get('external', {}).get(
                    'name', f"{self.name}_default"
                )
                networking_config = None
                try:
                    network = self.client.networks.get(network_name)
                    networking_config = self.client.api.create_networking_config({
                        network_name: self.client.api.create_endpoint_config()
                    })
                except Exception as e:
                    logger.warning(f"Failed to get network {network_name}: {e}")

                container = self.client.containers.run(
                    image=image,
                    name=container_name,
                    ports=ports,
                    environment=environment,
                    volumes=volumes,
                    detach=True,
                    networking_config=networking_config,
                    remove=False
                )

                container_list.append(ComposeContainer(container))

            except Exception as e:
                logger.error(f"Error starting service {service_name}: {e}")

        return container_list

    def stop(self) -> List[ComposeContainer]:
        """Stop all services defined in docker-compose.yml"""
        container_list = []
        services = self.config.get('services', {})

        for service_name in services.keys():
            try:
                container_name = f"{self.name}_{service_name}_1"
                existing_containers = self.client.containers.list(
                    all=True, filters={'name': container_name}
                )

                for container in existing_containers:
                    if container.status == 'running':
                        container.stop()
                    container_list.append(ComposeContainer(container))

            except Exception as e:
                logger.error(f"Error stopping service {service_name}: {e}")

        return container_list


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


def get_yml_path(path: str) -> Optional[str]:
    """Get path of docker-compose.yml file"""
    compose_files = ['docker-compose.yml', 'docker-compose.yaml']
    for filename in compose_files:
        full_path = os.path.join(path, filename)
        if os.path.exists(full_path):
            return full_path
    return None