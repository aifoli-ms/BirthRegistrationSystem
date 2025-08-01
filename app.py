from flask import Flask, request
import datetime
import random
import re
import logging

# --- Logging Configuration ---
# Sets up basic logging to the console.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# --- Dummy Database & Data Structures (Replace with real DB and APIs) ---

# A simple dictionary to act as our in-memory database.
registrations_db = {}

# Data structure for Ghana's regions and districts with their codes.
REGIONS_DISTRICTS = {
    "1": {
        "name": "Greater Accra", "code": "01",
        "districts": [
            {"name": "Accra Metropolis", "code": "027"},
            {"name": "Tema Metropolis", "code": "001"},
            {"name": "Ga East Municipal", "code": "024"},
        ]
    },
    "2": {
        "name": "Ashanti", "code": "02",
        "districts": [
            {"name": "Kumasi Metropolis", "code": "101"},
            {"name": "Obuasi Municipal", "code": "102"},
            {"name": "Asante Akim Central", "code": "105"},
        ]
    },
    "3": {"name": "Western", "code": "03", "districts": [{"name": "Sekondi-Takoradi Metropolis", "code": "211"}, {"name": "Tarkwa-Nsuaem Municipal", "code": "203"},]},
    "4": {"name": "Central", "code": "04", "districts": [{"name": "Cape Coast Metropolis", "code": "301"}]},
    "5": {"name": "Eastern", "code": "05", "districts": [{"name": "New Juaben South", "code": "401"}]},
    "6": {"name": "Volta", "code": "06", "districts": [{"name": "Ho Municipal", "code": "501"}]},
    "7": {"name": "Northern", "code": "07", "districts": [{"name": "Tamale Metropolis", "code": "601"}]},
    "8": {"name": "Upper East", "code": "08", "districts": [{"name": "Bolgatanga Municipal", "code": "701"}]},
    "9": {"name": "Upper West", "code": "09", "districts": [{"name": "Wa Municipal", "code": "801"}]},
    "10": {"name": "Bono", "code": "10", "districts": [{"name": "Sunyani Municipal", "code": "901"}]},
    "11": {"name": "Bono East", "code": "11", "districts": [{"name": "Techiman Municipal", "code": "911"}]},
    "12": {"name": "Ahafo", "code": "12", "districts": [{"name": "Asunafo North", "code": "921"}]},
    "13": {"name": "Western North", "code": "13", "districts": [{"name": "Sefwi Wiawso", "code": "231"}]},
    "14": {"name": "Oti", "code": "14", "districts": [{"name": "Krachi East", "code": "521"}]},
    "15": {"name": "North East", "code": "15", "districts": [{"name": "East Mamprusi", "code": "621"}]},
    "16": {"name": "Savannah", "code": "16", "districts": [{"name": "West Gonja", "code": "631"}]},
}


# --- Input Validation Functions ---

def validate_name(name):
    if name == '0': return True
    if not name: return False
    clean_name = name.strip()
    if not (2 <= len(clean_name) <= 50): return False
    return bool(re.match(r"^[a-zA-Z\s'-]+$", clean_name))

def validate_date_of_birth(dob):
    if not dob or len(dob) != 8 or not dob.isdigit(): return False
    try:
        day, month, year = int(dob[:2]), int(dob[2:4]), int(dob[4:])
        current_year = datetime.datetime.now().year
        if not (1 <= day <= 31 and 1 <= month <= 12 and (current_year - 10) <= year <= current_year): return False
        datetime.datetime(year, month, day)
        return True
    except (ValueError, TypeError): return False

def validate_sex_selection(sex_input):
    return sex_input in ['1', '2']

def validate_nin(nin):
    if not nin: return False
    return bool(re.match(r'^GHA-\d{9}-[\dA-Z]$', nin.upper()))

def validate_optional_nin(nin):
    if nin == '0': return True
    return validate_nin(nin)

def validate_ubrn(ubrn):
    if not ubrn: return False
    return bool(re.match(r'^GHA-\d{2}-\d{3}-\d{5}-\d{4}-[\dX]$', ubrn.upper()))


# --- UBRN Generation & DB Functions ---

def get_next_sequence_for_district_day(region_code, district_code, julian_day):
    return random.randint(1, 99)

def calculate_check_digit(number_string):
    digits = [int(d) for d in number_string if d.isdigit()]
    if not digits: return '0'
    weights = [7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    s = sum(digit * weights[i] for i, digit in enumerate(digits))
    remainder = s % 11
    check_digit = (11 - remainder) % 11
    return str(check_digit) if check_digit < 10 else 'X'

def generate_robust_ubrn(region_code, district_code):
    now = datetime.datetime.now()
    year_short, julian_day = now.strftime('%y'), now.strftime('%j')
    sequence = get_next_sequence_for_district_day(region_code, district_code, julian_day)
    sequence_str = f"{sequence:04d}"
    base_ubrn_numeric_part = f"{region_code}{district_code}{year_short}{julian_day}{sequence_str}"
    check_digit = calculate_check_digit(base_ubrn_numeric_part)
    return f"GHA-{region_code}-{district_code}-{year_short}{julian_day}-{sequence_str}-{check_digit}"

def save_registration(details):
    """Saves registration details to the DB and returns the UBRN."""
    ubrn = generate_robust_ubrn(details["region_code"], details["district_code"])
    details["ubrn"] = ubrn
    registrations_db[ubrn] = details
    logging.info(f"DATABASE: Saved record with UBRN {ubrn}. Details: {details}")
    return ubrn

def find_registration_by_ubrn(ubrn):
    """Finds a registration by UBRN from the DB."""
    logging.info(f"DATABASE: Searching for UBRN '{ubrn.upper()}'")
    return registrations_db.get(ubrn.upper())

def send_sms(phone_number, message):
    """Simulates sending an SMS via an API gateway."""
    logging.info(f"SMS GATEWAY: Sending SMS to {phone_number}. Message: '{message}'")
    return True


# --- Main Flask Application ---

app = Flask(__name__)

@app.route('/callback', methods=['POST'])
def ussd_callback():
    session_id = request.values.get("sessionId", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "").strip()
    
    # Log every incoming request for traceability
    logging.info(f"Request received - SessionID: {session_id}, Phone: {phone_number}, Text: '{text}'")

    response = ""
    try:
        inputs = [inp.strip()[:100] for inp in text.split('*')]

        # ================== MAIN MENU ==================
        if text == "":
            response = "CON Welcome to the Ghana e-Birth Service:\n1. Register a New Birth\n2. Verify Registration Status"

        # ================== REGISTRATION FLOW (Option 1) ==================
        elif inputs[0] == "1":
            if len(inputs) == 1:
                response = "CON Enter Child's Full Name (or enter 0 to skip)"
            elif len(inputs) == 2:
                if not validate_name(inputs[1]):
                    response = "END Invalid Name. Please enter alphabetic characters only."
                else:
                    response = "CON Enter Date of Birth (DDMMYYYY)"
            elif len(inputs) == 3:
                if not validate_date_of_birth(inputs[2]):
                    response = "END Invalid Date of Birth. Format must be DDMMYYYY and a valid date."
                else:
                    response = "CON Select Sex:\n1. Male\n2. Female"
            elif len(inputs) == 4:
                if not validate_sex_selection(inputs[3]):
                    response = "END Invalid selection for sex. Please restart."
                else:
                    region_menu = "\n".join([f"{key}. {REGIONS_DISTRICTS[key]['name']}" for key in REGIONS_DISTRICTS])
                    response = f"CON Select Region of Birth:\n{region_menu}"
            elif len(inputs) == 5:
                region_selection = inputs[4]
                if region_selection not in REGIONS_DISTRICTS:
                    response = "END Invalid region selection. Please restart."
                else:
                    districts = REGIONS_DISTRICTS[region_selection]["districts"]
                    district_menu = "\n".join([f"{i+1}. {d['name']}" for i, d in enumerate(districts)])
                    response = f"CON Select District:\n{district_menu}"
            elif len(inputs) == 6:
                region_selection = inputs[4]
                if region_selection not in REGIONS_DISTRICTS:
                     response = "END Session error. Invalid region. Please restart."
                else:
                    districts = REGIONS_DISTRICTS[region_selection]["districts"]
                    try:
                        district_index = int(inputs[5]) - 1
                        if not (0 <= district_index < len(districts)): raise ValueError
                        response = "CON Enter Mother's Ghana Card Number (e.g. GHA-123456789-0)"
                    except (ValueError, IndexError):
                        response = "END Invalid district selection. Please restart."
            elif len(inputs) == 7:
                if not validate_nin(inputs[6]):
                    response = "END Invalid Mother's Ghana Card Number. Please restart."
                else:
                    response = "CON Enter Father's Ghana Card Number (or enter 0 to skip)"
            elif len(inputs) == 8:
                if not validate_optional_nin(inputs[7]):
                    response = "END Invalid Father's Ghana Card Number. Please restart."
                else:
                    child_name_raw, dob_raw, sex_code, region_sel, district_sel, mother_nin, father_nin_raw = inputs[1:8]
                    child_name = "N/A" if child_name_raw == '0' else child_name_raw
                    dob_display = f"{dob_raw[:2]}/{dob_raw[2:4]}/{dob_raw[4:]}"
                    sex_display = "Male" if sex_code == '1' else "Female"
                    region_name = REGIONS_DISTRICTS[region_sel]['name']
                    district_name = REGIONS_DISTRICTS[region_sel]['districts'][int(district_sel)-1]['name']
                    father_nin = "N/A" if father_nin_raw == '0' else father_nin_raw

                    summary = (f"Confirm Details:\nName: {child_name}\nDOB: {dob_display}\nSex: {sex_display}\n"
                               f"Region: {region_name}\nDistrict: {district_name}\nMother NIN: {mother_nin}\n"
                               f"Father NIN: {father_nin}\n\n1. Confirm & Submit\n2. Cancel")
                    response = f"CON {summary}"
            elif len(inputs) == 9:
                if inputs[8] == '1':
                    region_code = REGIONS_DISTRICTS[inputs[4]]['code']
                    district_code = REGIONS_DISTRICTS[inputs[4]]['districts'][int(inputs[5])-1]['code']
                    details = {
                        "baby_name": "N/A" if inputs[1] == '0' else inputs[1],
                        "dob": f"{inputs[2][:2]}/{inputs[2][2:4]}/{inputs[2][4:]}",
                        "sex": "Male" if inputs[3] == '1' else "Female",
                        "region_code": region_code, "district_code": district_code,
                        "mother_nin": inputs[6],
                        "father_nin": "N/A" if inputs[7] == '0' else inputs[7],
                        "status": "Provisionally Registered"
                    }
                    ubrn = save_registration(details)
                    sms_message = (f"Congratulations! The birth of your child is provisionally registered. "
                                   f"Your Unique Birth Registration Number is {ubrn}. Keep this safe.")
                    send_sms(phone_number, sms_message)
                    response = "END Thank you! You will receive an SMS with the UBRN shortly."
                else:
                    response = "END Registration cancelled. Thank you."
        
        # ================== VERIFICATION FLOW (Option 2) ==================
        elif inputs[0] == "2":
            if len(inputs) == 1:
                response = "CON Please enter the complete UBRN to verify (e.g., GHA-01-027-25213-0001-5)."
            elif len(inputs) == 2:
                ubrn_to_check = inputs[1].strip()
                if not validate_ubrn(ubrn_to_check):
                    response = "END Invalid UBRN format. Please dial code to start again."
                else:
                    record = find_registration_by_ubrn(ubrn_to_check)
                    if record:
                        summary = f"Registration Found:\nName: {record['baby_name']}\nDOB: {record['dob']}\nStatus: {record['status']}"
                        logging.info(f"VERIFICATION: Found record for UBRN '{ubrn_to_check}'.")
                        response = f"END {summary}"
                    else:
                        logging.warning(f"VERIFICATION: No record found for UBRN '{ubrn_to_check}'.")
                        response = "END Registration Not Found. Please check the UBRN and try again."

        else:
            response = "END Invalid option. Please restart the process."

        # Log the response being sent back to the USSD gateway
        logging.info(f"Response sent - SessionID: {session_id}, Phone: {phone_number}, Response: '{response}'")
        return response

    except Exception as e:
        # Log the full exception traceback for debugging
        logging.error(f"FATAL ERROR in USSD callback for SessionID {session_id}: {e}", exc_info=True)
        # Provide a generic error to the user
        return "END A system error occurred. Please try again later."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)