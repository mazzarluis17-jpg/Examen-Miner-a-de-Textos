"""Solo preparación de manifiesto H5, sin entidades ni anotación H6."""

import fcntl

from mtx.ambito_ie import cargar_ambito
from mtx.app.componentes import ErrorAnotacion, atomico
from mtx.app.gazetteer import congelado
from mtx.congelacion import verificar_congelacion
from mtx.muestreo import sortear_muestra


def preparar_muestra(raiz):
    """Acción explícita de la app; muestra inmutable, nunca sobrescribe otra."""
    if not congelado(raiz):
        raise ErrorAnotacion("Pendiente congelación D15 antes de sortear")
    if not (raiz / "config/protocolo.txt").exists():
        raise ErrorAnotacion("Falta config/protocolo.txt para el protocolo de sustitución")
    ranking, pasajes = cargar_ambito(raiz)
    muestra = sortear_muestra(ranking, pasajes)
    if len(muestra) != 20 or muestra.query_id.nunique() != 10:
        raise ErrorAnotacion("Se exigen diez consultas y veinte IDs únicos")
    destino = raiz / "anotaciones/muestra_gold.csv"
    contenido = muestra.to_csv(index=False, lineterminator="\n").encode()
    if destino.exists():
        if destino.read_bytes() != contenido:
            raise ErrorAnotacion(
                "Muestra existente incompatible: conservar y revisar con el alumno"
            )
        return muestra
    verificar_congelacion(raiz)
    destino.parent.mkdir(exist_ok=True)
    with (destino.parent / ".muestra.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if destino.exists():
            raise ErrorAnotacion("Otra sesión creó la muestra: recarga")
        atomico(destino, contenido)
    return muestra


def mostrar(raiz):
    """No lee ni muestra predicciones. Anotación y cierre se implementan en H6."""
    import streamlit as st

    st.info("Preparación H5. La anotación de entidades y cierre Gold corresponde a H6.")
    st.caption("El sorteo requiere H4, criterios aprobados, protocolo y reglas congeladas.")
    confirmar = st.checkbox("Confirmo que aún no he visto predicciones sobre los candidatos")
    if st.button("Preparar muestra ciega (20 IDs)", disabled=not confirmar):
        try:
            muestra = preparar_muestra(raiz)
            st.success(f"Manifiesto conservado: {len(muestra)} IDs, sin entidades precargadas.")
        except (OSError, ValueError) as exc:
            st.error(str(exc))
