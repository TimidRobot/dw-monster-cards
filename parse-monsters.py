#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Ideas:
# - column output
# - yaml import/export
#   - separate data and programming
"""Parse monster setting files and output entries"""
# Standard library
import argparse
import codecs
import csv
import cStringIO
import glob
import os
from pprint import pprint
import sys
from xml.etree import ElementTree
# Third-party
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import ttfonts
from reportlab.platypus import (BaseDocTemplate, Frame, FrameBreak,
                                PageTemplate, Paragraph, Spacer)
from reportlab.platypus.tables import Table


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
        # ... and re-encode it into the target encoding
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
    ap.add_argument("-d", "--debug", action="store_true",
                    help="debug")
    ap.add_argument("-f", "--format", choices=["csv", "pdf", "plain"],
                    help="output format")
    ap.add_argument("file", nargs="*",
                    help="File(s) to parse.")
    args = ap.parse_args()
    return args


def parse(xml_file):
    tree = ElementTree.parse(xml_file)
    body = tree.find("Body")
    second = False
    setting = tree.find("h1").text
    setting_reference = setting_index[setting]
    for element in body:
        if element.tag == "p":
            style = element.attrib[
                "{http://ns.adobe.com/AdobeInDesign/4.0/}pstyle"]
            # MonsterName - name, tags
            if style == "MonsterName":
                # START - MonsterName is first p element attrib/style in
                #         monster_setting XML files
                # Initialize variables
                m = dict()
                m["name"] = None
                m["tags_desc"] = list()
                m["tags_org"] = list()
                m["tags_size"] = list()
                m["hp"] = None
                m["armor"] = None
                m["weapon"] = {"name": None, "damage": None,
                               "tags_desc": list(), "tags_range": list()}
                m["qualities"] = list()
                m["instincts"] = list()
                m["description"] = ""
                m["reference"] = None
                m["setting"] = setting
                m["setting_reference"] = setting_reference

                m["name"] = element.text.strip()
                m["reference"] = monster_index[m["name"].lower()]
                # Tags
                if len(element) > 0:
                    for tag in element[0].text.split(","):
                        tag = tag.strip()
                        if tag in monster_tags_org:
                            ti = monster_tags_org.index(tag)
                            m["tags_org"].insert(ti, tag)
                        elif tag in monster_tags_size:
                            ti = monster_tags_size.index(tag)
                            m["tags_size"].insert(ti, tag)
                        else:
                            m["tags_desc"].append(tag)
            # MonsterStats - Armor, HP, Weapon
            elif style == "MonsterStats":
                # Second occurrence is weapon tags
                if second:
                    # Weapon tags
                    for tag in element[0].text.split(","):
                        tag = tag.strip()
                        if tag in weapon_tags_range:
                            ti = weapon_tags_range.index(tag)
                            m["weapon"]["tags_range"].insert(ti, tag)
                        else:
                            m["weapon"]["tags_desc"].append(tag)
                    second = False
                # First occurrence is armor, hp, weapon name, or weapon damage
                else:
                    for stat in element.text.split("\t"):
                        # Weapon name and damage
                        name, damage = None, None
                        if stat.endswith(")"):
                            name, damage = stat.split("(")
                            m["weapon"]["name"] = name.strip()
                            damage = damage.strip(")")
                            m["weapon"]["damage"] = damage.strip()
                        # HP
                        elif stat.endswith("HP"):
                            m["hp"] = stat.split(" ")[0]
                        # Armor
                        elif stat.endswith("Armor"):
                            m["armor"] = stat.split(" ")[0]
                    second = True
            elif style == "MonsterQualities":
                for quality in element[0].tail.split(","):
                    m["qualities"].append(quality.strip())
            elif style == "MonsterDescription":
                if element.text:
                    m["description"] = element.text
                if len(element) > 0:
                    for e in element:
                        if e.text != "Instinct":
                            if e.text:
                                if e.tag == "em":
                                    text = "<i>%s</i>" % e.text
                                else:
                                    text = e.text
                                m["description"] = "%s%s" % (m["description"],
                                                             text)
                            if e.tail:
                                m["description"] = "%s%s" % (m["description"],
                                                             e.tail)
                        else:
                            instinct = e.tail
                            instinct = instinct.lstrip(":")
                            m["instincts"].insert(0, instinct.strip())
            elif style == "NoIndent":
                # Treant has non-standard description
                m["description"] = "%s, %s" % (m["description"], element.text)
                if len(element) > 0:
                    instinct = e.tail
                    instinct = instinct.lstrip(":")
                    m["instincts"].insert(0, instinct.strip())

        elif element.tag == "ul":
            for item in element:
                m["instincts"].append(item.text)

            # END - ul is last element in monster_setting XML files
            monsters[m["name"]] = m


def combine_monster_tags(monster_dictionary, formatted=False):
    m = monster_dictionary
    tags_combined = None
    if m["tags_desc"]:
        m["tags_desc"].sort()
        tags_combined = ", ".join(m["tags_desc"])
    if m["tags_org"]:
        m["tags_org"] = ", ".join(m["tags_org"])
        if tags_combined:
            tags_combined = "%s ~ %s" % (tags_combined, m["tags_org"])
        else:
            tags_combined = m["tags_org"]
    if m["tags_size"]:
        m["tags_size"] = ", ".join(m["tags_size"])
        if tags_combined:
            tags_combined = "%s ~ %s" % (tags_combined, m["tags_size"])
        else:
            tags_combined = m["tags_size"]
    if formatted:
        if tags_combined:
            tags_combined = "<i>%s</i>" % tags_combined
    return tags_combined


def combine_weapon(monster_dictionary, formatted=True):
    w = monster_dictionary["weapon"]
    weapon = None
    tags = None
    if w["name"] and w["damage"]:
        weapon = "%s (%s)" % (w["name"], w["damage"])
    else:
        return weapon
    if w["tags_desc"]:
        tags = ", ".join(w["tags_desc"])
    if w["tags_range"]:
        w["tags_range"] = ", ".join(w["tags_range"])
        if tags:
            tags = "%s ~ %s" % (tags, w["tags_range"])
        else:
            tags = w["tags_range"]
    if tags:
        if formatted:
            weapon = "%s<br /><i>%s</i>" % (weapon, tags)
        else:
            weapon = "%s %s" % (weapon, tags)
    return weapon


def pdf_create_page(m):
    # Name, HP, Armor
    hp_label = None
    hp_value = None
    armor_label = None
    armor_value = None
    if m["hp"]:
        hp_label = "HP:"
        hp_value = m["hp"]
    if m["armor"]:
        armor_label = "Armor:"
        armor_value = m["armor"]
    table = [[m["name"], hp_label, hp_value],
             ["", armor_label, armor_value]]
    style = [("LINEABOVE", (0, 0), (2, 0), 1, colors.black),
             ("LEFTPADDING", (0, 0), (2, 1), 0),
             ("RIGHTPADDING", (0, 0), (2, 1), 0),
             ("BOTTOMPADDING", (0, 0), (2, 1), 0),
             ("TOPPADDING", (0, 0), (2, 0), (space / 2)),
             ("TOPPADDING", (0, 1), (2, 1), 0),
             ("FONT", (0, 0), (0, 1), "Times-Roman", 16),
             ("VALIGN", (0, 0), (0, 1), "TOP"),
             ("SPAN", (0, 0), (0, 1)),
             ("FONT", (1, 0), (2, 1), font_default, 8),
             ("ALIGN", (1, 0), (2, 1), "RIGHT"),
             ]
    elements.append(Table(table, [(2.55 * inch) - 8, 0.9 * inch, 0.3 * inch],
                          style=style))
    # Tags
    monster_tags = combine_monster_tags(m, formatted=True)
    if monster_tags:
        elements.append(Paragraph(monster_tags, style_hang))
    # Weapon
    weapon = combine_weapon(m, formatted=True)
    if weapon:
        elements.append(Paragraph(weapon, style_hang))
    # Instincts
    if m["instincts"]:
        elements.append(Spacer(box_width, space))
        label = Paragraph("<i>Instincts</i>", style_default)
        items = list()
        for item in m["instincts"]:
            items.append(Paragraph(item, style_list))
        table = [[label, items]]
        style = [("LEFTPADDING", (0, 0), (1, 0), 0),
                 ("RIGHTPADDING", (0, 0), (1, 0), 0),
                 ("BOTTOMPADDING", (0, 0), (1, 0), 0),
                 ("TOPPADDING", (0, 0), (1, 0), 0),
                 ("VALIGN", (0, 0), (1, 0), "TOP"),
                 ]
        elements.append(Table(table, [0.65 * inch, (3.1 * inch) - 8],
                              style=style))
    # Qualities
    if m["qualities"]:
        elements.append(Spacer(box_width, space))
        label = Paragraph("<i>Qualities</i>", style_default)
        items = list()
        for item in m["qualities"]:
            items.append(Paragraph(item, style_list))
        table = [[label, items]]
        style = [("LEFTPADDING", (0, 0), (1, 0), 0),
                 ("RIGHTPADDING", (0, 0), (1, 0), 0),
                 ("BOTTOMPADDING", (0, 0), (1, 0), 0),
                 ("TOPPADDING", (0, 0), (1, 0), 0),
                 ("VALIGN", (0, 0), (1, 0), "TOP"),
                 ]
        elements.append(Table(table, [0.65 * inch, (3.1 * inch) - 8],
                              style=style))
    # Description
    elements.append(Spacer(box_width, space))
    table = [[Paragraph(m["description"], style_desc)]]
    style = [("LINEABOVE", (0, 0), (0, 0), 0.5, colors.black),
             ("LINEBELOW", (0, 0), (0, 0), 0.5, colors.black),
             ("LEFTPADDING", (0, 0), (0, 0), 0),
             ("RIGHTPADDING", (0, 0), (0, 0), 0),
             ("BOTTOMPADDING", (0, 0), (0, 0), (space / 2)),
             ("TOPPADDING", (0, 0), (0, 0), (space / 2)),
             ("VALIGN", (0, 0), (0, 0), "TOP"),
             ]
    elements.append(Table(table, [box_width - 8],
                          style=style))
    # References
    #elements.append(Spacer(box_width, space))
    reference = "%s of the %s<br />[DW %d, %d]" % (m["name"], m["setting"],
                                                   m["reference"],
                                                   m["setting_reference"])
    elements.append(Paragraph(reference, style_ref))
    # Next card
    elements.append(FrameBreak())


# setup
args = parser_setup()
monsters = dict()
xml_files = set()
# CSV
if args.format == "csv":
    csvwriter = UnicodeWriter(sys.stdout, quoting=csv.QUOTE_ALL,
                              lineterminator="\n")
    csvwriter.writerow(("name", "monster_tags", "hp", "armor", "weapon",
                        "weapon_tags", "qualities", "instincts",
                        "description", "monster_page", "setting",
                        "setting_page"))
# PDF
elif args.format == "pdf":
    elements = list()
    frames = list()
    pages = list()
    style = dict()
    # Default font and bullet
    menlo_path = "/System/Library/Fonts/Menlo.ttc"
    if os.path.exists(menlo_path):
        pdfmetrics.registerFont(ttfonts.TTFont("Menlo", menlo_path,
                                               subfontIndex=0))
        pdfmetrics.registerFont(ttfonts.TTFont("Menlo-Bold", menlo_path,
                                               subfontIndex=1))
        pdfmetrics.registerFont(ttfonts.TTFont("Menlo-Italic", menlo_path,
                                               subfontIndex=2))
        pdfmetrics.registerFont(ttfonts.TTFont("Menlo-BoldItalic", menlo_path,
                                               subfontIndex=3))
        pdfmetrics.registerFontFamily("Menlo", normal="Menlo",
                                      bold="Menlo-Bold",
                                      italic="Menlo-Italic",
                                      boldItalic="Menlo-boldItalic")
        font_default = "Menlo"
        bullet = "\xe2\x87\xa8"  # rightwards right arrow
    else:
        font_default = "Courier"
        bullet = "\xe2\x80\xa2"  # bullet

    # Sizes
    width, height = letter
    margin = 0.25 * inch  # 0.25"
    box_width = (width / 2) - (2 * margin)  # 3.75"
    box_height = (height / 2) - (2 * margin)  # 5.00"
    pad = 4  # 0.05"
    space = 6

    doc = BaseDocTemplate("monster_cards.pdf", pagesize=letter,
                          showBoundry=True,
                          leftMargin=margin, rightMargin=margin,
                          topMargin=margin, bottomMargin=margin,
                          title="Dungeon World Monster Cards",
                          allowSplitting=False)

    # Cards
    x_left = margin
    x_right = (width / 2) + margin
    y_top = (height / 2) + margin
    y_bottom = margin
    cards = ((x_left, y_top), (x_right, y_top), (x_left, y_bottom),
             (x_right, y_bottom))
    for coords in cards:
        frames.append(Frame(coords[0], coords[1], box_width, box_height,
                            leftPadding=pad, bottomPadding=pad,
                            rightPadding=pad,
                            topPadding=(pad * 0.75), showBoundary=True))

    style_default = getSampleStyleSheet()["Normal"].clone("default")
    style_default.fontName = font_default
    style_default.fontSize = 8
    style_default.leading = 10

    style_desc = style_default.clone("desc")
    style_desc.alignment = TA_JUSTIFY

    style_hang = style_default.clone("hang")
    style_hang.leftIndent = 16
    style_hang.firstLineIndent = -16
    style_hang.spaceBefore = space

    style_list = style_default.clone("list")
    style_list.leftIndent = 12
    style_list.firstLineIndent = -12
    style_list.bulletText = bullet
    style_list.bulletFontName = font_default

    style_ref = style_default.clone("ref")
    style_ref.alignment = TA_CENTER

# parse logs (into monsters dict)
for file_glob in args.file:
    for path in glob.iglob(file_glob):
        if os.path.exists(path):
            path = os.path.abspath(path)
            xml_files.add(path)
for xml_file in xml_files:
    parse(xml_file)

monsters_sorted = sorted(monsters.keys())

for name in monsters_sorted:
    if args.debug and name not in ("Deep Elf Swordmaster", "Fire Beetle",
                                   "Formian Centurion", "Orc Breaker"):
        continue
    monster = monsters[name]
    # CSV
    if args.format == "csv":
        csvwriter.writerow(monster)
    # PDF
    elif args.format == "pdf":
        pdf_create_page(monster)
    # Plain
    else:
        pprint(monster)
        print

if args.format == "pdf":
    pages.append(PageTemplate(frames=frames))
    doc.addPageTemplates(pages)
    doc.build(elements)
    if args.debug:
        os.system('open monster_cards.pdf')
