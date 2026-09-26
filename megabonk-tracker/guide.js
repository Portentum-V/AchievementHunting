// Guide data for the Megabonk tracker.
// Categories follow the Steam guide "Megabonk 100% Achievement Guide"
// (https://steamcommunity.com/sharedfiles/filedetails/?id=3579942583), which groups
// achievements by how you unlock them. Hard runs and Graveyard are added for content
// newer than that guide. Hat strategies come from "Every hat achievement"
// (https://steamcommunity.com/sharedfiles/filedetails/?id=3660638933).
// Keys are lower-case Steam API names. Achievements without a tip show Steam's description.
window.GUIDE = {
  appid: "3405340",
  title: "Megabonk",
  titleAccent: "bonk",
  subtitle: "Achievement tracker, synced from Steam",
  credit: "Categories and strategies from the Steam community guides \"Megabonk 100% Achievement Guide\" and \"Every hat achievement\".",
  defaultStatus: "todo",
  colors: {
    light: { accent: "#6a3cc9", accent2: "#b07400" },
    dark: { accent: "#a88bff", accent2: "#ffc94d" },
  },
  flags: {
    grind: { label: "Cumulative across runs", tone: "accent2" },
    run: { label: "Single run", tone: "accent" },
  },
  categories: [
    ["hats", "Hats"],
    ["progress", "Progression"],
    ["kills", "Kill counts"],
    ["easy", "Easy if you know"],
    ["upgrades", "Weapon & tome upgrades"],
    ["character", "Character-specific"],
    ["hard", "Hard runs"],
    ["challenges", "Challenges"],
    ["graveyard", "Graveyard"],
  ],
  achievements: {
    // Hats. All 7 remaining achievements are here, so they carry the detailed tips.
    a_hatcrown: { cat: "hats", flag: "grind", wide: true,
      tip: ["Rank XP comes from XP earned in a run and from moving on to the next stage, so full runs that clear stages rank a character fastest.",
            "Expect a long grind. Rank the characters you still need to play for other goals first."],
      steps: ["Fox", "Sir Oofie", "Megachad", "CL4NK", "Monke", "Calcium", "Ninja", "Robinette", "Tony McZoom", "Vlad",
              "Sir Chadwell", "Birdo", "Dicehead", "Spaceman", "Noelle", "Bush", "Bandit", "Ogre", "Athena", "Amog", "Roberto"] },
    a_hattophatlong: { cat: "hats", flag: "run", wide: true,
      tip: ["Needs 300,000 kills on Forest in one run. The hat guide's author reached 600,000 with this build.",
            "Top Hat (100,000 kills) unlocks on the way."],
      steps: [
        "Play Dicehead. Weapons: Dexecutioner, Katana, Dragon's Breath. Tomes: Luck, XP, Cursed, Chaos.",
        "Toggle off every item except Key, Echo Shard, Kevin, Grandma's Secret Tonic, Sucky Magnet, Lightning Orb, Anvil, Joe's Dagger, Pot (stainless steel), Wizard's Hat.",
        "Restart until the stage has 2 microwaves. Use them to stack Keys or Time Bracelets early.",
        "Prefer Shady Guys over moais early.",
        "Activate 2 Boss Curses on stage 1, not 3 or more. Aim for about 30% difficulty at the end of stage 1.",
        "Find a second weapon fast: Dragon's Breath, then Dexecutioner, then Katana.",
        "Level XP, then Luck, then Dragon's Breath, then Dexecutioner. Look for the green credit card and Grandma's Secret Tonic.",
        "Shrines: powerup drop chance, then projectile count, crit damage, damage to elites, elite spawn.",
        "Ban at once: Power Gloves, Ice Cube, Giant Fork. Ban after one copy: Spicy Meatball, Sucky Magnet. Ban Lightning Orb after 4 copies and Za Warudo after 10.",
        "Get Sucky Magnet on stage 2, so you can stand beyond the map edge and still collect XP.",
        "Stay after the timer: up to 1:30 on stage 1, 8 to 10 minutes on stage 2, up to 14 minutes on stage 3, then as long as you survive in the final arena.",
        "On stages 2 and 3, stand in a corner beyond the map near the boss portal. Pop Za Warudo when the swarm reaches you.",
      ] },
    a_hattophat: { cat: "hats", flag: "run",
      tip: "Needs 100,000 kills on Forest in one run. Use the Looooong Top Hat build; this one unlocks on the way." },
    a_hatmicrowave: { cat: "hats", flag: "grind",
      tip: "Use every microwave you find. The count carries across runs." },
    a_hatshadyblue: { cat: "hats", flag: "grind",
      tip: "Buy from every Rare Shady Guy you meet. Purchases count across runs." },
    a_hatshadypink: { cat: "hats", flag: "grind",
      tip: "Buy from every Epic Shady Guy you meet. Purchases count across runs." },
    a_hatshadygold: { cat: "hats", flag: "grind",
      tip: "Buy from every Legendary Shady Guy you meet. Purchases count across runs." },
    a_hatshadyblack: { cat: "hats", flag: "grind" },
    a_santahat: { cat: "hats" },
    a_hatfrog1: { cat: "hats" }, a_hatfrog2: { cat: "hats" }, a_hatfrog3: { cat: "hats" },
    a_hatkevin: { cat: "hats", flag: "grind" },
    a_hatsheriff: { cat: "hats" }, a_hatheadset: { cat: "hats" }, a_hatmagic: { cat: "hats" },
    a_hatmedieval: { cat: "hats" }, a_hatpilot: { cat: "hats" }, a_hatclown: { cat: "hats" },
    a_hatsunglasses: { cat: "hats" }, a_hatpot: { cat: "hats" }, a_hatcheese: { cat: "hats" },

    // Progression and quest milestones.
    a_clank: { cat: "progress" }, a_robinette: { cat: "progress" }, a_ninja: { cat: "progress" },
    a_vlad: { cat: "progress" }, a_chadwell: { cat: "progress" }, a_energycore: { cat: "progress" },
    a_refresh: { cat: "progress" }, a_weaponslots: { cat: "progress" }, a_skip: { cat: "progress" },
    a_tomeslots: { cat: "progress" }, a_banish: { cat: "progress" }, a_weaponslots2: { cat: "progress" },
    a_tomeslots2: { cat: "progress" }, a_dicehead: { cat: "progress" }, a_toggler: { cat: "progress" },

    // Kill counts.
    a_revolver: { cat: "kills" }, a_bloodtome: { cat: "kills" }, a_idlejuice: { cat: "kills" },
    a_calcium: { cat: "kills" }, a_ogre: { cat: "kills" }, a_axe: { cat: "kills" },
    a_brassknuckles: { cat: "kills" }, a_dexecutioner: { cat: "kills" }, a_joesdagger: { cat: "kills" },
    a_icecrystal: { cat: "kills" }, a_dragonfire: { cat: "kills" }, a_lightningorb: { cat: "kills" },
    a_grandmastonic: { cat: "kills" }, a_cannon: { cat: "kills" }, a_mines: { cat: "kills" },
    a_toxicbarrel: { cat: "kills" }, a_birdo: { cat: "kills" },

    // Easy once you know about them.
    a_forbiddenjuice: { cat: "easy" }, a_quantitytome: { cat: "easy" }, a_aura: { cat: "easy" },
    a_key: { cat: "easy" }, a_xptome: { cat: "easy" }, a_goldensneakers: { cat: "easy" },
    a_attractiontome: { cat: "easy" }, a_demonicblade: { cat: "easy" }, a_demonicblood: { cat: "easy" },
    a_chonkplate: { cat: "easy" }, a_thornstome: { cat: "easy" }, a_suckymagnet: { cat: "easy" },
    a_tornado: { cat: "easy" }, a_frostwalker: { cat: "easy" }, a_kevin: { cat: "easy" },
    a_noelle: { cat: "easy" }, a_poisongloves: { cat: "easy" }, a_amog: { cat: "easy" },
    a_curseddoll: { cat: "easy" }, a_wallhugger: { cat: "easy" }, a_bananarang: { cat: "easy" },
    a_monke: { cat: "easy" }, a_boombox: { cat: "easy" }, a_bush: { cat: "easy" },
    a_bandit: { cat: "easy" }, a_katana: { cat: "easy" }, a_shotgun: { cat: "easy" },
    a_lucktome: { cat: "easy" },

    // Weapon and tome upgrade levels.
    a_battery: { cat: "upgrades" }, a_turbosocks: { cat: "upgrades" }, a_turboskates: { cat: "upgrades" },
    a_megachad: { cat: "upgrades" }, a_shatteredknowledge: { cat: "upgrades" }, a_leechingcrystal: { cat: "upgrades" },
    a_echoshard: { cat: "upgrades" }, a_athena: { cat: "upgrades" }, a_blackhole: { cat: "upgrades" },
    a_sniperrifle: { cat: "upgrades" }, a_bloodmagic: { cat: "upgrades" }, a_dice: { cat: "upgrades" },
    a_durationtome: { cat: "upgrades" }, a_wirelessdaggers: { cat: "upgrades" },

    // One specific character.
    a_desert: { cat: "character" }, a_spacenoodle: { cat: "character" }, a_aegis: { cat: "character" },
    a_dragonsbreath: { cat: "character" }, a_gasmask: { cat: "character" }, a_armortome: { cat: "character" },
    a_eagleclaw: { cat: "character" }, a_sluttyrocket: { cat: "character" }, a_demonicsoul: { cat: "character" },
    a_bloodycleaver: { cat: "character" },

    // One-off feats in a run: bosses, curses, the final swarm.
    a_cursedtome: { cat: "hard" }, a_speedboi: { cat: "hard" }, a_bossbuster: { cat: "hard" },
    a_tacticalglasses: { cat: "hard" }, a_poisonflask: { cat: "hard" }, a_holybook: { cat: "hard" },
    a_gamergoggles: { cat: "hard" }, a_herosword: { cat: "hard" }, a_corruptedsword: { cat: "hard" },
    a_cursedgloves: { cat: "hard" }, a_skuleg: { cat: "hard" }, a_chaostome: { cat: "hard" },
    a_cactus: { cat: "hard" }, a_quinsmask: { cat: "hard" }, a_ghost: { cat: "hard" },
    a_bob: { cat: "hard" }, a_soulharvester: { cat: "hard" },

    // Challenge counts.
    a_tony: { cat: "challenges" }, a_anvil: { cat: "challenges" }, a_challenges1: { cat: "challenges" },
    a_spaceman: { cat: "challenges" }, a_challenges2: { cat: "challenges" }, a_challenges3: { cat: "challenges" },
    a_challenges4: { cat: "challenges" },

    // Graveyard map and its crypt.
    a_graveyard: { cat: "graveyard" }, a_pumpkin: { cat: "graveyard" }, a_snek: { cat: "graveyard" },
    a_potsteel: { cat: "graveyard" }, a_roberto: { cat: "graveyard" }, a_wizardshat: { cat: "graveyard" },
    a_scythe: { cat: "graveyard" }, a_bobslantern: { cat: "graveyard" }, a_oldmask: { cat: "graveyard" },
  },
};
