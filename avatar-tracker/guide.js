// Guide data for the Avatar: Frontiers of Pandora tracker.
// Keys are lower-case Steam API names, so Steam unlocks match exactly.
// `steps` become a per-achievement checklist saved in the browser.
// `flag` marks planning concerns: collectible hunts, reported bugs, and the
// two kinds of paid content (Season Pass story packs, From the Ashes).
// Sources:
//   https://www.powerpyx.com/avatar-frontiers-of-pandora-trophy-guide-roadmap/
//   https://www.powerpyx.com/avatar-frontiers-of-pandora-collectibles-locations-guide/
//     (and its linked per-collectible pages: kites, dolls, recon retrievals,
//      comics, flutes, totems, bladewing moths, budding watchers, audio logs,
//      notes, tarsyu saplings, tarsyu flowers, installations, outposts, bases)
//   https://steamcommunity.com/sharedfiles/filedetails/?id=3449087358 (100% guide incl. DLC)
//   https://steamcommunity.com/sharedfiles/filedetails/?id=3536978439 (legendary materials)
//   https://steamcommunity.com/app/2840770/discussions/0/770811991515214630/ (One Shot)
//   https://steamcommunity.com/app/2840770/discussions/0/565870281449610729/ (The Hunt saddle)
//   https://steamcommunity.com/app/2840770/discussions/0/4518882879950491752/ (Sky Breaker start)
//   https://steamcommunity.com/app/2840770/discussions/0/691999715068255360/ (Fight for Home bug)
//   https://www.exophase.com/game/avatar-frontiers-of-pandora-steam/achievements/ (DLC grouping)
//   https://james-camerons-avatar.fandom.com/wiki/Gear_Designs_in_Avatar:_Frontiers_of_Pandora
//   https://james-camerons-avatar.fandom.com/wiki/Tarsyu_Sapling_Skills
//   https://james-camerons-avatar.fandom.com/wiki/From_the_Ashes
//   https://james-camerons-avatar.fandom.com/wiki/Fireback_Mastodon
//   https://www.gamerguides.com/avatar-frontiers-of-pandora/guide/getting-started/tips-and-tricks/all-apex-skills-in-avatar-frontiers-of-pandora
//   https://patchcrazy.co.uk/all-8-zeykoma-fruits-locations-eywas-blessing-trophy-avatar-from-the-ashes/
//   https://platget.com/guides/avatar-frontiers-of-pandora-trophy-guide/ (58 RDA sites)
//   https://wand.com/maps/avatar-frontiers-of-pandora/pandora
//   https://james-camerons-avatar.fandom.com/wiki/An_Invitation (DLC skip)
//   https://allthings.how/avatar-frontiers-of-pandora-from-the-ashes-dlc-achievements-and-how-to-earn-them/
//   Steam news for app 2840770: Title Update 4.0, 1.2, 2.0, 2.5 patch notes and the From the Ashes FAQ.
window.GUIDE = {
  appid: "2840770",
  title: "Avatar: Frontiers of Pandora",
  titleAccent: "Pandora",
  subtitle: "Achievement tracker, synced from Steam",
  credit: "Tips from PowerPyx, Steam community guides and discussions, the Avatar Wiki (Fandom), PatchCrazy, allthings.how, Exophase, and Ubisoft patch notes.",
  defaultStatus: "todo",
  colors: {
    light: { accent: "#3b3fb5", accent2: "#a0258a" },
    dark: { accent: "#9b9cff", accent2: "#ff7ae0" },
  },
  flags: {
    collect: { label: "Collectible hunt", tone: "accent" },
    bug: { label: "Reported bug: read the tip first", tone: "accent" },
    season: { label: "Season Pass story pack", tone: "accent2" },
    ashes: { label: "From the Ashes (separate purchase)", tone: "accent2" },
  },
  highlight: { flag: "collect", label: "Collectible hunts left", note: "Best after the story, with the ikran in every region" },
  missables: "The DLC story skip offered after Main Quest 4 deletes the main story from that save; decline it. Also: Kame'tire contributions Part 3, the From the Ashes save import, and the From the Ashes race. Collectibles are not missable.",
  categories: [
    ["story", "Main story"],
    ["collect", "Collectibles"],
    ["nature", "Nature and hunting"],
    ["rda", "RDA facilities"],
    ["skills", "Skills, cooking, crafting"],
    ["side", "Side quests"],
    ["skybreaker", "The Sky Breaker (DLC 1)"],
    ["spires", "Secrets of the Spires (DLC 2)"],
    ["ashes", "From the Ashes expansion"],
  ],
  achievements: {
    // ---------------- Main story ----------------
    afop_ach_1: { cat: "story", wide: true, missable: "Decline the DLC story skip offered after Main Quest 4 (An Invitation, Anufi's Favor). Taking it removes the main story from that save.",
      tip: [
        "Finish the final main quest, Last Strike (Main Quest 31 per PowerPyx). Difficulty does not affect any achievement, so Easy is fine. The game has one autosave and no manual saves.",
        "Trap: after Main Quest 4: Songs of the Ancestor, the game offers a skip to the DLC (the Sky Breaker invitation and Anufi's Favor for the Spires). Decline both. The skip removes the main story from that save for good, which locks out this achievement and the story ones after it (Avatar Wiki, Title Update 1.2 notes).",
        "Apart from that skip, nothing on the base list is missable (PowerPyx). Free roam continues after the credits and every achievement task stays available. Resistance HQ in Kinglor Forest closes for good after Main Quest 20: A Victory Celebration; its notes and audio logs respawn at the second HQ in the Clouded Forest, except one audio log (see A Good Listener).",
        "Patch state: Title Update 2.0 (Dec 2025) added third person (J on PC) and New Game+. Title Update 2.5 (Dec 2025) added From the Ashes. The Steam news feed shows no later title update as of Oct 2026. NG+ needs a save that has finished Last Strike; nothing on this list needs NG+.",
        "Whole-game plan: work down the checklist. Content packs: the two story packs come with the Season Pass; From the Ashes is a separate purchase, launched from its own main-menu entry.",
      ],
      steps: [
        "Never accept the DLC story skip (An Invitation, Anufi's Favor) before Last Strike; it deletes the main story from the save",
        "Story to Main Quest 11: Take Flight (ikran unlocks). Scan every plant and animal with Na'vi senses for Wildlife Expert and Great Gatherer",
        "Harvest one of each plant and animal and keep a copy in the stash, for the clan contribution quests later",
        "Loot every wicker basket (specialty recipes) and grab free designs at clan merchants (Apprentice Crafter)",
        "Touch every tarsyu sapling, tarsyu flower and bellsprig you pass (skill points, ancestor skills, health)",
        "Spend skill points on 3 skills in each tree, then fill one whole tree for an Apex skill (Maker or Rider)",
        "As each region opens: Upper Plains kites (after Main Quest 14: The Wandering Clan) and wind flutes; Clouded Forest (from Main Quest 21: Escape Plan) budding watchers and dolls",
        "Do not finish Kame'tire contributions before you finish the story (One with the Clans Part 3 can get stuck)",
        "Finish the story (Last Strike). Free roam stays open",
        "Clean up: all 58 RDA sites for 100% air quality, then the remaining collectibles by map",
        "Revisit one budding watcher 24+ real hours after the first for the 10th Mushroom Navigator count",
        "Steady Wings 1-3 and clan contributions Part 3 for all three clans",
        "Non-feral thanator in Gossamer Lakes once your gear level is high (PowerPyx: level 16+ on Easy)",
        "Season Pass: The Sky Breaker (Heart of the Plains): story, 4 research points, a legendary craft",
        "Season Pass: Secrets of the Spires: story, all 11 Sky Hunter skills while inside the Spires region, 20 Ikran Smashes",
        "From the Ashes last: start it from its main-menu entry and import your Sarentu save",
        "From the Ashes: farm One Shot AMP kills from the start, collect 8 Zeykoma fruit, open So'lek stashes, clear all quests",
      ] },
    afop_ach_7: { cat: "story", missable: "Decline the DLC story skip offered after Main Quest 4 (An Invitation, Anufi's Favor). Taking it removes the main story from that save.",
      tip: "Story. Missable only through the DLC story skip. Unlocks when you finish Main Quest 5: Becoming. The quest before it, Main Quest 4: Songs of the Ancestor, gives the first ancestor skill (Air Boost)." },
    afop_ach_8: { cat: "story", missable: "Decline the DLC story skip offered after Main Quest 4 (An Invitation, Anufi's Favor). Taking it removes the main story from that save.",
      tip: "Story. Missable only through the DLC story skip. Unlocks when you finish Main Quest 13: Pushing Back." },
    afop_ach_9: { cat: "story", missable: "Decline the DLC story skip offered after Main Quest 4 (An Invitation, Anufi's Favor). Taking it removes the main story from that save.",
      tip: "Story. Missable only through the DLC story skip. Unlocks when you finish Main Quest 19: Combined Forces. This quest also clears the Extractor Plant base, one of the 3 bases for Reclaim Pandora." },
    afop_ach_10: { cat: "story", missable: "Decline the DLC story skip offered after Main Quest 4 (An Invitation, Anufi's Favor). Taking it removes the main story from that save.",
      tip: "Story. Missable only through the DLC story skip. Unlocks when you finish Main Quest 27: Revelations." },
    afop_ach_11: { cat: "story", missable: "Decline the DLC story skip offered after Main Quest 4 (An Invitation, Anufi's Favor). Taking it removes the main story from that save.",
      tip: "Story. Missable only through the DLC story skip. Unlocks when you finish Main Quest 29: Rising Pressure. Two quests remain after it before the campaign ends." },

    // ---------------- Collectibles ----------------
    afop_ach_6: { cat: "collect", flag: "collect",
      tip: [
        "9 windswept kites, all in the Upper Plains sub-regions Mother of Rivers and Shattered Bridge, close together. They are not marked on the map, so use PowerPyx's map pictures or the Map Genie map. You can grab them from the ikran.",
        "The first kite starts the side quest The Wind Will Carry Us. The achievement pops on the 9th kite; return to the kite owner at The Circle to close the quest. None are missable.",
      ],
      steps: ["Spite Kite", "Transforming Kite", "Storm Kite", "Spirit of the Clan Kite", "Flower Kite", "Warning Kite", "Fog Guiding Kite", "Fight Kite", "Kite of Water"] },
    afop_ach_12: { cat: "collect", flag: "collect",
      tip: [
        "9 windswept dolls (the quest calls them Shadow Puppets, the journal calls them Kame'tire Dolls), all in the Clouded Forest. They are not marked on the map and are tiny.",
        "All sit inside or under broken tree trunks, or in caves near water. They glow blue in Na'vi senses only within a few metres. Check progress in Journal > Lost Items > Kame'tire Dolls. The first starts the side quest The Dark Theater. None are missable.",
        "The Sitting Elder is next to a bellsprig in a cave: enter the rock formation, drop into the pool, take the hole in the wall, and look in the opening on the left before you turn right to the bellsprig.",
      ],
      steps: ["The Abandoned (drop into a big trunk from above)", "The Follow (cave by Nomad's River, east bank)", "The Sprinter (big trunk, jump from the fallen trunk)", "The Sitting Elder (bellsprig cave)", "One-Eyed Mother (fallen trunk, Great Stone Swamp)", "The Baby Face (small cave, rock formation near a river)", "The Strong (under a fallen trunk)", "The Siren (inside a fallen trunk)", "The Blonde Adonis (under a fallen trunk)"] },
    afop_ach_13: { cat: "collect", flag: "collect",
      tip: [
        "9 recon retrievals, called Data Collectors on the map. They appear on the map as you unfog it. None are missable.",
        "At each one, open the hacking tool (SID) and scan the station terminal. Then find and scan 3-4 antennas within about 30 m. Each antenna makes an electrical sound that gets louder as you close in, and they hide on cliffs and behind rocks. Turn up the volume and do not leave until the top-left tracker is full.",
        "Finishing all 9 also ends the side quest System Reboot (talk to Alexander at Resistance HQ).",
      ],
      steps: ["Kinglor Forest #1", "Kinglor Forest #2", "Upper Plains #3", "Upper Plains #4", "Upper Plains #5", "Clouded Forest #6", "Clouded Forest #7", "Clouded Forest #8", "Clouded Forest #9"] },
    afop_ach_16: { cat: "collect", flag: "collect",
      tip: [
        "Collect 30 unique audio logs (blue glowing tablets). More than 30 exist. Many have duplicate spawn points; picking one copy removes the others. Check Journal > Audio Logs.",
        "Look in human-made places: field labs, RDA sites, terminals. Some appear only after you conquer an outpost or base. The TAP Con-1 facility in the Clouded Forest holds 5, and the bunker behind the 11th treasure comic holds 2.",
        "Possible miss: Message for Priya: Meteor Shower sits upstairs in the first Resistance HQ and does not respawn after Main Quest 20 (PowerPyx). Grab it before that quest. Missing it still leaves more than 30.",
      ] },
    afop_ach_20: { cat: "collect", flag: "collect",
      tip: [
        "Collect 30 unique notes. More than 30 exist and duplicates vanish once one copy is taken, as with audio logs.",
        "10 notes (SciOps Work Orders 001-010) come free from hacking the 10 treasure-hunt computer terminals, so do Father and Son in the Stars alongside this. 6 more sit in the second Resistance HQ (Clouded Forest). Field labs hold many of the rest.",
        "PowerPyx says every note in the first Resistance HQ respawns in the second one.",
      ] },
    afop_ach_23: { cat: "collect", flag: "collect", wide: true,
      tip: [
        "11 treasure hunt comics. Each starts at a Computer Terminal on the map: hack it with SID to start a Finding Home side quest and get a clue note. The comic lies in a trailer near the clue spot. It renders only up close, so fly low or walk the area.",
        "Comic 11: after you pick up the 10th comic, Finding Home - Part 11 starts on its own. Track it to a door in a mountain wall. The last room is locked: shoot an arrow at the wall panel through the opening on the left (the hacking tool highlights it). The same bunker holds 2 audio logs.",
        "None are missable. The in-game book numbers do not follow map order; PowerPyx lists them in route order.",
      ],
      steps: ["Comic 1", "Comic 2", "Comic 3", "Comic 4", "Comic 5", "Comic 6", "Comic 7", "Comic 8", "Comic 9", "Comic 10", "Comic 11 (Finding Home - Part 11 bunker)"] },
    afop_ach_25: { cat: "collect", flag: "collect", wide: true,
      tip: [
        "17 aeolian wind flutes, all in the Upper Plains. You tune 4 during Main Quest 17: The Weeping Gorge. The other 13 sit in the open world and appear on the map as you unfog it (purple: unseen, blue: seen, green: done).",
        "At each flute, turn the lever to tune it. The 4 story flutes are not marked on the map. None are missable.",
      ],
      steps: ["Story flutes 1-4 (Main Quest 17: The Weeping Gorge)", "Flute 5", "Flute 6", "Flute 7", "Flute 8", "Flute 9", "Flute 10", "Flute 11", "Flute 12", "Flute 13", "Flute 14", "Flute 15", "Flute 16", "Flute 17"] },
    afop_ach_26: { cat: "collect", flag: "collect", wide: true,
      tip: [
        "12 Sarentu totems: big wooden totems with a blue kite sticking out. Follow the direction the kite points, then the trail of blue kites, to a viewpoint. Stand in the right spot until the interact prompt shows, then press it while looking at the totem.",
        "Each gives clan favor. None are missable. Flying makes this much faster, so it fits best after the story. A PowerPyx commenter reports that totems count for the co-op host only, so do these solo.",
      ],
      steps: ["Kinglor: Waterway Valley", "Kinglor: Spinner's Circle", "Kinglor: Silk Woods", "Kinglor: Gossamer Lakes", "Upper Plains: The Celebration Valley", "Upper Plains: Mother of Rivers (1 of 3)", "Upper Plains: Mother of Rivers (2 of 3)", "Upper Plains: Mother of Rivers (3 of 3)", "Upper Plains: The Stone Hold", "Clouded Forest: Cradling Pines", "Clouded Forest: The Cut", "Clouded Forest: Stone Cloud Valley"] },
    afop_ach_27: { cat: "collect", flag: "collect", wide: true,
      tip: [
        "Mycelium Network activities are the Budding Watchers on the map. Sources disagree on the count: PowerPyx and Gamer Guides list 9, while the Avatar Wiki and Platget say 10. PowerPyx puts all in the Clouded Forest; Gamer Guides places some in the Upper Plains. The achievement needs 10 completions.",
        "At each giant mushroom, follow each root path of small white mushrooms to a mid-size mushroom and touch it. When every path is done, the big mushroom opens. Walk in and loot the item: it counts only after you loot it.",
        "10th count: PowerPyx and others say the watchers refresh about 24 real-time hours after you complete them. Repeat any one after that wait. Do the first 9 early so the clock runs while you play other content. One Steam guide author doubts they can be repeated, so treat the refresh as the best-supported answer, not certain.",
      ],
      steps: ["Budding Watcher 1", "Budding Watcher 2", "Budding Watcher 3", "Budding Watcher 4", "Budding Watcher 5", "Budding Watcher 6", "Budding Watcher 7", "Budding Watcher 8", "Budding Watcher 9", "Repeat one after 24+ real hours (10th)"] },
    afop_ach_28: { cat: "collect", flag: "collect", wide: true,
      tip: [
        "11 bladewing moth trails. At each map marker a trail of moths takes off. Follow it back to the nest, then loot the fruit at the nest. The map icon turns green when done.",
        "In the Upper Plains and Clouded Forest the moths outrun you on foot; ride a direhorse or fly the ikran (Steam guide). None are missable.",
      ],
      steps: ["Kinglor Forest 1", "Kinglor Forest 2", "Kinglor Forest 3", "Kinglor Forest 4", "Upper Plains 5", "Upper Plains 6", "Upper Plains 7", "Upper Plains 8", "Upper Plains 9", "Clouded Forest 10", "Clouded Forest 11"] },

    // ---------------- Nature and hunting ----------------
    afop_ach_4: { cat: "nature",
      tip: "Touch 20 tarsyu saplings. PowerPyx found 50 (17 Kinglor, 20 Upper Plains, 13 Clouded Forest), and each gives a skill point, so take every one. Saplings in brown polluted zones appear only after you destroy the nearby RDA site." },
    afop_ach_5: { cat: "nature",
      tip: "Touch 20 bellsprigs. Each raises max health, and PowerPyx found more than 120. As with saplings, ones in polluted zones spawn after you clear the nearby RDA site." },
    afop_ach_14: { cat: "nature",
      tip: "Hold the Na'vi senses scan on animals to add Hunter's Guide entries; killing and harvesting one also adds it. Only gatherable wildlife counts (Hunter's Guide > Type > Wildlife (gatherable)). Keep scanning past 20: scanned entries can be pinned and tracked on the map, which the clan contribution quests need." },
    afop_ach_15: { cat: "nature",
      tip: "Scan or harvest 30 different gatherable plants (Hunter's Guide > Type > Flora (gatherable)). Comes naturally if you scan everything early. Pin entries to show them on the map later." },
    afop_ach_2: { cat: "nature",
      tip: [
        "Kill a non-feral thanator. Feral ones from missions do not count. PowerPyx places it in Kinglor Forest > Gossamer Lakes: the screen goes white and you hear a heartbeat. Walk toward the louder heartbeat until it attacks. It is level 20; PowerPyx suggests level 16+ on Easy, or simply after the story.",
        "While it stalks you, you cannot call the ikran. The Steam guide says non-feral ones also roam parts of the Clouded Forest, and a PowerPyx commenter met one near the budding watcher right of Carver's River (Cradling Pines). The Steam guide recommends a shotgun.",
      ] },

    // ---------------- RDA facilities ----------------
    afop_ach_18: { cat: "rda",
      tip: "Destroy 10 RDA mining installations (the small drill towers on brown ground). Use Na'vi senses to highlight each sabotage point and sabotage all of them. 3 of the 36 fall during the story. Comes on the way to Reclaim Pandora." },
    afop_ach_19: { cat: "rda",
      tip: "Conquer 5 RDA outposts (walled fortresses) by sabotaging every highlighted object. Each gives a fast travel point. 3 of the 19 fall during the story. Large yellow crates inside give gear, which raises your level." },
    afop_ach_24: { cat: "rda", wide: true,
      tip: [
        "100% air quality means destroying every RDA site: 36 installations, 19 outposts and 3 bases (58 total, per Platget and the Wand map). PowerPyx lists only 35 installations, and the region counts below follow PowerPyx, so one installation is missing from them. Use the Wand map to find it. They show as brown ground on the map even under fog. Check the percentage at the Resistance HQ once the Cleaning the Air side quest appears, or at field labs (Steam guide).",
        "The story clears 3 installations, 3 outposts and 2 bases (Extractor Plant in Combined Forces, Drill Base Omega in Last Strike), so finish the story first. The third base, Laser Ore Processor Alpha in north Kinglor Forest, is optional for the story and is the hardest site in the game (level 20). Level up before you go.",
        "Some players report the percentage looking stuck. No source confirms a fix, so recheck the list for a missed site before assuming a bug. Sources do not say whether the DLC regions count toward this; they predate or ignore it.",
      ],
      steps: ["Installations: Kinglor Forest (10 open world)", "Installations: Upper Plains (15)", "Installations: Clouded Forest (7)", "Installations: 3 story (Welcome to the Resistance, main story, Last Strike)", "Installation 36 (missing from PowerPyx; find it on the Wand map)", "Outposts: Kinglor Forest (6)", "Outposts: Upper Plains (6)", "Outposts: Clouded Forest (4)", "Outposts: 3 story (Eye of Eywa, Pushing Back, A New Plan)", "Base: Extractor Plant (Combined Forces)", "Base: Drill Base Omega (Last Strike)", "Base: Laser Ore Processor Alpha (open world, level 20)"] },

    // ---------------- Skills, cooking, crafting ----------------
    afop_ach_3: { cat: "skills",
      tip: "Touch 3 red tarsyu flowers (12 exist, marked with red beams; Main Quest 4: Songs of the Ancestor gives the first one). The Deeper Connection flower opens only after you clear Laser Ore Processor Alpha. Each flower gives an ancestor skill and 2 skill points. Most sit on peaks or floating rocks, so get the ikran (Main Quest 11: Take Flight) first. Count shown at the bottom of the Skills menu." },
    afop_ach_31: { cat: "skills",
      tip: "Buy any 3 skills in each of the 5 base trees: Survivor, Warrior, Hunter, Maker, Rider (15 skills). Rider opens after Main Quest 11: Take Flight. Skill points come from quests, tarsyu saplings (1 each) and tarsyu flowers (2 each). The Steam guide says the DLC Sky Hunter tree does not count. Cheapest skills are fine." },
    afop_ach_17: { cat: "skills",
      tip: [
        "Buy every skill in one tree, then complete that tree's Apex Challenge (shown at the top of the tree). Rider has the fewest skills (9); the others have 12-13 (Avatar Wiki).",
        "Maker - The Bow Master: craft the Energizing Longbow from exquisite Dawnsheen Branch (tops of the arches, Stone Sentinels, Clouded Forest), exquisite Shaded Waterweed Bast (Tranquility Bulbs under the arches, northeast Pillar Canyon, Upper Plains) and exquisite Hammerhead Horn (hammerhead titanothere, Kinglor Forest, some near Dyer's Bowl; check it is exquisite before the kill). No fighting. Gamer Guides calls it the easiest.",
        "Rider - Death on Wings: stun a Samson and a Scorpion helicopter, then do an ikran flying takedown on each. Storm ammo stuns them (all shotguns, most shortbows).",
        "Survivor - The Perfect Hunt: one-arrow weak-spot kills on a feral viperwolf and a feral thanator (weak spots on the sides of the neck). Hunter - Restoring Harmony: clean kills on a hammerhead titanothere and a soundblast colossus.",
      ] },
    afop_ach_21: { cat: "skills",
      tip: "Unlock 3 specialty recipes. They come at random from wicker baskets, from some quest rewards, and from some NPCs. Only the Specialties section of the cooking station's Recipes menu counts, not regular recipes. Loot every wicker basket and this comes naturally." },
    afop_ach_22: { cat: "skills",
      tip: [
        "Craft any purple (superior) or yellow (exquisite) weapon or gear piece. First, claim the free designs in the Designs tab of each clan merchant (one in The Hollows, Stone Cloud Valley, Clouded Forest, per PowerPyx).",
        "At a clan crafting table, pin any missing materials, then use the map's material tracker. Material quality matters: check the outline color in Na'vi senses (green fine, purple superior, yellow exquisite). The Maker skill Stable Hands makes pristine harvests more likely.",
      ] },

    // ---------------- Side quests ----------------
    afop_ach_29: { cat: "side", flag: "bug", wide: true, missable: "Keep Kame'tire Part 3 for after the story. Finishing every Kame'tire contribution before you advance the story can stick Part 3 at 0/5 for good.",
      tip: [
        "Finish Part 3 of the Community Contributions for Aranahe (Kinglor Forest), Zeswa (Upper Plains) and Kame'tire (Clouded Forest). Interact with community baskets at the clan home and at camps (red tents on the map). Each basket gives one delivery request; the same basket never gives a second, so visit a different camp each time. Part 1 is 3 deliveries, Part 2 is 5, Part 3 is 7 (Kame'tire needs fewer).",
        "Deliveries are plants, animal parts and cooked meals. Store one of each item in the stash as you play, and pin needed items in the Hunter's Guide to see them on the map.",
        "Trap (PowerPyx, Apr 2024): if you reach the Clouded Forest and finish every Kame'tire contribution before you advance the story, Part 3 can stick at 0/5 for good. Leave Kame'tire Part 3 until after the story.",
        "Zeswa stuck at Part 2 is not a bug: it waits on Zeswa side quests. Commenters name Flavor of the Past, and the Clouded Sky quest where you help three people. Ubisoft's 2.5 notes still list 'Some Clan Contribution quests do not properly update' as a known issue.",
        "A PowerPyx commenter reports that gathering quests do not work in co-op. Do these solo.",
      ],
      steps: ["Aranahe Part 1", "Aranahe Part 2", "Aranahe Part 3", "Zeswa Part 1", "Zeswa Part 2 (needs Zeswa side quests)", "Zeswa Part 3", "Kame'tire Part 1", "Kame'tire Part 2", "Kame'tire Part 3 (after the story)"] },
    afop_ach_30: { cat: "side",
      tip: "Talk to Etuwa on the top floor of the Hometree (Aranahe clan home, Kinglor Forest) to start Steady Wings. Take the queen moth from the flower behind Etuwa and lead her to each green waypoint tree. Keep her stress low: no swimming, flying or combat. Running raises stress but is fine below the max. After each of the 3 parts, return to Etuwa for the next. One PowerPyx commenter's achievement failed to pop after Part 3; no fix is known.",
      steps: ["Steady Wings Part 1", "Steady Wings Part 2", "Steady Wings Part 3"] },

    // ---------------- The Sky Breaker (DLC 1) ----------------
    afop_ach_36: { cat: "skybreaker", flag: "season", missable: false,
      tip: [
        "The Sky Breaker story pack (Season Pass, Steam app 3005000) is set in the Heart of the Plains, a new area of the Upper Plains. Finish its quest When the Zakru Walk.",
        "Start requirement (Avatar Wiki, An Invitation): finish the main story first. The game also offers a skip to this pack after Main Quest 4, but the skip removes the main story from that save for good; decline it. The 2.5 notes say the loading screen into this pack takes longer than intended.",
      ] },
    afop_ach_35: { cat: "skybreaker", flag: "season",
      tip: "Sky Breaker story: finish the quest The Sky Breaker. Story-locked." },
    afop_ach_32: { cat: "skybreaker", flag: "season",
      tip: "Sky Breaker story: finish the quest The Bitter End. Story-locked; the global rates suggest it is the last of the three Sky Breaker story achievements." },
    afop_ach_34: { cat: "skybreaker", flag: "season",
      tip: "Only the 4 research points in the Heart of the Plains count, not field labs in the base map. At each, activate the point as you normally would and also donate 10 spare parts in the orange box. The achievement pops on the fourth. Bring 40 spare parts (small yellow crates drop them).",
      steps: ["Research point 1 (+10 spare parts)", "Research point 2 (+10 spare parts)", "Research point 3 (+10 spare parts)", "Research point 4 (+10 spare parts)"] },
    afop_ach_33: { cat: "skybreaker", flag: "season", wide: true,
      tip: [
        "Steam groups this with The Sky Breaker. Legendary rarity arrived with that pack's update (Title Update 4.0), and the legendary materials in the sources come from the two DLC maps.",
        "Simplest route the sources support: Koranu in the Heart of the Plains gives the Healer's Shawl design (legendary moss, any exquisite tooth, superior crimson rock orchid cone). Scrubber Moss, the legendary moss, grows on top of the floating stones there; the guide author found it on one of the smallest stones. Crimson Rock Orchid grows on a hilltop and needs a direhorse to gather. Other Koranu designs: Fortified Headgear, Champion's Armguard, Confident Waistcloth.",
        "Legendary animal parts come from elder or mature animals (for example an elder heartlands colossus for legendary heavy hide). The Steam legendary-materials guide recommends the Nimble Gatherer III food buff before gathering.",
        "Bladewing Moth Wings raise a material by one rarity tier per wing (Steam discussion). Ubisoft lists a known issue: they may not upgrade rarity while offline. The Steam 100% guide says a Secrets of the Spires story quest also has you craft a legendary item; whether an ikran saddle counts as gear for this is unconfirmed.",
      ] },

    // ---------------- Secrets of the Spires (DLC 2) ----------------
    afop_ach_37: { cat: "spires", flag: "season", missable: false,
      tip: [
        "Secrets of the Spires (Season Pass, Steam app 3005010) adds the Spires of the Clouded Forest. Finish its quest Skybound.",
        "The quest log offers Anufi's Favor, which skips the main story to start this pack. Do not use it on your main save. The skip blocks the main story on that save for good, which locks out Our Reclamation and the story achievements after Becoming (Avatar Wiki, Title Update 1.2 notes).",
      ] },
    afop_ach_38: { cat: "spires", flag: "season",
      tip: [
        "Spires story: finish the quest Into the Mountain.",
        "Trap in the Spires quest The Hunt: craft the saddle the quest asks for (the Defender's saddle), not a different one. One player crafted another and wasted the elder chiroptera hide, then had to find another elder (they hang from the ceiling in caves marked as elder nests). The same player reports that quest crafting must happen inside the Spires region; crafting it in the Heart of the Plains failed the objective.",
      ] },
    afop_ach_39: { cat: "spires", flag: "season", missable: false,
      tip: "Spires story: finish the quest The Fight for Home (the pack's last quest). Known bug: the objective Open Valkyrie's Cargo Door sometimes takes no damage. One Ikran Smash hit should open it slightly. If nothing happens, quit and restart that part of the mission; one player reports it then worked first try." },
    afop_ach_40: { cat: "spires", flag: "bug",
      tip: [
        "Season Pass (Spires). Unlock all 11 skills in the Memories of the Sky Hunter tree: Ikran Launch, Ikran Smash I and II, Crossbow Expert, Ikran Defense Tactics I and II, Sky Finisher, Energizing Dive, Ikran Fury I and II, Aerial Banquet (Avatar Wiki).",
        "Some skills unlock through the pack's main quests and one through a side quest (Steam guide). Reported bug (PSNProfiles forum): the counter sticks at 10/11 if you unlock skills while back on the main map. Claim every Sky Hunter skill while you are inside the Spires region.",
      ],
      steps: ["Ikran Launch", "Ikran Smash I", "Ikran Smash II", "Crossbow Expert", "Ikran Defense Tactics I", "Ikran Defense Tactics II", "Sky Finisher", "Energizing Dive", "Ikran Fury I", "Ikran Fury II", "Aerial Banquet"] },
    afop_ach_41: { cat: "spires", flag: "season",
      tip: "Smash 20 objects with Ikran Smash, which a Spires main quest unlocks. On PC the Steam guide says press V on the ikran. The Steam guide says objects and enemies both work. The skill breaks open certain structures and containers; the legendary-materials guide uses it to open the chiroptera nests and the Dark Root cave." },

    // ---------------- From the Ashes ----------------
    afop_ach_48: { cat: "ashes", flag: "ashes", missable: "Pick your base-game save when From the Ashes starts. No source says you can import it later.",
      tip: [
        "From the Ashes is a separate purchase (Steam app 3823590, not in the Season Pass). It launches from its own From the Ashes entry on the main menu and reports to this same Steam achievement list. You need the base game but not a finished story.",
        "This one: when you start From the Ashes, pick your base-game save so your own Sarentu appears in the story. It pops shortly into the opening. Create your base-game character and play some first; sources do not say whether you can import later if you skip it.",
      ] },
    afop_ach_42: { cat: "ashes", flag: "ashes",
      tip: "Perform one stealth finisher on an unaware enemy. The opening quest sets one up as a tutorial. If you miss it, do one on any RDA AMP from stealth." },
    afop_ach_50: { cat: "ashes", flag: "ashes", missable: "Lose the race in Welcome Home. Sources call the race scripted; if you can win it, expect to lose this on that save.",
      tip: "Story: an ikran race against your Sarentu in the quest Welcome Home (the second main quest). The achievement requires losing, and allthings.how calls the race scripted. Do not try to win; let the Sarentu finish first." },
    afop_ach_49: { cat: "ashes", flag: "ashes",
      tip: "Heal once with a dapophet pod picked from a plant. allthings.how says the quest Ash on the Wind (third main quest) gives a chance. Any heal from one counts." },
    afop_ach_43: { cat: "ashes", flag: "ashes",
      tip: "Story: unlocks when the story gives So'lek Warrior Senses, the meter that fills from dealing and taking damage. Cannot be missed." },
    afop_ach_44: { cat: "ashes", flag: "ashes", wide: true,
      tip: [
        "Rarest on the list. Buy the One Shot skill early with skill points, then start counting right away. Sources say the count adds up over the expansion.",
        "Rules from Steam players: stay undetected (the marker in Na'vi senses must be white), and hit the pilot dead centre in the cockpit glass. A shellbreaker arrow from stealth is the suggested shot. It does not work on AMPs with armored metal plates over the pilot.",
        "Pin AMP types with an unarmored cockpit in the Hunter's Guide; they then show purple instead of red. Armored AMPs can still count: break the armor, break line of sight until they stop searching, then come back for the stealth shot. A PSNProfiles user stalled at 40/50 because One Shot failed on elite AMPs.",
        "Farm spots: after the From the Ashes story, the Home Tree base keeps patrolling AMPs (Steam guide). A PSNProfiles user names the large camp west of the Home Tree, with an AMP type whose window has a metal grate, as a one-shot every time. Some report the count carries across playthroughs; unconfirmed.",
      ] },
    afop_ach_45: { cat: "ashes", flag: "ashes", wide: true,
      tip: [
        "8 Zeykoma fruit in the burned Kinglor Forest and The Ravines. Each adds a health segment. PatchCrazy says tana'ring flowers often surround the plant.",
        "The Steam 100% guide and PatchCrazy describe the spots differently and do not map one to one. The checklist follows the Steam guide. PatchCrazy's spots: a clifftop near Fort Prometheus; between Spinner's Circle and Rising Spires near Nangi's Longing; a cave under a huge tree's roots at Fallen Grotto (go left, drop through the opening); the RDA site Teylan mentions near The Ravines (climb the left side); near Spinner's Circle by Shadow Hollow, where the Mangkwan raider Zatslew may appear; near Gossamer Lakes by The Boundless Range; Dawn's Glade during A Blessing; Glade of Light near Silk Woods, beside a stream.",
        "One comes during the main quest A Blessing (Dawn's Glade): follow the white tana'ring trail while you search for Teylan.",
      ],
      steps: [
        "Right above So'lek's camp",
        "Dawn's Glade, Rising Spires, during a Save Your People quest (A Blessing)",
        "East of Fort Prometheus, above the waterfall in Shadow Wood (Scorpion helicopters guard it)",
        "Inside Fallen Grotto, Spinner's Circle, with a So'lek stash",
        "West of the Home Tree, northeast of Eagle Echo, Silk Woods",
        "South side of Raven Alpha, The Ravines",
        "North of Shadow Hollow, Spinner's Circle",
        "North of Nangi's Landing, east of Dawn's Glade, burnt forest (RDA guard it)",
      ] },
    afop_ach_46: { cat: "ashes", flag: "bug",
      tip: [
        "From the Ashes purchase. Most gear sets unlock from the Save Your People and Sabotage RDA quests. The rest sit in So'lek stashes: a map at So'lek's camp marks caves, which the map shows with large flowers. Reach each cave, clear its obstacle and loot the stash. One stash is in Fallen Grotto (Spinner's Circle) with a Zeykoma fruit.",
        "Reported problem: a Steam user at 100% with 6 items in every gear slot still lacked it, and a PSNProfiles thread reports it not popping, with no fix. A TrueAchievements poster says the Windward quest chain never started for them, blocking this and We See You. No source names the exact set list.",
      ] },
    afop_ach_47: { cat: "ashes", flag: "ashes", missable: false,
      tip: [
        "Finish every quest in both From the Ashes quest groups, Save Your People and Sabotage RDA Operations. Expect around 20 hours for the whole expansion (Ubisoft FAQ).",
        "Ubisoft 2.5 known issue: the expansion's story progress displays 90% even after every quest is done. Judge by the quest log, not that number. If the Windward quest chain never appears, see Fashion-Forward.",
        "Separate catch (Avatar Wiki): scan the Tree of Voices Sapling near the start, or you can miss 100% Hunter's Guide completion. That is not this achievement, but it is permanent.",
      ] },
    afop_ach_51: { cat: "ashes", flag: "ashes",
      tip: "During the story So'lek and Teylan free a captured fireback mastodon. Later you find it on the east side of The Ravines, near Maintenance Post Bravo. Press the interact key (E on PC), approach and watch the cutscene, where So'lek pulls a tusk fragment from under its eye. Do not attack it." },
    afop_ach_52: { cat: "ashes", flag: "ashes",
      tip: "Defeat the four Mangkwan warband leaders: Rakx, Zari, Ka'sem and Wukula. You meet them while doing Save Your People quests and taking down RDA sites. It pops when Wukula, the last, falls near the end.",
      steps: ["Rakx", "Zari", "Ka'sem", "Wukula"] },
  },
};
