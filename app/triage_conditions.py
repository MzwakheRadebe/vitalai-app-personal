"""
VitalAI Triage Conditions Reference
====================================
Complete mapping of medical conditions → severity levels.

Severity levels:
  CRITICAL — Life-threatening. Call 10177 / 112 immediately.
  HIGH     — Urgent. Go to emergency room or 24-hour clinic today (same day).
  MEDIUM   — See a doctor within 24–48 hours. Book an appointment.
  LOW      — Monitor at home. Pharmacy or GP visit if no improvement.

This module is the single source of truth used by _force_severity() in chat.py
and serves as a reference for the VitalAI response engine.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL CONDITIONS — Call 10177 / 112 immediately
# ─────────────────────────────────────────────────────────────────────────────
CRITICAL_CONDITIONS: dict[str, list[str]] = {
    "Cardiovascular": [
        "Heart attack (myocardial infarction)",
        "Cardiac arrest",
        "Ventricular fibrillation",
        "Aortic dissection",
        "Severe hypertensive crisis (BP > 180/120 with organ damage)",
        "Massive pulmonary embolism",
        "Cardiac tamponade",
        "Ruptured aortic aneurysm",
    ],
    "Neurological": [
        "Stroke (ischaemic or haemorrhagic)",
        "Transient ischaemic attack (TIA) — treat as stroke",
        "Status epilepticus (prolonged or repeated seizures)",
        "Meningitis with altered consciousness",
        "Encephalitis",
        "Subarachnoid haemorrhage (thunderclap headache)",
        "Subdural haematoma",
        "Spinal cord injury with paralysis",
        "Brain herniation",
    ],
    "Respiratory": [
        "Complete airway obstruction / choking",
        "Respiratory arrest",
        "Acute severe asthma (not responding to inhaler)",
        "Tension pneumothorax",
        "Massive haemothorax",
        "Epiglottitis (adult or child unable to swallow/breathe)",
        "Acute respiratory distress syndrome (ARDS)",
        "Carbon monoxide poisoning",
    ],
    "Trauma": [
        "Uncontrolled haemorrhage / massive blood loss",
        "Penetrating chest or abdominal injury",
        "Open skull fracture",
        "Crush injury to chest or abdomen",
        "Traumatic amputation",
        "Spinal injury (do not move patient)",
        "High-energy trauma (motor vehicle accident, fall from height)",
        "Drowning / near-drowning",
        "Severe burns — > 20% body surface or face/airway burns",
        "Electrical injury from high voltage",
    ],
    "Toxicological": [
        "Drug overdose (opioids, benzodiazepines, paracetamol excess)",
        "Alcohol poisoning (unconscious, not rousable)",
        "Poisoning — ingested, inhaled, or injected toxin",
        "Snake bite with systemic symptoms",
        "Organophosphate poisoning (pesticide exposure)",
    ],
    "Obstetric / Gynaecological": [
        "Eclampsia (seizure in pregnancy)",
        "Placenta praevia with heavy bleeding",
        "Placental abruption",
        "Cord prolapse",
        "Uterine rupture",
        "Ectopic pregnancy with rupture",
        "Massive postpartum haemorrhage",
        "Amniotic fluid embolism",
    ],
    "Allergic / Immunological": [
        "Anaphylaxis (severe allergic reaction)",
        "Angio-oedema of the airway / tongue swelling blocking breathing",
        "Stevens-Johnson syndrome (skin peeling, mucous membrane involvement)",
        "Septic shock",
        "Toxic shock syndrome",
    ],
    "Paediatric": [
        "Febrile seizure (child, first time) — treat as critical until assessed",
        "Meningococcal disease (non-blanching rash + fever)",
        "Epiglottitis in a child",
        "Intussusception with peritonitis",
        "Neonatal sepsis",
        "Child with decreased consciousness",
        "Foreign body aspiration in an infant",
    ],
    "Mental Health / Self-Harm": [
        "Active suicidal intent with a plan",
        "Active self-harm (significant wound / blood loss)",
        "Overdose (intentional)",
        "Acute psychosis with risk to self or others",
    ],
    "Other": [
        "Diabetic ketoacidosis (DKA) with altered consciousness",
        "Hypoglycaemia with unconsciousness",
        "Heat stroke (core temp > 40°C, not sweating, confused)",
        "Hypothermia (core temp < 32°C)",
        "Sickle cell crisis with chest syndrome",
        "Acute liver failure",
        "Acute kidney failure with anuria",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# HIGH CONDITIONS — Go to emergency room or urgent care today (same day)
# ─────────────────────────────────────────────────────────────────────────────
HIGH_CONDITIONS: dict[str, list[str]] = {
    "Cardiovascular": [
        "Chest pain or pressure (not yet diagnosed as heart attack)",
        "Severe palpitations or irregular heartbeat",
        "Syncope (fainting) with chest pain",
        "Deep vein thrombosis (DVT) — swollen, painful, red leg",
        "Pulmonary embolism (mild) — shortness of breath, leg swelling",
        "Hypertensive urgency (BP > 180/120 without organ damage)",
        "Atrial fibrillation — first episode or rapid rate",
    ],
    "Neurological": [
        "Sudden severe headache ('worst headache of my life')",
        "New-onset facial drooping, arm weakness, or speech difficulty",
        "First-time seizure (adult)",
        "Bacterial meningitis (severe headache + stiff neck + fever)",
        "Sudden vision loss (one or both eyes)",
        "Sudden confusion or disorientation",
        "Weakness or paralysis of one side of the body",
        "Spinal cord compression — back pain + leg weakness/tingling",
    ],
    "Respiratory": [
        "Moderate-to-severe asthma attack (partially responding to inhaler)",
        "Pneumonia with high fever and difficulty breathing",
        "Pulmonary oedema (fluid in lungs, pink frothy sputum)",
        "Spontaneous pneumothorax (sudden chest pain + collapse)",
        "Croup in a child with significant stridor",
        "Haemoptysis (coughing up significant blood)",
        "Acute bronchospasm",
    ],
    "Trauma / Musculoskeletal": [
        "Fracture (broken bone) — any bone",
        "Open fracture (bone visible through skin)",
        "Dislocation — shoulder, knee, hip, elbow",
        "Torn ligament or tendon (ACL, Achilles, rotator cuff)",
        "Muscle separation or avulsion",
        "Severe sprain with inability to bear weight",
        "Deep laceration requiring stitches",
        "Significant wound that won't stop bleeding (>15 minutes pressure)",
        "Second-degree burn (> 5 cm) or any third-degree burn",
        "Severe head injury (loss of consciousness, confusion, vomiting)",
        "Eye trauma — chemical splash or penetrating injury",
        "Suspected internal injury (abdominal pain after trauma)",
    ],
    "Gastrointestinal": [
        "Appendicitis (severe right lower abdominal pain, fever, nausea)",
        "Acute cholecystitis (severe right upper abdominal pain after eating)",
        "Bowel obstruction (severe colicky abdominal pain, vomiting, no bowel movement)",
        "Diverticulitis with peritoneal signs",
        "Ruptured peptic ulcer (sudden severe abdominal pain)",
        "Acute pancreatitis (severe upper abdominal pain radiating to back)",
        "Rectal bleeding — significant or dark/tarry stools (melaena)",
        "Vomiting blood (haematemesis)",
    ],
    "Obstetric / Gynaecological": [
        "Ectopic pregnancy (lower abdominal pain in first trimester — rule out rupture)",
        "Severe pre-eclampsia (headache + visual changes + high BP in pregnancy)",
        "Preterm labour",
        "Abnormal vaginal bleeding in pregnancy",
        "Ovarian torsion (sudden severe pelvic pain)",
        "Testicular torsion (sudden severe scrotal pain)",
    ],
    "Infectious Disease": [
        "Sepsis (infection + high fever + confusion + rapid breathing)",
        "Necrotising fasciitis (rapidly spreading red/purple skin infection)",
        "Meningococcal disease (non-blanching purple rash + fever — call 10177)",
        "Rabies exposure (animal bite — wash immediately, go to hospital)",
        "Tetanus risk (deep or dirty wound, unvaccinated)",
        "Malaria with high fever in endemic area or recent travel",
    ],
    "Paediatric": [
        "High fever in infant < 3 months (any temp > 38°C)",
        "Febrile convulsion",
        "Child who is drowsy, difficult to rouse",
        "Breathing difficulty in a child — wheezing, grunting, nostril flaring",
        "Suspected meningitis in a child",
        "Child who is unable to swallow or drooling",
        "Severe dehydration in an infant or child",
        "Suspected child abuse / non-accidental injury",
    ],
    "Urological / Renal": [
        "Ureteric colic with stone (severe loin-to-groin pain)",
        "Acute urinary retention (cannot pass urine, painful bladder)",
        "Priapism (prolonged erection > 4 hours — medical emergency)",
        "Severe kidney infection (pyelonephritis) with high fever",
    ],
    "Ophthalmological": [
        "Acute angle-closure glaucoma (sudden eye pain, halos, nausea)",
        "Chemical burn to the eye",
        "Penetrating eye injury",
        "Sudden vision loss in one or both eyes",
        "Retinal detachment (flashes, floaters, shadow in vision)",
    ],
    "ENT": [
        "Severe throat infection with difficulty breathing or swallowing",
        "Peritonsillar abscess",
        "Sudden one-sided hearing loss",
        "Severe nose bleed that will not stop after 20 minutes",
        "Mastoiditis (swelling behind ear + fever)",
        "Foreign body in airway causing partial obstruction",
    ],
    "Mental Health": [
        "Suicidal ideation with a plan but no immediate act",
        "Severe manic episode with risk to self or others",
        "Severe alcohol or drug withdrawal (tremors, hallucinations)",
        "Acute psychotic break — disoriented and unpredictable",
    ],
    "Other": [
        "Diabetic ketoacidosis (DKA) — early, conscious",
        "Hypoglycaemia (low blood sugar) — conscious but confused",
        "Heat exhaustion (nearing heat stroke — stop exercise, cool down, rehydrate)",
        "Anaphylaxis — mild-moderate (no airway involvement yet)",
        "Sickle cell crisis (pain crisis without chest syndrome)",
        "Thyroid storm",
        "Adrenal crisis",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# MEDIUM CONDITIONS — See a doctor within 24–48 hours
# ─────────────────────────────────────────────────────────────────────────────
MEDIUM_CONDITIONS: dict[str, list[str]] = {
    "Cardiovascular": [
        "Mild-moderate palpitations (regular, no dizziness)",
        "Mild chest tightness without radiation",
        "Controlled hypertension — reading consistently above target",
        "Varicose veins with aching or swelling",
        "Mild oedema (ankle swelling)",
    ],
    "Neurological": [
        "Persistent or recurrent headache (not sudden onset)",
        "Migraine not responding to usual medication",
        "New or worsening dizziness or vertigo",
        "Facial numbness or tingling (new symptom)",
        "Memory problems or new confusion in an elderly patient",
        "Bell's palsy (sudden one-sided facial droop — needs same-day assessment)",
        "Carpal tunnel syndrome (wrist/hand numbness and tingling)",
        "Sciatica (shooting leg pain from lower back)",
    ],
    "Respiratory": [
        "Persistent cough (> 3 weeks)",
        "Mild-to-moderate asthma with controlled symptoms",
        "Shortness of breath on moderate exertion (new symptom)",
        "Productive cough with green or yellow phlegm",
        "Mild pneumonia in a healthy adult",
        "Pleurisy (sharp pain on breathing, no breathing difficulty)",
    ],
    "Gastrointestinal": [
        "Persistent nausea and vomiting (> 24 hours without improvement)",
        "Moderate abdominal pain — not severe, improving",
        "Diarrhoea > 48 hours or with blood",
        "Gastroenteritis with dehydration risk",
        "Heartburn / GERD not responding to antacids",
        "Suspected food poisoning with vomiting (stable)",
        "Unexplained weight loss (> 5 kg in 1 month)",
        "Change in bowel habits (new constipation or diarrhoea — 2+ weeks)",
        "Anal fissure or painful haemorrhoids",
    ],
    "Musculoskeletal": [
        "Moderate sprain or strain",
        "Back pain with limited mobility",
        "Muscle tear (partial) — painful but able to bear weight",
        "Tendinitis or bursitis",
        "Suspected hairline fracture",
        "Joint pain with swelling (no trauma — possible gout or arthritis)",
        "Mild to moderate sports injury",
    ],
    "Skin / Dermatological": [
        "Infected wound or wound not healing (redness, warmth, discharge)",
        "Cellulitis (spreading skin infection — red, warm, tender area)",
        "Moderate allergic skin reaction (rash, hives, swelling — not throat)",
        "Shingles (painful rash in a band pattern)",
        "Abscess requiring drainage",
        "Severe eczema or psoriasis flare",
        "Suspected skin infection (impetigo, folliculitis)",
        "Animal bite (not rabies risk area) — may need antibiotics",
    ],
    "Reproductive / Urological": [
        "Urinary tract infection (UTI) with fever",
        "Suspected sexually transmitted infection (STI)",
        "Vaginal infection with discharge and discomfort",
        "Menstrual irregularities (new or significant change)",
        "Moderate pelvic pain (not acute)",
        "Prostate symptoms worsening",
    ],
    "Ophthalmological": [
        "Conjunctivitis with significant discharge or pain",
        "Corneal abrasion (scratched eye)",
        "Eye infection not improving after 48 hours",
        "New floaters or mild flashes (needs urgent eye exam)",
    ],
    "ENT": [
        "Ear infection (otitis media) with significant pain",
        "Sinusitis with fever and face pain",
        "Tonsillitis — moderate throat pain, fever, difficulty swallowing",
        "Persistent ear pain or blocked ear",
        "Nosebleed — controlled but recurrent",
    ],
    "Mental Health": [
        "Moderate anxiety or panic attacks affecting daily life",
        "Moderate depression — persistent low mood for > 2 weeks",
        "Sleep disorder significantly affecting functioning",
        "Burnout or chronic stress affecting health",
        "Eating disorder — need assessment and monitoring",
    ],
    "Infectious Disease": [
        "Fever 38–39°C for > 48 hours without clear cause",
        "Viral illness not improving after 5–7 days",
        "Suspected COVID-19 or influenza in a high-risk individual",
        "Tuberculosis exposure or persistent productive cough",
        "Wound infection — increasing redness and pain",
        "Undiagnosed rash with fever",
    ],
    "Paediatric": [
        "Child fever 38–39°C lasting > 48 hours",
        "Child with persistent ear pain",
        "Persistent diarrhoea and vomiting in a child (mild dehydration)",
        "Child with a persistent cough > 2 weeks",
        "Suspected hand, foot, and mouth disease",
        "Throat infection in a child with difficulty swallowing",
    ],
    "Other": [
        "Newly diagnosed or uncontrolled diabetes (high blood sugar symptoms)",
        "Thyroid symptoms — unexplained weight gain/loss, fatigue, heat/cold intolerance",
        "Anaemia symptoms (fatigue, pale, breathless on exertion)",
        "Persistent fatigue with no clear cause",
        "Jaundice (yellow skin or eyes) — needs same-day assessment",
        "New lump or mass (needs assessment within 1–2 weeks)",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# LOW CONDITIONS — Monitor at home. Pharmacy/GP if no improvement.
# ─────────────────────────────────────────────────────────────────────────────
LOW_CONDITIONS: dict[str, list[str]] = {
    "General": [
        "Common cold (runny nose, mild sore throat, mild cough)",
        "Mild fever < 38.5°C in a healthy adult — monitor",
        "Mild fatigue or tiredness after illness",
        "Mild dehydration — increase fluid intake",
        "Jet lag or travel fatigue",
        "Mild insomnia (occasional, not chronic)",
    ],
    "Head / ENT": [
        "Mild tension headache",
        "Mild sinus congestion",
        "Minor earache without fever",
        "Mild ringing in the ears (occasional tinnitus)",
        "Motion sickness",
        "Blocked nose",
    ],
    "Respiratory": [
        "Mild dry cough without fever",
        "Mild sore throat — no difficulty swallowing, no fever",
        "Hay fever / allergic rhinitis",
        "Mild shortness of breath after unusual exertion (healthy person)",
        "Hiccups (prolonged > 48h should be checked)",
    ],
    "Gastrointestinal": [
        "Mild indigestion or heartburn (occasional)",
        "Mild nausea without vomiting",
        "Bloating or gas",
        "Mild constipation",
        "Mild diarrhoea < 24 hours without blood or fever (healthy adult)",
        "Mild food intolerance reaction",
    ],
    "Musculoskeletal": [
        "Mild muscle soreness after exercise (DOMS)",
        "Minor bruise",
        "Minor sprain — weight-bearing, no significant swelling",
        "Stiff neck after sleeping awkwardly",
        "Mild lower back ache",
        "Minor cut or scrape — controlled bleeding",
    ],
    "Skin": [
        "Minor rash without fever or spreading",
        "Mild sunburn (first-degree)",
        "Insect bite — local redness and itch only",
        "Dry skin or mild eczema",
        "Mild acne",
        "Minor allergic skin reaction — small area, no throat involvement",
    ],
    "Mental Health": [
        "Mild stress or anxiety — manageable, not affecting daily function",
        "Mild low mood — short duration, no suicidal thoughts",
        "Mild grief response",
        "Mild adjustment disorder",
    ],
    "Other": [
        "Well-controlled chronic conditions at routine visit",
        "Prescription refill for stable chronic medication",
        "Routine health check or blood pressure monitoring",
        "Mild urinary frequency without pain or fever",
        "Mild eye strain from screens",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Keyword lookup tables for _force_severity() in chat.py
# Flat lists used for fast `any(k in prompt for k in KEYWORDS_*)` checks
# ─────────────────────────────────────────────────────────────────────────────

CRITICAL_KEYWORDS: list[str] = [
    # Cardiac
    "heart attack", "cardiac arrest", "heart stopped", "no pulse",
    "ventricular fibrillation", "aortic dissection", "aortic rupture",
    # Neurological
    "stroke", "brain bleed", "thunderclap headache", "worst headache of my life",
    "seizure", "fitting", "convulsion", "unresponsive", "unconscious", "knocked out",
    "status epilepticus", "subdural", "subarachnoid",
    # Respiratory
    "can't breathe", "cannot breathe", "not breathing", "stopped breathing",
    "airway blocked", "choking", "respiratory arrest", "no air",
    "carbon monoxide", "co poisoning",
    # Trauma
    "massive bleeding", "uncontrolled bleeding", "arterial bleed",
    "bone through skin", "open skull", "skull fracture",
    "crush injury", "spinal injury", "traumatic amputation",
    "high-energy trauma", "hit by car", "fell from height",
    "electrocution", "high voltage",
    # Burns
    "airway burn", "face burn", "severe burn", "third degree burn", "80% burn",
    # Toxicological
    "overdose", "poisoning", "ingested poison", "snake bite",
    "organophosphate", "pesticide poisoning",
    # Allergic
    "anaphylaxis", "severe allergic reaction", "throat closing", "tongue swelling",
    "epipen", "epinephrine",
    # Obstetric
    "eclampsia", "placenta praevia", "placental abruption", "cord prolapse",
    "uterine rupture", "ectopic rupture", "postpartum haemorrhage",
    # Mental health
    "suicidal", "want to die", "end my life", "kill myself", "taking my life",
    "harming myself", "suicide attempt", "overdose on purpose",
    # Sepsis / shock
    "septic shock", "toxic shock", "organ failure",
    # Paediatric
    "child not breathing", "baby unresponsive", "infant not waking",
    "meningococcal", "non-blanching rash",
    # Other
    "heat stroke", "hypothermia", "diabetic coma", "dka unconscious",
    "liver failure", "kidney failure no urine",
]

HIGH_KEYWORDS: list[str] = [
    # Fractures / orthopaedic
    "broken bone", "broken", "fracture", "fractured", "compound fracture",
    "open fracture", "stress fracture", "hairline fracture",
    "dislocated", "dislocation", "popped out", "out of socket",
    "torn ligament", "torn tendon", "torn muscle", "torn acl", "torn mcl",
    "ruptured tendon", "ruptured achilles", "achilles tear",
    "separated shoulder", "acromioclavicular", "ac joint",
    "snapped", "bone snapped", "felt a pop", "heard a crack",
    "cannot move", "can't move", "unable to move", "won't move",
    "cannot walk", "can't walk", "unable to walk", "unable to bear weight",
    "numbness in arm", "numbness in leg", "numbness after injury",
    "paralysis", "paralyzed", "paralysed",
    # Bleeding / wounds
    "deep cut", "deep laceration", "gaping wound", "won't stop bleeding",
    "bleeding won't stop", "spurting blood", "arterial bleeding",
    "needs stitches",
    # Burns
    "second degree burn", "third degree", "blistering burn",
    "chemical burn", "acid burn",
    # Head injury
    "head injury", "hit head", "concussion", "knocked out",
    "loss of consciousness", "blacked out", "seeing double after",
    "vomited after head injury",
    # Abdominal emergency
    "appendicitis", "appendix pain", "appendix", "right side pain fever",
    "acute abdomen", "bowel obstruction", "twisted bowel",
    "vomiting blood", "coughing blood", "blood in vomit",
    "tarry stool", "melaena", "black stool with blood",
    "pancreatitis", "severe abdominal pain",
    # Chest
    "severe chest pain", "chest pressure", "crushing chest",
    "chest pain radiating", "pain in left arm", "jaw pain with chest",
    "rapid heart rate", "heart racing and dizzy",
    # Respiratory
    "asthma attack", "asthma not responding",
    "blue lips", "cyanosis", "coughing up blood",
    "difficulty breathing at rest",
    # Neurological
    "sudden vision loss", "sudden blindness", "face drooping",
    "arm weakness", "slurred speech", "facial droop",
    "sudden confusion", "sudden memory loss",
    "meningitis", "stiff neck with fever", "light sensitivity fever",
    "photophobia fever",
    # Infection / sepsis
    "spreading redness", "necrotising", "flesh eating",
    "infection spreading", "cellulitis spreading",
    "high fever", "fever above 39", "fever above 40", "fever over 39",
    "fever over 40", "fever 39", "fever 40",
    # Eye
    "eye injury", "chemical in eye", "acid in eye",
    "sudden vision", "seeing flashes suddenly", "shadow in vision",
    # Obstetric
    "ectopic pregnancy", "heavy bleeding pregnancy",
    "pre-eclampsia", "severe headache pregnancy",
    "testicular torsion", "ovarian torsion", "sudden groin pain",
    # Urological
    "cannot urinate", "can't urinate", "urinary retention",
    "priapism", "erection won't go down",
    # ENT
    "peritonsillar abscess", "unable to swallow",
    "tongue swelling", "lip swelling with breathing difficulty",
    # Paediatric
    "infant fever", "baby fever", "newborn fever",
    "child not waking", "child losing consciousness",
    "febrile convulsion", "child seizing",
]

MEDIUM_KEYWORDS: list[str] = [
    # Breathing — any mention is at minimum MEDIUM
    "breathing", "breath", "breathe", "inhale", "exhale", "respiratory",
    "shortness of breath", "short of breath", "breathless", "breathlessness",
    "difficulty breathing", "trouble breathing", "hard to breathe",
    "winded", "out of breath",
    "persistent cough", "cough for weeks", "coughing up phlegm",
    "yellow phlegm", "green phlegm", "productive cough",
    "shortness of breath when walking", "breathless on stairs",
    # Vision / sight — always needs a doctor
    "vision", "sight", "seeing", "eyesight",
    "blurry", "blurred", "double vision", "floaters", "flashes",
    "can't see", "cannot see", "trouble seeing", "difficulty seeing",
    # Head
    "persistent headache", "recurring headache", "migraine",
    "headache not going away", "headache for days",
    # Chest / heart
    "chest", "palpitation", "palpitations", "heart racing", "heart pounding",
    "irregular heartbeat", "heart flutter",
    # Neurological
    "dizzy", "dizziness", "vertigo", "fainting", "faint", "lightheaded",
    "numbness", "tingling", "weakness", "confusion", "memory loss",
    # Fever
    "fever", "high temperature",
    "fever two days", "fever 48 hours", "fever won't break", "fever and rash",
    # Serious pain
    "severe", "unbearable", "excruciating", "worst pain",
    # GI
    "nausea for days", "vomiting for 24 hours", "abdominal pain",
    "stomach pain", "diarrhoea and vomiting", "heartburn not improving",
    "weight loss unexplained",
    # Bleeding
    "blood in stool", "rectal bleeding", "blood in urine", "blood when urinating",
    "vomiting blood", "coughing blood",
    # Skin / infection
    "infection", "cellulitis", "infected wound", "wound not healing",
    "spreading rash", "shingles",
    # Swelling
    "swollen", "swelling",
    # Skin / eyes
    "rash with fever", "jaundice", "yellow skin", "yellow eyes",
    # Musculoskeletal
    "sprain swollen", "can't put weight on", "back pain severe",
    "muscle tear", "joint swollen",
    # Mental health
    "suicidal thoughts", "self harm", "self-harm", "depression",
    "panic attack", "panic attacks", "severe anxiety", "low mood weeks",
    # ENT
    "ear pain", "ear infection", "sinusitis", "tonsillitis",
    # Reproductive / urological
    "urinary infection fever", "uti fever", "pelvic pain",
    "vaginal discharge infection",
    # Paediatric
    "baby sick", "infant sick", "child fever",
    # Sudden onset — always worth checking
    "sudden", "suddenly",
    # Other
    "new lump", "new mass",
]


def get_severity_info(condition_name: str) -> str | None:
    """Look up a condition name and return its severity level.

    Case-insensitive partial match. Returns the first match found.
    Priority order: CRITICAL > HIGH > MEDIUM > LOW
    """
    cn = condition_name.lower()
    for cat, conditions in CRITICAL_CONDITIONS.items():
        for c in conditions:
            if cn in c.lower() or c.lower() in cn:
                return "CRITICAL"
    for cat, conditions in HIGH_CONDITIONS.items():
        for c in conditions:
            if cn in c.lower() or c.lower() in cn:
                return "HIGH"
    for cat, conditions in MEDIUM_CONDITIONS.items():
        for c in conditions:
            if cn in c.lower() or c.lower() in cn:
                return "MEDIUM"
    for cat, conditions in LOW_CONDITIONS.items():
        for c in conditions:
            if cn in c.lower() or c.lower() in cn:
                return "LOW"
    return None


def get_all_conditions() -> dict[str, dict[str, list[str]]]:
    """Return all conditions grouped by severity and body system."""
    return {
        "CRITICAL": CRITICAL_CONDITIONS,
        "HIGH": HIGH_CONDITIONS,
        "MEDIUM": MEDIUM_CONDITIONS,
        "LOW": LOW_CONDITIONS,
    }
