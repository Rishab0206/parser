import re
import os
import json
from typing import Optional, Dict, Any, List
from difflib import SequenceMatcher

# Indian State Codes for GST
GST_STATE_CODES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra & Nagar Haveli and Daman & Diu",
    "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh"
}

PAN_ENTITY_TYPES = {
    "P": "Sole Proprietorship / Individual",
    "C": "Company (Private / Public Limited)",
    "F": "Partnership Firm / LLP",
    "H": "Hindu Undivided Family (HUF)",
    "A": "Association of Persons (AOP)",
    "T": "Trust",
    "B": "Body of Individuals (BOI)",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government Agency"
}

CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def compute_gstin_checksum(gstin_14: str) -> str:
    """Computes the 15th Luhn Mod-36 checksum character for a 14-char GSTIN string."""
    try:
        factor = 1
        total = 0
        for char in gstin_14.upper():
            code_point = CHARS.index(char)
            addend = factor * code_point
            factor = 1 if factor == 2 else 2
            addend = (addend // 36) + (addend % 36)
            total += addend
        remainder = total % 36
        check_code = (36 - remainder) % 36
        return CHARS[check_code]
    except Exception:
        return "1"

def validate_gstin_checksum(gstin: str) -> bool:
    if len(gstin) != 15:
        return False
    expected = compute_gstin_checksum(gstin[:14])
    return gstin[14].upper() == expected

class GstPanService:

    @staticmethod
    def analyze_query(
        query: str,
        customer_name: Optional[str] = None,
        target_state: Optional[str] = None
    ) -> Dict[str, Any]:
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', query).strip().upper()
        
        is_pan = bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', cleaned))
        is_gstin = bool(re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', cleaned))

        if not is_pan and not is_gstin:
            return {
                "valid": False,
                "error": "Invalid format. Please enter a 10-digit PAN (e.g. ABCDE1234F) or a 15-digit GSTIN (e.g. 24ABCDE1234F1Z1)."
            }

        pan = cleaned if is_pan else cleaned[2:12]
        entity_code = pan[3] if len(pan) >= 4 else "P"
        entity_type = PAN_ENTITY_TYPES.get(entity_code, "Unknown Business Entity")
        name_initial = pan[4] if len(pan) >= 5 else ""

        gstins = []
        if is_gstin:
            state_code = cleaned[:2]
            state_name = GST_STATE_CODES.get(state_code, f"State {state_code}")
            is_valid_chk = validate_gstin_checksum(cleaned)
            gstins.append({
                "gstin": cleaned,
                "state_code": state_code,
                "state_name": state_name,
                "entity_number": cleaned[12],
                "checksum_valid": is_valid_chk,
                "status": "Verified GSTIN Format" if is_valid_chk else "Invalid Checksum",
                "source": "Direct GSTIN"
            })
        elif target_state and target_state in GST_STATE_CODES:
            # Only generate for the explicitly requested state
            base_14 = f"{target_state}{pan}1Z"
            chk = compute_gstin_checksum(base_14)
            full_gstin = f"{base_14}{chk}"
            gstins.append({
                "gstin": full_gstin,
                "state_code": target_state,
                "state_name": GST_STATE_CODES.get(target_state, f"State {target_state}"),
                "entity_number": "1",
                "checksum_valid": True,
                "status": "State GSTIN Format",
                "source": "Selected State"
            })

        # Underwriting Cross-Verification & Risk Assessment
        risk_flags = []
        risk_level = "LOW"
        match_score = 100

        # Don't penalize if placeholder name like 'Goods and Services Tax' is present
        is_generic_placeholder = customer_name and customer_name.strip().lower() in [
            "goods and services tax", "applicant", "new applicant", "customer"
        ]

        if customer_name and not is_generic_placeholder:
            customer_words = [w for w in re.split(r'\s+', customer_name.strip().upper()) if w]
            first_letters = [w[0] for w in customer_words if w]
            
            initial_match = name_initial in first_letters
            if not initial_match and first_letters:
                risk_flags.append(f"PAN 5th letter '{name_initial}' does not match customer name initials ({', '.join(first_letters)}).")
                match_score -= 25
                risk_level = "MEDIUM"

            # Check entity type mismatch
            is_claiming_company = any(k in customer_name.upper() for k in ["PVT", "LTD", "PRIVATE LIMITED", "LIMITED"])
            if is_claiming_company and entity_code != "C":
                risk_flags.append(f"Mismatch: Customer name contains 'Private Limited' but PAN 4th letter is '{entity_code}' ({entity_type}).")
                match_score -= 40
                risk_level = "HIGH"

            is_claiming_firm = any(k in customer_name.upper() for k in ["LLP", "PARTNERS", "ENTERPRISES", "ASSOCIATES"])
            if is_claiming_firm and entity_code not in ["F", "C"]:
                risk_flags.append(f"Notice: Trading firm name used with an Individual/Proprietorship PAN ('{entity_code}'). Sole Proprietorship status confirmed.")
                match_score -= 10

        if not risk_flags:
            risk_flags.append("PAN structure and entity classification verified.")

        underwriting_recommendation = (
            "Verified Sole Proprietorship / Individual entity. Acceptable for Unsecured Business Loans / MSME lending."
            if entity_code == "P" else
            "Corporate entity detected. Board resolution & MOA/AOA required for corporate loan processing."
            if entity_code == "C" else
            "Partnership / LLP entity detected. Partnership deed and partner KYC required."
            if entity_code == "F" else
            f"Entity Type: {entity_type}. Standard KYC verification applicable."
        )

        return {
            "valid": True,
            "input_type": "GSTIN" if is_gstin else "PAN",
            "input_value": cleaned,
            "pan": pan,
            "entity_code": entity_code,
            "entity_type": entity_type,
            "name_initial": name_initial,
            "gstins": gstins,
            "all_states": GST_STATE_CODES,
            "gov_search_url": "https://services.gst.gov.in/services/searchtpbypan",
            "matching": {
                "customer_name": "Applicant" if is_generic_placeholder else (customer_name or "Applicant"),
                "match_score": max(match_score, 20),
                "risk_level": risk_level,
                "observations": risk_flags,
                "underwriting_recommendation": underwriting_recommendation
            }
        }
