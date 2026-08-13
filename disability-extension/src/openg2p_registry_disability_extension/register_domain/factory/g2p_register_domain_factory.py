import importlib
import logging
from typing import Optional

from openg2p_fastapi_common.service import BaseService
from openg2p_registry_core.services import G2PRegisterDomainService

_logger = logging.getLogger('g2p-register-domain-factory')


class G2PRegisterDomainFactory(BaseService):
    """Resolves a register mnemonic to its domain service.

    The import target is `openg2p_registry_extensions`, NOT this package's own
    name: the platform entrypoints alias whatever REGISTRY_EXTENSION_MODULE names
    into sys.modules under that fixed alias at startup. Importing
    `openg2p_registry_disability_extension` directly here would work in this image
    and break the moment the base image's reference extension is the one selected.
    """

    g2p_register_domain_service: G2PRegisterDomainService = None

    def get_domain_service(self, register_mnemonic: str) -> Optional[G2PRegisterDomainService]:

        try:
            module = importlib.import_module("openg2p_registry_extensions.register_domain.services")
            register_class_prefix: str = "G2PRegisterDomainService"
            implementation_class_name: str = f"{register_class_prefix}{register_mnemonic}"
            implementation_class = getattr(module, implementation_class_name)
            _logger.info(
                f"Found specific implementation for register mnemonic '{register_mnemonic}': "
                f"{implementation_class_name}"
            )
            g2p_register_domain_service: G2PRegisterDomainService = implementation_class.get_component()
            if not g2p_register_domain_service:
                g2p_register_domain_service = implementation_class()
            return g2p_register_domain_service
        except (AttributeError, ModuleNotFoundError) as error:
            _logger.warning(
                f"Could not find specific implementation for register mnemonic '{register_mnemonic}': {error}. "
                f"Falling back to default implementations."
            )
            return None
