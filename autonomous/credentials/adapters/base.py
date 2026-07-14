from abc import ABC, abstractmethod


class CredentialAdapter(ABC):

    @abstractmethod
    def provider(self):
        pass

    @abstractmethod
    def acquire(self, request):
        pass

    @abstractmethod
    def validate(self, credential):
        pass

    @abstractmethod
    def revoke(self, credential):
        pass
