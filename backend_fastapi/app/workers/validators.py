import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list = field(default_factory=list)

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.is_valid = False

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        combined_errors = self.errors + other.errors
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=combined_errors
        )

    @property
    def error_message(self) -> Optional[str]:
        if not self.errors:
            return None
        return "; ".join(self.errors)


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, data: dict) -> ValidationResult:
        pass


class MessageValidator(BaseValidator):
    MIN_LENGTH = 1
    MAX_LENGTH = 10000

    def validate(self, data: dict) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        message = data.get("message", "")

        if not message:
            result.add_error("Message is required")
            return result

        if not isinstance(message, str):
            result.add_error("Message must be a string")
            return result

        message = message.strip()

        if len(message) < self.MIN_LENGTH:
            result.add_error("Message cannot be empty")

        if len(message) > self.MAX_LENGTH:
            result.add_error(f"Message exceeds maximum length of {self.MAX_LENGTH}")

        return result


class HistoryValidator(BaseValidator):
    MAX_HISTORY_LENGTH = 100
    ALLOWED_ROLES = {"user", "assistant", "system"}

    def validate(self, data: dict) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        history = data.get("conversation_history", [])

        if history is None:
            return result

        if not isinstance(history, list):
            result.add_error("Conversation history must be a list")
            return result

        if len(history) > self.MAX_HISTORY_LENGTH:
            result.add_error(
                f"Conversation history exceeds maximum length of {self.MAX_HISTORY_LENGTH}"
            )
            return result

        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                result.add_error(f"History item {idx} must be an object")
                continue

            if "role" not in item:
                result.add_error(f"History item {idx} missing 'role' field")
            elif item["role"] not in self.ALLOWED_ROLES:
                result.add_error(f"History item {idx} has invalid role")

            if "content" not in item:
                result.add_error(f"History item {idx} missing 'content' field")

        return result


class CompositeValidator(BaseValidator):
    def __init__(self, validators: list):
        self._validators = validators

    def validate(self, data: dict) -> ValidationResult:
        result = ValidationResult(is_valid=True)

        for validator in self._validators:
            validator_result = validator.validate(data)
            result = result.merge(validator_result)

        return result


class TaskValidatorFactory:
    @staticmethod
    def create_ml_task_validator() -> CompositeValidator:
        return CompositeValidator([
            MessageValidator(),
            HistoryValidator(),
        ])
