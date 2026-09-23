# Metadata institucional del Hospital Santa Clotilde

Este contrato versiona la identidad institucional que los consumidores deben leer de la
`Location` canónica `Hospital Santa Clotilde` (`35d2234e-129a-4c40-abb2-1ae0b72c1602`).

## Fuente y alcance

La ficha estatal de GeoPerú para la IPRESS `00000066`, consultada el 2026-08-25, publica el
distrito Napo, la provincia Maynas, la región Loreto y el teléfono `965336199`. La propia ficha
identifica su fuente como MINSA/SUSALUD y la fecha de actualización del conjunto como
2023-05-18:

- https://visor.geoperu.gob.pe/reportes/consulta_instituciones_salud.phtml?ocampo=gid&olayer=peru_hospitales&ovalor=00000066

La fuente no proporciona una calle utilizable. Por ello `Address 4` permanece vacío; no debe
completarse a partir de texto corrupto, referencias informales o inferencias.

## Ubicación canónica

| Campo OpenMRS | Valor |
| --- | --- |
| `Address 1` (Región) | `LORETO` |
| `State/Province` (Provincia) | `MAYNAS` |
| `County/District` (Distrito) | `NAPO` |
| `City/Village` | `SANTA CLOTILDE` |
| `Address 4` (Dirección/calle) | Vacío |
| `Country` | `PERU` |

Los significados de estos campos están definidos por
`configuration/addresshierarchy/addressConfiguration.xml`.

## Atributos institucionales

| Tipo de atributo `Location` | UUID | Valor del hospital |
| --- | --- | --- |
| `Teléfono institucional` | `07c79e2a-b4e8-4100-9210-6f87bc9b77c9` | `965 336 199` |
| `Código Único IPRESS` | `5fd2b028-5b40-4c85-9a65-01a7ea2cde2b` | `00000066` |

Ambos tipos son `FreeText`, opcionales y de cardinalidad máxima uno. Los consumidores deben
resolverlos por UUID y pueden usar el nombre únicamente para presentación.

Los valores se cargan desde `locations/hospital-institutional-attributes.csv`, que contiene solo
la fila del hospital y se procesa después del catálogo general. Esa fila repite nombre,
descripción, padre y todos los campos de dirección porque el cargador de ubicaciones de Initializer
los vuelve a asignar incluso cuando la cabecera no está presente; el validador exige que ambas filas
permanezcan sincronizadas. No se deben agregar las columnas de atributos al CSV compartido:
Initializer interpreta una celda de atributo vacía como anulación del valor activo de esa
ubicación.

El paquete también fija `drugOrder.requireOutpatientQuantity=true` para que una prescripción
ambulatoria no se guarde sin cantidad ni unidad de dispensación.
