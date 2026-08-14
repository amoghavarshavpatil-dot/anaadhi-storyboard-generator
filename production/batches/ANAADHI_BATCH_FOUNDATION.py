"""ANAADHI whole-movie P0 batch foundation.

Scenes 001-100 are divided into 34 production batches.
This file defines ONLY: location families, character/age/hair/costume/injury continuity,
and location-specific prop anchors.

Later phases will add action/blocking, Kannada recorded dialogue + lip sync,
inner voice/V.O./monologues, BGM/SFX, mix/mastering and final assembly.
"""

PROJECT = {
    "name": "ANAADHI",
    "source_screenplay": "ANAADHI_Scenes_001-100_Approved_Latest_Indian_English_Screenplay.docx",
    "scope": "SC001-SC100",
    "adult_anaadhi_height_cm": 193,
    "adult_anaadhi_height_display": "6'4",
    "master_raster": "3840x1608",
    "master_aspect": "2.39:1",
    "phase": "P0_BATCH_FOUNDATION",
}

RULES = {
    "identity": "Latest approved uploaded identity/location/prop reference overrides model defaults.",
    "height": "Adult Anaadhi remains 193 cm. Never shorten him to make composition easier.",
    "age": "Use exact Anaadhi ages stated by screenplay. Do not invent numeric ages for other characters when screenplay gives only a life-stage.",
    "hair_costume": "Never blend age, hair, costume or injury substates. Use the state named by the batch.",
    "child_identity": "Do not create child/teen Anaadhi by merely shrinking the adult Scene-100 body.",
    "parallel_earth": "Parallel variants inherit the physical identity/location anchor unless screenplay explicitly changes the world, age, role, injury or costume.",
    "props": "Named props are continuity anchors; do not replace them with generic sci-fi substitutes.",
    "dialogue": "No generated final dialogue. Creator-recorded Kannada dialogue is attached in P3.",
    "lip_sync": "No lip sync in P0. P3 explicitly marks visible-mouth dialogue windows.",
    "vo": "Inner voice, V.O. and monologues use separate creator-recorded audio in P4.",
    "audio": "BGM/ambience/Foley/SFX wait for P5. Mix/master waits for P6.",
    "revision": "Later approved scene overrides update only affected batch/scene manifests.",
    "violence": "If screenplay keeps a fatal act off-screen/symbolic, do not invent explicit mechanics.",
}

PHASES = [
    ("P0", "Batch foundation", "locations + character continuity + props"),
    ("P1", "Look and identity lock", "approved visual references"),
    ("P2", "Scene action and shot timeline", "blocking + camera + duration + transitions"),
    ("P3", "Kannada dialogue and lip sync", "uploaded dialogue + speaker/timecode + lip-sync yes/no"),
    ("P4", "Inner voice / V.O. / monologue", "uploaded non-lip-sync voice placement"),
    ("P5", "BGM / ambience / Foley / SFX", "second-by-second sound design"),
    ("P6", "Mix and master", "dialogue/BGM/SFX automation + theatrical mastering"),
    ("P7", "Final assembly", "shots -> scenes -> reels -> feature master"),
]


def batch(batch_id, title, scenes, epoch, locations, state, characters, props):
    return {
        "id": batch_id,
        "title": title,
        "scenes": scenes,
        "epoch": epoch,
        "locations": locations,
        "character_state": state,
        "characters": characters,
        "props": props,
        "action_blocking": "PENDING_P2",
        "kannada_dialogue_files": "PENDING_P3_UPLOAD",
        "lip_sync_map": "PENDING_P3",
        "inner_voice_vo_monologue_files": "PENDING_P4_UPLOAD",
        "bgm_sfx_timeline": "PENDING_P5",
        "mix_master": "PENDING_P6",
        "status": "FOUNDATION_DEFINED",
    }


BATCHES = [
    batch(
        "B01", "Opening Capture — Raised Cabin", [1,2,3,4,5],
        "Anaadhi age 27; capture-state cabin; pre-dawn black rain.",
        "EXT Bhaigaara buffer forest / raised cabin; INT raised cabin first floor.",
        "ANAADHI 27, 193 cm, heavy-athletic forest-built body, TOPLESS, shaved scalp with several days rough regrowth. AARATHI civilian field clothes, wet plait. SEMMAA present-day older disciplined state.",
        "Anaadhi; Aarathi; Semmaa; Police Commander; Sarjanya Officer; Medical Specialist; Allied Gangster; Parallel Aarathi/Child Anaadhi variants",
        "raised cabin; split floorboard; empty injector; compressed injector; ADK-7 cartridge; Paraane medical case/emblem; police shields; iron hook; wrist thermal display; hidden sensors; black-kite drones; medical transports",
    ),
    batch(
        "B02", "Adraka University — Founders Before Paraane", [6],
        "Years-earlier academic origin epoch.",
        "INT Adraka Medical University systems lab.",
        "ANAADHI absent. MARSYAA explicitly in his 50s. ANARVAA and PARVARAN are younger brilliant medical students; do not invent unsupported numeric ages.",
        "Marsyaa; Anarvaa; Parvaran; Lab Assistant",
        "red-stone university lab; carved timber ceiling beams; suspended holographic neural maps; integrated patient-flow model; lab console",
    ),
    batch(
        "B03", "Paraane Founding, Crisis, Protest and Council", [7,8,9,10],
        "Early Paraane institution-growth epoch.",
        "EXT Paraane inauguration/courtyard; INT registration hall; emergency coordination chamber; central assessment hub; founders council; EXT Workers District.",
        "ANAADHI absent. ANARVAA/PARVARAN founder-era continuity; MARSYAA mentor-era; ASANA explicitly young in SC008.",
        "Anarvaa; Parvaran; Marsyaa; Young Asana; Clerk; Dispatcher; Worker; Police Commander; System Operator",
        "Paraane emblem; village-fair canopies; Kannada digital signage; old rubber stamp; crisis holograms; rescue drones; protest banners; assessment drones; risk display; council files",
    ),
    batch(
        "B04", "Parlipatna Birth Hospital — Newborn Anaadhi", [11,12,13],
        "Birth-night / neonatal epoch.",
        "INT Parlipatna maternity hospital; neonatal diagnostic suite; records control room; maternity recovery room.",
        "ANAADHI newborn. PARVARAN arrives in founder/doctor coat with Paraane ID. JANNE postpartum patient state. No later Anaadhi body/hair references.",
        "Newborn Anaadhi; Parvaran; Janne; Maternity Nurse; Obstetrician; Neonatal Specialist; Records Clerk",
        "black-stone hospital; copper rain channels; solar tiles; biometric sandalwood doors; transparent cradle; neonatal scanner; N-4 report; Parvaran wrist device; records terminal; empty bedside cradle",
    ),
    batch(
        "B05", "Four-Road Junction, Sarjanya Patrol and Paraane Gate", [14,15,16],
        "Same newborn night; exterior monsoon continuity.",
        "EXT Parlipatna four-road junction; outer patrol road; Paraane Rehabilitation security gate.",
        "ANAADHI newborn in dark wool blanket then added shawl. SEMMAA younger than present day. ASANA young security officer.",
        "Newborn Anaadhi; Parvaran; Young Semmaa; Kenchaa; Driver; Sarjanya Members; Young Asana",
        "four-road junction; shrine stone; weak solar streetlight; dark wool blanket; Sarjanya jeep; broken route projector; holige container; extra shawl; security gate; intake interface; thermal cradle",
    ),
    batch(
        "B06", "Paraane Newborn Intake and Naming", [17,18],
        "Newborn + four-days-later continuity.",
        "INT Paraane emergency intake; Parvaran office overlooking child wing.",
        "ANAADHI newborn. MANIRE younger adult head nurse. PARVARAN same birth-era founder state.",
        "Newborn Anaadhi; Manire; Junior Intake Clerk; Child-Wing Doctor; Parvaran; Parallel Adult Anaadhi",
        "identity scanner; feed supplies; Advaita/non-duality diagram; quantum-consciousness model; hidden records; naming system",
    ),
    batch(
        "B07", "Paraane Child Wing — Age 5", [19],
        "Exact Anaadhi age 5.",
        "INT Paraane child wing; observation gallery.",
        "ANAADHI age 5, tall for age; shaved head grown into short uneven crop; child-wing clothing. PARVARAN/ANARVAA mid-career founders; MANIRE established ward nurse.",
        "Child Anaadhi; Manire; Parvaran; Anarvaa",
        "magnetic wooden road blocks; tiny cradle; medicine cup; blankets; one-way glass; clinical tablet",
    ),
    batch(
        "B08", "Paraane Child Wing / Assessment — Ages 7–8", [20,21],
        "SC020 age 7; SC021 age 8. Keep two separate identity substates.",
        "INT child wing; Manire consultation room; developmental assessment chamber.",
        "AGE 7: short uneven institutional haircut and clean identical child clothing. AGE 8: tall for age but narrow child shoulders. Never blend the two ages.",
        "Child Anaadhi; Manire; Elderly Resident; Distressed Resident; Parvaran; Anarvaa; System Voice",
        "medicinal-plant tray; torn sandal/fibre; fever/vitamin tablets; sweet; open door; circular assessment room; pulse/breath/eye mapping; face-test images; one-way glass; tablet",
    ),
    batch(
        "B09", "Paraane Courtyard and Medication — Ages 9–10", [22,23],
        "SC022 age 9; SC023 age 10.",
        "EXT child-wing courtyard; INT medication dispensary.",
        "ANAADHI child continuity; age 9 then age 10. Hair remains institutional/short unless a later approved reference overrides.",
        "Child Anaadhi; Manire; Jayasha; Sadhruna; Dispensary Attendant; Administrative Supervisor",
        "mechanical rain trees; wooden/holographic toys; paper-wing drone; antiseptic/bandage; automated copper medicine rail; wrist band; medicine cups; tablets; protocol display",
    ),
    batch(
        "B10", "Family Visitation — Age 11", [24],
        "Exact Anaadhi age 11; festival weekend.",
        "INT family visitation hall; child-wing community kitchen.",
        "ANAADHI age 11 in institutional child clothes; no family gift outfit. JAYASHA wears new festival dress; SADHRUNA carries toy vehicle.",
        "Child Anaadhi; Manire; Jayasha; Sadhruna; visiting families",
        "numbered pillar; holige boxes; new clothes; wooden toys; areca sweets; projected sky ceiling; vegetables; knife/cutting board; ceremonial waist thread",
    ),
    batch(
        "B11", "High Observation, Audit Escape and Service Anatomy — Age 12", [25,26,27],
        "Exact age 12; Paraane interior escape run.",
        "INT high-observation review; audit corridor; service corridors; security control; old drainage passage; EXT outer embankment.",
        "ANAADHI age 12, nearly adult-attendant height when standing; hair cut close again; institutional clothes. Tear/blood/dust clothing only as scene progression demands.",
        "Child Anaadhi; Manire; Anarvaa; Parvaran; Asana; Clinical Review Officer; Jayasha; Sadhruna; Attendant; Service Worker; Security Officer; Technician",
        "review table; risk screen; exit map; audit cameras/banners; medication cart; emergency injector; restraint launcher/dart; laundry steam; copper pipes; food lifts; maintenance drones; hatch; security screens; drainage grate",
    ),
    batch(
        "B12", "Age-12 Forest Escape, Survival and Search", [28,29,30,31,32,33,34],
        "Age-12 forest transition; weeks/months pass by SC033-034.",
        "EXT forest boundary/ravine/root shelter/shrine/stream/gathering slope/barter hamlet/path; INT Paraane search rooms and Parvaran-Janne house.",
        "ANAADHI begins age 12 in institutional clothes; barefoot from SC028; soaked/torn; close-cropped hair SC030; grass-fibre repairs SC032; unruly crop by SC033. Do not jump to teen hair.",
        "Child Anaadhi; Asana; Security Officers; Parvaran; Janne; Elderly Gatherer; Barter Woman; Forest Mechanic; Search Coordinator",
        "search vehicles/lights; root shelter; giant roots; shrine; copper disc; broken sensor; rainwater bowl; stream; wound cloth; figs; rain cover; medicinal leaves; boiled millet; market stalls; brass scales; weighing arms; filtration unit; cutting tool; forest map; age-12 photo",
    ),
    batch(
        "B13", "Forest-Raised Montage — Ages 13–16", [35],
        "Four explicit age states across seasonal montage.",
        "Forest shelter/stream/forest-edge hamlet/village edge across seasons.",
        "AGE 13 patched survivor; AGE 14 adolescent; AGE 15; AGE 16 rapid height growth, lean shoulders, hair reaches neck. Each age is its own identity substate.",
        "Young Anaadhi; Forest dog; forest-edge barter people",
        "bamboo joints; woven areca sheaths; sleeping mat; water containers; rain-catch basin; medicinal bark; sickle; grain/cloth barter; festival lamps; dog wound care; second-room materials; oil lamp",
    ),
    batch(
        "B14", "Forest Healer and First Permanent Cabin — Ages 17–18", [36,37],
        "Exact ages 17 and 18.",
        "EXT forest hamlet healing shelter/road; Anaadhi first permanent forest cabin.",
        "AGE 17 exceptionally tall, long-limbed. AGE 18 long loosely tied hair + faint moustache. Forest-labour clothing only; do not import age-19 beard density.",
        "Young Anaadhi; Village Elder; Young Woodcutter; Woodcutter Wife; Villagers; Elderly Gatherer; Parallel Parvaran",
        "healing canopy; clean water; cloth/bamboo splint; medicinal bark; ragi/lentils; solar bullock ambulance; rough timber cabin; laterite/bamboo; leaf shutters; rain sensors; copper solar threads; herbs; salvaged diagnostics; three doors; lower passage; loft; niches; clay pot",
    ),
    batch(
        "B15", "Age-19 Forest, Barter Market and Social Humiliation", [38,39,40,41,42],
        "Exact age 19 through final weeks before 20.",
        "EXT Bhaigaara path; barter market; village hand pump; forest stream; quiet market edge; cabin; INT mutton meals shack; cloth/salt/feast montage locations.",
        "ANAADHI 193 cm, lean/long-limbed, shoulder-length hair tied with fibre, thin uneven moustache + light beard, rough-spun dark tunic, repaired trousers, weathered sandals; tunic torn by SC042.",
        "Anaadhi; Trader; Shanthale; Sarvaraaj; Parallel Anaadhi; Server; Hotel Owner; Spice Seller; Mallayya; Cloth Seller; Young Woman; Feast Supervisor; Schoolboys",
        "timber cart with salvaged magnetic bearings; firewood; fruit; roots; bark extract; repair tools; grain/oil/blanket; hand pump/monitor; clay pots; stream stone; mutton packet; steel plates; cooling fans; spices; cooking fire; herbal extract; cloth strips; feast vessels; flask; smooth stone",
    ),
    batch(
        "B16", "Age-20 First Murder Cycle — Market / Village / Cabin", [43,44,45,46],
        "Exact age 20.",
        "EXT banyan salt stall; cloth lane; forest/jungle trails; hand pump/barn pump; fish lane; clearing; night alley; INT hidden/Anaadhi cabin.",
        "ANAADHI tall/lean; shoulder-length hair tied behind him at SC043; torn forest tunic continuity; first four cabin marks accumulate.",
        "Anaadhi; Mallayya; Nanjappa; Young Woman; Sarvaraaj; Shanthale; Gundappa",
        "salt sacks; stray-dog grain; smooth stone; marked cabin beam; cloth fabrics; hand pump; flask; medicinal stems; thrown stone; cold compress; hanging nets; smoky hut; clay cup; rusted two-wheeler",
    ),
    batch(
        "B17", "Age-21 Fever, Tea and Grain Episodes", [47,48],
        "Age 21 continuity.",
        "EXT roadside tea stall/back hut/forest road; INT forest hut/grain shop/cabin; EXT Basavaraj mud house.",
        "ANAADHI age 21; hair untied around fevered face; thinner and trembling from illness/hunger; wet forest-worn clothes/hollow eyes.",
        "Anaadhi; Chandru; Road Workers; Basavaraj; Parallel Janne; Watching Anaadhi",
        "tea cup/saucer; blankets; beedi; quantum grain scale; brass measure; empty sack; mud house threshold; cabin",
    ),
    batch(
        "B18", "Age-22 Religious / Butcher-River Episodes", [49,50],
        "Age 22 continuity.",
        "EXT leaking village shelter/rain path/butcher corner/riverside washing; INT burnt eucalyptus cabin.",
        "ANAADHI age 22 with accumulated forest scars/exhaustion; inherit post-age21 hair/beard unless later approved reference changes it. Do not beautify.",
        "Anaadhi; Devarajayya; Jabbar",
        "prayer beads; leaking shelter; burnt cabin; broken roof; medicinal roots; butcher counter; river washing area; beedis; cold river water; cabin name marks",
    ),
    batch(
        "B19", "Age-23 Suspicion and Palm-Liquor Road", [51,52],
        "Age 23 continuity.",
        "EXT abandoned grain road/multiple forest roads/dust road; Kendhalaa night road palm-liquor shed.",
        "ANAADHI age 23, forest-labour body, increasingly guarded; black motorcycle present in SC052.",
        "Anaadhi; Thimmegowda; Ramesha; Road-worker companions",
        "abandoned trader cart; missing money pouch; forest roads; black motorcycle; palm-liquor shed; weak lantern; dead tamarind tree; small wooden name piece",
    ),
    batch(
        "B20", "Age-24 Temple and Flooded Bullock Road", [53,54],
        "Age 24 continuity.",
        "EXT abandoned hillside temple; flooded bullock-cart rest road.",
        "ANAADHI age 24; same adult identity, forest-worn hair/beard/costume; hunger and rain exposure.",
        "Anaadhi; Krishnappa; Hanumantha",
        "medicine bundle; temple meal vessels; spring; bell; kitchen corridor; flooded trade road; covered bullock cart; bullocks/ropes; culvert; wooden wheel; victim-name tablet",
    ),
    batch(
        "B21", "Age-25 Burned Cabin / Logging and Market Road", [55,56],
        "Age 25 continuity.",
        "EXT hidden cabin/logging path; Kendhalaa market road/roadside shrine.",
        "ANAADHI age 25; injured bleeding hands during rebuild; mature forest-worn look; motorcycle chain break in SC056.",
        "Anaadhi; Shivappa; Linga; Cart-line men",
        "burned cabin; medicinal roots; drawings; preserved names; childhood objects; sawdust; logging lantern/machinery; new shelter/decoy cabins; motorcycle; broken chain; shrine; cart wheels",
    ),
    batch(
        "B22", "Age-26 Herb Buyer and Barber", [57,58],
        "Age 26 continuity with critical hair transformation.",
        "INT wealthy herb buyer storehouse; EXT forest clearing; roadside barber shelter.",
        "ANAADHI age 26, forest-burned skin, scars, overgrown hair + uneven beard. Preserve BEFORE / HALF-CUT / SELF-CUT hair substates from SC058.",
        "Anaadhi; Raghavendra; Chikkanna; Waiting Customer",
        "modern scale; brass weights; rare roots; burned herb bundle; roadside barber shelter; small mirror; haircut tools; low stone seat; herb payment; victim-name wall",
    ),
    batch(
        "B23", "Age-27 Final Cabin, Evidence Investigation and Surrender Contact", [59,60,61,62,63],
        "Age 27 pre-capture / primary-cabin investigation epoch.",
        "EXT forest rest path/abandoned cabins; INT final/primary cabin; Kendhalaa Police independent evidence room.",
        "ANAADHI 27, 193 cm. Start from SC058 self-cut hair state; forest-burned skin/scars; seventeen lamps/names. IMPORTANT: later capture has shaved scalp; transition must be resolved in P2 and never silently invented.",
        "Anaadhi; Madhava; Aarathi; Police Analyst; Unnath; Child from gatherer family",
        "mirror seller bag; mirrors; name tablets; seventeen lamps; covered mirrors; locked floorboard/weapons; 17 case files; transparent victim display; abandoned shelter tools; cooking vessels; burned alcohol; prayer stones; Madhava bag; primary cabin key",
    ),
    batch(
        "B24", "Paraane Command, ADK-7 Vault and Capture Operation", [64,65,66],
        "Age 27 operation-prep and capture bridge.",
        "INT Paraane central command operations hall; pharmaceutical transfer vault; EXT Bhaigaara buffer forest; INT/EXT Anaadhi raised cabin.",
        "ANAADHI capture state must match B01: 193 cm, heavy-athletic, shaved scalp with rough regrowth, topless when opening continuity requires. AARATHI civilian field clothes/wet plait. SEMMAA older disciplined present-day state.",
        "Anarvaa; Parvaran; Unnath; Aarathi; Semmaa; Asana; Medical Specialist; Administrative Officer; Pharmacy Technician; Inventory Assistant; Police Commander; Allied Gangster; Anaadhi",
        "operations table; forest map; surrender display; PNX-4 protocol; rubber stamp; magnetic medicine rails; crate; 12 cartridges; ADK-7 Unit 07; override layer; victim display; drones; iron hook; shields; injector; Paraane emblem",
    ),
    batch(
        "B25", "Lower Passage Escape and Flood Channel", [67,68],
        "Immediately post-ADK-7; age 27.",
        "INT primary cabin/lower passage; EXT ravine/flood channel.",
        "ANAADHI same capture body/hair; chemically impaired motor control; wet/soiled escape clothing inherited from SC066. AARATHI same operation field-clothes continuity.",
        "Anaadhi; Aarathi; Medical Specialist; Police Commander; Police Technician; Semmaa; Unnath; Anarvaa",
        "floor release; lower timber tunnel; field light; three-way tunnel; thermal sensors; drainage grate; ravine rocks; knee-deep water; field communicator; black-kite drones",
    ),
    batch(
        "B26", "Present-Day Paraane Return, Archive, Hall and Self-Harm Crisis", [69,70,71,72,73,74],
        "Age 27 return to Paraane after forest pursuit.",
        "EXT eastern drainage wall; INT old drainage passage/child wing/Manire room/central resident hall/archive core/old observation corridor/maintenance chamber.",
        "ANAADHI 27 wet post-operation state; preserve capture hair until approved transition. SC074 clothing becomes torn/bloodied and chest/abdomen wounds begin. MANIRE present-day older with grey hair. ASANA present-day security head.",
        "Anaadhi; Aarathi; Manire; Asana; Attendant; Residents; Anarvaa; Woman Resident; Child Anaadhi variants; victim variants",
        "drainage grate; childhood wall marks; adaptive walls; medicine cup; open consultation door; water cup; door override; recorder; victim list; suspended archive files; birth record; observation glass; maintenance debris; reflective panel; pressure dressing",
    ),
    batch(
        "B27", "Independent Ayurvedic Surgery Centre — Injury to Transfer", [75,76,77,78,79,80],
        "Age 27 surgical/recovery progression.",
        "EXT Paraane transfer bay/independent surgery centre courtyard/walkway/garden; INT emergency vehicle/operating theatre/recovery ward.",
        "SC075 acute wounds/stretcher; SC076 surgery; SC077 three days later broad chest+abdomen bandages; SC078-080 healing with dark shawl open over bandages. Keep four injury substates.",
        "Anaadhi; Aarathi; Manire; Asana; Unnath; Medical Officer; Independent Surgeon; Surgical Specialist; Paraane Representative; Parvaran; Recovery Clinician; Thalaar; Cameraman; Semmaa",
        "transfer bay; emergency vehicle; oxygen; medicine display; laterite surgical centre; copper roofs; medicinal gardens; diagnostic field; robotic micro-suture system; botanical surface sealant; recovery bed; open ward door; pain medicine; walkway; Janne photo; dark shawl; transfer order; medical vehicle; concealed media device",
    ),
    batch(
        "B28", "Forest Transfer Road and Communications Tower — Semmaa", [81,82],
        "Age 27 healing-transfer state, same-day continuity.",
        "EXT forest transfer road; forest communications tower.",
        "ANAADHI healing wounds under bandaging, walking slowly. SEMMAA out of uniform with Sarjanya communication band under sleeve. AARATHI rain/transfer continuity.",
        "Anaadhi; Aarathi; Semmaa; Field Officer; Recovery Medic; Cameraman",
        "police medical-transfer vehicle; fallen tree; red mud; rain canopy; recovery equipment; communications tower; Semmaa phone; communication band; Aarathi rain shawl",
    ),
    batch(
        "B29", "Anarvaa Collapse, Emergency Ward, Interim Council and Pharmacy Evidence", [83,84,85,86],
        "Present-day institutional crisis; Anaadhi mainly absent.",
        "INT Anarvaa Paraane office; Paraane hospital emergency ward; Kendhalaa convention council hall; certified pharmaceutical inventory vault.",
        "ANARVAA present-day head then acute patient/FND-like episode. PARVARAN/ATHRIMA/ASANA/MANIMANTHARAA current-day. Pharmacist/assistant professional workwear.",
        "Anarvaa; Sister Meera; Hospital Workers; Senior Physician; Neurologist; Athrima; Administrative Officer; Technical Clerk; Unnath; Manimantharaa; Asana; Parvaran; Pharmacist; Inventory Assistant",
        "office phone; consultation file; stretcher; suspended scanner; privacy glass; login terminals; integrated command chair; crisis map; 72-hour order; automated shelves; medicine cartridges; ADK-7 microseal; evidence drives; recording phone",
    ),
    batch(
        "B30", "Marsyaa / Media Network / Irrigation Live Confession / Truth War", [87,88,89,90,91,92],
        "Present-day media and evidence war.",
        "INT Marsyaa Adraka study; media executive/news floors; abandoned irrigation telemetry shelter; multi-location truth-war montage.",
        "ANAADHI 27 with reinforced bandaging at shelter. MARSYAA explicitly in his 60s. KADRAAYINI polished executive/news state. THALAAR/CAMERAMAN field-report state.",
        "Marsyaa; Pharmacist; Kadraayini; Graphic Editor; Producer; Technical Director; Thalaar; Cameraman; Aarathi; Anaadhi; Parvaran; Unnath; Athrima; Asana; Manimantharaa; Young Sarjanya Member",
        "ancient medical texts; damaged student notebooks; encrypted equipment; locked case; newsroom screens; monster/hero/patient packages; delay server; old groundwater computers; irrigation controls; camera/red tally; raw footage storage; victim list; Semmaa recording; evidence copies",
    ),
    batch(
        "B31", "Kendhalaa–Adraka Border Checkpoint and Emergency Tribunal", [93,94,95,96],
        "Pre-dawn to dawn border confrontation.",
        "EXT Kendhalaa-Adjraka joint checkpoint; INT temporary judicial evidence chamber.",
        "ANAADHI 27 unrestrained in protected judicial-transfer vehicle, healing wounds under dark shawl, 18-name list in pocket. MARSYAA grey-haired in traditional Adraka scholar clothes under modern medical overcoat. UNNATH uniform has NO Paraane emblem.",
        "Anaadhi; Aarathi; Unnath; Marsyaa; Manimantharaa; Asana; Pharmacist; Young Sarjanya Members; Thalaar; Cameraman; Medical-Law Judge; Criminal Judge; Civil Rights Judge; Marsyaa Counsel",
        "black-stone plateau; old watchtowers; scanning arches; transfer vehicle; Marsyaa convoy; Sarjanya vehicles; police units; cargo display; ADK-7 containers; research files; restricted chemicals; weapons; ledgers; Kadraayini payment instructions; Sarjanya consignments; evidence seals/video; evidence glass; judge links",
    ),
    batch(
        "B32", "Independent Judicial Complex — Family Contact and Remand Court", [97,98],
        "Age 27 judicial-custody state before six-month montage.",
        "INT independent judicial family-contact corridor; independent district court systemic-review chamber.",
        "ANAADHI 27, healing wounds still pull beneath clothes, no handcuffs. JANNE present-day mother state. PARVARAN present-day father/founder under scrutiny.",
        "Anaadhi; Janne; Parvaran; Legal Advocate; Court Officers; Independent Judge; Aarathi; Unnath; Asana; Manire; Pharmacist; Paraane Legal Officer; victim families; Paraane residents/advocates",
        "age-12 photo; current court photo; writing desk; paper/envelope; judicial corridor; courtroom; investigative table; case files; remand orders; independent medical-custody documents",
    ),
    batch(
        "B33", "Six-Month Dismantling Montage", [99],
        "Six months later; systemic aftermath across many institutions.",
        "Paraane Central; Kendhalaa Police HQ; detention review; Sarjanya compound; courts/tribunal; media network; Paraane Hospital rehab; public inquiry; child wing; memorial courtyard; Janne house; independent secure medical unit.",
        "ANAADHI primarily V.O., later independent secure medical-unit state six months later. Do not automatically substitute Scene-100 final anatomy unless that shot explicitly transitions. Other current-day characters have six months elapsed.",
        "Anaadhi; Unnath; Worker; Asana; Manimantharaa; Marsyaa; Pharmacist; Thalaar; Cameraman; Kadraayini; Anarvaa; Rehabilitation Specialist; Parvaran; Commission Counsel; Manire; Aarathi; Janne",
        "removed governing emblem; new separated signs; statutory separation order; cleaned police terminals; detention files; Sarjanya armoury/weapons; sealed drug rooms; tribunal evidence; media packages/editorial charter; rehab equipment; inquiry projection; Parvaran interim ID; unbolted child-room door; medicine cup; 18-name memorial; Madhava bag; FROM ANAADHI envelope; 18 case files; desk/pen",
    ),
    batch(
        "B34", "Scene 100 — Independent Judicial Medical Centre Final Identity", [100],
        "Final post-recovery dawn interview.",
        "INT Independent Judicial Medical Centre interview room.",
        "ANAADHI age 27, 193 cm/6'4; surgical wounds healed into long scars; lean, defined, masculine post-recovery body. Use uploaded Scene-100 face/hair lock: dense voluminous medium-long hair with natural lift/side taper; medium-full beard + disciplined moustache. Screenplay does not specify final garment, so do not invent costume until approved.",
        "Anaadhi; Independent Clinician; Legal Advocate; Court Officers",
        "simple room; one table; two chairs; wide window; open door; intake form; pen; victim files; morning light",
    ),
]

# Coverage QA: every scene exactly once in this P0 architecture.
_SCENES = [scene for item in BATCHES for scene in item["scenes"]]
assert len(BATCHES) == 34
assert sorted(_SCENES) == list(range(1, 101))
assert len(_SCENES) == len(set(_SCENES)) == 100

# The generator should stop if later phases are accidentally assumed before being supplied.
for item in BATCHES:
    assert item["action_blocking"] == "PENDING_P2"
    assert item["kannada_dialogue_files"] == "PENDING_P3_UPLOAD"
    assert item["bgm_sfx_timeline"] == "PENDING_P5"
