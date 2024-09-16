from dataclasses import asdict, dataclass

from autogen_core.components.models import LLMMessage


@dataclass
class GroupChatMessage:
    body: LLMMessage

    def to_dict(self):
        return asdict(self)


@dataclass
class RequestToSpeak:
    def to_dict(self):
        return asdict(self)
