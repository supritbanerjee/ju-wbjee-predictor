import os
import json
import re
import pandas as pd

def clean_branch(name):
    if not name or pd.isna(name):
        return ""
    name = str(name).strip()
    # Remove lateral entry markers, BE/BTech suffixes, etc.
    name = re.sub(r'^BE\s*\{Lateral\}\s*–\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\(BE\)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\(B\.Pharm\)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\(Lateral\)$', '', name, flags=re.IGNORECASE)
    name = name.strip()
    
    # Standardize names
    standard_names = {
        "Computer Science & Engineering": "Computer Science & Engineering",
        "Computer Science & Engg.": "Computer Science & Engineering",
        "Information Technology": "Information Technology",
        "Electronics & Tele-Comm. Engineering": "Electronics & Telecommunication Engineering",
        "Electronics & Telecommunication Engineering": "Electronics & Telecommunication Engineering",
        "Electronics & Tele-Comm.": "Electronics & Telecommunication Engineering",
        "Electronics & Telecomm": "Electronics & Telecommunication Engineering",
        "Electrical Engineering": "Electrical Engineering",
        "Mechanical Engineering": "Mechanical Engineering",
        "Chemical Engineering": "Chemical Engineering",
        "Civil Engineering": "Civil Engineering",
        "Metallurgical Engineering": "Metallurgical Engineering",
        "Metallurgical & Material Engineering": "Metallurgical Engineering",
        "Production Engineering": "Production Engineering",
        "Power Engineering": "Power Engineering",
        "Instrumentation & Electronics Engineering": "Instrumentation & Electronics Engineering",
        "Instrumentation & Electronics": "Instrumentation & Electronics Engineering",
        "Food Technology & Biochemical Engineering": "Food Technology & Biochemical Engineering",
        "Food Technology & Bio-Chemical Engg.": "Food Technology & Biochemical Engineering",
        "Food Tech. & Biochemical Engg.": "Food Technology & Biochemical Engineering",
        "Food Technology": "Food Technology & Biochemical Engineering",
        "Printing Engineering": "Printing Engineering",
        "Construction Engineering": "Construction Engineering",
        "Pharmaceutical Technology": "Pharmaceutical Technology",
        "B.Pharm": "Pharmaceutical Technology",
        "B.Pharm.": "Pharmaceutical Technology"
    }
    
    return standard_names.get(name, name)

def clean_category(cat):
    if not cat or pd.isna(cat):
        return ""
    cat = str(cat).strip().upper()
    
    # Standardize categories
    if "GENERAL" in cat or "GEN" in cat or "OP" in cat:
        if "PH" in cat or "PWD" in cat:
            return "General-PwD"
        return "General"
    if "OBC-A" in cat or "OBCA" in cat:
        return "OBC-A"
    if "OBC-B" in cat or "OBCB" in cat:
        return "OBC-B"
    if "OBC" in cat:
        return "OBC"
    if "SC" in cat:
        if "PH" in cat or "PWD" in cat:
            return "SC-PwD"
        return "SC"
    if "ST" in cat:
        if "PH" in cat or "PWD" in cat:
            return "ST-PwD"
        return "ST"
    if "TFW" in cat:
        return "TFW"
    if "PWD" in cat or "PH" in cat:
        return "PwD"
    
    return cat

def parse_rank_value(val):
    if val is None or pd.isna(val):
        return None, None
    val_str = str(val).strip()
    if not val_str or val_str == "–" or val_str == "-" or val_str == "nan":
        return None, None
    
    # Handle ranges like 22-309 or 22–309
    val_str = val_str.replace("–", "-").replace("to", "-").replace(" ", "")
    if "-" in val_str:
        parts = val_str.split("-")
        try:
            o_rank = int(float(parts[0]))
            c_rank = int(float(parts[1]))
            return o_rank, c_rank
        except ValueError:
            pass
    
    # Single rank
    try:
        rank = int(float(val_str))
        return rank, rank
    except ValueError:
        return None, None

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

wbjee_data = []
jeemain_data = []
jelet_data = []
bpharm_data = []

# --- 2022 ---
log("Parsing 2022...")
f22 = "JU_Cutoff_2022.xlsx"
if os.path.exists(f22):
    # WBJEE HS
    for cat_sheet, cat_name in [('General Category', 'General'), ('OBC Category', 'OBC'), ('SC Category', 'SC'), ('ST Category', 'ST')]:
        try:
            df = pd.read_excel(f22, sheet_name=cat_sheet, header=None)
            # Row 0 contains title, Row 1 contains headers: Branch / Course, Opening Rank, Closing Rank
            # Let's find where data starts
            start_row = 2
            for i in range(len(df)):
                if "Branch" in str(df.iloc[i, 0]) or "Course" in str(df.iloc[i, 0]):
                    start_row = i + 1
                    break
            for r in range(start_row, len(df)):
                branch_raw = df.iloc[r, 0]
                or_raw = df.iloc[r, 1]
                cr_raw = df.iloc[r, 2]
                
                if pd.isna(branch_raw) or str(branch_raw).strip() == "" or "total" in str(branch_raw).lower():
                    continue
                
                branch = clean_branch(branch_raw)
                o_rank, c_rank = parse_rank_value(or_raw)
                _, c_rank_alt = parse_rank_value(cr_raw)
                
                c_rank = c_rank_alt if c_rank_alt else c_rank
                if c_rank:
                    wbjee_data.append({
                        "year": 2022,
                        "branch": branch,
                        "category": cat_name,
                        "quota": "HS",
                        "round": "Final",
                        "or": o_rank if o_rank else c_rank,
                        "cr": c_rank
                    })
        except Exception as e:
            log(f"Error 2022 {cat_sheet}: {e}")
            
    # JEE Main
    try:
        df = pd.read_excel(f22, sheet_name='JEE-Main 2022', header=None)
        start_row = 2
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                start_row = i + 1
                break
        for r in range(start_row, len(df)):
            branch_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                jeemain_data.append({
                    "year": 2022,
                    "branch": branch,
                    "category": "General",
                    "quota": "AI",
                    "round": "Final",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2022 JEE-Main: {e}")
        
    # JELET
    try:
        df = pd.read_excel(f22, sheet_name='JELET 2022', header=None)
        start_row = 2
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                start_row = i + 1
                break
        for r in range(start_row, len(df)):
            branch_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                jelet_data.append({
                    "year": 2022,
                    "branch": branch,
                    "category": "General",
                    "quota": "HS",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2022 JELET: {e}")

    # B.Pharm
    try:
        df = pd.read_excel(f22, sheet_name='B.Pharm 2022', header=None)
        start_row = 2
        for i in range(len(df)):
            if "Category" in str(df.iloc[i, 0]):
                start_row = i + 1
                break
        for r in range(start_row, len(df)):
            cat_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            if pd.isna(cat_raw) or str(cat_raw).strip() == "": continue
            cat = clean_category(cat_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                bpharm_data.append({
                    "year": 2022,
                    "branch": "Pharmaceutical Technology",
                    "category": cat,
                    "quota": "HS",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2022 B.Pharm: {e}")

# --- 2023 ---
log("Parsing 2023...")
f23 = "JU_Cutoff_2023.xlsx"
if os.path.exists(f23):
    # WBJEE HS Category-wise
    try:
        df = pd.read_excel(f23, sheet_name='WBJEE 2023 – Category-wise', header=None)
        # Find header row
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        cols = [str(x).strip() for x in df.iloc[header_row]]
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            for c in range(1, len(cols)):
                cat = clean_category(cols[c])
                val = df.iloc[r, c]
                o_rank, c_rank = parse_rank_value(val)
                if c_rank:
                    wbjee_data.append({
                        "year": 2023,
                        "branch": branch,
                        "category": cat,
                        "quota": "HS",
                        "round": "Final",
                        "or": o_rank if o_rank else c_rank,
                        "cr": c_rank
                    })
    except Exception as e:
        log(f"Error 2023 Category-wise: {e}")
        
    # B.Pharm 2023
    try:
        df = pd.read_excel(f23, sheet_name='B.Pharm 2023', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Category" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            cat_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            notes = str(df.iloc[r, 3]).strip() if len(df.columns) > 3 else ""
            quota = "HS" if "Home State" in notes or "HS" in notes else "AI"
            if pd.isna(cat_raw) or str(cat_raw).strip() == "": continue
            cat = clean_category(cat_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                bpharm_data.append({
                    "year": 2023,
                    "branch": "Pharmaceutical Technology",
                    "category": cat,
                    "quota": quota,
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2023 B.Pharm: {e}")

    # JEE-Main 2023
    try:
        df = pd.read_excel(f23, sheet_name='JEE-Main 2023', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            quota_raw = str(df.iloc[r, 3]).strip() if len(df.columns) > 3 else "AI"
            quota = "HS" if "Home State" in quota_raw or "HS" in quota_raw else "AI"
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                jeemain_data.append({
                    "year": 2023,
                    "branch": branch,
                    "category": "General",
                    "quota": quota,
                    "round": "Final",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2023 JEE-Main: {e}")

    # JELET 2023
    try:
        df = pd.read_excel(f23, sheet_name='JELET 2023', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        cols = [str(x).strip() for x in df.iloc[header_row]]
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            for c in range(1, len(cols)):
                cat = clean_category(cols[c])
                val = df.iloc[r, c]
                o_rank, c_rank = parse_rank_value(val)
                if c_rank:
                    jelet_data.append({
                        "year": 2023,
                        "branch": branch,
                        "category": cat,
                        "quota": "HS",
                        "or": o_rank if o_rank else c_rank,
                        "cr": c_rank
                    })
    except Exception as e:
        log(f"Error 2023 JELET: {e}")

# --- 2024 ---
log("Parsing 2024...")
f24 = "JU_Cutoff_2024.xlsx"
if os.path.exists(f24):
    # WBJEE R1 HS (General)
    try:
        df = pd.read_excel(f24, sheet_name='WBJEE R1 – HS (General)', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                wbjee_data.append({
                    "year": 2024,
                    "branch": branch,
                    "category": "General",
                    "quota": "HS",
                    "round": "Round 1",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2024 R1: {e}")

    # Category-wise (HS) (This is typically Round 2 / Final)
    try:
        df = pd.read_excel(f24, sheet_name='Category-wise (HS)', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        cols = [str(x).strip() for x in df.iloc[header_row]]
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            for c in range(1, len(cols)):
                cat = clean_category(cols[c])
                val = df.iloc[r, c]
                o_rank, c_rank = parse_rank_value(val)
                if c_rank:
                    wbjee_data.append({
                        "year": 2024,
                        "branch": branch,
                        "category": cat,
                        "quota": "HS",
                        "round": "Round 2",
                        "or": o_rank if o_rank else c_rank,
                        "cr": c_rank
                    })
    except Exception as e:
        log(f"Error 2024 Category-wise: {e}")

    # WBJEE R2 AI (General)
    try:
        df = pd.read_excel(f24, sheet_name='WBJEE R2 – AI (General)', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            cr_raw = df.iloc[r, 1]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(cr_raw) # only closing provided
            if c_rank:
                wbjee_data.append({
                    "year": 2024,
                    "branch": branch,
                    "category": "General",
                    "quota": "AI",
                    "round": "Round 2",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2024 R2 AI: {e}")

    # JELET 2024
    try:
        df = pd.read_excel(f24, sheet_name='JELET 2024', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Program" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            cat_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            quota_raw = str(df.iloc[r, 3]).strip() if len(df.columns) > 3 else "HS"
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            cat = clean_category(cat_raw)
            o_rank, c_rank = parse_rank_value(cr_raw)
            if c_rank:
                jelet_data.append({
                    "year": 2024,
                    "branch": branch,
                    "category": cat,
                    "quota": quota_raw,
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2024 JELET: {e}")

    # JEE-Main 2024
    try:
        df = pd.read_excel(f24, sheet_name='JEE-Main 2024', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            cat_raw = df.iloc[r, 1]
            ai_or = df.iloc[r, 2]
            ai_cr = df.iloc[r, 3]
            hs_or = df.iloc[r, 4] if len(df.columns) > 4 else None
            hs_cr = df.iloc[r, 5] if len(df.columns) > 5 else None
            
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            cat = clean_category(cat_raw)
            
            # AI
            o, c = parse_rank_value(ai_or)
            _, c_alt = parse_rank_value(ai_cr)
            c = c_alt if c_alt else c
            if c:
                jeemain_data.append({
                    "year": 2024,
                    "branch": branch,
                    "category": cat,
                    "quota": "AI",
                    "round": "Round 3",
                    "or": o if o else c,
                    "cr": c
                })
            # HS
            o, c = parse_rank_value(hs_or)
            _, c_alt = parse_rank_value(hs_cr)
            c = c_alt if c_alt else c
            if c:
                jeemain_data.append({
                    "year": 2024,
                    "branch": branch,
                    "category": cat,
                    "quota": "HS",
                    "round": "Round 3",
                    "or": o if o else c,
                    "cr": c
                })
    except Exception as e:
        log(f"Error 2024 JEE-Main: {e}")

# --- 2025 ---
log("Parsing 2025...")
f25 = "Jadavpur_University_Cutoff_2025.xlsx"
if os.path.exists(f25):
    # WBJEE R1 HS (General)
    try:
        df = pd.read_excel(f25, sheet_name='WBJEE R1 – General (HS)', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                wbjee_data.append({
                    "year": 2025,
                    "branch": branch,
                    "category": "General",
                    "quota": "HS",
                    "round": "Round 1",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2025 R1 HS: {e}")

    # WBJEE R1 AI (General)
    try:
        df = pd.read_excel(f25, sheet_name='WBJEE R1 – AI (General)', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                wbjee_data.append({
                    "year": 2025,
                    "branch": branch,
                    "category": "General",
                    "quota": "AI",
                    "round": "Round 1",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2025 R1 AI: {e}")

    # WBJEE R2 AI (General)
    try:
        df = pd.read_excel(f25, sheet_name='WBJEE R2 – AI (General)', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            or_raw = df.iloc[r, 1]
            cr_raw = df.iloc[r, 2]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            o_rank, c_rank = parse_rank_value(or_raw)
            _, c_rank_alt = parse_rank_value(cr_raw)
            c_rank = c_rank_alt if c_rank_alt else c_rank
            if c_rank:
                wbjee_data.append({
                    "year": 2025,
                    "branch": branch,
                    "category": "General",
                    "quota": "AI",
                    "round": "Round 2",
                    "or": o_rank if o_rank else c_rank,
                    "cr": c_rank
                })
    except Exception as e:
        log(f"Error 2025 R2 AI: {e}")

    # Category-wise (HS) (Round 2)
    try:
        df = pd.read_excel(f25, sheet_name='Category-wise (HS)', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Branch" in str(df.iloc[i, 0]):
                header_row = i
                break
        cols = [str(x).strip() for x in df.iloc[header_row]]
        # Standardize 2025 column names
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            for c in range(1, len(cols)):
                cat = clean_category(cols[c])
                val = df.iloc[r, c]
                o_rank, c_rank = parse_rank_value(val)
                if c_rank:
                    wbjee_data.append({
                        "year": 2025,
                        "branch": branch,
                        "category": cat,
                        "quota": "HS",
                        "round": "Round 2",
                        "or": o_rank if o_rank else c_rank,
                        "cr": c_rank
                    })
    except Exception as e:
        log(f"Error 2025 Category-wise: {e}")

    # B.Pharm Cutoff
    try:
        df = pd.read_excel(f25, sheet_name='B.Pharm Cutoff', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Category" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            cat_raw = df.iloc[r, 0]
            quota_raw = str(df.iloc[r, 1]).strip()
            quota = "HS" if "HS" in quota_raw or "Home State" in quota_raw else "AI"
            r1_cr = df.iloc[r, 2]
            r2_cr = df.iloc[r, 3] if len(df.columns) > 3 else None
            
            if pd.isna(cat_raw) or str(cat_raw).strip() == "": continue
            cat = clean_category(cat_raw)
            
            # Round 1
            o, c = parse_rank_value(r1_cr)
            if c:
                bpharm_data.append({
                    "year": 2025,
                    "branch": "Pharmaceutical Technology",
                    "category": cat,
                    "quota": quota,
                    "round": "Round 1",
                    "or": o if o else c,
                    "cr": c
                })
            # Round 2
            o, c = parse_rank_value(r2_cr)
            if c:
                bpharm_data.append({
                    "year": 2025,
                    "branch": "Pharmaceutical Technology",
                    "category": cat,
                    "quota": quota,
                    "round": "Round 2",
                    "or": o if o else c,
                    "cr": c
                })
    except Exception as e:
        log(f"Error 2025 B.Pharm: {e}")

    # JELET 2025
    try:
        df = pd.read_excel(f25, sheet_name='JELET 2025', header=None)
        header_row = 1
        for i in range(len(df)):
            if "Program" in str(df.iloc[i, 0]):
                header_row = i
                break
        for r in range(header_row + 1, len(df)):
            branch_raw = df.iloc[r, 0]
            cat_raw = df.iloc[r, 1]
            cr25 = df.iloc[r, 2]
            cr24 = df.iloc[r, 3] if len(df.columns) > 3 else None
            
            if pd.isna(branch_raw) or str(branch_raw).strip() == "": continue
            branch = clean_branch(branch_raw)
            cat = clean_category(cat_raw)
            
            o, c = parse_rank_value(cr25)
            if c:
                jelet_data.append({
                    "year": 2025,
                    "branch": branch,
                    "category": cat,
                    "quota": "HS",
                    "or": o if o else c,
                    "cr": c
                })
    except Exception as e:
        log(f"Error 2025 JELET: {e}")

combined_dataset = {
    "wbjee": wbjee_data,
    "jeemain": jeemain_data,
    "jelet": jelet_data,
    "bpharm": bpharm_data
}

# Output files
with open("cutoff_data.json", "w", encoding="utf-8") as f:
    json.dump(combined_dataset, f, indent=2)
    
# Output as data.js to bypass CORS issues on local file:// protocol
with open("data.js", "w", encoding="utf-8") as f:
    f.write("const CUTOFF_DATA = ")
    json.dump(combined_dataset, f, indent=2)
    f.write(";\n")

# Copy the generated high-clarity logo to the workspace
import shutil
src_logo = r"C:\Users\HP\.gemini\antigravity\brain\65877000-abfa-4c0e-9f1f-15b5950c0918\sfi_ju_logo_1781845347720.png"
dst_logo = "logo.png"
if os.path.exists(src_logo):
    try:
        shutil.copy(src_logo, dst_logo)
        log("Copied high-clarity logo.png to workspace.")
    except Exception as e:
        log(f"Error copying logo: {e}")
else:
    log(f"Logo source not found: {src_logo}")
    
log(f"\nFinal Statistics:")
log(f"WBJEE Records: {len(wbjee_data)}")
log(f"JEE Main Records: {len(jeemain_data)}")
log(f"JELET Records: {len(jelet_data)}")
log(f"B.Pharm Records: {len(bpharm_data)}")

with open("parse_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
print("\nCleaned datasets successfully generated as 'cutoff_data.json' and 'data.js'.")
