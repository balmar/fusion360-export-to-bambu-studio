import subprocess
import traceback

import adsk.core
import adsk.fusion

try:
    from lib.export_utils import build_export_path, clear_export_directory, resolve_bambu_studio_executable
except ImportError:  # pragma: no cover - fallback for direct package execution
    from ..lib.export_utils import build_export_path, clear_export_directory, resolve_bambu_studio_executable

from ..config import (
    CMD_ID,
    CMD_NAME,
    TOOLTIP,
    RESOURCE_FOLDER,
    WORKSPACE_ID,
    PANEL_ID,
    COMMAND_BESIDE_ID,
    EXPORT_DIRECTORY,
    BAMBU_STUDIO_EXE,
    FUSION_BAMBU_CLEAR_EXPORTS_DIR_EACH_USE,
)

app = adsk.core.Application.get()
ui = app.userInterface
handlers = []


def start():
    global app, ui

    try:
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    except Exception as e:
        app.log('Error while initializing command definition: {}'.format(str(e)), adsk.core.LogLevels.ErrorLogLevel)
        cmd_def = None

    if not cmd_def:
        try:
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                TOOLTIP,
                RESOURCE_FOLDER,
            )
        except Exception as e:
            app.log('Error while creating command definition: {}. \nFalling back to default'.format(str(e)), adsk.core.LogLevels.ErrorLogLevel)
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                CMD_ID,
                CMD_NAME,
                TOOLTIP,
            )

    on_created = CommandCreatedHandler()
    cmd_def.commandCreated.add(on_created)
    handlers.append(on_created)

    panel = _get_toolbar_panel()

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
    if ui is None:
        return None

    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    if workspace:
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        if panel:
            return panel

    panel = ui.allToolbarPanels.itemById(PANEL_ID)

    if not panel:
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

            export_dir = EXPORT_DIRECTORY
            if FUSION_BAMBU_CLEAR_EXPORTS_DIR_EACH_USE:
                clear_export_directory(export_dir)

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

            studio_path = resolve_bambu_studio_executable(BAMBU_STUDIO_EXE)
            if studio_path:
                subprocess.Popen([studio_path, str(export_path)], shell=False)
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




def _build_unique_export_path(path):
    if not path.exists():
        return path

    suffix = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{suffix}{path.suffix}")
        if not candidate.exists():
            return candidate
        suffix += 1