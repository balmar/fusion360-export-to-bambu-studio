# Application Global Variables
# This module serves as a way to share variables across different
# modules (global variables).

import os

# Flag that indicates to run in Debug mode or not. When running in Debug mode
# more information is written to the Text Command window. Generally, it's useful
# to set this to True while developing an add-in and set it to False when you
# are ready to distribute it.
DEBUG = True

# Gets the name of the add-in from the name of the folder the py file is in.
# This is used when defining unique internal names for various UI elements
# that need a unique name. It's also recommended to use a company name as
# part of the ID to better ensure the ID is unique.
ADDIN_NAME = 'ExportSTLToBambuStudio'
COMPANY_NAME = 'balmar'

# Default output directory used by the STL export command.
EXPORT_DIRECTORY = os.getenv(
    'FUSION_BAMBU_EXPORT_DIR',
    os.path.join(os.path.expanduser('~'), 'Documents', 'Bambu Studio', 'Exports'),
)

# Optional explicit path to Bambu Studio. Leave blank to auto-detect.
BAMBU_STUDIO_EXE = os.getenv('BAMBU_STUDIO_PATH', 'C:\\Program Files\\Bambu Studio\\bambu-studio.exe')

FUSION_BAMBU_CLEAR_EXPORTS_DIR_EACH_USE = os.getenv('FUSION_BAMBU_CLEAR_EXPORTS_DIR_EACH_USE', 'False').lower() in ('true', '1', 'yes')

# Palettes
sample_palette_id = f'{COMPANY_NAME}_{ADDIN_NAME}_palette_id'

WORKSPACE_ID="FusionSolidEnvironment"
PANEL_ID="SolidScriptsAddinsPanel"
COMMAND_BESIDE_ID="ScriptsManagerCommand"

CMD_ID = "ExportSelectedSTL"
CMD_NAME = "Export to Bambu Studio"
TOOLTIP = "Export the selected body or root component to STL and open Bambu Studio"
RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources")
