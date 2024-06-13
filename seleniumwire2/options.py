from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class ProxyConfig:
    http: Optional[str] = None
    https: Optional[str] = None


@dataclass
class SeleniumWireOptions:
    host: str = "127.0.0.1"
    port: int = 0
    auto_config: bool = True
    disable_capture: bool = False
    disable_encoding: bool = False
    enable_har: bool = False
    exclude_hosts: list[str] = field(default_factory=list)
    ignore_http_methods: list[str] = field(default_factory=lambda: ["OPTIONS"])
    storage_base_dir: Optional[str] = None
    request_storage: Literal["disk", "memory"] = "disk"
    request_storage_max_size: Optional[int] = None
    upstream_proxy: Optional[ProxyConfig] = None
    verify_ssl: bool = False
    mitm_options: dict = field(default_factory=dict)
