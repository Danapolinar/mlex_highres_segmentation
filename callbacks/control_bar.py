from dash import (
    Input,
    Output,
    dcc,
    State,
    callback,
    Patch,
    ALL,
    ctx,
    clientside_callback,
    no_update,
)
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import json
from utils.annotations import Annotations
import copy


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output("open-freeform", "style"),
    Output("closed-freeform", "style"),
    Output("line", "style"),
    Output("circle", "style"),
    Output("rectangle", "style"),
    Output("drawing-off", "style"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("current-ann-mode", "data", allow_duplicate=True),
    Input("open-freeform", "n_clicks"),
    Input("closed-freeform", "n_clicks"),
    Input("line", "n_clicks"),
    Input("circle", "n_clicks"),
    Input("rectangle", "n_clicks"),
    Input("drawing-off", "n_clicks"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def annotation_mode(open, closed, line, circle, rect, off_mode, annotation_store):
    """This callback determines which drawing mode the graph is in"""
    if not annotation_store["visible"]:
        raise PreventUpdate

    patched_figure = Patch()
    triggered = ctx.triggered_id
    active = {"border": "3px solid black"}
    inactive = {"border": "1px solid"}
    open_style = inactive
    close_style = inactive
    line_style = inactive
    circle_style = inactive
    rect_style = inactive
    pan_style = inactive

    if triggered == "open-freeform" and open > 0:
        patched_figure["layout"]["dragmode"] = "drawopenpath"
        annotation_store["dragmode"] = "drawopenpath"
        open_style = active
    if triggered == "closed-freeform" and closed > 0:
        patched_figure["layout"]["dragmode"] = "drawclosedpath"
        annotation_store["dragmode"] = "drawclosedpath"
        close_style = active
    if triggered == "line" and line > 0:
        patched_figure["layout"]["dragmode"] = "drawline"
        annotation_store["dragmode"] = "drawline"
        line_style = active
    if triggered == "circle" and circle > 0:
        patched_figure["layout"]["dragmode"] = "drawcircle"
        annotation_store["dragmode"] = "drawcircle"
        circle_style = active
    if triggered == "rectangle" and rect > 0:
        patched_figure["layout"]["dragmode"] = "drawrect"
        annotation_store["dragmode"] = "drawrect"
        rect_style = active
    if triggered == "drawing-off" and off_mode > 0:
        patched_figure["layout"]["dragmode"] = "pan"
        annotation_store["dragmode"] = "pan"
        pan_style = active
    return (
        patched_figure,
        open_style,
        close_style,
        line_style,
        circle_style,
        rect_style,
        pan_style,
        annotation_store,
        triggered,
    )


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("paintbrush-width", "value"),
    prevent_initial_call=True,
)
def annotation_width(width_value):
    """
    This callback is responsible for changing the brush width.
    """
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["line"]["width"] = width_value
    return patched_figure


@callback(
    Output("current-annotation-classes", "children"),
    Output("current-annotation-classes-edit", "data"),
    Output("current-annotation-classes-hide", "children"),
    Input("annotation-class-selection", "children"),
)
def make_class_delete_edit_hide_modal(current_classes):
    """Creates buttons for the delete selected classes and edit selected class modal"""
    current_classes_edit = [button["props"]["children"] for button in current_classes]
    current_classes_delete = copy.deepcopy(current_classes)
    current_classes_hide = copy.deepcopy(current_classes)
    for button in current_classes_delete:
        color = button["props"]["style"]["background-color"]
        button["props"]["id"] = {"type": "annotation-delete-buttons", "index": color}
        button["props"]["style"]["border"] = "1px solid"
    for button in current_classes_hide:
        color = button["props"]["style"]["background-color"]
        button["props"]["id"] = {"type": "annotation-hide-buttons", "index": color}
        button["props"]["style"]["border"] = "1px solid"
    return current_classes_delete, current_classes_edit, current_classes_hide


@callback(
    Output({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    Input({"type": "annotation-delete-buttons", "index": ALL}, "n_clicks"),
    State({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def highlight_selected_classes(selected_classes, current_styles):
    """Highlights selected buttons in delete modal"""
    for i in range(len(selected_classes)):
        if selected_classes[i] is not None and selected_classes[i] % 2 != 0:
            current_styles[i]["border"] = "3px solid black"
        else:
            current_styles[i]["border"] = "1px solid"
    return current_styles


@callback(
    Output({"type": "annotation-hide-buttons", "index": ALL}, "style"),
    Input({"type": "annotation-hide-buttons", "index": ALL}, "n_clicks"),
    State({"type": "annotation-hide-buttons", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def highlight_selected_hide_classes(selected_classes, current_styles):
    """Highlights selected buttons in hide modal"""
    for i in range(len(selected_classes)):
        if selected_classes[i] is not None and selected_classes[i] % 2 != 0:
            current_styles[i]["border"] = "3px solid black"
        else:
            current_styles[i]["border"] = "1px solid"
    return current_styles


@callback(
    Output("image-viewer", "figure", allow_duplicate=True),
    Output({"type": "annotation-color", "index": ALL}, "style"),
    Input({"type": "annotation-color", "index": ALL}, "n_clicks"),
    State({"type": "annotation-color", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def annotation_color(color_value, current_style):
    """
    This callback is responsible for changing the color of the brush.
    """
    color = ctx.triggered_id["index"]
    if all(v is None for v in color_value):
        color = current_style[-1]["background-color"]
    for i in range(len(current_style)):
        if current_style[i]["background-color"] == color:
            current_style[i]["border"] = "3px solid black"
        else:
            current_style[i]["border"] = "1px solid"
    patched_figure = Patch()
    patched_figure["layout"]["newshape"]["fillcolor"] = color
    patched_figure["layout"]["newshape"]["line"]["color"] = color
    return patched_figure, current_style


@callback(
    Output("delete-all-warning", "opened"),
    Input("delete-all", "n_clicks"),
    Input("modal-cancel-button", "n_clicks"),
    Input("modal-delete-button", "n_clicks"),
    State("delete-all-warning", "opened"),
    prevent_initial_call=True,
)
def open_warning_modal(delete, cancel, delete_4_real, opened):
    return not opened


@callback(
    Output("generate-annotation-class-modal", "opened"),
    Input("generate-annotation-class", "n_clicks"),
    Input("create-annotation-class", "n_clicks"),
    State("generate-annotation-class-modal", "opened"),
    prevent_initial_call=True,
)
def open_annotation_class_modal(generate, create, opened):
    return not opened


@callback(
    Output("delete-annotation-class-modal", "opened"),
    Input("delete-annotation-class", "n_clicks"),
    Input("remove-annotation-class", "n_clicks"),
    State("delete-annotation-class-modal", "opened"),
    prevent_initial_call=True,
)
def open_delete_class_modal(delete, remove, opened):
    return not opened


@callback(
    Output("edit-annotation-class-modal", "opened"),
    Input("edit-annotation-class", "n_clicks"),
    Input("relabel-annotation-class", "n_clicks"),
    State("edit-annotation-class-modal", "opened"),
    prevent_initial_call=True,
)
def open_edit_class_modal(edit, relabel, opened):
    return not opened


@callback(
    Output("hide-annotation-class-modal", "opened"),
    Input("hide-annotation-class", "n_clicks"),
    Input("conceal-annotation-class", "n_clicks"),
    State("hide-annotation-class-modal", "opened"),
    prevent_initial_call=True,
)
def open_hide_class_modal(hide, conceal, opened):
    return not opened


@callback(
    Output("create-annotation-class", "disabled"),
    Output("bad-label-color", "children"),
    Input("annotation-class-label", "value"),
    Input("annotation-class-colorpicker", "value"),
    State({"type": "annotation-color", "index": ALL}, "children"),
    State({"type": "annotation-color", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def disable_class_creation(label, color, current_labels, current_colors):
    triggered_id = ctx.triggered_id
    warning_text = []
    if triggered_id == "annotation-class-label":
        if label in current_labels:
            warning_text.append(
                dmc.Text("This annotation class label is already in use.", color="red")
            )
    if color is None:
        color = "rgb(255,255,255)"
    else:
        color = color.replace(" ", "")
    if color == "rgb(255,255,255)" or triggered_id == "annotation-class-colorpicker":
        current_colors = [style["background-color"] for style in current_colors]
        if color in current_colors:
            warning_text.append(
                dmc.Text("This annotation class color is already in use.", color="red")
            )
    if (
        label is None
        or len(label) == 0
        or label in current_labels
        or color in current_colors
    ):
        return True, warning_text
    else:
        return False, warning_text


@callback(
    Output("relabel-annotation-class", "disabled"),
    Output("bad-label", "children"),
    Input("annotation-class-label-edit", "value"),
    State({"type": "annotation-color", "index": ALL}, "children"),
    prevent_initial_call=True,
)
def disable_class_editing(label, current_labels):
    warning_text = []
    if label in current_labels:
        warning_text.append(
            dmc.Text("This annotation class label is already in use.", color="red")
        )
    if label is None or len(label) == 0 or label in current_labels:
        return True, warning_text
    else:
        return False, warning_text


@callback(
    Output("remove-annotation-class", "disabled"),
    Output("at-least-one", "style"),
    Input({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def disable_class_deletion(highlighted):
    num_selected = 0
    for style in highlighted:
        if style["border"] == "3px solid black":
            num_selected += 1
    if num_selected == 0:
        return True, {"display": "none"}
    if num_selected == len(highlighted):
        return True, {"display": "initial"}
    else:
        return False, {"display": "none"}


@callback(
    Output("conceal-annotation-class", "disabled"),
    Output("at-least-one-hide", "style"),
    Input({"type": "annotation-hide-buttons", "index": ALL}, "style"),
    prevent_initial_call=True,
)
def disable_class_hiding(highlighted):
    num_selected = 0
    for style in highlighted:
        if style["border"] == "3px solid black":
            num_selected += 1
    if num_selected == 0:
        return True, {"display": "initial"}
    else:
        return False, {"display": "none"}


@callback(
    Output("annotation-class-selection", "children"),
    Output("annotation-class-label", "value"),
    Output("annotation-class-label-edit", "value"),
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("create-annotation-class", "n_clicks"),
    Input("remove-annotation-class", "n_clicks"),
    Input("relabel-annotation-class", "n_clicks"),
    Input("conceal-annotation-class", "n_clicks"),
    State("annotation-class-label", "value"),
    State("annotation-class-colorpicker", "value"),
    State("annotation-class-selection", "children"),
    State({"type": "annotation-delete-buttons", "index": ALL}, "style"),
    State({"type": "annotation-hide-buttons", "index": ALL}, "style"),
    State("current-annotation-classes-edit", "value"),
    State("annotation-class-label-edit", "value"),
    State("annotation-store", "data"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def add_delete_edit_hide_classes(
    create,
    remove,
    edit,
    hide,
    class_label,
    class_color,
    current_classes,
    classes_to_delete,
    classes_to_hide,
    old_label,
    new_label,
    annotation_store,
    image_idx,
):
    """
    Updates the list of available annotation classes,
    triggers other things that should happen when classes
    are added or deleted like removing annotations or updating
    the drawing mode.
    """
    triggered = ctx.triggered_id
    image_idx = str(image_idx - 1)
    patched_figure = Patch()
    current_stored_classes = annotation_store["label_mapping"]
    current_annotations = annotation_store["annotations"]
    if class_color is None:
        class_color = "rgb(255,255,255)"
    else:
        class_color = class_color.replace(" ", "")
    if triggered == "create-annotation-class":
        last_id = int(current_stored_classes[-1]["id"])
        annotation_store["label_mapping"].append(
            {
                "color": class_color,
                "id": last_id + 1,
                "label": class_label,
            }
        )
        if class_color == "rgb(255,255,255)":
            current_classes.append(
                dmc.ActionIcon(
                    id={"type": "annotation-color", "index": class_color},
                    w=30,
                    variant="filled",
                    style={
                        "background-color": class_color,
                        "border": "1px solid",
                        "color": "black",
                        "width": "fit-content",
                        "padding": "5px",
                        "margin-right": "10px",
                    },
                    children=class_label,
                )
            )
        else:
            current_classes.append(
                dmc.ActionIcon(
                    id={"type": "annotation-color", "index": class_color},
                    w=30,
                    variant="filled",
                    style={
                        "background-color": class_color,
                        "border": "1px solid",
                        "width": "fit-content",
                        "padding": "5px",
                        "margin-right": "10px",
                    },
                    children=class_label,
                )
            )
        return current_classes, "", "", annotation_store, no_update
    elif triggered == "relabel-annotation-class":
        for i in range(len(current_stored_classes)):
            if current_stored_classes[i]["label"] == old_label:
                annotation_store["label_mapping"][i]["label"] = new_label
                current_classes[i]["props"]["children"] = new_label
        return current_classes, "", "", annotation_store, no_update
    else:
        color_to_delete = []
        color_to_keep = []
        annotations_to_keep = {}
        for i in range(len(classes_to_delete)):
            if classes_to_delete[i]["border"] == "3px solid black":
                color_to_delete.append(
                    classes_to_delete[i]["background-color"].replace(" ", "")
                )
        current_stored_classes = [
            class_pair
            for class_pair in current_stored_classes
            if class_pair["color"] not in color_to_delete
        ]
        for key, val in current_annotations.items():
            val = [
                shape for shape in val if shape["line"]["color"] not in color_to_delete
            ]
            if len(val):
                annotations_to_keep[key] = val
        for color in current_classes:
            if color["props"]["id"]["index"] not in color_to_delete:
                color_to_keep.append(color)
        annotation_store["label_mapping"] = current_stored_classes
        annotation_store["annotations"] = annotations_to_keep
        if image_idx in annotation_store["annotations"]:
            patched_figure["layout"]["shapes"] = annotation_store["annotations"][
                image_idx
            ]
        else:
            patched_figure["layout"]["shapes"] = []
        return color_to_keep, "", "", annotation_store, patched_figure


@callback(
    Output("annotation-store", "data", allow_duplicate=True),
    Output("image-viewer", "figure", allow_duplicate=True),
    Input("view-annotations", "checked"),
    Input("modal-delete-button", "n_clicks"),
    State("annotation-store", "data"),
    State("image-viewer", "figure"),
    State("image-selection-slider", "value"),
    prevent_initial_call=True,
)
def annotation_visibility(checked, delete_all, annotation_store, figure, image_idx):
    """
    This callback is responsible for toggling the visibility of the annotation layer.
    It also saves the annotation data to the store when the layer is hidden, and then loads it back in when the layer is shown again.
    """
    image_idx = str(image_idx - 1)
    patched_figure = Patch()
    if ctx.triggered_id == "modal-delete-button":
        annotation_store["annotations"][image_idx] = []
        patched_figure["layout"]["shapes"] = []
    else:
        if checked:
            annotation_store["visible"] = True
            patched_figure["layout"]["visible"] = True
            if str(image_idx) in annotation_store["annotations"]:
                patched_figure["layout"]["shapes"] = annotation_store["annotations"][
                    image_idx
                ]
            patched_figure["layout"]["dragmode"] = annotation_store["dragmode"]
        else:
            new_annotation_data = (
                [] if "shapes" not in figure["layout"] else figure["layout"]["shapes"]
            )
            annotation_store["visible"] = False
            patched_figure["layout"]["dragmode"] = False
            annotation_store["annotations"][image_idx] = new_annotation_data
            patched_figure["layout"]["shapes"] = []

    return annotation_store, patched_figure


clientside_callback(
    """
    function dash_filters_clientside(brightness, contrast) {
    console.log(brightness, contrast)
        js_path = "#image-viewer > div.js-plotly-plot > div > div > svg:nth-child(1)"
        changeFilters(js_path, brightness, contrast)
        return ""
    }
    """,
    Output("dummy-output", "children", allow_duplicate=True),
    Input("figure-brightness", "value"),
    Input("figure-contrast", "value"),
    prevent_initial_call=True,
)


@callback(
    Output("figure-brightness", "value", allow_duplicate=True),
    Output("figure-contrast", "value", allow_duplicate=True),
    Input("filters-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(n_clicks):
    default_brightness = 100
    default_contrast = 100
    return default_brightness, default_contrast


# TODO: check this when plotly is updated
clientside_callback(
    """
    function eraseShape(_, graph_id) {
        Plotly.eraseActiveShape(graph_id)
        return dash_clientside.no_update
    }
    """,
    Output("image-viewer", "id", allow_duplicate=True),
    Input("eraser", "n_clicks"),
    State("image-viewer", "id"),
    prevent_initial_call=True,
)


@callback(
    Output("notifications-container", "children"),
    Output("export-annotation-metadata", "data"),
    Output("export-annotation-mask", "data"),
    Input("export-annotation", "n_clicks"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def export_annotation(n_clicks, annotation_store):
    EXPORT_AS_SPARSE = False  # todo replace with input
    if not annotation_store["annotations"]:
        metadata_data = no_update
        notification_title = "No Annotations to Export!"
        notification_message = "Please annotate an image before exporting."
        notification_color = "red"
    else:
        annotations = Annotations(annotation_store)

        # medatada
        annotations.create_annotation_metadata()
        metadata_file = {
            "content": json.dumps(annotations.get_annotations()),
            "filename": "annotation_metadata.json",
            "type": "application/json",
        }

        # mask data
        annotations.create_annotation_mask(sparse=EXPORT_AS_SPARSE)
        mask_data = annotations.get_annotation_mask_as_bytes()
        mask_file = dcc.send_bytes(mask_data, filename=f"annotation_masks.zip")

        # notification
        notification_title = "Annotation Exported!"
        notification_message = "Succesfully exported in .json format."
        notification_color = "green"

    notification = dmc.Notification(
        title=notification_title,
        message=notification_message,
        color=notification_color,
        id="export-annotation-notification",
        action="show",
        icon=DashIconify(icon="entypo:export"),
    )
    return notification, metadata_file, mask_file


@callback(
    Output("drawer-controls", "opened"),
    Output("image-slice-selection-parent", "style"),
    Input("drawer-controls-open-button", "n_clicks"),
    # prevent_initial_call=True,
)
def open_controls_drawer(n_clicks):
    return True, {"padding-left": "450px"}


@callback(
    Output("image-slice-selection-parent", "style", allow_duplicate=True),
    Input("drawer-controls", "opened"),
    prevent_initial_call=True,
)
def open_controls_drawer(is_opened):
    if is_opened:
        raise PreventUpdate
    return {"padding-left": "50px"}
