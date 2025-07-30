from flask import Flask, request
import datetime
import random
import re

# --- Dummy Database & Helper Functions (Replace with real DB and APIs) ---

# A simple dictionary to act as our in-memory database.
# In production, use a robust database like PostgreSQL or MySQL.
registrations_db = {
    "GHA-2025-0000001": {
        "baby_name": "Test Baby", "dob": "01/01/2025", "sex": "Male",
        "mother_name": "Test Mother", "status": "Provisionally Registered"
    }
}

# --- Input Validation Functions ---

def validate_region_selection(region_input):
    """Validates region selection (1-16)"""
    try:
        region_num = int(region_input)
        return 1 <= region_num <= 16
    except (ValueError, TypeError):
        return False

def validate_district_code(district_code):
    """Validates 3-digit district code"""
    if not district_code or len(district_code) != 3:
        return False
    return district_code.isdigit()

def validate_date_of_birth(dob):
    """Validates date format DDMMYYYY and checks if it's a reasonable date"""
    if not dob or len(dob) != 8:
        return False
    
    if not dob.isdigit():
        return False
    
    try:
        day = int(dob[:2])
        month = int(dob[2:4])
        year = int(dob[4:8])
        
        current_year = datetime.datetime.now().year
        if not (1 <= day <= 31 and 1 <= month <= 12 and (current_year - 10) <= year <= current_year):
            return False
            
        datetime.datetime(year, month, day)
        return True
    except (ValueError, TypeError):
        return False

def validate_sex_selection(sex_input):
    """Validates sex selection (1 or 2)"""
    return sex_input in ['1', '2']

def validate_name(name):
    """Validates name input - must be alphabetic and reasonable length"""
    if not name:
        return False
    clean_name = name.strip()
    if not (2 <= len(clean_name) <= 50):
        return False
    pattern = r"^[a-zA-Z\s'-]+$"
    return bool(re.match(pattern, clean_name))

def validate_nin(nin):
    """Validates 15-character Ghana Card Number format (GHA-123456789-0)"""
    if not nin:
        return False
    pattern = r'^GHA-\d{9}-[\dA-Z]$'
    return bool(re.match(pattern, nin.upper()))

def validate_health_worker_id(hw_id):
    """Validates 6-digit health worker ID"""
    if not hw_id or len(hw_id) != 6:
        return False
    return hw_id.isdigit()

def validate_phone_number(phone):
    """Validates 10-digit phone number format"""
    if not phone:
        return False
    clean_phone = ''.join(filter(str.isdigit, phone))
    return len(clean_phone) == 10 and clean_phone.startswith('0')

def validate_ubrn(ubrn):
    """Validates UBRN format"""
    if not ubrn:
        return False
    pattern = r'^GHA-\d{2}-\d{3}-\d{5}-\d{4}-[\dX]$'
    return bool(re.match(pattern, ubrn.upper()))

# --- UBRN Generation & DB Functions ---

def get_next_sequence_for_district_day(region_code, district_code, julian_day):
    """ *** SIMULATED FUNCTION *** """
    return random.randint(1, 5)

def calculate_check_digit(number_string):
    """Calculates a check digit using the Modulo 11 algorithm."""
    digits = [int(d) for d in number_string if d.isdigit()]
    if not digits: return '0'
    weights = list(range(len(digits), 0, -1))
    s = sum(digit * weights[i] for i, digit in enumerate(digits))
    remainder = s % 11
    check_digit = (11 - remainder) % 11
    return str(check_digit) if check_digit < 10 else 'X'

def generate_robust_ubrn(region_code, district_code):
    """Generates a structured, information-rich, and highly unique UBRN."""
    now = datetime.datetime.now()
    year_short, julian_day = now.strftime('%y'), now.strftime('%j')
    sequence = get_next_sequence_for_district_day(region_code, district_code, julian_day)
    sequence_str = f"{sequence:04d}"
    base_ubrn_numeric_part = f"{region_code}{district_code}{year_short}{julian_day}{sequence_str}"
    check_digit = calculate_check_digit(base_ubrn_numeric_part)
    return f"GHA-{region_code}-{district_code}-{year_short}{julian_day}-{sequence_str}-{check_digit}"

def save_registration(details, region_code, district_code):
    """Saves registration details to the DB and returns the UBRN."""
    ubrn = generate_robust_ubrn(region_code, district_code)
    details["ubrn"] = ubrn
    registrations_db[ubrn] = details
    print("="*20 + f"\nDATABASE: Saved record with UBRN {ubrn}\nDetails: {details}\n" + "="*20)
    return ubrn

def find_registration_by_ubrn(ubrn):
    """Finds a registration by UBRN from the DB."""
    return registrations_db.get(ubrn.upper())

def send_sms(phone_number, message):
    """Simulates sending an SMS via an API gateway."""
    print("="*20 + f"\nSMS GATEWAY: Sending SMS to {phone_number}:\n{message}\n" + "="*20)
    return True

# --- Main Flask Application ---

app = Flask(__name__)

@app.route('/callback', methods=['POST'])
def ussd_callback():
    try:
        session_id = request.values.get("sessionId", None)
        phone_number = request.values.get("phoneNumber", None)
        text = request.values.get("text", "").strip()
        
        response = ""
        inputs = [inp.strip()[:100] for inp in text.split('*')]

        # ================== MAIN MENU ==================
        if text == "":
            response = "CON Welcome to the Ghana e-Birth Service:\n1. Register a New Birth\n2. Verify Registration\n3. Help"

        # ================== REGISTRATION FLOW (Option 1) ==================
        elif inputs[0] == "1":
            if len(inputs) == 1:
                response = "CON You are registering as:\n1. Parent/Guardian\n2. Health Worker"
            
            # --- PATH 1.1: Parent/Guardian Flow ---
            elif inputs[1] == "1":
                if len(inputs) == 2:
                    region_list = "1. G. Accra\n2. Ashanti\n3. Western\n4. Central\n5. Eastern\n6. Volta\n7. Northern\n8. U. East\n9. U. West\n10. Bono\n11. Bono E\n12. Ahafo\n13. W. North\n14. Oti\n15. N. East\n16. Savannah"
                    response = f"CON Select the region of birth:\n{region_list}"
                elif len(inputs) == 3:
                    if not validate_region_selection(inputs[2]): response = "END Invalid region. Please dial code to start again."
                    else: response = "CON Enter your 3-digit District Code (e.g., 027 for Accra Metro)"
                elif len(inputs) == 4:
                    if not validate_district_code(inputs[3]): response = "END Invalid district code. Please dial code to start again."
                    else: response = "CON Enter baby's Date of Birth (DDMMYYYY)"
                elif len(inputs) == 5:
                    if not validate_date_of_birth(inputs[4]): response = "END Invalid date. Please dial code to start again."
                    else: response = "CON Select baby's sex:\n1. Male\n2. Female"
                elif len(inputs) == 6:
                    if not validate_sex_selection(inputs[5]): response = "END Invalid sex selection. Please dial code to start again."
                    else: response = "CON Enter baby's First Name(s)"
                elif len(inputs) == 7:
                    if not validate_name(inputs[6]): response = "END Invalid first name. Please dial code to start again."
                    else: response = "CON Enter baby's Surname"
                elif len(inputs) == 8:
                    if not validate_name(inputs[7]): response = "END Invalid surname. Please dial code to start again."
                    else: response = "CON Enter Mother's Full Name (as on Ghana Card)"
                elif len(inputs) == 9:
                    if not validate_name(inputs[8]): response = "END Invalid mother's name. Please dial code to start again."
                    else: response = "CON Enter Mother's Ghana Card Number (e.g. GHA-123456789-0)"
                elif len(inputs) == 10:
                    if not validate_nin(inputs[9]): response = "END Invalid mother's NIN. Please dial code to start again."
                    else: response = "CON Add Father's Details?\n1. Yes\n2. No"
                
                # --- Flow diverges here based on Father Details selection ---
                elif len(inputs) >= 11:
                    add_father_choice = inputs[10]
                    if add_father_choice not in ['1', '2']:
                        response = "END Invalid choice for father's details. Please start again."
                    # --- PATH 1.1.1: NO Father Details ---
                    elif add_father_choice == '2':
                        if len(inputs) == 11: # Show confirmation
                            region_code, district_code, dob_raw, sex_code, first_name, surname, mother_name = inputs[2:9]
                            dob = f"{dob_raw[0:2]}/{dob_raw[2:4]}/{dob_raw[4:8]}"
                            sex = "Male" if sex_code == "1" else "Female"
                            summary = f"Please Confirm:\nDistrict: {district_code}\nName: {first_name} {surname}\nDOB: {dob}\nSex: {sex}\nMother: {mother_name}\n\n1. Confirm & Submit\n2. Cancel"
                            response = f"CON {summary}"
                        elif len(inputs) == 12: # Process submission
                            if inputs[11] == '1':
                                region_code_fmt = f"{int(inputs[2]):02d}"
                                details = {
                                    "baby_name": f"{inputs[6]} {inputs[7]}", "dob": f"{inputs[4][0:2]}/{inputs[4][2:4]}/{inputs[4][4:8]}",
                                    "sex": "Male" if inputs[5] == "1" else "Female", "mother_name": inputs[8], "mother_nin": inputs[9],
                                    "district_code": inputs[3], "region_code": region_code_fmt, "status": "Provisionally Registered"
                                }
                                ubrn = save_registration(details, region_code_fmt, inputs[3])
                                sms_message = f"Congratulations! The birth of {details['baby_name']} is registered. Your UBRN is {ubrn}. Keep this safe."
                                send_sms(phone_number, sms_message)
                                response = "END Thank you! You will receive an SMS with the UBRN shortly."
                            else:
                                response = "END Registration cancelled. Thank you."

                    # --- PATH 1.1.2: YES Father Details ---
                    elif add_father_choice == '1':
                        if len(inputs) == 11:
                            response = "CON Enter Father's Full Name"
                        elif len(inputs) == 12:
                            if not validate_name(inputs[11]): response = "END Invalid father's name. Please start again."
                            else: response = "CON Enter Father's Ghana Card Number (e.g. GHA-123456789-0)"
                        elif len(inputs) == 13: # Show confirmation
                            if not validate_nin(inputs[12]): response = "END Invalid father's NIN. Please start again."
                            else:
                                _, _, dob_raw, sex_code, first_name, surname, mother_name, _, _, father_name = inputs[2:12]
                                dob = f"{dob_raw[0:2]}/{dob_raw[2:4]}/{dob_raw[4:8]}"
                                sex = "Male" if sex_code == "1" else "Female"
                                summary = f"Please Confirm:\nName: {first_name} {surname}\nDOB: {dob}\nSex: {sex}\nMother: {mother_name}\nFather: {father_name}\n\n1. Confirm & Submit\n2. Cancel"
                                response = f"CON {summary}"
                        elif len(inputs) == 14: # Process submission
                            if inputs[13] == '1':
                                region_code_fmt = f"{int(inputs[2]):02d}"
                                details = {
                                    "baby_name": f"{inputs[6]} {inputs[7]}", "dob": f"{inputs[4][0:2]}/{inputs[4][2:4]}/{inputs[4][4:8]}",
                                    "sex": "Male" if inputs[5] == "1" else "Female", "mother_name": inputs[8], "mother_nin": inputs[9],
                                    "father_name": inputs[11], "father_nin": inputs[12],
                                    "district_code": inputs[3], "region_code": region_code_fmt, "status": "Provisionally Registered"
                                }
                                ubrn = save_registration(details, region_code_fmt, inputs[3])
                                sms_message = f"Congratulations! The birth of {details['baby_name']} is registered. Your UBRN is {ubrn}. Keep this safe."
                                send_sms(phone_number, sms_message)
                                response = "END Thank you! You will receive an SMS with the UBRN shortly."
                            else:
                                response = "END Registration cancelled. Thank you."

            # --- PATH 1.2: Health Worker Flow ---
            elif inputs[1] == "2":
                if len(inputs) == 2:
                    response = "CON Enter your 6-digit Health Worker ID."
                elif len(inputs) == 3:
                    if not validate_health_worker_id(inputs[2]): response = "END Invalid Health Worker ID. Please start again."
                    else: 
                        region_list = "1. G. Accra\n2. Ashanti\n3. Western\n4. Central\n5. Eastern\n6. Volta\n7. Northern\n8. U. East\n9. U. West\n10. Bono\n11. Bono E\n12. Ahafo\n13. W. North\n14. Oti\n15. N. East\n16. Savannah"
                        response = f"CON Select the region of birth:\n{region_list}"
                elif len(inputs) == 4:
                    if not validate_region_selection(inputs[3]): response = "END Invalid region. Please start again."
                    else: response = "CON Enter the 3-digit District Code"
                elif len(inputs) == 5:
                    if not validate_district_code(inputs[4]): response = "END Invalid district code. Please start again."
                    else: response = "CON Enter baby's Date of Birth (DDMMYYYY)"
                elif len(inputs) == 6:
                    if not validate_date_of_birth(inputs[5]): response = "END Invalid date. Please start again."
                    else: response = "CON Select baby's sex:\n1. Male\n2. Female"
                elif len(inputs) == 7:
                    if not validate_sex_selection(inputs[6]): response = "END Invalid sex selection. Please start again."
                    else: response = "CON Enter baby's First Name(s)"
                elif len(inputs) == 8:
                    if not validate_name(inputs[7]): response = "END Invalid first name. Please start again."
                    else: response = "CON Enter baby's Surname"
                elif len(inputs) == 9:
                    if not validate_name(inputs[8]): response = "END Invalid surname. Please start again."
                    else: response = "CON Enter Mother's Full Name"
                elif len(inputs) == 10:
                    if not validate_name(inputs[9]): response = "END Invalid mother's name. Please start again."
                    else: response = "CON Enter Mother's Ghana Card Number"
                elif len(inputs) == 11:
                    if not validate_nin(inputs[10]): response = "END Invalid mother's NIN. Please start again."
                    else: response = "CON Enter Parent's 10-digit phone number for SMS"
                elif len(inputs) == 12:
                    if not validate_phone_number(inputs[11]): response = "END Invalid phone number. Please start again."
                    else: response = "CON Add Father's Details?\n1. Yes\n2. No"

                # --- Flow diverges here based on Father Details selection ---
                elif len(inputs) >= 13:
                    add_father_choice = inputs[12]
                    if add_father_choice not in ['1', '2']:
                        response = "END Invalid choice for father's details. Please start again."

                    # --- PATH 1.2.1: NO Father Details ---
                    elif add_father_choice == '2':
                        if len(inputs) == 13: # Show confirmation
                            hw_id, _, _, dob_raw, sex_code, first_name, surname, mother_name, _, parent_phone = inputs[2:12]
                            dob = f"{dob_raw[0:2]}/{dob_raw[2:4]}/{dob_raw[4:8]}"
                            sex = "Male" if sex_code == "1" else "Female"
                            summary = f"Confirm for HW {hw_id}:\nName: {first_name} {surname}\nDOB: {dob}\nMother: {mother_name}\nSMS to: {parent_phone}\n1. Confirm\n2. Cancel"
                            response = f"CON {summary}"
                        elif len(inputs) == 14: # Process submission
                            if inputs[13] == '1':
                                region_code_fmt = f"{int(inputs[3]):02d}"
                                details = {
                                    "baby_name": f"{inputs[7]} {inputs[8]}", "dob": f"{inputs[5][0:2]}/{inputs[5][2:4]}/{inputs[5][4:8]}",
                                    "sex": "Male" if inputs[6] == "1" else "Female", "mother_name": inputs[9], "mother_nin": inputs[10],
                                    "district_code": inputs[4], "region_code": region_code_fmt, "status": "Provisionally Registered",
                                    "registered_by": f"HW-{inputs[2]}"
                                }
                                ubrn = save_registration(details, region_code_fmt, inputs[4])
                                sms_message = f"The birth of {details['baby_name']} has been registered by a health worker. Your UBRN is {ubrn}. Keep this safe."
                                send_sms(inputs[11], sms_message)
                                response = "END Registration submitted. An SMS will be sent to the parent's number."
                            else:
                                response = "END Registration cancelled. Thank you."

                    # --- PATH 1.2.2: YES Father Details ---
                    elif add_father_choice == '1':
                        if len(inputs) == 13:
                            response = "CON Enter Father's Full Name"
                        elif len(inputs) == 14:
                            if not validate_name(inputs[13]): response = "END Invalid father's name. Please start again."
                            else: response = "CON Enter Father's Ghana Card Number"
                        elif len(inputs) == 15: # Show confirmation
                            if not validate_nin(inputs[14]): response = "END Invalid father's NIN. Please start again."
                            else:
                                hw_id, _, _, dob_raw, sex_code, first_name, surname, _, _, parent_phone, _, father_name = inputs[2:14]
                                dob = f"{dob_raw[0:2]}/{dob_raw[2:4]}/{dob_raw[4:8]}"
                                sex = "Male" if sex_code == "1" else "Female"
                                summary = f"Confirm for HW {hw_id}:\nName: {first_name} {surname}\nDOB: {dob}\nFather: {father_name}\nSMS to: {parent_phone}\n1. Confirm\n2. Cancel"
                                response = f"CON {summary}"
                        elif len(inputs) == 16: # Process submission
                            if inputs[15] == '1':
                                region_code_fmt = f"{int(inputs[3]):02d}"
                                details = {
                                    "baby_name": f"{inputs[7]} {inputs[8]}", "dob": f"{inputs[5][0:2]}/{inputs[5][2:4]}/{inputs[5][4:8]}",
                                    "sex": "Male" if inputs[6] == "1" else "Female", "mother_name": inputs[9], "mother_nin": inputs[10],
                                    "father_name": inputs[13], "father_nin": inputs[14],
                                    "district_code": inputs[4], "region_code": region_code_fmt, "status": "Provisionally Registered",
                                    "registered_by": f"HW-{inputs[2]}"
                                }
                                ubrn = save_registration(details, region_code_fmt, inputs[4])
                                sms_message = f"The birth of {details['baby_name']} has been registered by a health worker. Your UBRN is {ubrn}. Keep this safe."
                                send_sms(inputs[11], sms_message)
                                response = "END Registration submitted. An SMS will be sent to the parent's number."
                            else:
                                response = "END Registration cancelled. Thank you."
            else:
                response = "END Invalid role selection. Please try again."

        # ================== VERIFICATION FLOW (Option 2) ==================
        elif inputs[0] == "2":
            if len(inputs) == 1:
                response = "CON Please enter the complete UBRN to verify (e.g., GHA-01-027-25210-0001-5)."
            elif len(inputs) == 2:
                ubrn_to_check = inputs[1].strip()
                if not validate_ubrn(ubrn_to_check):
                    response = "END Invalid UBRN format. Please dial code to start again."
                else:
                    record = find_registration_by_ubrn(ubrn_to_check)
                    if record:
                        summary = f"Registration Found:\nName: {record['baby_name']}\nDOB: {record['dob']}\nStatus: {record['status']}"
                        response = f"END {summary}"
                    else:
                        response = "END Registration Not Found. Please check the UBRN and try again."

        # ================== HELP FLOW (Option 3) ==================
        elif inputs[0] == "3":
            if len(inputs) == 1:
                response = "CON HELP MENU:\n1. About\n2. Cost\n3. Requirements\n4. Contact"
            elif inputs[1] == "1":
                response = "END This is the official Govt. of Ghana service to register births using your mobile phone for free."
            elif inputs[1] == "2":
                response = "END Registering via USSD is FREE. Fees for the printed certificate may apply at the Registry office."
            elif inputs[1] == "3":
                response = "END You need: Baby's name & DOB, Mother's full name & Ghana Card number. Father's details are optional."
            elif inputs[1] == "4":
                response = "END For help, please call the Births & Deaths Registry toll-free number: 0800-123-456 (Mon-Fri, 8am-5pm)."
        else:
            response = "END Invalid option. Please restart the process."

        return response

    except Exception as e:
        print(f"ERROR in USSD callback: {str(e)}")
        return "END System error occurred. Please try again later."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
