from openg2p_fastapi_common.service import BaseService
from openg2p_registry_core.interfaces import G2PIdGeneratorInterface, IdAffix
from openg2p_registry_core.models.g2p_register import G2PRegister


class G2PIdGeneratorService(BaseService, G2PIdGeneratorInterface):
    """Functional-ID affixes for the Disability Registry.

    Only PersonWithDisability generates functional IDs — it is the only register
    with `functional_id_generation_required = TRUE` in
    `meta_data/register-metadata/g2p_register_definitions.sql`. The sub-registers
    are detail tables reached through their parent, so an ID pool for them would
    be provisioned and never drawn from. The fallback below therefore only ever
    fires if that metadata and this file disagree.
    """

    def generate_prefix_suffix(
        self, g2p_register: G2PRegister, register_mnemonic: str
    ) -> IdAffix:
        mnemonic = (register_mnemonic or "").lower()

        if mnemonic == "personwithdisability":
            return IdAffix(prefix="PWD-", suffix="")

        return IdAffix(prefix="DEFAULT-", suffix="")
