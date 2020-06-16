Overview
=========

DW Monster Cards eases the creation of 4" x 5.5" `Dungeon World`_ monster cards
(ex. `monster_cards.pdf`_). In addition to the primary PDF creation
functionality, dwmc.py also has has some utility functions.


Inputs
------

- `Dungeon World Github`_ source XML files
- YAML files


Outputs
-------

- CSV (ex. mail merge your own cards, import into DB)
- **PDF**

  - front document: `monster_cards.pdf`_ (39 pages)
  - back/reverse document: `back_example.pdf`_ (1 page)

- plain text

.. _`Dungeon World`: http://www.dungeon-world.com/
.. _`monster_cards.pdf`:
   https://raw.github.com/TimZehta/dw-monster-cards/main/monster_cards.pdf
.. _`back_example.pdf`:
   https://raw.github.com/TimZehta/dw-monster-cards/main/back_example.pdf
.. _`Dungeon World Github`: https://github.com/Sagelt/Dungeon-World


Create Your Own Custom Monster Cards
====================================

Custom monster can easily be created in YAML format and used to generate a PDF.


Formatting
==========

To aid readability and reference, the tags are sorted first by category, then
by either size or alphabitically. The categories are delimited by tildas ("~").

The last item on the cards are page references to the monster and setting page
numbers in the main Dungeon World book.


Requirements
=============

- Python 2.7
- Python Packages:

  - PIL_
  - PyYAML_
  - ReportLab_

.. _PIL: https://pypi.python.org/pypi/PIL/
.. _PyYAML: https://pypi.python.org/pypi/PyYAML/
.. _ReportLab: https://pypi.python.org/pypi/reportlab/


Help and Examples
=================

Help::

    usage: dwmc.py [-h] [--back-image FILE] [--back-pdf FILE] [--csv FILE]
                   [--pdf FILE] [--plain] [--yaml DIR]
                   [FILE [FILE ...]]

    Create Dungeon World Monster Cards PDF (reads source XML and YAML, also
    writes CSV and YAML).

    optional arguments:
      -h, --help         show this help message and exit
      --back-image FILE  Image to use for back of monster cards (requires
                         --back-pdf)

    Output Arguments:
      Mutually exclusive arguments that determine type of output.

      --back-pdf FILE    Create PDF of back of monster cards (requires
                         --back-image)
      --csv FILE         Create CSV of monsters
      --pdf FILE         Create PDF of monster cards
      --plain            Output plain text monster entries (handy for
                         debugging)
      --yaml DIR         Create YAML files for each monster in DIR

    Source File(s):
      FILE               XML or YAML source file(s) to parse (required by all
                         output arguments except --back-pdf)

Read `Dungeon World Github`_ and custom YAML files to create a CSV file
containing both::

    ./dwmc.py --csv all_monsters.csv alpha-monsters/*.yaml \
        ~/git/Dungeon-World/text/monster_settings/*.xml

Use leviathan_old.jpg to create example back page::

    ./dwmc.py --pdf-back back_example.pdf --pdf-image leviathan_old.jpg

Read custom YAML files to create a single page of monster of four monster
cards::

    ./dwmc.py --pdf alpha_campaign.pdf alpha-monsters/phi.yaml \
        alpha-monsters/chi.yaml alpha-monsters/psi.yaml \
        alpha-monsters/omega.yaml

Read `Dungeon World Github`_ source XML files and export to YAML files in
``yaml`` directory::

    ./dwmc.py --yaml yaml/ ~/git/Dungeon-World/text/monster_settings/*.xml


Licenses
========

- `LICENSE.txt`_


dwmc.py
-------

- `MIT License`_


Monster Definitions
-------------------

- `Open Gaming License version 1.0a`_ [RTF]


Dungeon World and Index Data
----------------------------

- `Creative Commons Attribution 3.0 Unported License`_


.. _`LICENSE.txt`:
   https://github.com/TimZehta/dw-monster-cards/blob/main/LICENSE.txt
.. _`MIT License`: http://www.opensource.org/licenses/MIT
.. _`Open Gaming License version 1.0a`:
   http://www.wizards.com/d20/files/OGLv1.0a.rtf
.. _`Creative Commons Attribution 3.0 Unported License`:
   http://creativecommons.org/licenses/by/3.0/
