"""Deterministic, typed plan → guard → act protocol for the local MVP."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Intent = Literal['bus', 'bill', 'scheme', 'compare']
Action = Literal['navigate', 'fill', 'click', 'handoff', 'compare']

class Goal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    goal: str = Field(min_length=1, max_length=300)
    intent: Intent | None = None

class Step(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    action: Action
    target: str
    narration: str
    value: str | None = None

# The model is never allowed to invent URLs, selectors or actions.
ROUTES = {'bus': '/demo/bus', 'bill': '/demo/bill', 'scheme': '/demo/scheme', 'compare': '/demo/bus'}
KEYWORDS = {
    'compare': ('compare', 'comparison', 'cheapest', 'तुलना', 'सस्ता', 'ಹೋಲಿಸಿ', 'ಅಗ್ಗ'),
    'bill': ('bill', 'electricity', 'power', 'बिल', 'बिजली', 'ಬಿಲ್', 'ವಿದ್ಯುತ್'),
    'scheme': ('scheme', 'government', 'scholarship', 'योजना', 'सरकारी', 'ಯೋಜನೆ', 'ಸರ್ಕಾರಿ'),
    'bus': ('bus', 'ticket', 'बस', 'टिकट', 'ಬಸ್', 'ಟಿಕೆಟ್'),
}


def classify(goal: str) -> Intent | None:
    g = goal.casefold()
    matches = [k for k, words in KEYWORDS.items() if any(w in g for w in words)]
    if 'compare' in matches and not any(x in matches for x in ('bill', 'scheme')):
        return 'compare'
    return matches[0] if len(matches) == 1 else None


def make_plan(intent: Intent) -> list[Step]:
    def step(action, target, narration, value=None):
        return Step(action=action, target=target, narration=narration, value=value)
    # Deliberately use fictional defaults, never infer personal information.
    plans = {
        'bus': [step('navigate', ROUTES['bus'], 'Opening the sample bus booking page.'),
                step('fill', 'from', 'Entering the sample origin: Bengaluru.', 'Bengaluru'),
                step('fill', 'to', 'Entering the sample destination: Mysuru.', 'Mysuru'),
                step('click', 'search-buses', 'Searching for sample buses.'),
                step('handoff', 'checkout', 'Search complete. Choose a bus yourself. Sahaj will not book or pay.')],
        'bill': [step('navigate', ROUTES['bill'], 'Opening the fictional electricity bill portal.'),
                 step('fill', 'consumer-id', 'Entering a fictional consumer number.', 'DEMO-1042'),
                 step('click', 'lookup-bill', 'Looking up the sample bill.'),
                 step('handoff', 'payment', 'Bill found. Payment requires your own action; no money will be transferred.')],
        'scheme': [step('navigate', ROUTES['scheme'], 'Opening the sample scheme portal.'),
                   step('fill', 'district', 'Entering a sample district: Bengaluru.', 'Bengaluru'),
                   step('click', 'check-scheme', 'Showing sample eligibility information.'),
                   step('handoff', 'application', 'Review the information yourself. Sahaj will not submit an application.')],
        'compare': [step('compare', 'bus-offers', 'Reading two fictional bus providers in parallel.'),
                    step('handoff', 'checkout', 'Comparison complete. Choose an option yourself.')],
    }
    return plans[intent]


def guard(intent: Intent, index: int, step: Step) -> bool:
    """Exact, position-specific allowlist. No arbitrary browser actions."""
    plan = make_plan(intent)
    return 0 <= index < len(plan) and step == plan[index]
