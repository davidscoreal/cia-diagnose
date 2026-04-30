"""Objection handling with A.A.A. technique (Doc03).

A.A.A. = Acknowledge → Ask → Answer
  1. Acknowledge the concern (validate, don't dismiss)
  2. Ask a clarifying question (dig into the real issue)
  3. Answer with proof/framework (resolve with data)

9 common objections from Doc03 + per-ICP unique objections from icps.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Objection:
    """A single objection with A.A.A. response."""
    id: str
    trigger_phrases: list[str]  # phrases that trigger this objection

    # The objection itself
    objection_es: str
    objection_en: str

    # A.A.A. response
    acknowledge_es: str
    acknowledge_en: str
    ask_es: str
    ask_en: str
    answer_es: str
    answer_en: str


# ═══════════════════════════════════════════════════════════
# 9 Universal Objections (Doc03)
# ═══════════════════════════════════════════════════════════

OBJECTIONS: list[Objection] = [
    Objection(
        id="too_expensive",
        trigger_phrases=["caro", "expensive", "presupuesto", "budget", "no tenemos plata", "costly"],
        objection_es="Es muy caro / No tenemos presupuesto",
        objection_en="It's too expensive / We don't have budget",
        acknowledge_es="Entiendo. El presupuesto siempre es una preocupación real.",
        acknowledge_en="I understand. Budget is always a real concern.",
        ask_es="¿Cuánto te está costando el problema ahora mismo cada mes? ¿Lo has medido?",
        ask_en="How much is the problem costing you right now each month? Have you measured it?",
        answer_es="La auditoría cuesta $2-5K. Si procedes en 30 días, se acredita 100%. Pero el costo de NO actuar — las cotizaciones perdidas, los no-shows, las horas manuales — ese sí se paga cada mes.",
        answer_en="The audit costs $2-5K. If you proceed within 30 days, it's credited 100%. But the cost of NOT acting — lost quotes, no-shows, manual hours — you're paying that every month.",
    ),

    Objection(
        id="not_ready",
        trigger_phrases=["no estamos listos", "not ready", "no es el momento", "not the right time", "después"],
        objection_es="No estamos listos / No es el momento",
        objection_en="We're not ready / It's not the right time",
        acknowledge_es="Lo respeto. Hay momentos para cada cosa.",
        acknowledge_en="I respect that. There's a time for everything.",
        ask_es="¿Qué tendría que pasar para que sea el momento correcto?",
        ask_en="What would need to happen for it to be the right time?",
        answer_es="El audit es precisamente para los que no están listos — mapea dónde estás y qué necesitas. No implementamos nada que no quieras. Y recuerda: no todo es IA. Empezamos con lo simple.",
        answer_en="The audit is precisely for those who aren't ready — it maps where you are and what you need. We don't implement anything you don't want. And remember: not everything is AI. We start simple.",
    ),

    Objection(
        id="tried_before",
        trigger_phrases=["ya probamos", "tried before", "consultores", "consultants", "no funcionó", "didn't work"],
        objection_es="Ya probamos con consultores y no funcionó",
        objection_en="We already tried consultants and it didn't work",
        acknowledge_es="Frustrante. Dinero gastado sin resultados es lo peor.",
        acknowledge_en="Frustrating. Money spent without results is the worst.",
        ask_es="¿Qué entregaron exactamente? ¿PowerPoints o sistemas funcionando?",
        ask_en="What did they deliver exactly? PowerPoints or running systems?",
        answer_es="CIA no entrega PPTs. Entregamos sistemas corriendo. La diferencia: si no funciona, no pagas el siguiente milestone. Y te mostramos 3 opciones por cada recomendación — paga, open source, y CIA — para que tú decidas.",
        answer_en="CIA doesn't deliver PPTs. We deliver running systems. The difference: if it doesn't work, you don't pay the next milestone. And we show you 3 options per recommendation — paid, open source, and CIA — so you decide.",
    ),

    Objection(
        id="do_it_ourselves",
        trigger_phrases=["lo hacemos nosotros", "do it ourselves", "interno", "in-house", "tenemos equipo"],
        objection_es="Lo hacemos internamente / Tenemos equipo",
        objection_en="We'll do it in-house / We have a team",
        acknowledge_es="Tener equipo propio es una ventaja enorme.",
        acknowledge_en="Having your own team is a huge advantage.",
        ask_es="¿Cuánto tiempo lleva tu equipo evaluando herramientas sin implementar?",
        ask_en="How long has your team been evaluating tools without implementing?",
        answer_es="El audit no reemplaza a tu equipo — lo acelera. En 2 semanas les damos el mapa que les tomaría 6 meses construir solos. Y las opciones open source que recomendamos las puede implementar tu equipo directamente.",
        answer_en="The audit doesn't replace your team — it accelerates them. In 2 weeks we give them the map that would take 6 months to build alone. And the open source options we recommend can be implemented by your team directly.",
    ),

    Objection(
        id="too_small",
        trigger_phrases=["somos muy pequeños", "too small", "pequeña empresa", "small business", "no aplica"],
        objection_es="Somos muy pequeños para esto",
        objection_en="We're too small for this",
        acknowledge_es="Entiendo la percepción. Automatización suena a grandes empresas.",
        acknowledge_en="I understand the perception. Automation sounds like big company stuff.",
        ask_es="¿Cuántas horas a la semana pierdes en tareas repetitivas que podrían ser automáticas?",
        ask_en="How many hours a week do you lose on repetitive tasks that could be automatic?",
        answer_es="De hecho, las empresas pequeñas son las que más ganan. Un freelancer que ahorra 10 horas/semana ganó un empleado. Te mostramos herramientas open source gratuitas que puedes usar hoy mismo.",
        answer_en="Actually, small companies gain the most. A freelancer who saves 10 hours/week gained an employee. We show you free open source tools you can start using today.",
    ),

    Objection(
        id="ai_hype",
        trigger_phrases=["IA es hype", "AI hype", "moda", "trend", "burbuja", "bubble", "chatgpt"],
        objection_es="IA es puro hype / No creo en IA",
        objection_en="AI is just hype / I don't believe in AI",
        acknowledge_es="Hay mucho ruido, es verdad. El 90% de lo que ves en LinkedIn es marketing vacío.",
        acknowledge_en="There's a lot of noise, that's true. 90% of what you see on LinkedIn is empty marketing.",
        ask_es="¿Qué parte de tu operación es más manual y te gustaría que fuera automática — sin importar si usa IA o no?",
        ask_en="What part of your operation is most manual and you'd want automated — regardless of whether it uses AI or not?",
        answer_es="No se trata de IA. Se trata de automatizar lo que ya funciona. 70% de lo que recomendamos no usa IA — son workflows, integraciones, y procesos. La IA entra solo donde agrega valor real.",
        answer_en="It's not about AI. It's about automating what already works. 70% of what we recommend doesn't use AI — it's workflows, integrations, and processes. AI comes in only where it adds real value.",
    ),

    Objection(
        id="data_security",
        trigger_phrases=["datos", "data", "seguridad", "security", "privacidad", "privacy", "sensible", "sensitive"],
        objection_es="Me preocupa la seguridad de mis datos",
        objection_en="I'm worried about data security",
        acknowledge_es="Es una preocupación legítima y la tomamos muy en serio.",
        acknowledge_en="That's a legitimate concern and we take it very seriously.",
        ask_es="¿Qué tipo de datos manejas que consideras más sensibles?",
        ask_en="What type of data do you handle that you consider most sensitive?",
        answer_es="CIA no almacena datos de tu empresa. Las herramientas que recomendamos corren en tu infraestructura. Y las opciones open source las puedes auditar tú mismo — el código es público.",
        answer_en="CIA doesn't store your company data. The tools we recommend run on your infrastructure. And the open source options you can audit yourself — the code is public.",
    ),

    Objection(
        id="team_resistance",
        trigger_phrases=["equipo no va a usar", "team won't use", "resistencia", "resistance", "change management", "adopción"],
        objection_es="Mi equipo no va a adoptar nuevas herramientas",
        objection_en="My team won't adopt new tools",
        acknowledge_es="La resistencia al cambio es el killer silencioso de proyectos de tecnología.",
        acknowledge_en="Change resistance is the silent killer of tech projects.",
        ask_es="¿Qué herramientas ya usa tu equipo voluntariamente? ¿WhatsApp? ¿Email?",
        ask_en="What tools does your team already use voluntarily? WhatsApp? Email?",
        answer_es="No les pedimos que aprendan software nuevo. Automatizamos alrededor de lo que ya usan. Si tu equipo usa WhatsApp, captamos info desde WhatsApp. Ellos siguen igual, tú ves todo.",
        answer_en="We don't ask them to learn new software. We automate around what they already use. If your team uses WhatsApp, we capture info from WhatsApp. They continue as usual, you see everything.",
    ),

    Objection(
        id="need_to_think",
        trigger_phrases=["déjame pensarlo", "let me think", "lo consulto", "consultarlo", "hablarlo", "talk it over"],
        objection_es="Déjame pensarlo / Lo consulto con mi socio",
        objection_en="Let me think about it / I'll talk to my partner",
        acknowledge_es="Por supuesto. Decisiones así no se toman a la ligera.",
        acknowledge_en="Of course. Decisions like this shouldn't be taken lightly.",
        ask_es="¿Qué información necesitas para tomar la decisión? Te la puedo preparar.",
        ask_en="What information do you need to make the decision? I can prepare it for you.",
        answer_es="Te envío el reporte completo con tu Revenue Leak Score, las recomendaciones con 3 opciones cada una, y el estimado de ROI. Así tienes todo para la conversación con tu socio. ¿Te parece si agendamos una llamada corta de 15 min la próxima semana?",
        answer_en="I'll send you the complete report with your Revenue Leak Score, recommendations with 3 options each, and the ROI estimate. That way you have everything for the conversation with your partner. Shall we schedule a short 15-min call next week?",
    ),
]

# ─── Registry ────────────────────────────────────────────

OBJECTIONS_BY_ID: dict[str, Objection] = {o.id: o for o in OBJECTIONS}


def detect_objection(text: str) -> Objection | None:
    """Detect objection from free text using trigger phrases.

    Returns the first matching objection, or None.
    """
    if not text:
        return None

    text_lower = text.lower().strip()

    for objection in OBJECTIONS:
        for phrase in objection.trigger_phrases:
            if phrase in text_lower:
                return objection

    return None


def format_aaa_response(objection: Objection, lang: str = "es") -> str:
    """Format the A.A.A. response as a natural conversation flow."""
    if lang == "es":
        return (
            f"{objection.acknowledge_es}\n\n"
            f"Pregunta: {objection.ask_es}\n\n"
            f"{objection.answer_es}"
        )
    return (
        f"{objection.acknowledge_en}\n\n"
        f"Question: {objection.ask_en}\n\n"
        f"{objection.answer_en}"
    )
