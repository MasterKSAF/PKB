from sqlalchemy.orm import Session
from api.v1.models.registry_service_enums import RegistryServiceEnums

def classifier_system_status(db: Session):
    """Get classification status codes from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'classification_status_code')

def classifier_system(db: Session):
    """Get classifier systems from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'classifier_system')

def document_status(db: Session):
    """Get document statuses from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'document_status')

def chunk_type(db: Session):
    """Get chunk types from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'chunk_type')

def classifier_status(db: Session):
    """Get classifier statuses from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'classifier_status')

def source_type(db: Session):
    """Get source types from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'source_type')

def era(db: Session):
    """Get eras from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'era')

def validity_status(db: Session):
    """Get validity statuses from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'validity_status')

def jurisdiction(db: Session):
    """Get jurisdictions from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'jurisdiction')

def term_type(db: Session):
    """Get term types from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'term_type')

def pending_status(db: Session):
    """Get pending statuses from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'pending_status')

def validation_status(db: Session):
    """Get validation statuses from rs_enums."""
    return RegistryServiceEnums.get_values_by_key(db, 'validation_status')
