from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class NormalizedCost:
    external_id: str
    usage_date: date
    provider: str
    account_id: str
    service: str
    category: str
    resource: str
    project: str
    department: str
    environment: str
    currency: str
    cost: float
    source: str


class CostProvider(ABC):
    @abstractmethod
    async def fetch_costs(self, window: str) -> list[NormalizedCost]:
        raise NotImplementedError
