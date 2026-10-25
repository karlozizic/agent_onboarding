import hashlib
import rfc8785

#kid_date: date of the Key Information Document (KID) the customer is shown.
FUNDS = {
    "HRRBAGEQ0000": {"name": "RBA Global Equity Fund", "ongoing_costs_percent": 1.2, "kid_date": "2026-09-30"},
    "HRERSTEB0009": {"name": "Erste Euro Bond Fund", "ongoing_costs_percent": 0.6, "kid_date": "2026-09-30"},
}
TERMS_VERSION = "2026-10"

PARTNER_BANKS = {
    "SPK-KOELNBONN": "Sparkasse KölnBonn",
    "SPK-MUENCHEN": "Stadtsparkasse München",
}

#ISIN - International Securities Identification Number
def build_offer(fund_isin, monthly_amount, offer_version):
    fund = FUNDS[fund_isin]
    return {
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