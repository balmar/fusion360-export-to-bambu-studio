import os
import subprocess
import traceback
from pathlib import Path

import adsk.core
import adsk.fusion

try:
    import config
except ImportError:  # pragma: no cover - fallback for direct package execution
    from .. import config

try:
    from lib.export_utils import build_export_path, resolve_bambu_studio_executable
except ImportError:  # pragma: no cover - fallback for direct package execution
    from ..lib.export_utils import build_export_path, resolve_bambu_studio_executable

app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

CMD_ID = "ExportSelectedSTL"
CMD_NAME = "Export to Bambu Studio"
TOOLTIP = "Export the selected body or root component to STL and open Bambu Studio"
RESOURCE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "")
RESOURCE_FILE = "bambu_icon.png"

WORKSPACE_ID="FusionSolidEnvironment"
PANEL_ID="SolidScriptsAddinsPanel"
COMMAND_BESIDE_ID="ScriptsManagerCommand"


def start():
    global app, ui

    # app = adsk.core.Application.get()
    # ui = app.userInterface

    try:
        app.log('Hello from Bambu Studio Export Add-in', adsk.core.LogLevels.InfoLogLevel)
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    except Exception as e:
        app.log('Error while initializing command definition: {}'.format(str(e)), adsk.core.LogLevels.ErrorLogLevel)
        cmd_def = None

    if not cmd_def:
        try:
            app.log('Adding command definition', adsk.core.LogLevels.InfoLogLevel)
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                TOOLTIP,
                RESOURCE_FOLDER,
            )
        except Exception as e:
            app.log('Error while creating command definition: {}'.format(str(e)), adsk.core.LogLevels.ErrorLogLevel)
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                TOOLTIP,
            )

    on_created = CommandCreatedHandler()
    cmd_def.commandCreated.add(on_created)
    handlers.append(on_created)

    panel = _get_toolbar_panel()
    app.log(f'Adding command to toolbar panel: {panel.name if panel else "None"}', adsk.core.LogLevels.InfoLogLevel)
    if panel:
        control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
        if control:
            control.isPromoted = True
            control.isPromotedByDefault = True


def stop():
    panel = _get_toolbar_panel()
    if panel:
        control = panel.controls.itemById(CMD_ID)
        if control:
            control.deleteMe()

    definition = ui.commandDefinitions.itemById(CMD_ID)
    if definition:
        definition.deleteMe()


def _get_toolbar_panel():
    global app, ui
    if ui is None:
        return None

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    app.log('Workspace: {}'.format(workspace.name if workspace else 'None'), adsk.core.LogLevels.InfoLogLevel)
    if workspace:
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        if panel:
            return panel

    panel = ui.allToolbarPanels.itemById(PANEL_ID)
    app.log('Panel: {}'.format(panel.name if panel else 'None'), adsk.core.LogLevels.InfoLogLevel)
    if not panel:
        app.log('Falling back to SolidCreatePanel', adsk.core.LogLevels.InfoLogLevel)
        panel = ui.allToolbarPanels.itemById("SolidCreatePanel")
    return panel


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        cmd = args.command
        execute = ExecuteHandler()
        cmd.execute.add(execute)
        handlers.append(execute)


class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox("This add-in requires an active Fusion design.")
                return

            export_target = _get_export_target()
            if not export_target:
                ui.messageBox("Select a body or component to export, or use the root component.")
                return

            export_dir = _resolve_output_directory()
            export_path = build_export_path(export_dir, app.activeDocument.name)
            export_path = _build_unique_export_path(export_path)

            export_mgr = design.exportManager
            options = export_mgr.createSTLExportOptions(export_target, str(export_path))
            options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            options.isBinaryFormat = True
            options.sendToPrintUtility = False

            success = export_mgr.execute(options)
            if not success:
                ui.messageBox(f"STL export failed for {export_path.name}.")
                return

            studio_path = resolve_bambu_studio_executable(getattr(config, "BAMBU_STUDIO_EXE", None))
            if studio_path:
                subprocess.Popen([studio_path, str(export_path)], shell=False)
                # ui.messageBox(f"Exported STL:\n{export_path}\n\nOpened Bambu Studio.")
            else:
                ui.messageBox(
                    f"Exported STL:\n{export_path}\n\nBambu Studio was not found. "
                    "Set BAMBU_STUDIO_EXE in config.py or install Bambu Studio."
                )

        except Exception:  # pylint:disable=broad-except
            ui.messageBox(f"Failed:\n{traceback.format_exc()}")
            app.log(f"Failed:\n{traceback.format_exc()}")


def _get_export_target():
    if ui.activeSelections.count == 1:
        entity = ui.activeSelections.item(0).entity
        if entity:
            body = adsk.fusion.BRepBody.cast(entity)
            if body:
                return body

            component = adsk.fusion.Component.cast(entity)
            if component:
                return component

    design = adsk.fusion.Design.cast(app.activeProduct)
    if design:
        return design.rootComponent

    return None


def _resolve_output_directory():
    configured_dir = getattr(config, "EXPORT_DIRECTORY", None)
    if configured_dir:
        return Path(configured_dir).expanduser()

    return Path.home() / "Documents" / "Bambu Studio" / "Exports"


def _build_unique_export_path(path):
    if not path.exists():
        return path

    suffix = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{suffix}{path.suffix}")
        if not candidate.exists():
            return candidate
        suffix += 1