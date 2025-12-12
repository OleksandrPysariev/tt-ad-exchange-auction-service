from abc import ABC, abstractmethod


class BaseBuilder(ABC):
    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs):  # noqa
        raise NotImplementedError
