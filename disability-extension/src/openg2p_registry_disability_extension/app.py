# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_registry_core.app import Initializer as CoreInitializer

from .register_domain.models import (
    G2PRegisterPersonWithDisability,
    G2PRegisterHistoryPersonWithDisability,
    G2PIntakeFormPersonWithDisability,
    G2PRegisterDisabilityDetail,
    G2PRegisterHistoryDisabilityDetail,
    G2PIntakeFormDisabilityDetail,
    G2PRegisterHumanAssistance,
    G2PRegisterHistoryHumanAssistance,
    G2PIntakeFormHumanAssistance,
    G2PRegisterAssistiveTechnology,
    G2PRegisterHistoryAssistiveTechnology,
    G2PIntakeFormAssistiveTechnology,
    G2PRegisterMedicalCare,
    G2PRegisterHistoryMedicalCare,
    G2PIntakeFormMedicalCare,
    G2PRegisterHousingSupport,
    G2PRegisterHistoryHousingSupport,
    G2PIntakeFormHousingSupport,
    G2PRegisterAnimalAssistance,
    G2PRegisterHistoryAnimalAssistance,
    G2PIntakeFormAnimalAssistance,
    G2PRegisterRelatedPerson,
    G2PRegisterHistoryRelatedPerson,
    G2PIntakeFormRelatedPerson,
    G2PRegisterProgramEnrolment,
    G2PRegisterHistoryProgramEnrolment,
    G2PIntakeFormProgramEnrolment,
)
from .register_domain.services import (
    G2PRegisterDomainServicePersonWithDisability,
    G2PRegisterDomainServiceDisabilityDetail,
    G2PRegisterDomainServiceHumanAssistance,
    G2PRegisterDomainServiceAssistiveTechnology,
    G2PRegisterDomainServiceMedicalCare,
    G2PRegisterDomainServiceHousingSupport,
    G2PRegisterDomainServiceAnimalAssistance,
    G2PRegisterDomainServiceRelatedPerson,
    G2PRegisterDomainServiceProgramEnrolment,
)

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        CoreInitializer().initialize()

        # Instantiated eagerly so `get_component()` resolves them later. Every
        # register in this extension has domain behaviour — validation, naming,
        # or the support-summary recompute — so all nine are registered. A
        # register whose service is not constructed here silently falls back to
        # the core default and loses that behaviour without erroring.
        G2PRegisterDomainServicePersonWithDisability()
        G2PRegisterDomainServiceDisabilityDetail()
        G2PRegisterDomainServiceHumanAssistance()
        G2PRegisterDomainServiceAssistiveTechnology()
        G2PRegisterDomainServiceMedicalCare()
        G2PRegisterDomainServiceHousingSupport()
        G2PRegisterDomainServiceAnimalAssistance()
        G2PRegisterDomainServiceRelatedPerson()
        G2PRegisterDomainServiceProgramEnrolment()

    def migrate_database(self, args):

        async def migrate():
            _logger.info("Migrating extensions database")

            # PersonWithDisability first: every other table links to it.
            await G2PRegisterPersonWithDisability.create_migrate()
            await G2PRegisterHistoryPersonWithDisability.create_migrate()
            await G2PIntakeFormPersonWithDisability.create_migrate()

            await G2PRegisterDisabilityDetail.create_migrate()
            await G2PRegisterHistoryDisabilityDetail.create_migrate()
            await G2PIntakeFormDisabilityDetail.create_migrate()

            await G2PRegisterHumanAssistance.create_migrate()
            await G2PRegisterHistoryHumanAssistance.create_migrate()
            await G2PIntakeFormHumanAssistance.create_migrate()

            await G2PRegisterAssistiveTechnology.create_migrate()
            await G2PRegisterHistoryAssistiveTechnology.create_migrate()
            await G2PIntakeFormAssistiveTechnology.create_migrate()

            await G2PRegisterMedicalCare.create_migrate()
            await G2PRegisterHistoryMedicalCare.create_migrate()
            await G2PIntakeFormMedicalCare.create_migrate()

            await G2PRegisterHousingSupport.create_migrate()
            await G2PRegisterHistoryHousingSupport.create_migrate()
            await G2PIntakeFormHousingSupport.create_migrate()

            await G2PRegisterAnimalAssistance.create_migrate()
            await G2PRegisterHistoryAnimalAssistance.create_migrate()
            await G2PIntakeFormAnimalAssistance.create_migrate()

            await G2PRegisterRelatedPerson.create_migrate()
            await G2PRegisterHistoryRelatedPerson.create_migrate()
            await G2PIntakeFormRelatedPerson.create_migrate()

            await G2PRegisterProgramEnrolment.create_migrate()
            await G2PRegisterHistoryProgramEnrolment.create_migrate()
            await G2PIntakeFormProgramEnrolment.create_migrate()

        asyncio.run(migrate())
