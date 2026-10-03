# Excel Data Cleaner

English: [README.md](README.md)

![CI](https://github.com/gabrielvalle-491/excel-data-cleaner/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Limpia, valida y estandariza planillas grandes de forma automática.

Se le entrega una exportación desordenada de un CRM o una lista de clientes armada a mano (Excel o CSV)
y devuelve una tabla limpia, una lista de cada problema encontrado (con el número de fila original),
los duplicados que se eliminaron y un resumen, todo en un único informe de Excel.

## El problema de negocio

Un equipo de ventas guarda sus clientes en planillas completadas por distintas personas durante años:
nombres con mayúsculas y minúsculas al azar, correos con errores de tipeo (`@gmial.com`), teléfonos escritos de 5 maneras
distintas (`0351-15-1438687`, `+54 9 2657 717867`, `542657277863`), fechas en 5 formatos,
montos como `$ 1.234,56` o `USD 1234.5`, el mismo cliente cargado dos veces… Importar
eso a un CRM o enviar una campaña termina en errores o en correos rebotados.

## Qué hace

| Tipo de columna | Limpieza | Validación (va a la hoja Issues) |
|-----------------|----------|----------------------------------|
| `name` | Corrige espacios y mayúsculas, conserva las tildes, pasa a minúscula las partículas (*de la*) | Falta el dato, contiene dígitos |
| `email` | Pasa a minúsculas, quita espacios, **corrige automáticamente errores de tipeo comunes en el dominio** | Formato inválido, falta el dato |
| `phone` | Normaliza al formato internacional **E.164** (`+5492657351236`), quita el antiguo prefijo de celular `15`, detecta códigos de país | Longitud inválida, **el prefijo no coincide con la columna de país** |
| `date` | 8 formatos de entrada → ISO `YYYY-MM-DD` | Fechas imposibles (`31/02/2025`), formatos desconocidos |
| `amount` | `$ 1.234,50`, `1,234.50`, `USD 99.9` → `1234.5` | No es un número, negativo |
| `country` | Alias (`ARG`, `mx`, `EEUU`, `España`) → nombre estándar | País desconocido |
| `place` | Mayúscula inicial + espacios (`  buenos   AIRES` → `Buenos Aires`) | – |

Además:

- Reconoce **variaciones en los encabezados** (`E-mail`, `Correo`, `Mail` → `email`) mediante `config.yaml`.
- Descarta las filas completamente vacías y **elimina duplicados** después de normalizar (así, `ANA@GMAIL.COM ` y `ana@gmail.com` son el mismo cliente).
- Conserva el número de fila original de la planilla en cada problema, para poder rastrear las correcciones.

Todo se controla desde `config.yaml`: adaptarlo a otro archivo consiste en editar unas pocas líneas, no código.

## Inicio rápido

```bash
pip install -r requirements.txt

# 1) create a deliberately messy 500-row customer file
python -m data_cleaner.generate_messy_data samples/customers_messy.xlsx --rows 500

# 2) clean it
python -m data_cleaner samples/customers_messy.xlsx -o output/customers_clean_report.xlsx
```

```
Rows in: 541 | rows out: 499 | duplicates removed: 42
Issues logged: 246 (in 219 rows) -> output/customers_clean_report.xlsx
```

## Antes → después (salida real del comando anterior)

**Antes** (`samples/customers_messy.xlsx`)

| Nombre | E-mail | Telefono | País | Fecha alta | Monto compra | Ciudad |
|---|---|---|---|---|---|---|
| MARÍA pérez | MARIA.PEREZ95@GMAIL.COM | +54 9 2657 717867 | Argentina | 08.10.2024 | $ 62.355,63 | - |
| Carlos sosa | CARLOS.SOSA54@GMAIL.COM | 542657277863 | Argentina | 13-08-2024 | $ 113.128,45 | villa mercedes |
| Carlos GÓMEZ | sin dato | 541141794522 | argentina | 08/11/2025 | USD 58132.72 | CÓRDOBA |
| Carlos Fernández | carlos.fernandez90@gmial.com | 541142841438 | argentina | 30/11/2025 | USD 162536.79 | villa mercedes |

**Después** (hoja `Clean data`)

| name | email | phone | country | signup_date | purchase_amount | city |
|---|---|---|---|---|---:|---|
| María Pérez | maria.perez95@gmail.com | +5492657717867 | Argentina | 2024-10-08 | 62,355.63 | |
| Carlos Sosa | carlos.sosa54@gmail.com | +5492657277863 | Argentina | 2024-08-13 | 113,128.45 | Villa Mercedes |
| Carlos Gómez | | +5491141794522 | Argentina | 2025-11-08 | 58,132.72 | Córdoba |
| Carlos Fernández | carlos.fernandez90@gmail.com | +5491142841438 | Argentina | 2025-11-30 | 162,536.79 | Villa Mercedes |

**Problemas encontrados** (parte superior de la hoja `Summary`)

| Columna | Problema | Cantidad |
|---|---|---:|
| email | Fixed email typo: gmial.com | 67 |
| email | Fixed email typo: hotmail.con | 63 |
| email | Missing email | 49 |
| country | Unknown country | 24 |
| signup_date | Unrecognized date | 13 |
| phone | Phone prefix does not match country (Chile) | 9 |

El libro del informe tiene 4 hojas: **Summary** (resumen), **Clean data** (datos limpios), **Issues** (problemas) y **Duplicates** (duplicados).

## Estructura del proyecto

```
data_cleaner/
├── rules.py                # one function per column type: value -> (clean value, issue)
├── pipeline.py             # header aliases, rule application, dedupe, stats
├── report.py               # formatted Excel report
├── generate_messy_data.py  # realistic dirty demo data
└── cli.py
config.yaml                 # column -> rule mapping, aliases, required fields, dedupe keys
tests/                      # 31 pytest tests, run on every push (GitHub Actions)
```

## Pruebas

```bash
pytest -q
```

## Cómo se lo entregaría a un cliente

Si me contrata para esto, yo:

- Le pediría una o dos exportaciones reales (o anonimizadas) del archivo que hoy limpian, en Excel o CSV y con los encabezados que su equipo ya usa, y configuraría esos encabezados y reglas en `config.yaml`, de modo que no haga falta tocar código para su archivo.
- Acordaría con usted qué columnas son obligatorias y cuáles definen un duplicado (por ejemplo, correo y teléfono), y las cargaría en `required` y `dedupe_on`.
- Lo dejaría funcionando como un único comando, `python -m data_cleaner <your file> -o <report>.xlsx`, que usted o una tarea programada (Programador de tareas de Windows o cron) pueden ejecutar cada semana sobre la última exportación.
- Entregaría un informe de Excel por cada ejecución: **Clean data** listo para importar, **Issues** con el número de fila original y el valor de cada problema, **Duplicates** con los registros eliminados y un **Summary** con los totales.
- Haría visibles los problemas en lugar de ocultarlos: los valores incorrectos van a la hoja Issues, una columna que falta en su archivo aparece allí como `Column missing in file`, y si falta el archivo de entrada o el de configuración, la ejecución se detiene con el mensaje `File not found` y el código de salida 1, para que una tarea programada pueda detectar la falla.
- Agregaría una prueba por cada regla nueva o particularidad del archivo que encontremos, para que la ejecución semanal siga dando los mismos resultados.

## Notas

- Los datos de demostración son sintéticos (`generate_messy_data.py`). No se usan datos reales de clientes.
- Desarrollado con Python (pandas, openpyxl) y [Claude Code](https://claude.com/claude-code) como programador asistente con IA.

## Autor

**Gabriel Valle** — Automatización de datos e IA (Excel, PDF, flujos de trabajo) · Villa Mercedes, Argentina · Remoto
