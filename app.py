
import streamlit as st

from src.agent import (
    procesar_turno,
    aprobar_plan,
    nuevo_thread_id,
    historial_checkpoints,
)
from src.state import crear_estado
from src import config_grafo

st.set_page_config(page_title="Asistente PcComponentes", page_icon="🖥️")


# --------------------------------------------------
# ESTADO Y UTILIDADES
# --------------------------------------------------

def nueva_conversacion():
    """Chat vacío, estado de producto nuevo y nuevo thread_id (nuevo hilo en el MemorySaver)."""
    st.session_state.thread_id = nuevo_thread_id()
    st.session_state.estado = crear_estado("")
    st.session_state.messages = []
    st.session_state.debug_error = None


if "thread_id" not in st.session_state:
    nueva_conversacion()


def registrar_respuesta(estado_actual):
    """Añade al chat la respuesta más reciente del estado de producto."""
    respuesta = estado_actual.get("respuesta", "")

    if respuesta:
        st.session_state.messages.append({
            "role": "assistant",
            "content": respuesta,
        })


def mostrar_debug():
    """Muestra información de la ejecución sin invocar herramientas."""
    estado_actual = st.session_state.estado
    thread_id = st.session_state.thread_id

    with st.expander("🛠️ Depuración del agente", expanded=False):
        st.markdown("**Thread ID**")
        st.code(thread_id)

        st.markdown("**Estado HITL y finalización**")
        st.json({
            "pendiente_hitl": estado_actual.get("pendiente_hitl", False),
            "done": estado_actual.get("done", False),
            "error": estado_actual.get("error"),
        })

        st.markdown("**Log del grafo**")
        log = estado_actual.get("log", [])
        if log:
            st.code("\n".join(map(str, log)))
        else:
            st.caption("Todavía no hay entradas en el log.")

        st.markdown("**Traza de herramientas**")
        traza_tools = estado_actual.get("traza_tools", [])
        if traza_tools:
            st.json(traza_tools)
        else:
            st.caption("Todavía no hay llamadas registradas.")

        st.markdown("**Traza de turnos**")
        traza = estado_actual.get("traza", [])
        if traza:
            st.json(traza)
        else:
            st.caption("Todavía no hay turnos registrados.")

        st.markdown("**Historial de checkpoints**")
        try:
            checkpoints = historial_checkpoints(thread_id, limite=20)
            if checkpoints:
                st.json(checkpoints)
            else:
                st.caption("No hay checkpoints disponibles.")
        except Exception as exc:
            st.warning(f"No se pudo consultar el historial: {exc}")

        st.markdown("**Plan actual**")
        plan = estado_actual.get("plan", [])
        if plan:
            for item in plan:
                st.markdown(f"- {item}")
        else:
            st.caption("No hay un plan pendiente en el estado.")

        st.markdown("**Preferencias detectadas**")
        st.json(estado_actual.get("preferencias", {}))


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.title("⚙️ Configuración")

    max_steps = st.slider(
        "Máximo de pasos LLM ↔ tools por especialista",
        min_value=1,
        max_value=10,
        value=config_grafo.MAX_STEPS_DEFAULT,
    )

    max_turns = st.slider(
        "Máximo de mensajes por conversación",
        min_value=1,
        max_value=12,
        value=config_grafo.MAX_TURNS_DEFAULT,
    )

    st.caption(f"Modelo del agente: `{config_grafo.GEMINI_MODEL}`")

    st.divider()

    st.markdown("### 💬 Conversación")
    st.caption(f"Thread: {st.session_state.thread_id}")

    if st.button("🆕 Nueva conversación", use_container_width=True):
        nueva_conversacion()
        st.rerun()

    st.divider()

    # Los botones HITL solo aparecen si existe una pausa real.
    if st.session_state.estado.get("pendiente_hitl", False):
        st.warning("Hay un plan pendiente de decisión humana.")

        st.markdown("**Plan que se va a revisar**")
        for item in st.session_state.estado.get("plan", []):
            st.markdown(f"- {item}")

        if st.button(
            "✅ Aprobar plan",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner("Reanudando el grafo..."):
                    estado_nuevo = aprobar_plan(
                        st.session_state.thread_id,
                        True,
                        st.session_state.estado,
                    )

                st.session_state.estado = estado_nuevo
                st.session_state.debug_error = estado_nuevo.get("error")
                registrar_respuesta(estado_nuevo)
                st.rerun()

            except Exception as exc:
                st.error(f"No se pudo aprobar el plan: {exc}")

        comentario_rechazo = st.text_area(
            "Motivo del rechazo (opcional)",
            key="comentario_rechazo",
            placeholder="Ej.: supera el presupuesto o quiero otra gráfica.",
        )

        if st.button("❌ Rechazar plan", use_container_width=True):
            try:
                estado_nuevo = aprobar_plan(
                    st.session_state.thread_id,
                    False,
                    st.session_state.estado,
                    comentario=comentario_rechazo,
                )

                st.session_state.estado = estado_nuevo
                st.session_state.debug_error = estado_nuevo.get("error")
                registrar_respuesta(estado_nuevo)
                st.rerun()

            except Exception as exc:
                st.error(f"No se pudo rechazar el plan: {exc}")

    elif st.session_state.estado.get("done", False):
        st.success("El plan ha sido aprobado y la ejecución ha terminado.")

    st.divider()
    st.markdown("**Asistente PcComponentes**")
    st.caption("Project Break 2 · The Bridge")


# --------------------------------------------------
# CHAT
# --------------------------------------------------

st.title("🖥️ Asistente PcComponentes")
st.caption(
    "Asistente multiagente para componentes, compatibilidad "
    "y requisitos de videojuegos."
)

# Historial visible.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# No aceptar nuevos mensajes mientras el grafo espera HITL
# ni cuando el plan aprobado ya ha cerrado la conversación.
bloqueado = (
    st.session_state.estado.get("pendiente_hitl", False)
    or st.session_state.estado.get("done", False)
)

question = st.chat_input(
    "Pregunta sobre componentes, presupuesto o videojuegos...",
    disabled=bloqueado,
)

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    with st.chat_message("user"):
        st.markdown(question)

    # Mismo contrato que la CLI: un mensaje → un turno del grafo (puede acabar en pausa HITL).
    with st.spinner("Grafo multiagente (supervisor + especialistas + tools)..."):
        estado_nuevo = procesar_turno(
            st.session_state.estado,
            question,
            st.session_state.thread_id,
            max_steps=max_steps,
            max_turns=max_turns,
        )

    st.session_state.estado = estado_nuevo
    st.session_state.debug_error = estado_nuevo.get("error")
    registrar_respuesta(estado_nuevo)
    # La sidebar ya se dibujó: rerun para mostrar Aprobar / Rechazar si hay pausa.
    st.rerun()

if st.session_state.debug_error:
    st.error(st.session_state.debug_error)

mostrar_debug()
