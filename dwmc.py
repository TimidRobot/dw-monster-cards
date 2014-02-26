#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Create monster cards; read XML and YAML; write CSV, PDF, and YAML"""
# Standard library
import argparse
import codecs
import collections
import csv
import cStringIO
import glob
import os.path
import sys
import textwrap
from xml.etree import ElementTree
# Third-party
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase import ttfonts
from reportlab.platypus import (BaseDocTemplate, Frame, FrameBreak,
                                PageTemplate, Paragraph, Spacer)
from reportlab.platypus.tables import Table
import yaml

# Tag order lists
monster_tags_org = ["Solitary", "Group", "Horde"]
monster_tags_size = ["Tiny", "Small", "Large", "Huge"]
weapon_tags_range = ["Hand", "Close", "Reach", "Near", "Far"]

yaml_tag = u"tag:yaml.org,2002:map"
monsters = dict()
xml_files = set()
yaml_files = set()
index = None


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


# From ... #TODO#
def represent_odict(dump, tag, mapping, flow_style=None):
    """Like BaseRepresenter.represent_mapping, but does not issue the sort().
    """
    value = list()
    node = yaml.MappingNode(tag, value, flow_style=flow_style)
    if dump.alias_key is not None:
        dump.represented_objects[dump.alias_key] = node
    best_style = True
    if hasattr(mapping, "items"):
        mapping = mapping.items()
    for item_key, item_value in mapping:
        node_key = dump.represent_data(item_key)
        node_value = dump.represent_data(item_value)
        if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
            best_style = False
        if (not (isinstance(node_value, yaml.ScalarNode) and
                 not node_value.style)):
            best_style = False
        value.append((node_key, node_value))
    if flow_style is None:
        if dump.default_flow_style is not None:
            node.flow_style = dump.default_flow_style
        else:
            node.flow_style = best_style
    return node


def parser_setup():
    """Instantiate, configure and return an ArgumentParser instance."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", metavar="DST_FILE",
                    help="Create CSV table of monsters")
    ap.add_argument("--pdf", metavar="DST_FILE",
                    help="Create monster cards PDF")
    ap.add_argument("--yaml", metavar="DST_DIR",
                    help="Create YAML files for each monster")
    ap.add_argument("file", metavar="SRC_FILE", nargs="*",
                    help="XML or YAML file(s) to parse.")
    args = ap.parse_args()
    return args


def parse_xml(xml_file):
    tree = ElementTree.parse(xml_file)
    body = tree.find("Body")
    second = False
    setting = tree.find("h1").text
    setting_reference = index["settings"][setting]
    for element in body:
        if element.tag == "p":
            style = element.attrib[
                "{http://ns.adobe.com/AdobeInDesign/4.0/}pstyle"]
            # MonsterName - name, tags
            if style == "MonsterName":
                # START - MonsterName is first p element attrib/style in
                #         monster_setting XML files
                # Initialize variables (and set order)
                m = collections.OrderedDict()
                m["name"] = None
                m["tags_desc"] = list()
                m["tags_org"] = list()
                m["tags_size"] = list()
                m["hp"] = None
                m["armor"] = None
                m["weapon"] = collections.OrderedDict()
                m["weapon"]["name"] = None
                m["weapon"]["damage"] = None
                m["weapon"]["tags_desc"] = list()
                m["weapon"]["tags_range"] = list()
                m["instincts"] = list()
                m["qualities"] = list()
                m["description"] = ""
                m["reference"] = None
                m["setting"] = setting
                m["setting_reference"] = setting_reference

                m["name"] = element.text.strip()
                m["reference"] = index["monsters"][m["name"].lower()]
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
                            m["hp"] = int(stat.split(" ")[0])
                        # Armor
                        elif stat.endswith("Armor"):
                            m["armor"] = int(stat.split(" ")[0])
                    second = True
            elif style == "MonsterQualities":
                for quality in element[0].tail.split(","):
                    m["qualities"].append(quality.strip())
            elif style == "MonsterDescription":
                if element.text:
                    # Normal description
                    m["description"] = element.text.strip()
                if len(element) > 0:
                    # Fire Bettle decription
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
                # Treant description
                if element.text:
                    m["description"] = "%s<br />%s" % (m["description"],
                                                       element.text)
                if len(element) > 0:
                    instinct = e.tail
                    instinct = instinct.lstrip(":")
                    m["instincts"].insert(0, instinct.strip())

        elif element.tag == "ul":
            for item in element:
                m["instincts"].append(item.text)

            # END - ul is last element in monster_setting XML files
            monsters[m["name"]] = m


def parse_yaml(yaml_file):
    m = collections.OrderedDict()
    m["name"] = None
    m["tags_desc"] = list()
    m["tags_org"] = list()
    m["tags_size"] = list()
    m["hp"] = None
    m["armor"] = None
    m["weapon"] = collections.OrderedDict()
    m["weapon"]["name"] = None
    m["weapon"]["damage"] = None
    m["weapon"]["tags_desc"] = list()
    m["weapon"]["tags_range"] = list()
    m["instincts"] = list()
    m["qualities"] = list()
    m["description"] = ""
    m["reference"] = None
    m["setting"] = None
    m["setting_reference"] = None
    with open(yaml_file, "r") as stream:
        temp = yaml.safe_load(stream)
        for key in temp:
            if key != "weapon":
                m[key] = temp[key]
            else:
                for key in temp["weapon"]:
                    m["weapon"][key] = temp["weapon"][key]
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


def combine_weapon(monster_dictionary, formatted=False):
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


def csv_write_row(monster_dict):
    m = monster_dict
    # Cleanup italics (ex. Fire Beetle)
    description = m["description"].replace("<i>", "").replace("</i>", "")
    # Clean up line breaks (ex. Treant)
    description = description.replace("<br />", " \ ")
    csvwriter.writerow([m["name"], str(m["hp"]), str(m["armor"]),
                       combine_monster_tags(m), combine_weapon(m),
                       ", ".join(m["instincts"]), ", ".join(m["qualities"]),
                       description, str(m["reference"]), m["setting"],
                       str(m["setting_reference"])])


def pdf_create_page(monster_dict):
    m = monster_dict
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
    name = m["name"].upper()
    words = list()
    for word in name.split(" "):
        words.append("%s<font size=14>%s</font>" % (word[0:1], word[1:]))
    name = " ".join(words)
    name = Paragraph(name, style_title)
    table = [[name, hp_label, hp_value],
             ["", armor_label, armor_value]]
    style = [("LINEABOVE", (0, 0), (2, 0), 1, colors.black),
             ("LEFTPADDING", (0, 0), (2, 1), 0),
             ("RIGHTPADDING", (0, 0), (2, 1), 0),
             ("BOTTOMPADDING", (0, 0), (2, 1), 0),
             ("TOPPADDING", (0, 0), (2, 1), 0),
             ("TOPPADDING", (1, 0), (2, 0), (spacer / 2)),
             ("VALIGN", (0, 0), (2, 1), "TOP"),
             ("SPAN", (0, 0), (0, 1)),
             ("FONT", (1, 0), (2, 1), font_default, 8),
             ("ALIGN", (1, 0), (2, 1), "RIGHT"),
             ]
    elements.append(Table(table, [(3.15 * inch) - 8, 0.4 * inch, 0.2 * inch],
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
        elements.append(Spacer(box_width, spacer))
        label = Paragraph("<b>Instincts</b>", style_default)
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
        elements.append(Table(table, [0.675 * inch, (3.075 * inch) - 8],
                              style=style))
    # Qualities
    if m["qualities"]:
        elements.append(Spacer(box_width, spacer))
        label = Paragraph("<b>Qualities</b>", style_default)
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
        elements.append(Table(table, [0.675 * inch, (3.075 * inch) - 8],
                              style=style))
    # Description
    elements.append(Spacer(box_width, spacer))
    table = [[Paragraph(m["description"], style_desc)]]
    style = [("LINEABOVE", (0, 0), (0, 0), 0.5, colors.black),
             ("LINEBELOW", (0, 0), (0, 0), 0.5, colors.black),
             ("LEFTPADDING", (0, 0), (0, 0), 0),
             ("RIGHTPADDING", (0, 0), (0, 0), 0),
             ("BOTTOMPADDING", (0, 0), (0, 0), (spacer / 2)),
             ("TOPPADDING", (0, 0), (0, 0), (spacer / 2)),
             ("VALIGN", (0, 0), (0, 0), "TOP"),
             ]
    elements.append(Table(table, [box_width - 8],
                          style=style))
    # References
    elements.append(Spacer(box_width, (spacer / 2)))
    reference = "%s of the %s" % (m["name"], m["setting"])
    elements.append(Paragraph(reference, style_ref))
    reference = None
    if m["reference"] and m["setting_reference"]:
        reference = "[DW %d, %d]" % (m["reference"], m["setting_reference"])
    elif m["setting_reference"]:
        reference = "[DW %d]" % (m["setting_reference"])
    if reference:
        elements.append(Paragraph(reference, style_ref))
    # Next card
    elements.append(FrameBreak())


def plain_write(monster_dict):
    m = monster_dict
    print "=" * 80
    # Name, HP, and Armor
    if m["hp"]:
        print u"%-70s%6s%4d" % (m["name"].upper(), "HP:", m["hp"])
    else:
        print m["name"].upper()
    if m["armor"]:
        print u"%76s%4d" % ("Armor:", m["armor"])
    # Tags
    tags = combine_monster_tags(m)
    if tags:
        print tags
    # Weapon
    weapon = combine_weapon(m)
    if weapon:
        print weapon
    # Instincts
    if m["instincts"]:
        leader = textwrap.TextWrapper(width=80,
                                      initial_indent=u"%-10s> " % "Instincts",
                                      subsequent_indent=u"%12s" % "")
        print leader.fill(m["instincts"].pop(0))
        follow = textwrap.TextWrapper(width=80,
                                      initial_indent=u"%-10s> " % "",
                                      subsequent_indent=u"%12s" % "")
        for instinct in m["instincts"]:
            print follow.fill(instinct)
    # Qualities
    if m["qualities"]:
        leader = textwrap.TextWrapper(width=80,
                                      initial_indent=u"%-10s> " % "Qualities",
                                      subsequent_indent=u"%12s" % "")
        print leader.fill(m["qualities"].pop(0))
        follow = textwrap.TextWrapper(width=80,
                                      initial_indent=u"%-10s> " % "",
                                      subsequent_indent=u"%12s" % "")
        for quality in m["qualities"]:
            print follow.fill(quality)
    # Description
    if m["description"]:
        print "-" * 80
        # Cleanup italics (ex. Fire Beetle)
        description = m["description"].replace("<i>", "").replace("</i>", "")
        if "<br />" in description:
            # Multilined description (ex. Treant)
            description = description.replace("<br />", "\n")
            print description
        else:
            # Normal description
            print textwrap.fill(description, width=80)
        print "-" * 80
    # References
    print u"{: ^80}".format(u"%s of the %s" % (m["name"], m["setting"]))
    if m["reference"] and m["setting_reference"]:
        print u"{: ^80}".format(u"[DW %d, %d]" % (m["reference"],
                                                  m["setting_reference"]))
    elif m["setting_reference"]:
        print u"{: ^80}".format(u"[DW %d]" % (m["setting_reference"]))
    print


#TODO: convert utf8 to ascii for filenames
def yaml_write(monster_dict):
    m = monster_dict
    # Remove empty keys
    bad_keys = list()
    for key in m["weapon"]:
        if not m["weapon"][key]:
            bad_keys.append(key)
    for key in bad_keys:
        del m["weapon"][key]
    bad_keys = list()
    for key in m:
        if not m[key]:
            bad_keys.append(key)
    for key in bad_keys:
        del m[key]
    # Print or Write to file
    if args.yaml == "-":
        print yaml.safe_dump(m, default_flow_style=False, width=70,
                             explicit_start=True)
    else:
        file_name = m["name"].replace(" ", "_").lower()
        args.yaml = os.path.abspath(args.yaml)
        file_path = "%s/%s.yaml" % (args.yaml, file_name)
        with open(file_path, "w") as stream:
            yaml.safe_dump(m, stream, default_flow_style=False, width=70,
                           explicit_start=True)


# Setup
args = parser_setup()
yaml.SafeDumper.add_representer(collections.OrderedDict,
                                lambda dumper, value: represent_odict(dumper,
                                                                      yaml_tag,
                                                                      value))
# CSV
if args.csv:
    if args.csv == "-":
        csv_path = sys.stdout
    else:
        csv_path = os.path.abspath(args.csv)
        csv_path = open(args.csv, 'wb')
    csvwriter = UnicodeWriter(csv_path, quoting=csv.QUOTE_ALL,
                              lineterminator="\n")
    csvwriter.writerow(("name", "tags", "hp", "armor", "weapon",
                        "qualities", "instincts", "description", "reference",
                        "setting", "setting_reference"))
# PDF
elif args.pdf:
    elements = list()
    frames = list()
    pages = list()
    style = dict()
    # Default font and bullet
    menlo_path = "/System/Library/Fonts/Menlo.ttc"
    if os.path.exists(menlo_path):
        registerFont(ttfonts.TTFont("Menlo", menlo_path, subfontIndex=0))
        registerFont(ttfonts.TTFont("Menlo-Bold", menlo_path, subfontIndex=1))
        registerFont(ttfonts.TTFont("Menlo-Italic", menlo_path,
                                    subfontIndex=2))
        registerFont(ttfonts.TTFont("Menlo-BoldItalic", menlo_path,
                                    subfontIndex=3))
        registerFontFamily("Menlo", normal="Menlo", bold="Menlo-Bold",
                           italic="Menlo-Italic",
                           boldItalic="Menlo-boldItalic")
        font_default = "Menlo"
        #bullet = "\xe2\x87\xa8"  # rightwards white arrow
        bullet = "\xe2\x86\xa3"  # rightwards arrow with tail
    else:
        font_default = "Courier"
        bullet = "\xe2\x80\xa2"  # bullet
    # Title font
    font_title = "Times-Roman"

    # Sizes
    width, height = letter
    margin = 0.25 * inch  # 0.25"
    box_width = (width / 2) - (2 * margin)  # 3.75"
    box_height = (height / 2) - (2 * margin)  # 5.00"
    pad = 4  # 0.05"
    spacer = 6

    doc = BaseDocTemplate(args.pdf, pagesize=letter, showBoundry=True,
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
                            leftPadding=pad, bottomPadding=(pad / 2),
                            rightPadding=pad,
                            topPadding=(pad / 1.5), showBoundary=True))

    style_default = getSampleStyleSheet()["Normal"].clone("default")
    style_default.fontName = font_default
    style_default.fontSize = 8
    style_default.leading = 10

    style_desc = style_default.clone("desc")
    style_desc.alignment = TA_JUSTIFY

    style_hang = style_default.clone("hang")
    style_hang.leftIndent = 16
    style_hang.firstLineIndent = -16
    style_hang.spaceBefore = spacer

    style_list = style_default.clone("list")
    style_list.leftIndent = 12
    style_list.firstLineIndent = -12
    style_list.bulletText = bullet
    style_list.bulletFontName = font_default

    style_desc = style_default.clone("desc")
    style_desc.alignment = TA_JUSTIFY

    style_ref = style_default.clone("ref")
    style_ref.alignment = TA_CENTER

    style_title = style_default.clone("title")
    style_title.fontName = font_title
    style_title.fontSize = 20

# Create monsters dict from parse files
for file_glob in args.file:
    for path in glob.iglob(file_glob):
        if os.path.exists(path):
            path = os.path.abspath(path)
            if path.endswith(".xml"):
                xml_files.add(path)
            if path.endswith(".yml") or path.endswith(".yaml"):
                yaml_files.add(path)
if xml_files:
    with open("index.yaml", "r") as stream:
        index = yaml.safe_load(stream)
    for xml_file in xml_files:
        parse_xml(xml_file)
for yaml_file in yaml_files:
    parse_yaml(yaml_file)
monsters_sorted = sorted(monsters.keys())
# Process monsters dict
for name in monsters_sorted:
    monster = monsters[name]
    # CSV
    if args.csv:
        csv_write_row(monster)
    # PDF
    elif args.pdf:
        pdf_create_page(monster)
    # YAML
    elif args.yaml:
        yaml_write(monster)
    # Plain
    else:
        plain_write(monster)

if args.pdf:
    pages.append(PageTemplate(frames=frames))
    doc.addPageTemplates(pages)
    doc.build(elements)
