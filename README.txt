================================================================================
  NUMISMATIC COLLECTION MANAGER
  Grand Duchy of Lithuania · Personal Coin Collection Web Application
================================================================================

OVERVIEW
--------
A Flask-based web application for managing and cataloguing a personal
numismatic collection, specialised for coins of the Grand Duchy of Lithuania
(Kęstutis through Sigismund III Vasa). Data is stored in a plain JSON file —
no database server required.


REQUIREMENTS
------------
  Python 3.7 or later
  pip (Python package manager)


INSTALLATION
------------
1. Open a terminal and navigate to the application directory:

     cd /home/tank/collection

2. Install the required Python packages:

     pip install -r requirements.txt

   Packages installed:
     Flask       — web framework
     Pillow      — image handling
     reportlab   — PDF catalogue generation (requires version < 4.0)


LAUNCHING THE APPLICATION
--------------------------
From the application directory, run:

     python app.py

Then open your browser and go to:

     http://localhost:5000

The application runs in debug mode by default. To run in production mode:

     FLASK_ENV=production python app.py

To bind to a specific host or port:

     python -c "import app; app.app.run(host='0.0.0.0', port=8080)"


FILE STRUCTURE
--------------
  app.py                 Main Flask application (routes)
  models.py              JSON database layer (all reads/writes)
  pdf_generator.py       PDF catalogue generator (ReportLab)
  requirements.txt       Python dependencies
  data/
    collection.json      The database file (edit directly if needed)
  uploads/               Uploaded coin photos (created automatically)
  static/
    css/style.css        Stylesheet (parchment/navy/gold theme)
    js/main.js           Frontend interactivity
  templates/
    base.html            Shared layout and navigation
    index.html           Collection overview with search and filters
    coin_detail.html     Single coin page with photo viewer
    coin_form.html       Add / edit coin form
    export.html          PDF export selection page
    settings.html        Collection name and owner settings


COIN FIELDS
-----------
Each coin entry stores the following information:

  Identity:
    Ruler               e.g. Jogaila, Vytautas the Great
    Denomination        e.g. Denar, Grosz, Trojak, Talar
    Mint                e.g. Vilnius, Riga, Kraków
    Material            e.g. Silver, Gold, Billon, Copper

  Date:
    Year / Range        Display string, e.g. "1386–1392"
    Year from / to      Numeric values used for sorting

  Physical:
    Weight (g)
    Diameter (mm)
    Condition / Grade   e.g. Very Fine (VF-30), Extremely Fine (EF-45)

  Descriptions:
    Obverse             Heads side description
    Reverse             Tails side description
    Edge                Edge description (plain, reeded, lettered…)

  Catalogue References:
    Ivanauskas          E. Ivanauskas catalogue number
    Bagdonas            Bagdonas catalogue number
    Huletski            Huletski / Huletski-Karpaw reference
    Sarankinas          Sarankinas reference
    Custom / Other      Any additional catalogue reference

  Acquisition:
    Purchase price (€)
    Purchase date
    Source / auction house
    Sale price (€) and sale date (if sold)

  Provenance & Notes:
    Provenance          Collection history, previous owners
    Notes               Observations, strike quality, die varieties, etc.

  Tags                  Comma-separated keywords for filtering


FEATURES
--------
  Collection overview
    - Responsive card grid with coin images
    - Full-text search across all fields
    - Dropdown filters: ruler, denomination, material, tag, sold status
    - Sort by any field (ascending or descending)
    - Running totals: coin count and total invested

  Coin detail page
    - Multi-photo viewer with thumbnail strip
    - Click any photo to zoom fullscreen (press Esc to close)
    - Drag-and-drop photo upload (JPG, PNG, WEBP, TIF, up to 32 MB each)
    - Individual photo deletion

  Add / Edit coin
    - Autocomplete suggestions for rulers, denominations, mints, materials
    - Tag preview updates as you type
    - Year display auto-fills from numeric year fields
    - Sold checkbox reveals sale price / date fields

  PDF catalogue export
    - Select any subset of coins (Select All / None / Invert)
    - Publication-style PDF with cover page, coin images, spec grid,
      descriptions, catalogue references, provenance, and tags
    - Downloaded as "catalogue.pdf"

  JSON API (read-only)
    GET /api/coins          Returns all coins as JSON
    GET /api/coin/<id>      Returns a single coin as JSON

  Settings
    - Collection name (appears in navigation and PDF header)
    - Collector name (appears in PDF footer)


DATA FILE
---------
All collection data is stored in:

     data/collection.json

The file is human-readable and can be edited directly in a text editor,
backed up with a simple file copy, or version-controlled with git.
To back up the collection including photos:

     cp -r data/ uploads/ /path/to/backup/


NOTES
-----
  - The application uses reportlab version 3.x. Version 4.x requires
    Python 3.8 or later and will not work on Python 3.7 installations.
  - Secret key: set the SECRET_KEY environment variable in production.
  - Upload folder and data file are created automatically on first run.

================================================================================
