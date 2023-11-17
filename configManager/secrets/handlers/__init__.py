from abc import ABC, abstractmethod
from typing import TypedDict, List, Optional
from ...parseServerConfig import Server


class KeyValuePair(TypedDict):
    key: str
    value: str


# Typed Dict which encorporates Key Value Pairs for Secrets
class KV_ContainerSecrets(TypedDict):
    public: Optional[List[KeyValuePair]]
    private: Optional[List[KeyValuePair]]
    fixed: Optional[List[KeyValuePair]]


# Typed Dict which encorporates Key Value Pairs for Secrets
class KV_Container(TypedDict):
    name: str
    secrets: KV_ContainerSecrets


# Typed Dict which encorporates Key Value Pairs for Secrets
class KV_Server(TypedDict):
    name: str
    containers: List[KV_Container]


class SecretHandler(ABC):
    @staticmethod
    @abstractmethod
    def get_hander_name() -> str:
        pass

    @abstractmethod
    def generate_secrets(self, server_config: List[Server], root_directory: str, debug: bool) -> List[KV_Server]:
        pass

    @abstractmethod
    def publish_public_secrets(self, kv_server_config: List[KV_Server], root_directory: str, debug: bool) -> None:
        pass

    @abstractmethod
    def clean(self, target: str, root_directory: str, debug: bool) -> None:
        pass
