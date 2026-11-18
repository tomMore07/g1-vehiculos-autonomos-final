"""Genera con Graphviz las figuras del PDF: uml_clases, dfd_nivel0 y dfd_nivel1 (python3 gen_diagramas.py).
Las versiones Mermaid (fuente para GitHub) están en 02_arquitectura_uml.md."""
import html, subprocess

def esc(t): return html.escape(t, quote=False)
FONT = "DejaVu Sans"

# ------------------------------------------------------------------ UML de clases
def cls(name, stereo, attrs, ops, fill):
    def wrap(i, w=44):
        out, cur = [], ""
        for tok in i.replace(", ", ",\x00").split("\x00"):
            if cur and len(cur) + len(tok) > w: out.append(cur); cur = "    " + tok
            else: cur += tok
        out.append(cur); return out
    rows = lambda items: "".join('<TR><TD ALIGN="LEFT" BALIGN="LEFT">' + '<BR ALIGN="LEFT"/>'.join(
        esc(l).replace("    ", "&nbsp;&nbsp;&nbsp;&nbsp;") for l in wrap(i)) + '</TD></TR>' for i in items) or '<TR><TD> </TD></TR>'
    st = f'<TR><TD><FONT POINT-SIZE="9">«{stereo}»</FONT></TD></TR>' if stereo else ""
    ital = f"<I>{esc(name)}</I>" if stereo in ("abstract", "interface") else f"<B>{esc(name)}</B>"
    return (f'{name} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" BGCOLOR="{fill}">'
            f'{st}<TR><TD>{ital}</TD></TR><HR/>{rows(attrs)}<HR/>{rows(ops)}</TABLE>>];\n')

D, R, A, P, M = "#EEEDFE", "#FAECE7", "#E1F5EE", "#FAEEDA", "#F1EFE8"
nodes = [
 cls("MotorDecision", "", ["-estrategia: EstrategiaEvaluacionRiesgo", "-actuador: ActuadorFrenado", "-historial: List<EventoTelemetria>"],
     ["+MotorDecision(e: EstrategiaEvaluacionRiesgo, a: ActuadorFrenado)", "+evaluarYActuar(obs: Obstaculo): NivelRiesgo",
      "+procesarPercepcion(p: ProveedorPercepcion): Optional<NivelRiesgo>", "+setEstrategia(e: EstrategiaEvaluacionRiesgo): void",
      "+getHistorial(): List<EventoTelemetria>", "-frenar(presion: double, tipo: String): String"], D),
 cls("EstrategiaEvaluacionRiesgo", "interface", [], ["+evaluar(obs: Obstaculo): NivelRiesgo"], A),
 cls("RiesgoPorDistancia", "", ["-umbralCriticoM: double", "-umbralAltoM: double"], ["+evaluar(obs: Obstaculo): NivelRiesgo"], A),
 cls("RiesgoPorTiempoColision", "", ["-ttcCriticoS: double", "-ttcAltoS: double"], ["+evaluar(obs: Obstaculo): NivelRiesgo"], A),
 cls("ActuadorFrenado", "abstract", ["-bitacora: List<String>"],
     ["+ejecutarSecuenciaFrenado(presion: double): boolean {final}", "#verificarSistema(): boolean {abstract}", "#aplicarPresion(presion: double): void {abstract}",
      "#registrarEvento(msg: String): void", "+getBitacora(): List<String>"], R),
 cls("FrenoHidraulico", "", ["-nivelLiquido: double", "-presionLineaBar: double"], ["#verificarSistema(): boolean", "#aplicarPresion(presion: double): void"], R),
 cls("FrenoRegenerativo", "", ["-cargaBateria: double", "-torqueNm: double"], ["#verificarSistema(): boolean", "#aplicarPresion(presion: double): void"], R),
 cls("ProveedorPercepcion", "interface", [], ["+obstaculoMasCercano(): Optional<Obstaculo>", "+anomaliasRecientes(): List<Anomalia>"], P),
 cls("AdaptadorKernelCpp", "", ["-raiz: Path", "-nPuntos: int", "-velocidadVehiculoMs: double", "-limiteAnomalias: int"],
     ["+obstaculoMasCercano(): Optional<Obstaculo>", "+anomaliasRecientes(): List<Anomalia>", "+leerCampo(json: String, clave: String): double {static}", "-ejecutar(cmd: List<String>, dir: Path): List<String>"], P),
 cls("Obstaculo", "record", ["+distanciaM: double", "+velocidadRelativaMs: double"], [], M),
 cls("EventoTelemetria", "record", ["+nivel: NivelRiesgo", "+descripcion: String"], [], M),
 cls("Anomalia", "record", ["+t: long", "+valor: double", "+zscore: double"], [], M),
 cls("NivelRiesgo", "enumeration", ["BAJO", "MEDIO", "ALTO", "CRITICO"], [], M),
]
E = []
def real(a, b): E.append(f'{b} -> {a} [dir=back, arrowtail=empty, style=dashed];')
def gen(a, b):  E.append(f'{b} -> {a} [dir=back, arrowtail=empty];')
def dep(a, b):  E.append(f'{a} -> {b} [arrowhead=vee, style=dashed];')
def agg(a, b, l): E.append(f'{a} -> {b} [dir=both, arrowtail=odiamond, arrowhead=none, xlabel="{l}", fontsize=9];')
def comp(a, b, l): E.append(f'{a} -> {b} [dir=both, arrowtail=diamond, arrowhead=none, xlabel="{l} 0..*", fontsize=9];')
real("RiesgoPorDistancia", "EstrategiaEvaluacionRiesgo"); real("RiesgoPorTiempoColision", "EstrategiaEvaluacionRiesgo")
real("AdaptadorKernelCpp", "ProveedorPercepcion"); gen("FrenoHidraulico", "ActuadorFrenado"); gen("FrenoRegenerativo", "ActuadorFrenado")
agg("MotorDecision", "EstrategiaEvaluacionRiesgo", "estrategia"); agg("MotorDecision", "ActuadorFrenado", "actuador")
comp("MotorDecision", "EventoTelemetria", "historial")
dep("MotorDecision", "ProveedorPercepcion"); dep("EstrategiaEvaluacionRiesgo", "Obstaculo")
dep("ProveedorPercepcion", "Obstaculo"); dep("ProveedorPercepcion", "Anomalia")
E.append("EventoTelemetria -> NivelRiesgo [arrowhead=vee];")
uml = ('digraph UML { rankdir=TB; nodesep=0.3; ranksep=0.6; splines=ortho; '
       f'node [shape=plain, fontname="{FONT}", fontsize=10]; edge [fontname="{FONT}"];\n' + "".join(nodes) + "\n".join(E) + "\n}")
open("uml_clases.dot", "w", encoding="utf-8").write(uml)

# ------------------------------------------------------------------ DFD (Yourdon–DeMarco)
HEAD = (f'rankdir=LR; nodesep=0.55; ranksep=0.9; fontname="{FONT}"; '
        f'edge [fontname="{FONT}", fontsize=9, arrowhead=normal]; ')
ENT = f'shape=box, style=filled, fillcolor="#F1EFE8", fontname="{FONT}", fontsize=10, penwidth=1.6'
PRO = f'shape=circle, style=filled, fontname="{FONT}", fontsize=9, penwidth=1.2, margin=0.05'
def store(id_, label):  # almacén de datos: rectángulo abierto por un lado (líneas paralelas)
    return (f'{id_} [shape=plain, label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">'
            f'<TR><TD SIDES="TB" BORDER="1" CELLPADDING="6" BGCOLOR="#FAEEDA"><B>{id_}</B> │ {esc(label)}</TD></TR></TABLE>>];\n')

dfd0 = f'digraph DFD0 {{ {HEAD}\nnode [{ENT}];\n' + '''
E1 [label="E1\\nSensor LIDAR"]; E2 [label="E2\\nSensor de telemetría"];
E3 [label="E3\\nSistema de frenos"]; E4 [label="E4\\nOperador / auditoría"];
P0 [shape=circle, style=filled, fillcolor="#EEEDFE", fontsize=10, penwidth=1.4, width=2.0, fixedsize=true, label="0\\nSistema de detección\\ny frenado de\\nemergencia"];
E1 -> P0 [label="nube de puntos"]; E2 -> P0 [label="lecturas de telemetría"];
P0 -> E3 [label="orden de frenado (presión 0..1)"]; P0 -> E4 [label="historial de eventos (instantánea)"];
}'''
dfd1 = f'digraph DFD1 {{ {HEAD.replace("rankdir=LR", "rankdir=TB").replace("ranksep=0.9", "ranksep=0.75")}\nnode [{ENT}];\n{{rank=same; E1; E2}} {{rank=same; E3; D2; D1}}\n' + '''
E1 [label="E1\\nSensor LIDAR"]; E2 [label="E2\\nSensor de telemetría"];
E3 [label="E3\\nSistema de frenos"]; E4 [label="E4\\nOperador / auditoría"];
P1 [shape=circle, style=filled, fillcolor="#FAECE7", fontsize=9, width=1.55, fixedsize=true, label="1.0\\nFiltrar nube LIDAR\\n[C++ / OpenMP]"];
P2 [shape=circle, style=filled, fillcolor="#E1F5EE", fontsize=9, width=1.55, fixedsize=true, label="2.0\\nDetectar anomalías\\n[Python funcional]"];
P3 [shape=circle, style=filled, fillcolor="#EEEDFE", fontsize=9, width=1.55, fixedsize=true, label="3.0\\nEvaluar riesgo\\n[Java · Strategy]"];
P4 [shape=circle, style=filled, fillcolor="#EEEDFE", fontsize=9, width=1.55, fixedsize=true, label="4.0\\nEjecutar frenado\\n[Java · Template\\nMethod]"];
''' + store("D1", "Historial de eventos") + store("D2", "Bitácora del actuador") + '''
E1 -> P1 [label="nube de puntos\\n(x, y, z, intensidad)"];
E2 -> P2 [label="lecturas de telemetría"];
P1 -> P3 [label="obstáculo más cercano\\n(JSON)"];
P2 -> P3 [label="anomalías (JSON)"];
P3 -> P4 [label="nivel de riesgo\\n(CRÍTICO / ALTO)"];
P4 -> E3 [label="orden de frenado\\n(presión 0..1)"];
P3 -> D1 [label="evento de riesgo\\ny anomalías"];
P4 -> D2 [label="pasos de la\\nsecuencia"];
D1 -> E4 [label="historial\\n(instantánea inmutable)"];
D2 -> E4 [label="bitácora\\n(instantánea inmutable)"];
}'''
open("dfd_nivel0.dot", "w", encoding="utf-8").write(dfd0)
open("dfd_nivel1.dot", "w", encoding="utf-8").write(dfd1)
for n in ("uml_clases", "dfd_nivel0", "dfd_nivel1"):
    subprocess.run(["dot", "-Tsvg", f"{n}.dot", "-o", f"{n}.svg"], check=True)
    subprocess.run(["dot", "-Tpng", "-Gdpi=150", f"{n}.dot", "-o", f"{n}.png"], check=True)
print("ok")
