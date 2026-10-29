import hashlib

import rfc8785

# keys are ISINs (International Securities Identification Number).
# kid_date: date of the Key Information Document (KID) the customer is shown.
FUNDS = {
    "DE000DEMO015": {
        "name": "Global Equity Fund",
        "objective": "Long-term growth through shares worldwide.",
        "risk_class": 4,
        "ongoing_costs_percent": 1.2,
        "kid_date": "2026-09-30",
    },
    "DE000DEMO023": {
        "name": "Euro Bond Fund",
        "objective": "Stable income from bonds in euro.",
        "risk_class": 2,
        "ongoing_costs_percent": 0.6,
        "kid_date": "2026-09-30",
    },
}
TERMS_VERSION = "2026-10"

REQUIREMENTS = [
    "German ID card or residence permit with the online ID function on, and its 6-digit PIN",
    "A smartphone with the AusweisApp, also used to confirm the application",
    "Residence in Germany and age 18 or older",
    "An IBAN of the customer's own current account for the monthly payments",
]

PARTNER_BANKS = {
    "SPK-KOELNBONN": "Sparkasse KölnBonn",
    "SPK-MUENCHEN": "Stadtsparkasse München",
}

# application_id and hausbank make the hash unique to this customer's application.
def build_offer(application_id, fund_isin, monthly_amount, offer_version):
    fund = FUNDS[fund_isin]
    return {
        "application_id": application_id,
        "hausbank": "",
        "offer_version": offer_version,
        "fund_isin": fund_isin,
        "fund_name": fund["name"],
        "monthly_amount_eur": monthly_amount,
        "ongoing_costs_percent": fund["ongoing_costs_percent"],
        "kid_date": fund["kid_date"],
        "terms_version": TERMS_VERSION,
    }

# RFC 8785 turns the offer into canonical JSON (sorted keys, fixed number format)
def offer_hash(offer):
    return hashlib.sha256(rfc8785.dumps(offer)).hexdigest()


def estimate_costs(fund_isin, monthly_amount):
    yearly = monthly_amount * 12
    costs = yearly * FUNDS[fund_isin]["ongoing_costs_percent"] / 100
    return {"paid_in_per_year_eur": yearly, "costs_per_year_eur": round(costs, 2)}
