# Presentaciones adicionales del catálogo clínico

Initializer carga los principios activos de
`concepts/clinical_drug_concepts.csv` antes de las presentaciones de
`drugs/clinical-drugs.csv`. Los UUID son estables y las referencias son
explícitas; la instalación y las actualizaciones usan los cargadores nativos
del paquete de contenido.

El ácido ursodesoxicólico faltaba tanto en el export OCL de medicamentos
incluido en este paquete como en `minsa-drugs.csv`. Se incorpora como concepto
`Drug` con tipo `N/A` y una presentación ordenable de 250 mg en tableta. La
forma farmacéutica reutiliza el concepto existente `Tableta`
(`bd1e9059-62b4-4967-a804-a63eda4f8657`).

La identidad y presentación proceden del [Petitorio Farmacológico de
EsSalud](https://ietsi.essalud.gob.pe/petitorio-farmacologico-essalud/), entrada
`010450038`, consultado el 12 de septiembre de 2026. Ese código pertenece a
EsSalud: no se le asigna un código MINSA ni se modifica el export OCL. Estos
archivos pertenecen al catálogo local SIHSALUS; una futura incorporación al
diccionario OCL debe conservar los UUID para evitar duplicados.

El registro describe una presentación, no existencias, disponibilidad física,
indicación, pauta de administración ni autorización de dispensación.

La aceptación del frontend comprueba que la búsqueda devuelva un medicamento
activo con concepto `Drug`, concentración y forma farmacéutica; no acepta
texto libre. Antes de publicar, debe pasar además la carga completa del
paquete por Initializer y una recarga sin duplicar el concepto o presentación.

El ensayo de CI con backend real comprueba esa carga en una instalación nueva
y en una actualización. Consulta las identidades, clase, tipo, concentración y
forma farmacéutica persistidas; después del reinicio exige que se conserven sin
duplicados. La búsqueda REST usa la misma representación que el buscador de
medicamentos del frontend. Estos controles usan una base desechable y no
sustituyen la aceptación de médicos en DEV/QLTY.
