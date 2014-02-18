#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Parse monster setting files and output entries"""
# Ideas:
# - column output
import argparse
import codecs
import csv
import cStringIO
import glob
import os
import sys
import xml.etree.ElementTree as ET


setting_index = {"Dark Woods": 228, "Folk of the Realm": 227,
                 "Lower Depths": 229, "Planar Powers": 230,
                 "Ravenous Hordes": 229, "Twisted Experiments": 229,
                 "Undead Legions": 228, "Cavern Dwellers": 227,
                 "Swamp Denizens": 228}
monster_index = {"aboleth": 297, "abomination": 255, "acolyte": 313,
                 "adventurer": 313, "angel": 305, "ankheg": 233,
                 "apocalypse dragon": 297, "apocalypse dragon": 297,
                 "assassin vine": 265, "bakunawa": 243, "bandit": 314,
                 "bandit king": 314, "banshee": 255, "barbed devil": 305,
                 "basilisk": 243, "black pudding": 244, "black pudding": 244,
                 "blink dog": 265, "blink dog": 265, "bulette": 287,
                 "cave rat": 233, "centaur": 266, "chain devil": 306,
                 "chaos ooze": 266, "chaos spawn": 298, "chimera": 287,
                 "choker": 234, "chuul": 298, "cloaker": 234,
                 "cockatrice": 267, "concept elemental": 306,
                 "corrupter": 307, "coutal": 244, "crocodilian": 245,
                 "deep elf assassin": 299, "deep elf priest": 300,
                 "deep elf swordmaster": 299, "derro": 288, "devourer": 256,
                 "digester": 288, "djinn": 307, u"doppelg\xe4nger": 245,
                 "dragon": 300, "dragon turtle": 246, "dragon whelp": 246,
                 "dragonbone": 256, "draugr": 257, "dryad": 267,
                 "dwarven warrior": 235, "eagle lord": 268,
                 "earth elemental": 235, "ekek": 247,
                 "elvish high arcanist": 269, "elvish warrior": 268,
                 "ethereal filcher": 289, "ettin": 289, "fire beetle": 236,
                 "fire eels": 247, "flesh golem": 291, "flesh golem": 291,
                 "fool": 314, "formian centurion": 276, "formian drone": 275,
                 "formian queen": 277, "formian taskmaster": 275,
                 "frogman": 248, "gargoyle": 236, "gelatinous cube": 237,
                 "ghost": 257, "ghoul": 258, "girallon": 290,
                 "gnoll alpha": 279, "gnoll emissary": 278,
                 "gnoll tracker": 278, "goblin": 237, "goblin orkaster": 237,
                 "goliath": 238, "gray render": 301, "griffin": 269,
                 "guardsman": 315, "halfling thief": 315,
                 "halfling thief": 315, "hedge wizard": 316,
                 "hell hound": 308, "high priest": 316, "hill giant": 270,
                 "hill giant": 270, "hunter": 316, "hydra": 248, "imp": 308,
                 "inevitable": 309, "iron golem": 290, "knight": 317,
                 "kobold": 249, "kraken": 291, "larvae": 309, "lich": 258,
                 "lizardman": 249, "maggot-squid": 239, "magmin": 301,
                 "manticore": 292, "medusa": 250, "merchant": 317,
                 "minotaur": 302, "mohrg": 259, "mummy": 259, "naga": 302,
                 "nightmare": 310, "nightwing": 260, "noble": 317, "ogre": 270,
                 "orc berserker": 280, "orc bloodwarrior": 280,
                 "orc breaker": 281, "orc one-eye": 281,
                 "orc shadowhunter": 283, "orc shaman": 282, "orc slaver": 282,
                 "orc warchief": 283, "otyugh": 238, "owlbear": 292,
                 "peasant": 318, "pegasus": 293, "purple worm": 239,
                 "quasit": 310, "razor boar": 270, "rebel": 318, "roper": 240,
                 "rot grub": 240, "rot grub": 240, "rust monster": 293,
                 "sahuagin": 250, "salamander": 303, "satyr": 271,
                 "sauropod": 251, "shadow": 260, "sigben": 261,
                 "skeleton": 261, "soldier": 319, "spectre": 262,
                 "spiderlord": 241, "sprite": 271, "spy": 319,
                 "swamp shambler": 251, "the tarrasque": 311, "tinkerer": 319,
                 "treant": 272, "triton noble": 285, "triton spy": 284,
                 "triton sub-mariner": 285, "triton tidecaller": 284,
                 "troglodyte": 241, "troll": 252, "vampire": 262,
                 "werewolf": 272, "wight-wolf": 263, "will-o-wisp": 252,
                 "word demon": 311, "worg": 273, "xorn": 294, "zombie": 263}
monster_tags_org = ["Solitary", "Group", "Horde"]
monster_tags_size = ["Tiny", "Small", "Large", "Huge"]
weapon_tags_range = ["Hand", "Close", "Reach", "Near", "Far"]

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        new_row = list()
        for s in row:
            if s is None:
                s = ""
            new_row.append(s)
        self.writer.writerow([s.encode("utf-8") for s in new_row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def parser_setup():
    """Instantiate, configure and return an ArgumentParser instance."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-f", "--format", choices=["csv", "plain"],
                    help="output format")
    ap.add_argument("file", nargs="*",
                    help="File(s) to parse.")
    args = ap.parse_args()
    return args


def parse(xml_file):
    tree = ET.parse(xml_file)
    body = tree.find("Body")
    setting = tree.find("h1").text
    setting_page = setting_index[setting]
    second = False
    for element in body:
        if element.tag == "p":
            style = element.attrib[
                "{http://ns.adobe.com/AdobeInDesign/4.0/}pstyle"]
            if style == "MonsterName":
                # Initialize variables
                name = None
                monster_desc = list()
                monster_org = list()
                monster_size = list()
                hp = None
                armor = None
                weapon = None
                weapon_desc = list()
                weapon_range = list()
                qualities = None
                primary_instinct = None
                instincts = list()
                description = None
                monster_page = None

                name = element.text.strip()
                monster_page = monster_index[name.lower()]
                # Not all monsters have tags (many of the Folk do not)
                if len(element) > 0:
                    # Monster tags
                    for tag in element[0].text.split(","):
                        tag = tag.strip()
                        if tag in monster_tags_org:
                            ti = monster_tags_org.index(tag)
                            monster_org.insert(ti, tag)
                        elif tag in monster_tags_size:
                            ti = monster_tags_size.index(tag)
                            monster_size.insert(ti, tag)
                        else:
                            monster_desc.append(tag)
            elif style == "MonsterStats":
                if second:
                    # Weapon tags
                    for tag in element[0].text.split(","):
                        tag = tag.strip()
                        if tag in weapon_tags_range:
                            ti = weapon_tags_range.index(tag)
                            weapon_range.insert(ti, tag)
                        else:
                            weapon_desc.append(tag)
                    second = False
                else:
                    for stat in element.text.split("\t"):
                        if stat.endswith(")"):
                            # Weapon damage
                            weapon = stat
                        elif stat.endswith("HP"):
                            # HP
                            hp = stat.split(" ")[0]
                        elif stat.endswith("Armor"):
                            # Armor
                            armor = stat.split(" ")[0]
                    second = True
            elif style == "MonsterQualities":
                qualities = element[0].tail
                qualities = qualities.strip()
            elif style == "MonsterDescription":
                description = element.text
                if len(element) > 0:
                    for e in element:
                        if e.text != "Instinct":
                            description = "%s %s" % (description, e.text)
                            description = "%s %s" % (description, e.tail)
                        else:
                            primary_instinct = e.tail
                            primary_instinct = primary_instinct.lstrip(":")
                            primary_instinct = primary_instinct.strip()
            elif style == "NoIndent":
                # Treant has non-standard description
                description = "%s, %s" % (description, element.text)
                if len(element) > 0:
                    primary_instinct = element[0].tail
                    primary_instinct = primary_instinct.lstrip(":")
                    primary_instinct = primary_instinct.strip()

        elif element.tag == "ul":
            for item in element:
                instincts.append(item.text)

            # Process Record
            # Create monster tags string
            monster_tags = None
            if monster_desc:
                monster_desc.sort()
                monster_tags = ", ".join(monster_desc)
            if monster_org:
                monster_org = ", ".join(monster_org)
                if monster_tags:
                    monster_tags = "%s ~ %s" % (monster_tags, monster_org)
                else:
                    monster_tags = monster_org
            if monster_size:
                monster_size = ", ".join(monster_size)
                if monster_tags:
                    monster_tags = "%s ~ %s" % (monster_tags, monster_size)
                else:
                    monster_tags = monster_size
            # Create monster tags string
            weapon_tags = None
            if weapon_range:
                weapon_tags = ", ".join(weapon_range)
            if weapon_desc:
                weapon_desc = ", ".join(weapon_desc)
                if weapon_tags:
                    weapon_tags = "%s ~ %s" % (weapon_tags, weapon_desc)
                else:
                    weapon_tags = weapon_desc
            # Create instincts string
            instincts.insert(0, primary_instinct)
            instincts = ", ".join(instincts)
            instincts = "INSTINCTS: %s" % instincts
            # Create qualities string
            if qualities:
                qualities = "QUALITIES: %s" % qualities
            monsters.append((name, monster_tags, hp, armor, weapon,
                             weapon_tags, qualities, instincts, description,
                             str(monster_page), setting, str(setting_page)))


# setup
args = parser_setup()

if args.format == "csv":
    csvwriter = UnicodeWriter(sys.stdout, quoting=csv.QUOTE_ALL,
                              lineterminator="\n")
    csvwriter.writerow(("name", "monster_tags", "hp", "armor", "weapon",
                        "weapon_tags", "qualities", "instincts",
                        "description", "monster_page", "setting",
                        "setting_page"))

monsters = list()

# parse logs (into data dict)
xml_files = set()
for file_glob in args.file:
    for path in glob.iglob(file_glob):
        if os.path.exists(path):
            path = os.path.abspath(path)
            xml_files.add(path)
for xml_file in xml_files:
    parse(xml_file)

monsters.sort()

for m in monsters:
    if args.format == "csv":
        csvwriter.writerow(m)
    else:
        for i in m:
            if i != None:
                print i
        print
