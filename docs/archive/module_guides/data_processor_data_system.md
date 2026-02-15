# Documentación Completa del Módulo data_system (Data Processor)

Este documento detalla la arquitectura, componentes y lógica del sistema de datos de Aipha, actualizado para la estructura simplificada y la persistencia en **DuckDB**.

## 1. Estructura de Archivos (Data Processor)

El módulo ha sido simplificado para seguir una estructura plana y profesional, eliminando subdirectorios innecesarios y consolidando la lógica.

### Árbol de Directorios
```
data_processor/
├── data_system/         # Módulo principal
│   ├── __init__.py      # Exportaciones públicas
│   ├── client.py        # Cliente HTTP (ApiClient)
│   ├── fetcher.py       # Lógica de Binance (BinanceKlinesFetcher)
│   ├── templates.py     # Contratos de datos (Base + Klines)
│   ├── storage.py       # Persistencia (DuckDB + JSON Templates)
│   └── main.py          # Automatización y carga masiva
├── tests/               # Pruebas de integración y unitarias
├── docs/                # Guías y documentación técnica
└── data/                # Bases de datos y archivos temporales
```

### Resumen de Componentes
- **Total:** 6 archivos Python en el módulo core.
- **Persistencia:** DuckDB (Local OLAP) y JSON (Plantillas).
- **Dependencias Clave:** `requests`, `pandas`, `duckdb`.

---

## 2. ApiClient - Cliente HTTP (`client.py`)

### Propósito
Un cliente genérico para realizar peticiones HTTP/HTTPS robustas. Utiliza `requests.Session` para optimizar conexiones y maneja streaming para descargas grandes.

### Código Principal
```python
class ApiClient:
    def __init__(self, base_headers: Optional[Dict[str, str]] = None, timeout: int = 10):
        self._session = requests.Session()
        self._default_timeout = timeout
        # ... (inicialización)

    def make_request(self, url: str, method: str = "GET", ...) -> Optional[requests.Response]:
        # Maneja reintentos y errores comunes de red
        # ...

    def download_file(self, url: str, destination_path: str, ...) -> bool:
        # Implementa streaming (8KB chunks) para descargas eficientes
        # ...
```

---

## 3. Sistema de Templates (`templates.py`)

### Propósito
Define los **contratos de datos**. Utiliza un patrón de registro automático para permitir la extensibilidad de nuevas fuentes de datos sin modificar el core.

### Componentes
1. **BaseDataRequestTemplate**: Clase base abstracta que implementa el auto-registro mediante `__init_subclass__`.
2. **KlinesDataRequestTemplate**: Implementación específica para velas de Binance, incluyendo validación de fechas y símbolos.

---

## 4. BinanceKlinesFetcher (`fetcher.py`)

### Propósito
Especializado en la adquisición de datos de Binance Vision. Traduce los templates en peticiones físicas y procesa los resultados.

### Flujo de Trabajo
1. **Construcción de URL**: Genera la ruta al archivo ZIP en Binance Vision.
2. **Descarga**: Utiliza `ApiClient.download_file` con caché local.
3. **Parsing**: Extrae el CSV del ZIP y lo convierte en un `pd.DataFrame` tipado.
4. **Consolidación**: Une múltiples días en un solo DataFrame ordenado cronológicamente.

---

## 5. Persistencia y Gestión (`storage.py`)

### DuckDB (Persistencia de Datos)
Reemplaza la dependencia de bases de datos externas (Cloud SQL) por un motor OLAP local extremadamente rápido.
- **Función**: `save_results_to_duckdb(df, table_name)`
- **Ventaja**: Inserción directa de DataFrames de Pandas sin necesidad de mapeo manual de esquemas.

### DataRequestTemplateManager (Gestión de Plantillas)
Gestiona una colección persistente de configuraciones de descarga en formato JSON.
- **Archivo**: `data_processor/data/project_data_templates.json`
- **Funciones**: Carga, guarda, añade y recupera plantillas por nombre.

---

## 6. Automatización (`main.py`)

### Propósito
Proporciona una interfaz de línea de comandos para tareas de mantenimiento y carga masiva.
- **Lógica**: Lee archivos CSV locales y los inyecta en tablas de DuckDB.
- **Uso**: Ideal para migrar datos históricos o resultados de procesos externos al sistema central.

---

## 7. Verificación y Tests

### Test de Integración (`tests/data_system/test_integration.py`)
Valida el flujo completo:
1. Creación de plantilla.
2. Descarga de datos reales de Binance.
3. Procesamiento en Pandas.
4. Persistencia en DuckDB.
5. Verificación de conteo de filas en la base de datos.

---

## 8. Mejores Prácticas Implementadas
- **Logging Estructurado**: Cada componente utiliza su propio logger para facilitar el debugging.
- **Manejo de Errores**: Uso de bloques `try-except` específicos y limpieza de archivos parciales en descargas fallidas.
- **Modularidad**: Separación clara entre transporte (client), lógica de negocio (fetcher) y persistencia (storage).
