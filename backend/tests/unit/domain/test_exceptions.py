import pytest
from domain.exceptions import DomainError, EntityNotFoundError, InvalidEntityError


def test_domain_error_can_be_raised():
    """Verify that domain exceptions can be raised and carry messages."""
    with pytest.raises(DomainError) as exc_info:
        raise DomainError("Base error")
    assert str(exc_info.value) == "Base error"


def test_entity_not_found_error_can_be_raised():
    """Verify that entity not found exceptions can be raised."""
    with pytest.raises(EntityNotFoundError) as exc_info:
        raise EntityNotFoundError("Entity missing")
    assert str(exc_info.value) == "Entity missing"


def test_invalid_entity_error_can_be_raised():
    """Verify that invalid entity exceptions can be raised."""
    with pytest.raises(InvalidEntityError) as exc_info:
        raise InvalidEntityError("Invalid format")
    assert str(exc_info.value) == "Invalid format"
