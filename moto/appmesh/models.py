"""AppMeshBackend class with methods for supported APIs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from uuid import uuid4

from moto.appmesh.exceptions import MeshNotFoundError
from moto.core.base_backend import BackendDict, BaseBackend


@dataclass
class Mesh:
    mesh_name: str
    metadata: Dict[str, Optional[Union[str, int, datetime]]]
    spec: Dict[str, Optional[Dict[str, Optional[str]]]]
    status: Dict[Literal["status"], str]
    tags: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:  # type ignore[misc]
        service_discovery = self.spec.get("service_discovery") or {}

        return {
            "meshName": self.mesh_name,
            "metadata": {
                "arn": self.metadata.get("arn"),
                "createdAt": self.metadata.get("created_at"),
                "lastUpdatedAt": self.metadata.get("last_updated_at"),
                "meshOwner": self.metadata.get("mesh_owner"),
                "resourceOwner": self.metadata.get("resource_owner"),
                "uid": self.metadata.get("uid"),
                "version": self.metadata.get("version"),
            },
            "spec": {
                "egressFilter": self.spec.get("egress_filter"),
                "serviceDiscovery": {
                    "ipPreference": service_discovery.get("ip_preference")
                },
            },
            "status": self.status,
        }

PAGINATION_MODEL = {
    "list_meshes": {
        "input_token": "next_token",
        "limit_key": "max_results",
        "limit_default": 100,
        "unique_attribute": "mesh_name",
    },
    "list_tags_for_resource": {
        "input_token": "next_token",
        "limit_key": "limit",
        "limit_default": 100,
        "unique_attribute": "resource_arn",
    },
}

class AppMeshBackend(BaseBackend):
    """Implementation of AppMesh APIs."""

    def __init__(self, region_name: str, account_id: str) -> None:
        super().__init__(region_name, account_id)
        self.meshes: Dict[str, Mesh] = dict()

    def create_mesh(
        self,
        client_token: Optional[str],
        mesh_name: str,
        spec: Dict[str, Dict[str, str]],
        tags: List[Dict[str, str]],
    ) -> Mesh:
        from moto.sts import sts_backends

        sts_backend = sts_backends[self.account_id][self.region_name]
        user_id, _, _ = sts_backend.get_caller_identity(
            self.account_id, region=self.region_name
        )

        service_discovery = spec.get("serviceDiscovery") or {}
        now = datetime.now()
        mesh = Mesh(
            mesh_name=mesh_name,
            spec={
                "egress_filter": spec.get("egressFilter"),
                "service_discovery": {
                    "ip_preference": service_discovery.get("ipPreference")
                },
            },
            status="ACTIVE",
            metadata={
                "arn": f"arn:aws:appmesh:{self.region_name}:{self.account_id}:{mesh_name}",
                "created_at": now,
                "last_updated_at": now,
                "mesh_owner": user_id,  # AppMesh uses IAM IDs
                "uid": uuid4(),
                "version": 1,
            },
            tags=tags,
        )
        self.meshes[mesh_name] = mesh
        return mesh

    def update_mesh(
        self,
        client_token: Optional[str],
        mesh_name: str,
        spec: Optional[Dict[str, Dict[str, str]]],
    ) -> Mesh:
        if mesh_name not in self.meshes:
            raise MeshNotFoundError(mesh_name)
        if spec:
            self.meshes[mesh_name].spec["egress_filter"] = spec.get("egressFilter")
            self.meshes[mesh_name].spec["service_discovery"] = {
                "ip_preference": (spec.get("serviceDiscovery") or {}).get(
                    "ipPreference"
                )
            }
            self.meshes[mesh_name].metadata["last_updated_at"] = datetime.now()
            self.meshes[mesh_name].metadata["version"] += 1
        return self.meshes[mesh_name]

    def describe_mesh(self, mesh_name: str, mesh_owner: str) -> Mesh:
        if mesh_name not in self.meshes:
            raise MeshNotFoundError(mesh_name)
        return self.meshes[mesh_name]

    def delete_mesh(self, mesh_name: str) -> Mesh:
        if mesh_name not in self.meshes:
            raise MeshNotFoundError(mesh_name)
        self.meshes[mesh_name].status["status"] = "DELETED"
        mesh = self.meshes[mesh_name].copy()
        del self.meshes[mesh_name]
        return mesh

    @paginate(pagination_model=PAGINATION_MODEL)  # type: ignore 
    def list_tags_for_resource(
        self, limit: int, next_token: str, resource_arn: str
    ) -> Tuple[str, List[Dict[str, str]]]:
        # implement here
        return next_token, tags

    def tag_resource(self, resource_arn: str, tags: List[Dict[str, str]]):
        # implement here
        return

    @paginate(pagination_model=PAGINATION_MODEL)  # type: ignore
    def list_meshes(self, limit: Optional[int], next_token: Optional[str]):
        return [mesh for mesh in self.meshes.values()]


appmesh_backends = BackendDict(AppMeshBackend, "appmesh")
