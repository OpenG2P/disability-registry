"""Code lists for the Disability Registry.

Every list here is INTERNATIONAL, not country-specific: they are drawn from the
WHO/World Bank framing of disability data (ICF), the Washington Group question
sets, the WHO Priority Assistive Products List, and the UNCRPD vocabulary around
legal capacity and independent living.

These enums are the *shape* the ORM and the API accept. The values an operator
actually sees in a dropdown come from `g2p_attribute_values`, seeded from
`meta_data/lookup-data/*_defaults.sql` and overridable by a country pack. Keep
the two in step: a value that exists in one and not the other is a field that
silently refuses to save (enum missing) or a dropdown with no options (code list
missing).
"""

import enum


# ---------------------------------------------------------------------------
# DO.DR.03 PersonwithDisability — status, assessment, living situation
# ---------------------------------------------------------------------------


class DisabilityStatusEnum(str, enum.Enum):
    """`disability_status` — the outcome of a disability assessment.

    Distinct from `self_id_disability`, which is what the person says about
    themselves. A registry needs both: self-identification drives outreach,
    assessment drives entitlement.
    """

    ASSESSED_DISABLED = "ASSESSED_DISABLED"
    ASSESSED_NOT_DISABLED = "ASSESSED_NOT_DISABLED"
    PENDING_ASSESSMENT = "PENDING_ASSESSMENT"
    SELF_DECLARED = "SELF_DECLARED"
    UNKNOWN = "UNKNOWN"


class DisabilityStatusLevelEnum(str, enum.Enum):
    """`disability_status_level` — severity category assigned after assessment."""

    NONE = "NONE"
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    PROFOUND = "PROFOUND"


class SupportNeedsLevelEnum(str, enum.Enum):
    """Intensity-of-support classification (AAIDD-style), independent of severity.

    Two people with the same impairment level can need very different amounts of
    support depending on their environment — which is the social model of
    disability the UNCRPD is built on, and the reason this is a separate field.
    """

    INDEPENDENT = "INDEPENDENT"
    INTERMITTENT_SUPPORT = "INTERMITTENT_SUPPORT"
    LIMITED_SUPPORT = "LIMITED_SUPPORT"
    EXTENSIVE_SUPPORT = "EXTENSIVE_SUPPORT"
    PERVASIVE_SUPPORT = "PERVASIVE_SUPPORT"


class LegalCapacityStatusEnum(str, enum.Enum):
    """UNCRPD Article 12 — supported vs substituted decision-making."""

    FULL_CAPACITY = "FULL_CAPACITY"
    SUPPORTED_DECISION_MAKING = "SUPPORTED_DECISION_MAKING"
    PARTIAL_GUARDIANSHIP = "PARTIAL_GUARDIANSHIP"
    FULL_GUARDIANSHIP = "FULL_GUARDIANSHIP"
    UNDER_REVIEW = "UNDER_REVIEW"
    UNKNOWN = "UNKNOWN"


class TransportRequirementEnum(str, enum.Enum):
    """`transport_requirement` — type of transport/mobility the person needs."""

    NONE = "NONE"
    ACCESSIBLE_PUBLIC_TRANSPORT = "ACCESSIBLE_PUBLIC_TRANSPORT"
    ADAPTED_VEHICLE = "ADAPTED_VEHICLE"
    WHEELCHAIR_ACCESSIBLE_VEHICLE = "WHEELCHAIR_ACCESSIBLE_VEHICLE"
    ESCORTED_TRAVEL = "ESCORTED_TRAVEL"
    AMBULANCE_TRANSPORT = "AMBULANCE_TRANSPORT"
    TRANSPORT_ALLOWANCE = "TRANSPORT_ALLOWANCE"
    OTHER = "OTHER"


class HousingTypeEnum(str, enum.Enum):
    """`housing_type` — where the person is living."""

    INDEPENDENT_HOME = "INDEPENDENT_HOME"
    FAMILY_HOME = "FAMILY_HOME"
    SUPPORTED_LIVING = "SUPPORTED_LIVING"
    GROUP_HOME = "GROUP_HOME"
    RESIDENTIAL_INSTITUTION = "RESIDENTIAL_INSTITUTION"
    HOSPITAL_LONG_STAY = "HOSPITAL_LONG_STAY"
    TEMPORARY_SHELTER = "TEMPORARY_SHELTER"
    HOMELESS = "HOMELESS"
    OTHER = "OTHER"


class CommunicationNeedEnum(str, enum.Enum):
    """Accessible-communication requirements (UNCRPD Article 21).

    Stored as a JSON list on the person, because these genuinely co-occur — a
    deafblind registrant may need both tactile signing and large print.
    """

    SIGN_LANGUAGE = "SIGN_LANGUAGE"
    TACTILE_SIGNING = "TACTILE_SIGNING"
    BRAILLE = "BRAILLE"
    LARGE_PRINT = "LARGE_PRINT"
    EASY_READ = "EASY_READ"
    AUDIO = "AUDIO"
    CAPTIONING = "CAPTIONING"
    PICTOGRAMS = "PICTOGRAMS"
    INTERPRETER_REQUIRED = "INTERPRETER_REQUIRED"
    NONE = "NONE"


# ---------------------------------------------------------------------------
# DO.DR.04 DisabilityDetails
# ---------------------------------------------------------------------------


class ImpairmentTypeEnum(str, enum.Enum):
    """`impairment_type` — ICF body-function/structure grouping."""

    VISUAL = "VISUAL"
    HEARING = "HEARING"
    DEAFBLIND = "DEAFBLIND"
    PHYSICAL_MOBILITY = "PHYSICAL_MOBILITY"
    SPEECH_LANGUAGE = "SPEECH_LANGUAGE"
    INTELLECTUAL = "INTELLECTUAL"
    PSYCHOSOCIAL = "PSYCHOSOCIAL"
    NEUROLOGICAL = "NEUROLOGICAL"
    LEARNING = "LEARNING"
    CHRONIC_ILLNESS = "CHRONIC_ILLNESS"
    MULTIPLE = "MULTIPLE"
    OTHER = "OTHER"


class ImpairmentLevelEnum(str, enum.Enum):
    """`impairment_level` — the Washington Group functional-difficulty scale.

    Used rather than a bespoke mild/severe ladder because it is the scale
    national censuses already collect, so a registry seeded from census or
    household-survey data does not have to be re-coded.
    """

    NO_DIFFICULTY = "NO_DIFFICULTY"
    SOME_DIFFICULTY = "SOME_DIFFICULTY"
    A_LOT_OF_DIFFICULTY = "A_LOT_OF_DIFFICULTY"
    CANNOT_DO_AT_ALL = "CANNOT_DO_AT_ALL"


class ImpairmentCauseEnum(str, enum.Enum):
    """`impairment_cause` — reason for the disability."""

    CONGENITAL = "CONGENITAL"
    ILLNESS = "ILLNESS"
    WORK_ACCIDENT = "WORK_ACCIDENT"
    ROAD_ACCIDENT = "ROAD_ACCIDENT"
    OTHER_ACCIDENT = "OTHER_ACCIDENT"
    CONFLICT_VIOLENCE = "CONFLICT_VIOLENCE"
    NATURAL_DISASTER = "NATURAL_DISASTER"
    AGEING = "AGEING"
    MEDICAL_COMPLICATION = "MEDICAL_COMPLICATION"
    UNKNOWN = "UNKNOWN"
    OTHER = "OTHER"


class AgeOnsetBandEnum(str, enum.Enum):
    """Banded companion to the numeric `age_on_set`.

    The band is what reporting groups by, and it is answerable ("since birth")
    when the exact age is not.
    """

    AT_BIRTH = "AT_BIRTH"
    EARLY_CHILDHOOD_0_5 = "EARLY_CHILDHOOD_0_5"
    CHILDHOOD_6_12 = "CHILDHOOD_6_12"
    ADOLESCENCE_13_17 = "ADOLESCENCE_13_17"
    ADULTHOOD_18_59 = "ADULTHOOD_18_59"
    OLD_AGE_60_PLUS = "OLD_AGE_60_PLUS"
    UNKNOWN = "UNKNOWN"


class AssessmentMethodEnum(str, enum.Enum):
    """How the impairment was established — provenance for the level recorded."""

    CLINICAL_ASSESSMENT = "CLINICAL_ASSESSMENT"
    WASHINGTON_GROUP_SHORT_SET = "WASHINGTON_GROUP_SHORT_SET"
    WASHINGTON_GROUP_EXTENDED = "WASHINGTON_GROUP_EXTENDED"
    WHODAS_2_0 = "WHODAS_2_0"
    ICF_BASED = "ICF_BASED"
    MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE"
    SELF_REPORT = "SELF_REPORT"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.05 DisabilitySupport — shared across DO.DR.06 - DO.DR.10
# ---------------------------------------------------------------------------


class SupportStatusEnum(str, enum.Enum):
    """`support_status` — shared by every support sub-register.

    The REQUIRED/RECEIVING split is the whole point of the disability registry
    as an interface to social protection: the gap between the two is the unmet
    need a programme is meant to close.
    """

    REQUIRED = "REQUIRED"
    RECEIVING = "RECEIVING"
    RECEIVED = "RECEIVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    NOT_REQUIRED = "NOT_REQUIRED"
    DISCONTINUED = "DISCONTINUED"


class SupportFrequencyEnum(str, enum.Enum):
    """`frequency` — how often the support is required or received."""

    PERMANENT = "PERMANENT"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    OCCASIONAL = "OCCASIONAL"
    AS_NEEDED = "AS_NEEDED"
    TEMPORARY = "TEMPORARY"


class ProvisionSourceEnum(str, enum.Enum):
    """Who supplied the support — needed to avoid double-counting across programmes."""

    GOVERNMENT_PROGRAM = "GOVERNMENT_PROGRAM"
    NGO = "NGO"
    INSURANCE = "INSURANCE"
    PRIVATE_PURCHASE = "PRIVATE_PURCHASE"
    DONATION = "DONATION"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.06 HumanAssistance
# ---------------------------------------------------------------------------


class HumanAssistanceTypeEnum(str, enum.Enum):
    """`type` — kind of human assistance required or received."""

    PERSONAL_CARE = "PERSONAL_CARE"
    MOBILITY = "MOBILITY"
    COMMUNICATION = "COMMUNICATION"
    SIGN_LANGUAGE_INTERPRETATION = "SIGN_LANGUAGE_INTERPRETATION"
    DOMESTIC_SUPPORT = "DOMESTIC_SUPPORT"
    MEDICAL_SUPPORT = "MEDICAL_SUPPORT"
    EDUCATIONAL_SUPPORT = "EDUCATIONAL_SUPPORT"
    EMPLOYMENT_SUPPORT = "EMPLOYMENT_SUPPORT"
    FINANCIAL_MANAGEMENT = "FINANCIAL_MANAGEMENT"
    SUPERVISION = "SUPERVISION"
    OTHER = "OTHER"


class CaregiverRelationshipEnum(str, enum.Enum):
    """`relationship` — the caregiver's relationship to the person with disability."""

    SPOUSE = "SPOUSE"
    PARENT = "PARENT"
    CHILD = "CHILD"
    SIBLING = "SIBLING"
    OTHER_RELATIVE = "OTHER_RELATIVE"
    NEIGHBOUR = "NEIGHBOUR"
    FRIEND = "FRIEND"
    PAID_CAREGIVER = "PAID_CAREGIVER"
    COMMUNITY_VOLUNTEER = "COMMUNITY_VOLUNTEER"
    INSTITUTION = "INSTITUTION"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.07 AssistiveTechnology
# ---------------------------------------------------------------------------


class AssistiveTechnologyTypeEnum(str, enum.Enum):
    """`type` — drawn from the WHO Priority Assistive Products List (APL).

    Using the APL rather than an invented list means a country's procurement and
    the registry's unmet-need report are already talking about the same objects.
    """

    CANES = "CANES"
    CRUTCHES = "CRUTCHES"
    WALKING_FRAMES = "WALKING_FRAMES"
    MANUAL_WHEELCHAIR = "MANUAL_WHEELCHAIR"
    ELECTRIC_WHEELCHAIR = "ELECTRIC_WHEELCHAIR"
    PROSTHESES = "PROSTHESES"
    ORTHOSES = "ORTHOSES"
    THERAPEUTIC_FOOTWEAR = "THERAPEUTIC_FOOTWEAR"
    HEARING_AIDS = "HEARING_AIDS"
    COCHLEAR_IMPLANTS = "COCHLEAR_IMPLANTS"
    SPECTACLES = "SPECTACLES"
    MAGNIFIERS = "MAGNIFIERS"
    BRAILLE_DEVICES = "BRAILLE_DEVICES"
    SCREEN_READERS = "SCREEN_READERS"
    COMMUNICATION_BOARDS = "COMMUNICATION_BOARDS"
    SPEECH_GENERATING_DEVICES = "SPEECH_GENERATING_DEVICES"
    PRESSURE_RELIEF_CUSHIONS = "PRESSURE_RELIEF_CUSHIONS"
    INCONTINENCE_PRODUCTS = "INCONTINENCE_PRODUCTS"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.08 MedicalCare
# ---------------------------------------------------------------------------


class MedicalCareTypeEnum(str, enum.Enum):
    """`type` — chronic care that generates recurring out-of-pocket cost."""

    MAINTENANCE_MEDICINE = "MAINTENANCE_MEDICINE"
    PHYSIOTHERAPY = "PHYSIOTHERAPY"
    OCCUPATIONAL_THERAPY = "OCCUPATIONAL_THERAPY"
    SPEECH_THERAPY = "SPEECH_THERAPY"
    PSYCHIATRIC_CARE = "PSYCHIATRIC_CARE"
    PSYCHOLOGICAL_COUNSELLING = "PSYCHOLOGICAL_COUNSELLING"
    DIALYSIS = "DIALYSIS"
    REGULAR_SPECIALIST_REVIEW = "REGULAR_SPECIALIST_REVIEW"
    SURGERY = "SURGERY"
    WOUND_CARE = "WOUND_CARE"
    RESPIRATORY_SUPPORT = "RESPIRATORY_SUPPORT"
    NUTRITION_SUPPORT = "NUTRITION_SUPPORT"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.09 HousingSupport
# ---------------------------------------------------------------------------


class HousingSupportTypeEnum(str, enum.Enum):
    """`type` — support addressing barriers in housing."""

    RAMP_INSTALLATION = "RAMP_INSTALLATION"
    HANDRAILS = "HANDRAILS"
    BATHROOM_MODIFICATION = "BATHROOM_MODIFICATION"
    DOOR_WIDENING = "DOOR_WIDENING"
    GROUND_FLOOR_ALLOCATION = "GROUND_FLOOR_ALLOCATION"
    RELOCATION = "RELOCATION"
    RENT_SUBSIDY = "RENT_SUBSIDY"
    ACCESSIBLE_SOCIAL_HOUSING = "ACCESSIBLE_SOCIAL_HOUSING"
    ASSISTED_LIVING_FACILITY = "ASSISTED_LIVING_FACILITY"
    RESIDENTIAL_CARE = "RESIDENTIAL_CARE"
    HOME_REPAIR = "HOME_REPAIR"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.10 AnimalAssistance
# ---------------------------------------------------------------------------


class AnimalAssistanceTypeEnum(str, enum.Enum):
    """`type` — assistance animal by the task it is trained for."""

    GUIDE_DOG = "GUIDE_DOG"
    HEARING_DOG = "HEARING_DOG"
    ALERT_DOG = "ALERT_DOG"
    MOBILITY_ASSISTANCE_DOG = "MOBILITY_ASSISTANCE_DOG"
    PSYCHIATRIC_SERVICE_DOG = "PSYCHIATRIC_SERVICE_DOG"
    SEIZURE_RESPONSE_DOG = "SEIZURE_RESPONSE_DOG"
    THERAPY_ANIMAL = "THERAPY_ANIMAL"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.02 Member — related persons, socio-economic attributes
# ---------------------------------------------------------------------------


class RelationshipTypeEnum(str, enum.Enum):
    """`related_person.relationship_type`."""

    SPOUSE = "SPOUSE"
    PARENT = "PARENT"
    CHILD = "CHILD"
    SIBLING = "SIBLING"
    GRANDPARENT = "GRANDPARENT"
    GRANDCHILD = "GRANDCHILD"
    GUARDIAN = "GUARDIAN"
    OTHER_RELATIVE = "OTHER_RELATIVE"
    NON_RELATIVE = "NON_RELATIVE"


class EmploymentStatusEnum(str, enum.Enum):
    """`employment_status` — with the disability-specific employment modes.

    Sheltered and supported employment are separated from plain EMPLOYED because
    conflating them hides exactly the transition an inclusion programme exists to
    produce.
    """

    EMPLOYED = "EMPLOYED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    SHELTERED_EMPLOYMENT = "SHELTERED_EMPLOYMENT"
    SUPPORTED_EMPLOYMENT = "SUPPORTED_EMPLOYMENT"
    UNEMPLOYED_SEEKING = "UNEMPLOYED_SEEKING"
    UNEMPLOYED_NOT_SEEKING = "UNEMPLOYED_NOT_SEEKING"
    STUDENT = "STUDENT"
    RETIRED = "RETIRED"
    UNABLE_TO_WORK = "UNABLE_TO_WORK"
    OTHER = "OTHER"


class PreferredContactMethodEnum(str, enum.Enum):
    """How to reach this person — an accessibility question, not a convenience one."""

    CALL = "CALL"
    SMS = "SMS"
    EMAIL = "EMAIL"
    SIGN_LANGUAGE_VIDEO_CALL = "SIGN_LANGUAGE_VIDEO_CALL"
    VIA_CAREGIVER = "VIA_CAREGIVER"
    VIA_LOCAL_OFFICE = "VIA_LOCAL_OFFICE"
    NONE = "NONE"


# ---------------------------------------------------------------------------
# Identity and provenance
# ---------------------------------------------------------------------------


class VerificationStatusEnum(str, enum.Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    EXCEPTION = "EXCEPTION"


class IdentityEvidenceTypeEnum(str, enum.Enum):
    FOUNDATIONAL_ID_VERIFIED = "FOUNDATIONAL_ID_VERIFIED"
    DISABILITY_CERTIFICATE = "DISABILITY_CERTIFICATE"
    DOCUMENT = "DOCUMENT"
    NONE = "NONE"
    EXCEPTION = "EXCEPTION"


class RegistrationChannelEnum(str, enum.Enum):
    """How the person came into the registry — an equity measure in its own right."""

    SELF_REGISTRATION = "SELF_REGISTRATION"
    ASSISTED_REGISTRATION = "ASSISTED_REGISTRATION"
    HOME_VISIT = "HOME_VISIT"
    HEALTH_FACILITY_REFERRAL = "HEALTH_FACILITY_REFERRAL"
    SCHOOL_REFERRAL = "SCHOOL_REFERRAL"
    OPD_REFERRAL = "OPD_REFERRAL"
    SOCIAL_REGISTRY_TRANSFER = "SOCIAL_REGISTRY_TRANSFER"
    CRVS_TRANSFER = "CRVS_TRANSFER"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# DO.DR.03 programs_enrolments
# ---------------------------------------------------------------------------


class ProgramEnrolmentStatusEnum(str, enum.Enum):
    APPLIED = "APPLIED"
    ENROLLED = "ENROLLED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXITED = "EXITED"
    REJECTED = "REJECTED"


class ProgramEnum(str, enum.Enum):
    """Matches ``PROGRAM_NAME`` ``value_id`` rows in ``g2p_attribute_values``.

    Deliberately generic disability-relevant programme archetypes — a country
    pack replaces these with its own.
    """

    PROG_DISABILITY_ALLOWANCE = "PROG_DISABILITY_ALLOWANCE"
    PROG_CAREGIVER_ALLOWANCE = "PROG_CAREGIVER_ALLOWANCE"
    PROG_ASSISTIVE_DEVICE_GRANT = "PROG_ASSISTIVE_DEVICE_GRANT"
    PROG_HEALTH_INSURANCE = "PROG_HEALTH_INSURANCE"
    PROG_REHABILITATION_SERVICES = "PROG_REHABILITATION_SERVICES"
    PROG_INCLUSIVE_EDUCATION = "PROG_INCLUSIVE_EDUCATION"
    PROG_VOCATIONAL_TRAINING = "PROG_VOCATIONAL_TRAINING"
    PROG_EMPLOYMENT_QUOTA = "PROG_EMPLOYMENT_QUOTA"
    PROG_HOUSING_ADAPTATION = "PROG_HOUSING_ADAPTATION"
    PROG_TRANSPORT_CONCESSION = "PROG_TRANSPORT_CONCESSION"
