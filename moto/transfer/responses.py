"""Handles incoming transfer requests, invokes methods, returns responses."""

import json
from typing import List

from moto.core.responses import BaseResponse
from moto.transfer.types import ServerEndpointDetails, ServerIdentityProviderDetails, ServerProtocolDetails, ServerS3StorageOptions, ServerWorkflowDetails, UserHomeDirectoryMapping, UserPosixProfile

from .models import TransferBackend, transfer_backends


class TransferResponse(BaseResponse):
    """Handler for Transfer requests and responses."""

    def __init__(self) -> None:
        super().__init__(service_name="transfer")

    @property
    def transfer_backend(self) -> TransferBackend:
        return transfer_backends[self.current_account][self.region]

    def create_user(self) -> str:
        params = json.loads(self.body)
        home_directory_mappings = params.get("HomeDirectoryMappings")
        if home_directory_mappings is not None and len(home_directory_mappings) > 0:
            home_directory_mappings: List[UserHomeDirectoryMapping] = [
                {
                    "entry": mapping.get("Entry"),
                    "target": mapping.get("Target"),
                    "type": mapping.get("Type")
                } for mapping in home_directory_mappings
            ]
        posix_profile = params.get("PosixProfile")
        if posix_profile is not None:
            posix_profile: UserPosixProfile = {
                "gid": posix_profile.get("Gid"),
                "uid": posix_profile.get("Uid"),
                "secondary_gids": posix_profile.get("SecondaryGids")
            }
        server_id, user_name = self.transfer_backend.create_user(
            home_directory=params.get("HomeDirectory"),
            home_directory_type=params.get("HomeDirectoryType"),
            home_directory_mappings=home_directory_mappings,
            policy=params.get("Policy"),
            posix_profile=posix_profile,
            role=params.get("Role"),
            server_id=params.get("ServerId"),
            ssh_public_key_body=params.get("SshPublicKeyBody"),
            tags=params.get("Tags"),
            user_name=params.get("UserName"),
        )
        return json.dumps(dict(ServerId=server_id, UserName=user_name))

    def describe_user(self) -> str:
        params = json.loads(self.body)
        server_id, user = self.transfer_backend.describe_user(
            server_id=params.get("ServerId"),
            user_name=params.get("UserName"),
        )
        return json.dumps(dict(ServerId=server_id, User=user.to_dict()))

    def delete_user(self) -> str:
        params = json.loads(self.body)
        self.transfer_backend.delete_user(
            server_id=params.get("ServerId"),
            user_name=params.get("UserName"),
        )
        return json.dumps(dict())

    def import_ssh_public_key(self) -> str:
        params = json.loads(self.body)
        server_id, ssh_public_key_id, user_name = (
            self.transfer_backend.import_ssh_public_key(
                server_id=params.get("ServerId"),
                ssh_public_key_body=params.get("SshPublicKeyBody"),
                user_name=params.get("UserName"),
            )
        )
        return json.dumps(
            dict(
                ServerId=server_id, SshPublicKeyId=ssh_public_key_id, UserName=user_name
            )
        )

    def delete_ssh_public_key(self) -> str:
        params = json.loads(self.body)
        self.transfer_backend.delete_ssh_public_key(
            server_id=params.get("ServerId"),
            ssh_public_key_id=params.get("SshPublicKeyId"),
            user_name=params.get("UserName"),
        )
        return json.dumps(dict())

    def create_server(self) -> str:
        params = json.loads(self.body)
        endpoint_details = params.get("EndpointDetails")
        if endpoint_details is not None:
            endpoint_details: ServerEndpointDetails = {
                "address_allocation_ids": endpoint_details.get("AddressAllocationIds"),
                "subnet_ids": endpoint_details.get("SubnetIds"),
                "vpc_endpoint_id": endpoint_details.get("VpcEndpointId"),
                "vpc_id": endpoint_details.get("VpcId"),
                "security_group_ids": endpoint_details.get("SecurityGroupIds")
            }
        identity_provider_details = params.get("IdentityProviderDetails")
        if identity_provider_details is not None:
            identity_provider_details: ServerIdentityProviderDetails = {
                "url": identity_provider_details.get("Url"),
                "invocation_role": identity_provider_details.get("InvocationRole"),
                "directory_id": identity_provider_details.get("DirectoryId"),
                "function": identity_provider_details.get("Function"),
                "sftp_authentication_methods": identity_provider_details.get("SftpAuthenticationMethods")
            }
        protocol_details = params.get("ProtocolDetails")
        if protocol_details is not None:
            protocol_details: ServerProtocolDetails = {
                "passive_ip": protocol_details.get("PassiveIp"),
                "tls_session_resumption_mode": protocol_details.get("TlsSessionResumptionMode"),
                "set_stat_option": protocol_details.get("SetStatOption"),
                "as2_transports": protocol_details.get("As2Transports"), 
            }
        s3_storage_options = params.get("S3StorageOptions")
        if s3_storage_options is not None:
            s3_storage_options: ServerS3StorageOptions = {
                "directory_listing_optimization": s3_storage_options.get("DirectoryListingOptimization")
            }
        workflow_details = params.get("WorkflowDetails")
        if workflow_details is not None:
            workflow_details: ServerWorkflowDetails = {
                "on_upload": [
                    {
                        "workflow_id": workflow.get("WorkflowId"),
                        "execution_role": workflow.get("ExecutionRole")
                    } for workflow in (workflow_details.get("OnUpload") or [])
                ],
                "on_partial_upload": [                    
                    {
                        "workflow_id": workflow.get("WorkflowId"),
                        "execution_role": workflow.get("ExecutionRole")
                    } for workflow in (workflow_details.get("OnPartialUpload") or [])
                ]
            }

        server_id = self.transfer_backend.create_server(
            certificate=params.get("Certificate"),
            domain=params.get("Domain"),
            endpoint_details=endpoint_details,
            endpoint_type=params.get("EndpointType"),
            host_key=params.get("HostKey"),
            identity_provider_details=identity_provider_details,
            identity_provider_type=params.get("IdentityProviderType"),
            logging_role=params.get("LoggingRole"),
            post_authentication_login_banner=params.get(
                "PostAuthenticationLoginBanner"
            ),
            pre_authentication_login_banner=params.get("PreAuthenticationLoginBanner"),
            protocols=params.get("Protocols"),
            protocol_details=protocol_details,
            security_policy_name=params.get("SecurityPolicyName"),
            structured_log_destinations=params.get("StructuredLogDestinations"),
            s3_storage_options=s3_storage_options,
            tags=params.get("Tags"),
            workflow_details=workflow_details,
        )
        return json.dumps(dict(ServerId=server_id))

    def describe_server(self) -> str:
        params = json.loads(self.body)
        server = self.transfer_backend.describe_server(
            server_id=params.get("ServerId"),
        )
        return json.dumps(dict(Server=server.to_dict()))

    def delete_server(self) -> str:
        params = json.loads(self.body)
        self.transfer_backend.delete_server(
            server_id=params.get("ServerId"),
        )
        return json.dumps(dict())
