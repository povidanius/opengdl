================================================================================
  NUMISMATIC COLLECTION MANAGER
  Grand Duchy of Lithuania · Personal Coin Collection Web Application
================================================================================

OVERVIEW
--------
A Flask-based web application for managing and cataloguing a personal
numismatic collection, specialised for coins of the Grand Duchy of Lithuania
(Mindaugas through Augustus II the Strong). Data is stored in a plain JSON
file — no database server required.


================================================================================
  OPTION 1: RUN WITH DOCKER (recommended — works on Linux and Windows)
================================================================================

PREREQUISITES
-------------
  Install Docker:
    Linux:    https://docs.docker.com/engine/install/
    Windows:  https://docs.docker.com/desktop/install/windows-install/
              (Docker Desktop requires Windows 10/11 64-bit with WSL 2)

BUILD THE IMAGE
---------------
Open a terminal (Linux) or Command Prompt / PowerShell (Windows) and
navigate to the application directory, then run:

     docker build -t coin-collection .

RUN THE CONTAINER
-----------------
Linux:

     docker run -d --name coins \
       -p 5000:5000 \
       -v "$(pwd)/data:/app/data" \
       -v "$(pwd)/uploads:/app/uploads" \
       coin-collection

Windows (Command Prompt):

     docker run -d --name coins ^
       -p 5000:5000 ^
       -v "%cd%/data:/app/data" ^
       -v "%cd%/uploads:/app/uploads" ^
       coin-collection

Windows (PowerShell):

     docker run -d --name coins `
       -p 5000:5000 `
       -v "${PWD}/data:/app/data" `
       -v "${PWD}/uploads:/app/uploads" `
       coin-collection

Then open your browser and go to:

     http://localhost:5000

STOP / START / REMOVE
---------------------
     docker stop coins
     docker start coins
     docker rm coins


================================================================================
  OPTION 2: RUN WITHOUT DOCKER (Python)
================================================================================

REQUIREMENTS
------------
  Python 3.7 or later
  pip (Python package manager)

INSTALLATION
------------
1. Open a terminal and navigate to the application directory:

     cd /home/tank/collection          (Linux)
     cd C:\path\to\collection          (Windows)

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


================================================================================
  REFERENCE
================================================================================

FILE STRUCTURE
--------------
  Dockerfile             Docker image definition
  .dockerignore          Files excluded from Docker build
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
    portraits/           Ruler portrait images
    seals/               Ruler seal images
    coats_of_arms/       Ruler coats of arms images
  templates/
    base.html            Shared layout and navigation
    index.html           Collection overview with search and filters
    coin_detail.html     Single coin page with photo viewer
    coin_form.html       Add / edit coin form
    export.html          PDF export selection page
    settings.html        Collection name and owner settings
    ruler_edit.html      Ruler notes / seals / coats of arms editor


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
    - Drag-and-drop photo upload (JPG, PNG, WEBP, TIF, up to 64 MB each)
    - Individual photo deletion

  Add / Edit coin
    - Autocomplete suggestions for rulers, denominations, mints, materials
    - Tag preview updates as you type
    - Year display auto-fills from numeric year fields
    - Sold checkbox reveals sale price / date fields
    - Delete coin button (with confirmation)

  Ruler pages
    - Portrait, biography, seal and coat of arms galleries
    - Editable custom notes per ruler

  PDF catalogue export
    - Select any subset of coins (Select All / None / Invert)
    - Publication-style PDF with cover page, ruler intro sections
      (portrait + biography), coin images, spec grid, descriptions,
      catalogue references, provenance, and tags
    - Downloaded as "catalogue.pdf"

  JSON API (read-only)
    GET /api/coins          Returns all coins as JSON
    GET /api/coin/<id>      Returns a single coin as JSON

  Settings
    - Collection name (appears in navigation and PDF header)
    - Collector name (appears in PDF footer)
    - Show/hide prices
    - Confidential mode (footer watermark on web and PDF)


DATA & BACKUP
-------------
All collection data is stored in:

     data/collection.json

The file is human-readable and can be edited directly in a text editor,
backed up with a simple file copy, or version-controlled with git.
To back up the collection including photos:

     Linux:    cp -r data/ uploads/ /path/to/backup/
     Windows:  xcopy data backup\data /E /I
               xcopy uploads backup\uploads /E /I

When using Docker, data/ and uploads/ are mounted as volumes, so your
data lives on the host filesystem and persists across container restarts.


NOTES
-----
  - The application uses reportlab version 3.x. Version 4.x requires
    Python 3.8 or later and will not work on Python 3.7 installations.
  - The Docker image installs DejaVu fonts, which are required by the
    PDF generator. When running without Docker, these fonts must be
    present on the host system (pre-installed on most Linux distributions;
    on Windows, install them manually or use the Docker option).
  - Secret key: set the SECRET_KEY environment variable in production.
  - Upload folder and data file are created automatically on first run.

================================================================================
