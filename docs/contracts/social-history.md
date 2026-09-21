# Historia social: alcohol y tabaco

El paquete 1.25.21 incorpora un formulario AMPATH independiente para historia social.
Reutiliza preguntas y respuestas existentes en `SIHSALUS/sihsalus/2026-09-09-1`;
no añade ni reinterpreta conceptos OCL. El frontend debe usar el mismo componente
para la entrada desde Consulta Externa y desde Historia Social.

## Identidades

| Recurso                                  | Identidad                              |
| ---------------------------------------- | -------------------------------------- |
| Nombre y versión                         | `CE-SOC-001-HISTORIA SOCIAL`, `1.0.0`  |
| UUID del JSON                            | `f18f4320-690b-4c34-9b20-89a9bf7fec71` |
| UUID del Form persistido por Initializer | `76067e7a-48e5-3f69-92a4-70cf53e3e994` |
| Tipo de encuentro Historia social        | `c7059f4b-385f-45e7-82ad-204e5b380196` |

El UUID del Form se deriva del nombre y versión con la regla de Initializer 2.12,
verificada por `validate_social_history_contract.py`. El UUID del JSON no sirve
como identificador REST del Form. Cambiar la versión requiere coordinar el nuevo
UUID persistido con el frontend y conservar la lectura de versiones anteriores.

## Datos y acceso

| Dato                           | Concepto existente                     | Respuestas / unidad               |
| ------------------------------ | -------------------------------------- | --------------------------------- |
| Consumo de alcohol             | `fcd7736e-39d4-4ecd-84e0-9129e9690809` | Sí / No                           |
| Consumo de tabaco              | `a79047b1-aa5c-44ab-9410-02afb350c80a` | Sí / No                           |
| Cigarrillos por día            | `1546AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Entero, mínimo 0                  |
| Duración del consumo de tabaco | `159931AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Años, mínimo 0; admite fracciones |

Las respuestas son Sí (`372a262c-8d57-4b57-ad29-b24a2941b749`) y No
(`5b2a0f81-22df-4ee1-ae2e-3c547cd7ec9f`). El validador general comprueba sus
mappings Q-AND-A contra ambos conceptos. Las observaciones son opcionales, sin
valor inicial, copia automática ni ocultamiento condicional. No evaluado se
conserva como ausencia de observación, nunca como No o cero. No se deduce un
diagnóstico ni se calcula exposición acumulada.

Fecha, profesional y ubicación son obligatorios. El frontend vincula registros
nuevos a una visita ambulatoria activa, recupera un registro ya existente de ese
formulario en esa visita y bloquea duplicados ambiguos. Al editar, conserva la
visita original del encuentro. La lectura usa `app:hoja.clinica.historiaSocial` y
la edición `app:hoja.clinica.historiaSocial.editar`, sin cambios de roles.

## Compatibilidad y puesta en servicio

El formulario genérico `e958f902-64df-4819-afd4-7fb061f59308` no está en este
paquete. Su tipo configurado históricamente, `465a92f2-baf8-42e9-9612-53064be868e8`,
es Terapia física. Ninguno se sustituye o migra. Los registros previos siguen
visibles y conservan su semántica; no se editan con este formulario nuevo.
Los estados codificados antiguos sin respuestas Q-AND-A no se reutilizan como
preguntas de Sí/No. Otras sustancias quedan para una iteración clínica posterior.

Referencia revisada el 21/09/2026: [R.M. 214-2018/MINSA y NTS 139](https://www.gob.pe/institucion/minsa/normas-legales/187487-214-),
que incluye antecedentes personales y hábitos dentro de la historia clínica.
La [R.M. 265-2018/MINSA](https://www.gob.pe/institucion/minsa/normas-legales/187373-265-2018-minsa)
modifica la definición de acto de salud. Estas referencias no prescriben este
formulario de cuatro preguntas ni sustituyen la aceptación clínica institucional.

Se debe publicar y cargar el content antes de habilitar el frontend dependiente;
preparar estos PR no modifica el pin del distro ni despliega entornos. Pendiente
en DEV/QLTY coordinado: verificar importación con Initializer, UUID REST efectivo,
permisos por rol, guardar/editar/reabrir con datos sintéticos, ausencia de cambios
en visitas anteriores y aceptación clínica. Los validadores locales no prueban
la persistencia en OpenMRS. Para rollback, retirar el frontend dependiente y
conservar encuentros, observaciones y metadata ya utilizada; no borrar datos.

## Validación local

```sh
python3 .github/scripts/validate_social_history_contract.py
python3 .github/scripts/test_social_history_contract.py
python3 .github/scripts/validate_ampath_forms.py
python3 .github/scripts/validate_form_concept_integrity.py
python3 .github/scripts/validate_csv_widths.py
mvn clean verify --batch-mode --file pom.xml
```
