"""
seed_indore.py
Demo data for Indore, used by seed_data.py. Only data lives here, no logic.
All names, phones and addresses are made up.
"""

LOCALITIES = [
    "Vijay Nagar", "Palasia", "Bhawarkuan", "Sudama Nagar", "Rajwada", "Bengali Square", "Nipania",
    "Scheme No. 54", "Annapurna Road", "MR 10", "AB Road", "Sapna Sangeeta", "Khajrana", "LIG Colony",
    "Saket Nagar", "Rau", "Mahalaxmi Nagar", "Tilak Nagar", "Old Palasia", "Bicholi Mardana",
]

# name, email, phone, locality
CUSTOMERS = [
    ("Riya Jain", "riya@demo.com", "9827000101", "Vijay Nagar"),
    ("Aditya Sharma", "aditya@demo.com", "9827000102", "Palasia"),
    ("Pooja Malviya", "pooja@demo.com", "9827000103", "Bhawarkuan"),
    ("Harsh Agrawal", "harsh@demo.com", "9827000104", "Sudama Nagar"),
    ("Sakshi Patidar", "sakshi@demo.com", "9827000105", "Nipania"),
    ("Mohit Chouhan", "mohit@demo.com", "9827000106", "Scheme No. 54"),
    ("Nidhi Verma", "nidhi@demo.com", "9827000107", "Annapurna Road"),
    ("Rahul Tiwari", "rahult@demo.com", "9827000108", "MR 10"),
    ("Kritika Joshi", "kritika@demo.com", "9827000109", "Sapna Sangeeta"),
    ("Ankit Solanki", "ankit@demo.com", "9827000110", "Khajrana"),
    ("Shruti Dubey", "shruti@demo.com", "9827000111", "LIG Colony"),
    ("Yash Rathore", "yash@demo.com", "9827000112", "Saket Nagar"),
    ("Megha Khandelwal", "megha@demo.com", "9827000113", "Mahalaxmi Nagar"),
    ("Deepak Yadav", "deepak@demo.com", "9827000114", "Rau"),
    ("Tanvi Gupta", "tanvi@demo.com", "9827000115", "Tilak Nagar"),
    ("Saurabh Mishra", "saurabh@demo.com", "9827000116", "Old Palasia"),
    ("Isha Parmar", "isha@demo.com", "9827000117", "Bicholi Mardana"),
    ("Vivek Bansal", "vivek@demo.com", "9827000118", "Bengali Square"),
    ("Aakriti Soni", "aakriti@demo.com", "9827000119", "AB Road"),
    ("Kunal Saxena", "kunal@demo.com", "9827000120", "Rajwada"),
]

# name, email, phone, experience, bio, status, {service: charge}, quality (typical star rating)
PROVIDERS = [
    ("Malwa Plumbers", "malwa@demo.com", "9827111001", 9, "Trusted plumbers across Indore, same-day visits.",
     "verified", {"Plumbing": 299, "Carpentry": 349}, 4.7),
    ("Sharma Plumbing Services", "sharmaplumb@demo.com", "9827111002", 15, "15 years of leak, drain and fitting work.",
     "verified", {"Plumbing": 349}, 4.3),
    ("Quick Fix Plumbers", "quickfix@demo.com", "9827111003", 3, "Budget plumbing, quick response.",
     "verified", {"Plumbing": 229}, 3.6),
    ("Rajwada Sanitary Works", "rajwada@demo.com", "9827111004", 7, "Bathroom fittings, tanks and pipelines.",
     "verified", {"Plumbing": 279}, 4.0),
    ("Indore Electric Care", "indoreelec@demo.com", "9827111005", 6, "Wiring, fans and appliance repair.",
     "verified", {"Electrical Repair": 249, "Appliance Repair": 329}, 3.9),
    ("PowerLine Electricians", "powerline@demo.com", "9827111006", 12, "Licensed electricians, MCB and full-house wiring.",
     "verified", {"Electrical Repair": 299}, 4.6),
    ("Vijay Electricals", "vijayelec@demo.com", "9827111007", 2, "Affordable switch, fan and light fixes.",
     "verified", {"Electrical Repair": 199}, 3.4),
    ("ChillZone AC", "chillzone@demo.com", "9827111008", 11, "Split and window AC experts.",
     "verified", {"AC Repair and Maintenance": 499}, 4.4),
    ("CoolBreeze Indore", "coolbreeze@demo.com", "9827111009", 5, "AC service, gas refill and installation.",
     "verified", {"AC Repair and Maintenance": 449, "Appliance Repair": 349}, 4.1),
    ("Arctic AC Care", "arctic@demo.com", "9827111010", 8, "Inverter AC specialists. Currently on leave.",
     "verified", {"AC Repair and Maintenance": 529}, 3.5),
    ("CleanNest Indore", "cleannest@demo.com", "9827111011", 4, "Deep cleaning and pest control.",
     "verified", {"Home Cleaning": 749, "Pest Control": 649}, 4.2),
    ("ShineHome Cleaning", "shinehome@demo.com", "9827111012", 6, "Kitchen, bathroom and sofa deep cleaning.",
     "verified", {"Home Cleaning": 849}, 4.6),
    ("Sparkle Indore", "sparkleindore@demo.com", "9827111013", 2, "Affordable full-home cleaning.",
     "verified", {"Home Cleaning": 699}, 3.7),
    ("FixIt Appliances", "fixit@demo.com", "9827111014", 10, "Washing machine, fridge and microwave repair.",
     "verified", {"Appliance Repair": 379}, 4.5),
    ("Holkar Home Appliances", "holkar@demo.com", "9827111015", 7, "Geyser, RO and chimney service.",
     "verified", {"Appliance Repair": 319}, 3.9),
    ("Rang Mahal Painters", "rangmahal@demo.com", "9827111016", 14, "Premium interior, texture and exterior painting.",
     "verified", {"Painting": 1699}, 4.7),
    ("Malwa Colours", "malwacolours@demo.com", "9827111017", 6, "Wall painting and waterproofing.",
     "verified", {"Painting": 1399}, 4.0),
    ("Brush and Roll", "brushroll@demo.com", "9827111018", 3, "Budget painting and touch-ups.",
     "verified", {"Painting": 1199}, 3.6),
    ("WoodCraft Indore", "woodcraft@demo.com", "9827111019", 13, "Custom furniture, wardrobes and repairs.",
     "verified", {"Carpentry": 399}, 4.5),
    ("Ahilya Furniture Works", "ahilya@demo.com", "9827111020", 5, "Door, window and furniture fixing.",
     "verified", {"Carpentry": 299}, 3.8),
    ("PestAway Indore", "pestaway@demo.com", "9827111021", 9, "Cockroach, termite and bed bug treatment.",
     "verified", {"Pest Control": 699}, 4.4),
    ("Termite Shield", "termiteshield@demo.com", "9827111022", 12, "Anti-termite specialists with warranty.",
     "verified", {"Pest Control": 799}, 4.1),
    ("Nayi Soch Services", "nayisoch@demo.com", "9827111023", 1, "New multi-service team, awaiting verification.",
     "pending", {"Plumbing": 199, "Electrical Repair": 179}, 3.5),
    ("Shiv Shakti Repairs", "shivshakti@demo.com", "9827111024", 4, "Appliance repairs, awaiting verification.",
     "pending", {"Appliance Repair": 279}, 3.5),
    ("Unverified Repairs", "unverified@demo.com", "9827111025", 0, "Documents did not match.",
     "rejected", {"Carpentry": 149}, 3.0),
]

UNAVAILABLE = {"arctic@demo.com"}      # verified but switched off availability

PROBLEMS = {
    "Plumbing": ["Kitchen tap is leaking non-stop.", "Bathroom drain is blocked, water not going down.",
                 "Flush tank is not filling.", "Overhead tank is overflowing.", "Pipe under the wash basin is leaking.",
                 "Low water pressure in the shower."],
    "Electrical Repair": ["Ceiling fan stopped working.", "MCB keeps tripping at night.", "Switchboard is sparking.",
                          "Lights flicker in the hall.", "No power in the bedroom sockets.", "Need a new fan installed."],
    "AC Repair and Maintenance": ["AC is not cooling properly.", "Water dripping from the indoor unit.",
                                  "Need AC service before summer.", "AC making loud noise.", "Gas refill needed."],
    "Home Cleaning": ["Full home deep cleaning before Diwali.", "Kitchen is very greasy, need deep clean.",
                      "Bathroom tiles need cleaning.", "Sofa and carpet shampoo.", "Moving into a new flat, need cleaning."],
    "Appliance Repair": ["Washing machine not spinning.", "Fridge not cooling.", "Geyser not heating water.",
                         "Microwave not heating.", "RO purifier leaking."],
    "Painting": ["Paint 2BHK flat before shifting.", "Damp patches on the bedroom wall.", "Texture paint on living room wall.",
                 "Exterior painting of the house.", "Terrace waterproofing needed."],
    "Carpentry": ["Wardrobe hinge broken.", "Main door not closing properly.", "Need a new TV unit made.",
                  "Bed is creaking and loose.", "Kitchen cabinet door came off."],
    "Pest Control": ["Too many cockroaches in the kitchen.", "Termites in the wooden door.", "Bed bugs in the bedroom.",
                     "Ants everywhere in the kitchen.", "Mosquito problem after the rains."],
}

# Review comments grouped by star rating
REVIEWS = {
    5: ["Excellent service, very professional and on time. Highly recommended!",
        "Superb work, fixed everything in one visit. Will book again.",
        "Very polite and skilled. Cleaned up after the work too.",
        "Best service in Indore, very happy with the work.",
        "Great experience, reasonable price and quick work."],
    4: ["Very good service, came on time and did neat work.",
        "Good work overall, the problem is solved.",
        "Happy with the service, price was fair.",
        "Nice and polite technician, did a good job."],
    3: ["Service was okay. Came a little late but did the job.",
        "Average experience, work is done but took long.",
        "It was fine, nothing special.",
        "Okay work, price was a bit high."],
    2: ["Not happy. The technician came very late.",
        "Work quality was not good, had to call again.",
        "Not satisfied, charged more than the estimate."],
    1: ["Very bad experience. He was rude and did not fix the problem.",
        "Worst service, did not show up on time and work was poor.",
        "Terrible, the problem came back the next day. Not recommended."],
}

# Sample problem texts typed into the AI suggestion box (for admin AI stats)
AI_QUERIES = [
    "kitchen tap leaking since morning", "fan is not running", "AC not cooling in this heat",
    "need deep cleaning of my flat", "washing machine not spinning", "want to paint my house before Diwali",
    "door hinge is broken", "cockroaches everywhere in kitchen", "MCB tripping again and again",
    "water dripping from AC", "fridge stopped cooling", "termites in the wardrobe", "bathroom drain blocked",
    "geyser not giving hot water", "sofa needs cleaning", "damp patches on wall", "switch board sparking",
    "bed bugs in bedroom", "need new TV unit", "flush not working",
]
