"""
[V33.6 GOD MODE] Technical Tag Library
The ultimate vocabulary for high-dimensional semantic audio analysis.
"""

# --------------------------------------------------------------------------
# 1. GENRES (Discogs 400+ Standard)
# --------------------------------------------------------------------------
GENRES_DISCOGS_400 = [
    "Abstract", "Acid", "Acid House", "Acid Jazz", "Acoustic", "African", "Afro-Cuban", "Afrobeat", "Alternative Rock", "Ambient", 
    "Anarcho-punk", "Andean Music", "AOR", "Apache", "Apala", "Appalachian Music", "Arabesque", "Arabic", "Arena Rock", "Armenian", 
    "Art Rock", "Avant-garde", "Avant-garde Jazz", "Avant-garde Metal", "Axe", "Bachata", "Bakersfield Sound", "Ballad", "Ballroom", 
    "Baltimore Club", "Bambuco", "Banda", "Baroque", "Baroque Pop", "Bass Music", "Bebop", "Begeisterung", "Bengali Music", "Bhangra", 
    "Big Band", "Big Beat", "Black Metal", "Bluegrass", "Blues", "Blues Rock", "Bolero", "Bongo Flava", "Boogie", "Boogie-Woogie", 
    "Bop", "Bossa Nova", "Bounce", "Breakbeat", "Breakcore", "Breaks", "Brit Pop", "Broken Beat", "Bubbling", "Burmese Music", 
    "Cajun", "Calypso", "Canterbury Scene", "Canzone Napoletana", "Cape Jazz", "Capoeira", "Celtic", "Chachacha", "Chakalaka", 
    "Chamber Jazz", "Chambeta", "Champeta", "Chanson", "Charanga", "Chicago Blues", "Children's", "Chillout", "Chiptune", "Choral", 
    "Christian", "Cine", "City Pop", "Classic Metal", "Classic Rock", "Classical", "Coldwave", "Comedy", "Compas", "Conjunto", 
    "Contemporary", "Contemporary Jazz", "Contemporary R&B", "Copla", "Corrido", "Country", "Country Blues", "Country Rock", 
    "Crust", "Cuarteto", "Cumbia", "Dance-pop", "Dancehall", "Dark Ambient", "Dark Wave", "Death Metal", "Deathcore", "Deep House", 
    "Deep Techno", "Delta Blues", "Descarga", "Desert Rock", "Digital", "Disco", "Dixieland", "DJ Battle Tool", "Donk", "Doo Wop", 
    "Doom Metal", "Downtempo", "Dream Pop", "Drill", "Drone", "Drum n Bass", "Dub", "Dub Techno", "Dubstep", "Early Music", 
    "East Coast Hip Hop", "Easy Listening", "EBM", "Educational", "Electric Blues", "Electro", "Electro House", "Electronic", 
    "Experimental", "Fado", "Field Recording", "Flamenco", "Folclore", "Folk", "Folk Metal", "Folk Rock", "Free Improvisation", 
    "Free Jazz", "Freestyle", "Funk", "Funk Metal", "Fusion", "Future Jazz", "FuturePop", "Gabber", "Garage House", "Garage Rock", 
    "Ghetto", "Ghetto House", "Ghetto Techno", "Gille", "Glam", "Glitch", "Goa Trance", "Gospel", "Goth Rock", "Grime", "Grindcore", 
    "Grunge", "Guaguancó", "Guitarrada", "Gypsy Jazz", "Hands Up", "Happy Hardcore", "Hard Bop", "Hard House", "Hard Rock", 
    "Hard Techno", "Hard Trance", "Hardcore", "Hardcore Hip Hop", "Hardstyle", "Harmonica Blues", "Heavy Metal", "Hi-NRG", 
    "Highlife", "Hillbilly", "Hindustani", "Hip Hop", "Hip-House", "Hiplife", "Honky Tonk", "Horrorcore", "House", "Hyphy", 
    "IDM", "Illbient", "Impressionist", "Indian Classical", "Indie Pop", "Indie Rock", "Industrial", "Instrumental", "Interview", 
    "Islamic", "Italo-Disco", "Italo House", "J-pop", "J-Rock", "Jazz", "Jazz-Funk", "Jazz-Rock", "Jazy", "Jit", "Jive", "Jongo", 
    "Jumpstyle", "Jungle", "K-pop", "Kizomba", "Klezmer", "Kwaito", "Laika", "Latin", "Latin Jazz", "Leftfield", "Lo-Fi", 
    "Louisiana Blues", "Lounge", "Lovers Rock", "Lullaby", "Makossa", "Maloya", "Mambo", "Mandopop", "Marabi", "March", "Mariachi", 
    "Math Rock", "Medieval", "Melodic Death Metal", "Melodic Hardcore", "Melodic Metal", "Memphis Blues", "Merengue", "Metal", 
    "Metalcore", "Miami Bass", "Military", "Minimal", "Minimal Techno", "Mizrahi", "Mod", "Modern", "Modern Classical", "Morna", 
    "MPB", "Music Hall", "Musique Concrète", "NDW", "Neo-Prog", "Neo-Psi", "Neo-Romantic", "Neo-Soul", "New Age", "New Beat", 
    "New Wave", "No Wave", "Noise", "Non-Music", "Norteño", "Novelty", "Nu-Disco", "Nu Metal", "Nursery Rhymes", "Oi", 
    "Opera", "Operetta", "Ottoman", "P.Funk", "Pachanga", "Pacific", "Palo", "Pasodoble", "Philippine Classical", "Phonk", 
    "Piano Blues", "Piedmont Blues", "Pipe & Drum", "Polka", "Pop", "Pop Metal", "Pop Punk", "Pop Rap", "Pop Rock", "Post-Bop", 
    "Post-Hardcore", "Post-Modern", "Post-Punk", "Post-Rock", "Power Electronics", "Power Metal", "Power Pop", "Progressive House", 
    "Progressive Metal", "Progressive Rock", "Progressive Trance", "Promotional", "Psy-Trance", "Psychedelic", "Psychedelic Rock", 
    "Psychobilly", "Pub Rock", "Public Broadcast", "Punk", "Quechua", "Radioplay", "Ragga", "Ragga Hip Hop", "Ragtime", 
    "Raï", "Ranchera", "Rapcore", "Rebetiko", "Reggae", "Reggae-Pop", "Reggaeton", "Religious", "Renaissance", "Rhythm & Blues", 
    "RnB/Swing", "Rock", "Rock & Roll", "Rockabilly", "Romani", "Roots Reggae", "Rumba", "Salsa", "Samba", "Schlager", 
    "Score", "Sega", "Ska", "Skiffle", "Sludge Metal", "Smooth Jazz", "Soca", "Soft Rock", "Soul", "Soul-Jazz", "Sound Effects", 
    "Soundtrack", "Southern Rock", "Space-Age", "Space Rock", "Special Effects", "Speech", "Speed Garage", "Speed Metal", 
    "Spoken Word", "Stoner Rock", "Surf", "Swing", "Symphonic Metal", "Symphonic Rock", "Synth-pop", "Synthwave", "Tech House", 
    "Techno", "Teen Pop", "Texas Blues", "Therapy", "Thrash", "Trance", "Tribal", "Tribal House", "Trip Hop", "Turntablism", 
    "UK Garage", "Vaporwave", "Vaudeville", "Video Game Music", "Viking Metal", "Vocal", "Vocal Jazz", "World", "Zouk", "Zydeco"
]

# --------------------------------------------------------------------------
# 2. INSTRUMENTS (Producers Vocabulary)
# --------------------------------------------------------------------------
INSTRUMENTS_VOCAB = [
    "Acoustic Guitar", "Electric Guitar", "Bass Guitar", "Upright Bass", "Synthesizer Lead", "Synthesizer Pad", 
    "Piano", "Electric Piano", "Rhodes", "Wurlitzer", "Clavinet", "Hammond Organ", "Church Organ", 
    "Drums", "Drum Machine", "Roland TR-808", "Roland TR-909", "MPC-60", "MPC-2000", "LinnDrum", 
    "Percussion", "Congas", "Bongos", "Tabla", "Shakers", "Tambourine", "Cowbell", "Claps", "Snaps", 
    "Violin", "Viola", "Cello", "Double Bass", "Orchestral Strings", "Harp", 
    "Trumpet", "Trombone", "Saxophone", "Flute", "Clarinet", "Oboe", "Bassoon", "Brass Section", 
    "French Horn", "Tuba", "Bagpipes", "Harmonica", "Accordion", 
    "Sitar", "Shamisen", "Koto", "Erhu", "Pipa", "Guzheng", "Marimba", "Vibraphone", "Steel Drums", 
    "Banjo", "Mandolin", "Ukulele", "Sitar", "Didgeridoo", "Kalimba", "Handpan", 
    "Analog Lead", "Acid Bassline", "Plucked Synth", "Stab Synth", "Sub Bass", "Wobble Bass", 
    "808 Bass", "Cinematic Braam", "Risers", "Downlifters", "Impacts", "Scratch", "Vocoder", "Talkbox"
]

# --------------------------------------------------------------------------
# 3. VOCAL DNA (Acoustic Persona)
# --------------------------------------------------------------------------
VOCAL_DNA = [
    # Biological / Type
    "Male Vocal", "Female Vocal", "Child Vocal", "Deep Bass Voice", "Baritone Voice", "Tenor Voice", 
    "Alto Voice", "Mezzo-Soprano", "Soprano Voice", "High-pitched Voice", "Husky Voice", "Gravelly Voice",
    # Techniques
    "Vibrato", "Falsetto", "Head Voice", "Chest Voice", "Belting", "Whispering", "Breathy Vocals", 
    "Lyrical Singing", "Rapping", "Spoken Word", "Shouting", "Growling", "Screaming", "Melisma", 
    "Yodeling", "Operatic singing", "Chanting", "Scatting", "Ad-libs", "Vocal Runs",
    # Processing
    "Autotuned", "Pitch Corrected", "Hard Autotune Effect", "Natural Vocals", "Dry Vocals", 
    "Doubled Vocals", "Layered Harmonies", "Backing Vocals", "Vocal Chops", "Reverberant Vocals", 
    "Telephonic Vocals", "Distorted Vocals"
]

# --------------------------------------------------------------------------
# 4. HARDWARE & ENGINEERING DNA (Analog/Digital Signatures)
# --------------------------------------------------------------------------
HARDWARE_DNA = [
    # Compression Signatures
    "FET Compression (1176 style)", "Opto Compression (LA-2A style)", "VCA Bus Compression", 
    "Variable-Mu Tube Compression", "Pumping Compression", "Aggressive Limiting", "Brickwall Limiting",
    # Saturation / Preamp
    "Analog Tape Saturation", "Tube Warmth", "Vacuum Tube Distortion", "Transistor Grit", 
    "Transformer Color", "Digital Clipping", "Bitcrushed", "Lo-fi vinyl texture", "Cassette Wow & Flutter",
    # EQ / Tone
    "Pultec-style Low End", "Neve-style Silky Highs", "SSL-style Surgical EQ", "Baxandall Air", 
    "Mid-forward Mix", "Bottom-heavy Mix", "Bright & Crisp", "Warm & Round", "Boxy Midrange", "Muddy Lows", 
    "Harsh Highs", "High Fidelity", "Audiophile Grade"
]

# --------------------------------------------------------------------------
# 5. MUSICOLOGY & MODAL DNA (Structural Intelligence)
# --------------------------------------------------------------------------
MUSICOLOGY_DNA = [
    # Modes
    "Ionian Mode (Major)", "Aeolian Mode (Natural Minor)", "Dorian Mode (Soulful)", 
    "Phrygian Mode (Dark/Exotic)", "Lydian Mode (Dreamy)", "Mixolydian Mode (Bluesy)", 
    "Locrian Mode (Dissonant)", "Pentatonic Scale", "Blues Scale", "Harmonic Minor", "Melodic Minor",
    # Rhythm
    "Straight Rhythm", "Swing Feel", "Shuffle", "Polyrhythmic", "Syncopated", "Dilla Swing (Laggy)", 
    "Driving Rhythm", "Broken Beat", "Four-on-the-floor", "Half-time", "Double-time", 
    "Complex Meter", "Odd Time Signature",
    # Harmony
    "Consonant Harmony", "Dissonant Clusters", "Jazz Extensions (9th/13th)", "Sus Chords", 
    "Power Chords", "Minimalist Harmony", "Wall of Sound"
]

# --------------------------------------------------------------------------
# 6. SPATIAL & ACOUSTIC DNA (Immersive Signature)
# --------------------------------------------------------------------------
SPATIAL_DNA = [
    # Environment
    "Dry Studio Space", "Small Room Ambience", "Intimate Jazz Club Space", "Large Concert Hall", 
    "Cathedral Reverb", "Stadium Envelopment", "Open Air Field", "Underground Echo",
    # Spatial Attributes
    "Mono Center Focused", "Stereo Wide", "Super Wide Field", "Narrow Stereo", "Binaural Perception", 
    "Front-loaded Mix", "Deep Reverb Tail", "Short Slapback Delay", "Ping-pong Delay", 
    "Immersive Surround Vibe", "Phasey Texture", "Holographic Depth",
    # 2026 SOTA Spatial Hearing
    "3D Source Separation", "Acoustic Pinpointing", "Edge-diffraction Modeling", "Proximal Proximity Effect"
]

# --------------------------------------------------------------------------
# 7. PRODUCTION ERA & CULTURE (Chronological DNA)
# --------------------------------------------------------------------------
PRODUCTION_DNA = [
    "50s Vintage Mono", "60s Psych-Rock production", "70s Analog Disco", "80s Gated Reverb Drums", 
    "80s Synthwave aesthetic", "90s Boom Bap MPC texture", "90s Eurodance", "Early 2000s Pop Gloss", 
    "Modern Trap High-end", "Hyperpop Glitch", "Bedroom Pop Lo-fi", "Organic World Music", 
    "High-budget Studio Production", "DIY Garage Recording",
    # 2025/2026 Chronological DNA
    "Hyper-Real AI Gloss", "Generative Lo-fi (2025)", "Post-Streaming Era Polish"
]

# --------------------------------------------------------------------------
# 8. SYNTHESIS DNA (Sound Design Signatures)
# --------------------------------------------------------------------------
SYNTHESIS_DNA = [
    "Subtractive Synthesis", "FM Synthesis (Metallic/Glassy)", "Additive Synthesis", 
    "Wavetable Synthesis (Shifting)", "Granular Texture (Glitched)", "Physical Modeling (Acoustic-like)", 
    "Vector Synthesis", "Analog Drift", "Digital Precision", "Modulated Filters"
]

# --------------------------------------------------------------------------
# 9. COGNITIVE & INTENT DNA (Strongest Brain V34 - 2026 SOTA)
# --------------------------------------------------------------------------
COGNITIVE_DNA = [
    "Aggressive Intent", "Nostalgic Comfort", "Hype Catalyst", "Melancholic Drift", 
    "Euphoric Peak", "Cerebral Complexity", "Minimalist Focus", "Chaos/Disturbance",
    "Social-Media Hookiness", "Cinematic Narrative", "Dance-Floor Dominance"
]
