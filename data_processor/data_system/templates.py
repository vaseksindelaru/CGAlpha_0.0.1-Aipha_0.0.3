from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional, Dict, Any, List, Type, TypeVar, ClassVar
import logging

logger = logging.getLogger(__name__)

T_BaseTemplate = TypeVar('T_BaseTemplate', bound='BaseDataRequestTemplate')

class BaseDataRequestTemplate(ABC):
    """Clase base abstracta para todas las plantillas de solicitud de datos."""
    _registry: ClassVar[Dict[str, Type['BaseDataRequestTemplate']]] = {}

    name: str
    description: Optional[str]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        template_type_name = getattr(cls, 'TEMPLATE_TYPE', None)
        if template_type_name:
            cls._registry[template_type_name] = cls
            logger.debug(f"Plantilla tipo '{template_type_name}' registrada para la clase {cls.__name__}.")

    def __init__(self, name: str, description: Optional[str] = None):
        if not name or not name.strip():
            raise ValueError("El nombre de la plantilla (name) no puede estar vacío.")
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def template_type(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    def from_dict(cls: Type[T_BaseTemplate], data: Dict[str, Any]) -> T_BaseTemplate:
        template_type_name = data.get('template_type')
        if not template_type_name:
            raise ValueError("El diccionario debe contener 'template_type'.")
        
        subclass = cls._registry.get(template_type_name)
        if not subclass:
            raise ValueError(f"Tipo de plantilla desconocido o no registrado: '{template_type_name}'.")
        
        if hasattr(subclass, '_deserialize_specific'):
            return subclass._deserialize_specific(data) # type: ignore
        else:
            raise NotImplementedError(f"La subclase {subclass.__name__} no implementa _deserialize_specific.")

@dataclass(eq=False)
class KlinesDataRequestTemplate(BaseDataRequestTemplate):
    """Plantilla específica para solicitar datos de klines (velas) de Binance."""
    TEMPLATE_TYPE: str = field(default="klines", init=False, repr=False)

    # Campos sin valor por defecto (deben ir primero)
    name: str
    symbol: str
    interval: str
    start_date: date
    end_date: date

    # Campos con valor por defecto (deben ir después)
    description: Optional[str] = None

    def __post_init__(self):
        super().__init__(self.name, self.description)
        
        if not self.symbol or not self.symbol.strip():
            raise ValueError("El símbolo (symbol) no puede estar vacío.")
        if self.end_date < self.start_date:
            raise ValueError(f"La fecha final ({self.end_date}) no puede ser anterior a la inicial ({self.start_date}).")

    @property
    def template_type(self) -> str:
        return self.TEMPLATE_TYPE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_type": self.template_type,
            "name": self.name,
            "description": self.description,
            "symbol": self.symbol,
            "interval": self.interval,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
        }

    @classmethod
    def _deserialize_specific(cls: Type['KlinesDataRequestTemplate'], data: Dict[str, Any]) -> 'KlinesDataRequestTemplate':
        try:
            return cls(
                name=data['name'],
                symbol=data['symbol'],
                interval=data['interval'],
                start_date=date.fromisoformat(data['start_date']),
                end_date=date.fromisoformat(data['end_date']),
                description=data.get('description'),
            )
        except KeyError as e:
            raise ValueError(f"Datos incompletos para KlinesDataRequestTemplate: falta {e}") from e

    def get_date_range(self) -> List[date]:
        dates = []
        current_date = self.start_date
        while current_date <= self.end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates
