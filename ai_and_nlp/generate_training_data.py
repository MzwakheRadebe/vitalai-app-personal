"""
generate_training_data.py
=========================
Generates triage_enhanced.csv — synthetic training examples covering
all major medical conditions across 4 severity levels.

Run once:  python generate_training_data.py
Output  :  triage_enhanced.csv  (merged with triage2.csv automatically)

The ML model (non_final_draft.py) will pick up the merged file on next start.
"""

import csv
import os
import random

# ─────────────────────────────────────────────────────────────────────────────
# TRAINING EXAMPLES
# Each tuple: ("symptom description the user might type", "SEVERITY")
# Multiple phrasings per condition — the SentenceTransformer handles synonyms,
# but diversity helps the LogisticRegression boundary learn correctly.
# ─────────────────────────────────────────────────────────────────────────────

TRAINING_DATA = []

# ══════════════════════════════════════════════════════════════════
# CRITICAL — life-threatening
# ══════════════════════════════════════════════════════════════════
CRITICAL_EXAMPLES = [
    # Cardiac
    "I think I'm having a heart attack, crushing chest pain spreading to my left arm",
    "Severe chest pain, my left arm is numb and I'm sweating",
    "My heart stopped, I can't feel a pulse",
    "Cardiac arrest, person is unresponsive",
    "Aortic dissection, sudden tearing chest pain radiating to back",
    "My blood pressure is 210/130 and I have a splitting headache",
    "Chest pain so severe I can't breathe, spreading to my jaw",
    "I think I'm having a massive heart attack",
    "Sudden severe chest pressure with shortness of breath and sweating",
    "My husband collapsed, he's not breathing and has no pulse",

    # Stroke
    "I think I'm having a stroke, my face is drooping and I can't speak",
    "Sudden face drooping, arm weakness, and slurred speech",
    "I woke up and can't move my right side at all",
    "Sudden vision loss in both eyes and I feel very confused",
    "Thunderclap headache, worst headache of my life, started suddenly",
    "Sudden paralysis on one side of my body",
    "My speech is slurred suddenly and one arm won't move",
    "Brain bleed symptoms, sudden severe headache and confusion",
    "I had a stroke, I can't lift my arm and my face is drooping",

    # Seizure / unconscious
    "My child is having a seizure and won't stop",
    "Status epilepticus, seizure lasting more than 5 minutes",
    "She's fitting and not responding",
    "He's unconscious and not waking up",
    "Patient is unresponsive, can't be roused",
    "My son fell and is unconscious, won't wake up",
    "Seizure followed by unconsciousness",
    "Convulsions and not breathing properly",

    # Respiratory arrest
    "I can't breathe at all, airway is blocked",
    "He's choking and can't get air",
    "Not breathing, respiratory arrest",
    "Airways completely blocked, she's turning blue",
    "Carbon monoxide poisoning, entire family collapsed",
    "Severe anaphylaxis, throat is closing, can't breathe",
    "My throat is swelling shut after eating peanuts",
    "Anaphylactic shock, epipen used but still struggling to breathe",
    "Severe allergic reaction, tongue and throat swelling",

    # Overdose / poisoning
    "I took an overdose of pills, I'm drowsy",
    "Drug overdose, he took everything in the cabinet",
    "She overdosed on purpose and is barely conscious",
    "Opioid overdose, he's not responsive and breathing slowly",
    "Alcohol poisoning, she drank a whole bottle and passed out",
    "Organophosphate poisoning after working with pesticides",
    "Ingested poison, don't know what",
    "Snake bite with spreading swelling and vomiting",

    # Bleeding / trauma
    "Uncontrolled bleeding, blood won't stop",
    "Arterial bleed, blood spurting with each heartbeat",
    "Penetrating chest wound from a knife",
    "Stab wound to the abdomen",
    "Open skull fracture after fall",
    "High energy trauma, hit by a car at speed",
    "Fell from a second floor roof",
    "Traumatic amputation of the hand",
    "Crush injury to the chest after accident",
    "Vomiting large amounts of blood repeatedly",
    "Coughing up blood in large quantities",
    "Internal bleeding after abdominal trauma",

    # Obstetric
    "Eclampsia seizure during pregnancy",
    "Heavy vaginal bleeding, placenta praevia",
    "Cord prolapse, baby's cord is outside",
    "Ruptured ectopic pregnancy, severe pain and shoulder tip pain",
    "Massive postpartum haemorrhage after delivery",
    "My pregnant wife is having a seizure",

    # Mental health crisis
    "I am actively suicidal with a plan",
    "I took pills to end my life",
    "I'm going to kill myself tonight",
    "I've already hurt myself badly and there's a lot of blood",
    "I want to die and I have the means to do it",

    # Septic shock / meningitis
    "Septic shock, BP is crashing and very confused",
    "Meningococcal rash, non-blanching purple spots with high fever",
    "Meningitis, stiff neck high fever and rash that doesn't fade",
    "Toxic shock syndrome after surgery",

    # Heat / hypothermia
    "Heat stroke, no longer sweating, very confused and hot",
    "Severe hypothermia, core temperature below 30",
    "Diabetic coma, found unconscious with sugar meter reading high",
    "DKA unconscious, breathing like Kussmaul",
]

# ══════════════════════════════════════════════════════════════════
# HIGH — urgent, go to emergency same day
# ══════════════════════════════════════════════════════════════════
HIGH_EXAMPLES = [
    # Fractures / dislocations
    "I broke my leg, I can hear it cracked",
    "Broken arm after falling off a bicycle",
    "I fractured my wrist when I fell",
    "My collarbone is broken after the accident",
    "Compound fracture, bone is visible through the skin",
    "Open fracture on my forearm",
    "I dislocated my shoulder in rugby",
    "My knee is dislocated, it looks completely out of place",
    "Hip dislocation after a car accident",
    "Dislocated elbow playing sport",
    "Torn ACL in my knee, felt a pop and can't put weight on it",
    "I tore my Achilles tendon while running, heard a snap",
    "Ruptured tendon in my ankle",
    "Torn rotator cuff, shoulder is in severe pain",
    "Separated shoulder after falling on my arm",
    "I broke my toe, it's very swollen and bent",
    "Fractured ribs after the fall",
    "Hairline fracture in my foot",
    "I think I've broken my finger, it's swollen and I can't move it",
    "I fractured my ankle and can't walk",
    "My bone snapped, I heard it break",
    "Felt a pop in my knee and can't straighten it",
    "Can't move my arm after the accident",
    "Unable to walk after landing badly on my ankle",

    # Severe bleeding / wounds
    "Deep laceration that won't stop bleeding after 20 minutes",
    "Bleeding won't stop from a deep cut",
    "Gaping wound on my leg that needs stitches",
    "Deep knife cut on my hand",
    "Wound too deep for home care, still bleeding",

    # Burns
    "Second degree burn from boiling water, blistering all over arm",
    "Severe burn from fire, large area affected",
    "Third degree burn, skin looks white and leathery",
    "Chemical burn on my skin from cleaning products",
    "Acid burn on my arm at work",

    # Head injury
    "Head injury from a fall, lost consciousness briefly",
    "Concussion, hit my head and was confused",
    "Severe head injury after car accident",
    "Knocked out and woke up confused",
    "Vomited twice after hitting my head",

    # Chest pain / cardiac
    "Severe chest pain that comes and goes with exertion",
    "Chest pressure with shortness of breath",
    "Palpitations and dizziness",
    "Heart racing and I feel faint",
    "New onset atrial fibrillation",
    "DVT suspected, calf is red, swollen and painful",
    "Pulmonary embolism suspected, shortness of breath and leg swelling",
    "Blood pressure 180 over 110, severe headache",

    # Respiratory
    "Asthma attack not responding to inhaler",
    "Severe asthma, can barely speak",
    "Coughing up blood repeatedly",
    "Difficulty breathing at rest",
    "Pneumonia with high fever and difficulty breathing",
    "Spontaneous pneumothorax, sudden chest pain and collapse",
    "Blue lips from lack of oxygen",

    # Neurological
    "Sudden severe headache unlike any before",
    "Sudden loss of vision in my left eye",
    "New facial drooping on the right side",
    "Sudden arm weakness and numbness",
    "Bacterial meningitis, stiff neck and fever and sensitivity to light",
    "Stiff neck with high fever and headache",
    "Sudden confusion in an elderly person",
    "First time seizure in an adult",
    "Back pain with weakness in both legs, can't walk properly",
    "Spinal cord injury, numbness from chest down",

    # Abdominal emergency
    "Appendicitis, severe pain in lower right abdomen with fever",
    "Appendix pain, can't move without severe pain",
    "Right lower abdominal pain with fever and nausea",
    "Vomiting blood, haematemesis",
    "Dark tarry stools, melaena",
    "Black stools and feeling faint",
    "Acute pancreatitis, severe upper abdominal pain going to back",
    "Bowel obstruction, severe cramping and no bowel movement for 3 days",
    "Severe abdominal pain after eating, cholecystitis",
    "Upper right abdominal pain after fatty meal with fever",

    # Obstetric
    "Ectopic pregnancy, severe one-sided pain at 7 weeks",
    "Severe pre-eclampsia symptoms, headache and visual changes",
    "Ovarian torsion, sudden severe pelvic pain",
    "Testicular torsion, sudden severe scrotal pain",
    "Preterm labour at 30 weeks",
    "Heavy bleeding in pregnancy",

    # Serious infection
    "Sepsis, high fever and confused and fast breathing",
    "Necrotising fasciitis, rapidly spreading infection with purple skin",
    "Malaria with very high fever after travel to endemic area",
    "Rabies exposure from an animal bite",

    # Eye
    "Acute glaucoma, sudden eye pain with halos around lights",
    "Chemical splash in the eye at work",
    "Penetrating eye injury",
    "Sudden vision loss in one eye",
    "Retinal detachment, seeing flashes and a shadow in vision",

    # ENT
    "Peritonsillar abscess, can't swallow and throat very swollen",
    "Severe croup in child with significant stridor",
    "Foreign body stuck in airway, partial blockage",
    "Severe nosebleed won't stop after 30 minutes",

    # Urological
    "Kidney stone, severe loin to groin pain",
    "Urinary retention, can't pass urine and bladder full and painful",
    "Priapism, erection for 5 hours and very painful",
    "Severe kidney infection with high fever and back pain",

    # Paediatric
    "Infant fever over 38 degrees, baby is 2 months old",
    "Baby has a fever and is very floppy and difficult to rouse",
    "Child with stiff neck and fever",
    "Febrile convulsion in my toddler",
    "Child is drowsy and can't be properly woken up",
    "Breathing difficulty in a child with stridor and grunting",

    # High fever
    "High fever above 39 degrees for two days",
    "Fever of 40 degrees celsius",
    "Fever over 40 and very confused",

    # Mental health urgent
    "Suicidal thoughts with a specific plan",
    "Severe manic episode putting herself in danger",
    "Alcohol withdrawal with shaking and hallucinations",
    "Acute psychosis, violent and disoriented",
]

# ══════════════════════════════════════════════════════════════════
# MEDIUM — see a doctor within 24–48 hours
# ══════════════════════════════════════════════════════════════════
MEDIUM_EXAMPLES = [
    # Head
    "I've had a persistent headache for 3 days",
    "Migraine that isn't responding to my usual tablets",
    "Recurring headaches for a week now",
    "Headache getting worse over two days",
    "I've been dizzy for 24 hours",
    "Severe vertigo when I move my head",
    "Facial numbness on one side — new symptom",
    "Bell's palsy, one side of my face drooped this morning",
    "Carpal tunnel, hand and wrist very numb at night",
    "Sciatica, shooting pain from my lower back down my leg",
    "Memory confusion in my elderly father that's new",

    # Respiratory
    "Persistent cough for 3 weeks now",
    "Cough with yellow and green phlegm for several days",
    "Shortness of breath when walking upstairs, new symptom",
    "Productive cough with thick mucus for a week",
    "Mild pneumonia, stable but need treatment",
    "Pleurisy, sharp stabbing pain every time I breathe",
    "Asthma symptoms getting worse this week",

    # Chest / cardiovascular
    "Mild chest tightness on exertion",
    "Persistent palpitations for the past 2 days",
    "My blood pressure has been consistently high all week",
    "Swollen ankles that have been getting worse",
    "Calf pain and swelling, worried about DVT",

    # Gastrointestinal
    "Nausea and vomiting for 24 hours straight",
    "Persistent stomach pain that comes and goes",
    "Diarrhoea and vomiting for 2 days",
    "Blood in my stool this morning",
    "Black stool without fresh blood",
    "Heartburn not improving despite antacids",
    "Stomach pain spreading across abdomen, no fever",
    "I've lost 6kg without trying in the last month",
    "Change in bowel habits for 3 weeks",
    "Severe abdominal cramps with diarrhoea",
    "Food poisoning, vomiting all day but still conscious",
    "Abdominal pain not severe but persistent for two days",

    # Musculoskeletal
    "Moderate sprain, ankle swollen and painful but can walk a little",
    "Suspected hairline fracture in my foot",
    "Back pain limiting my movement",
    "Severe muscle strain, can't straighten my back",
    "Joint swelling in my knee with no injury, possibly gout",
    "Tendinitis in my shoulder, very painful for a week",

    # Skin
    "Infected wound with spreading redness and warmth",
    "Wound not healing after 5 days, getting worse",
    "Cellulitis spreading up my arm",
    "Shingles, blistering rash on one side of my body",
    "Abscess that needs draining",
    "Severe eczema flare across my body",
    "Impetigo spreading on my child's face",
    "Animal bite that might need antibiotics",

    # Fever
    "Fever of 38.5 for two days without improvement",
    "Fever won't break after 48 hours",
    "Fever and rash together",
    "Undiagnosed rash with mild fever",
    "Viral illness not improving after 6 days",

    # Eye
    "Eye very red with discharge for 2 days",
    "Corneal scratch from a branch",
    "Conjunctivitis not improving after 48 hours",
    "New floaters and occasional flashes in my vision",

    # Ear / ENT
    "Ear infection with significant pain and mild fever",
    "Sinusitis with face pain and fever",
    "Tonsillitis, sore throat and fever and difficulty swallowing",
    "Ear blocked and painful for several days",
    "Recurrent nosebleeds this week",
    "Sudden hearing loss in one ear this morning",

    # Reproductive / urological
    "UTI with fever and back pain",
    "Urinary tract infection not improving with fluids",
    "Pelvic pain for 2 days",
    "Painful vaginal discharge with fever",
    "Symptoms of sexually transmitted infection",

    # Mental health
    "Panic attacks every day affecting my work",
    "Severe depression, can't get out of bed for 2 weeks",
    "Anxiety so bad I can't leave the house",
    "Not sleeping for days, it's affecting my health",

    # Paediatric
    "Child fever 38.5 for more than 48 hours",
    "Persistent ear pain in my child",
    "Toddler with diarrhoea and vomiting for 2 days, mild dehydration",
    "Child has been coughing for 3 weeks",
    "My daughter has tonsillitis and can't swallow",

    # Other
    "Jaundice, my skin and eyes are yellow",
    "New lump under my arm that appeared last week",
    "Extreme fatigue with no explanation for weeks",
    "Blood sugar consistently high, possible uncontrolled diabetes",
    "Thyroid symptoms, rapid unexplained weight loss",
    "Anaemia symptoms, very pale and breathless walking upstairs",
]

# ══════════════════════════════════════════════════════════════════
# LOW — monitor at home, pharmacy or GP if no improvement
# ══════════════════════════════════════════════════════════════════
LOW_EXAMPLES = [
    # Head
    "I have a mild headache today",
    "Slight tension headache at the back of my head",
    "Minor headache after looking at a screen all day",
    "I feel a little dizzy after standing up quickly",
    "Mild blocked nose",
    "Slight sinus congestion",
    "Minor earache without fever",
    "Occasional ringing in my ears",
    "Motion sickness on the bus",

    # Respiratory
    "Mild dry cough, no fever",
    "Common cold, runny nose and mild sore throat",
    "Hay fever, itchy eyes and runny nose",
    "Mild sore throat, no difficulty swallowing",
    "Scratchy throat in the morning",
    "Mild congestion and sneezing",

    # Fever
    "Low grade fever under 38, feeling tired",
    "Mild temperature of 37.5",
    "Feeling warm but no thermometer reading",

    # Gastrointestinal
    "Mild indigestion after a heavy meal",
    "Slight nausea this morning, no vomiting",
    "Bloating and gas after eating",
    "Mild constipation for one day",
    "Mild diarrhoea this morning, no blood, feeling okay",
    "Minor stomach discomfort after eating",
    "Heartburn after spicy food",

    # Musculoskeletal
    "Sore muscles after gym yesterday",
    "Minor bruise on my shin",
    "Small cut on my finger, bleeding stopped",
    "Stiff neck from sleeping awkwardly",
    "Mild lower back ache at end of day",
    "Minor sprain, can still walk, mild swelling",
    "Slight ankle twist, no swelling",
    "Light muscle cramp in my calf",

    # Skin
    "Small rash on my wrist, no fever, mild itch",
    "Dry skin on my hands and arms",
    "Minor insect bite, small red area and itch only",
    "Mild sunburn on my shoulders",
    "Minor skin irritation from soap",
    "Small pimple or spot",
    "Mild eczema on my elbow",

    # Eye
    "Mild eye strain after working on computer all day",
    "Dry eyes from air conditioning",
    "Minor eye irritation from dust",

    # Ear
    "Slight blocked ear after flying",
    "Mild ear discomfort, no pain",

    # Urinary
    "Going to the toilet slightly more than usual",
    "Mild bladder pressure, drinking more water",

    # Mental health
    "Feeling a bit stressed about work",
    "Mild anxiety before an exam",
    "Feeling a little low after a difficult week",

    # General
    "Feeling tired today",
    "Mild fatigue after being ill last week",
    "Feeling a bit run down",
    "Thirsty and slightly dehydrated",
    "Jet lag after long flight",
    "Slight loss of appetite",

    # Appointment / routine
    "I would like to book an appointment",
    "I need to schedule a check-up",
    "I want to see a doctor for a routine visit",
    "Can I book an appointment at the clinic",
    "I need a prescription refill",
    "Just need a general health check",
    "I would like to schedule a follow-up",
]

# ─────────────────────────────────────────────────────────────────────────────
# Build the dataset
# ─────────────────────────────────────────────────────────────────────────────

def build_dataset():
    rows = []
    for text in CRITICAL_EXAMPLES:
        rows.append((text.strip(), "CRITICAL"))
    for text in HIGH_EXAMPLES:
        rows.append((text.strip(), "HIGH"))
    for text in MEDIUM_EXAMPLES:
        rows.append((text.strip(), "MEDIUM"))
    for text in LOW_EXAMPLES:
        rows.append((text.strip(), "LOW"))

    random.seed(42)
    random.shuffle(rows)
    return rows


def load_existing_csv(path: str) -> list[tuple[str, str]]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text", "").strip()
            severity = row.get("severity", "").strip().upper()
            if text and severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                rows.append((text, severity))
    return rows


def write_csv(path: str, rows: list[tuple[str, str]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["text", "severity"])
        for text, severity in rows:
            writer.writerow([text, severity])
    print(f"Written {len(rows)} rows to {path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    original_csv = os.path.join(base_dir, "triage2.csv")
    enhanced_csv = os.path.join(base_dir, "triage_enhanced.csv")
    merged_csv   = os.path.join(base_dir, "triage_merged.csv")

    print("Loading original training data...")
    original_rows = load_existing_csv(original_csv)
    print(f"   Original rows: {len(original_rows)}")

    print("Generating new training examples...")
    new_rows = build_dataset()
    print(f"   New examples: {len(new_rows)}")
    write_csv(enhanced_csv, new_rows)

    print("Merging datasets...")
    # Deduplicate by text (case-insensitive)
    seen = set()
    merged = []
    for text, severity in original_rows + new_rows:
        key = text.lower()
        if key not in seen:
            seen.add(key)
            merged.append((text, severity))

    random.seed(42)
    random.shuffle(merged)
    write_csv(merged_csv, merged)

    # Count per severity
    from collections import Counter
    counts = Counter(s for _, s in merged)
    print("\nMerged dataset breakdown:")
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        print(f"   {level:8s}: {counts.get(level, 0)} examples")
    print(f"   {'TOTAL':8s}: {len(merged)} examples")

    print("\nDone! The ML model will use triage_merged.csv on next start.")
    print("Delete severity_classifier.joblib and embedder_model/ to force retrain.")
