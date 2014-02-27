Overview
=========

DW Monster Cards eases the generation of 4 by 5.5 inch `Dungeon World`_ monster
cards (ex. `monster_cards.pdf`_). In addition to the primary PDF creation
functionality, dwmc.py also has has some utility functions.

See  for an example

Inputs
------

- `Dungeon World Github`_ source XML files
- YAML files


Outputs
-------

- CSV (ex. mail merge your own cards, import into DB)
- **PDF** (ex. `monster_cards.pdf`_)
- plain text

.. _`Dungeon World`: http://www.dungeon-world.com/
.. _`monster_cards.pdf`:
   https://github.com/TimZehta/dw-monster-cards/blob/master/monster_cards.pdf
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
- ReportLab_
- PyYAML_ (Ubuntu package: `python-yaml`)

.. _ReportLab: http://www.reportlab.com/software/opensource/
.. _PyYAML: https://pypi.python.org/pypi/PyYAML/



Licenses
========

- `LICENSE.txt`_


dwmc.py
-------

- `MIT License`_


Monster Definitions (``yaml-dw/\*.yaml``)
-----------------------------------------

- `Open Gaming License version 1.0a`_ [rtf]


Dungeon World and Index Data
----------------------------

- `Creative Commons Attribution 3.0 Unported License`_


.. _`LICENSE.txt`:
   https://github.com/TimZehta/dw-monster-cards/blob/master/LICENSE.txt
.. _`MIT License`: http://www.opensource.org/licenses/MIT
.. _`Open Gaming License version 1.0a`:
   http://www.wizards.com/d20/files/OGLv1.0a.rtf
.. _`Creative Commons Attribution 3.0 Unported License`:
   http://creativecommons.org/licenses/by/3.0/
