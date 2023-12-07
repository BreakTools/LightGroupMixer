import nuke


def update_light_group_mixer() -> None:
    """This function adds/removes our lightgroups to/from our gizmo."""
    lightgroup_mixer_node = nuke.thisNode()

    channels = _get_all_channels(lightgroup_mixer_node)
    if channels is None:
        return

    all_lightgroups, lightgroups_to_build = _get_lightgroups(
        lightgroup_mixer_node, channels
    )

    to_connect_to = _get_node_to_connect_to()

    _add_lightgroups(lightgroups_to_build, to_connect_to, lightgroup_mixer_node)

    lightgroups_to_remove = _get_old_unused_lightgroups(
        lightgroup_mixer_node, all_lightgroups
    )
    _remove_lightgroupgrade_nodes(lightgroup_mixer_node, lightgroups_to_remove)

    reset_solos()


def _get_all_channels(lightgroup_mixer_node: nuke.Node) -> list:
    """This function returns all the channels from the input node."""
    try:
        return lightgroup_mixer_node.input(0).channels()
    except AttributeError:
        nuke.message("You haven't connected your input node.")
        return None


def _get_node_to_connect_to() -> nuke.Node:
    """This functions returns the node our next node should connect to."""
    try:
        if nuke.toNode("Output1").input(0).Class() == "LightGroupGrade":
            to_connect_to = nuke.toNode("Output1").input(0)
        else:
            to_connect_to = nuke.toNode("Input1")

    except AttributeError:
        to_connect_to = nuke.toNode("Input1")

    return to_connect_to


def _get_lightgroups(lightgroup_mixer_node: nuke.Node, channels) -> tuple:
    """This function returns all the lightgroups and the lightgroups we still need to build."""
    all_knobs = lightgroup_mixer_node.knobs()
    all_lightgroups = []
    lightgroups_to_build = []
    for channel in channels:
        if not channel.startswith("LG_"):
            continue

        # Seeing as lightgroups contains several subchannels, we just
        # pick one. Blue is my favorite color, so I went with that :)
        if not channel.endswith("blue"):
            continue

        all_lightgroups.append(channel.split(".")[0])

        if f"{channel.split('.')[0]}_tab_begin" in all_knobs:
            continue

        lightgroups_to_build.append(channel)

    return all_lightgroups, lightgroups_to_build


def _add_lightgroups(
    lightgroups_to_build, to_connect_to, lightgroup_mixer_node: nuke.Node
) -> None:
    """This function creates grader nodes and adds the proper menu items."""
    for lightgroup in lightgroups_to_build:
        grader_node = _create_grader_node(to_connect_to, lightgroup)
        to_connect_to = grader_node

        _create_menu_tab(lightgroup, lightgroup_mixer_node, grader_node)

    nuke.toNode("Output1").setInput(0, to_connect_to)


def _create_menu_tab(
    lightgroup: str, lightgroup_mixer_node: nuke.Node, grader_node: nuke.Node
) -> None:
    """This function creates the tab for a lightgroup and adds knobs to it."""
    light_group_name = f"{lightgroup.split('LG_')[1].split('.')[0]}"

    lightgroup_tab_begin = nuke.Tab_Knob(
        f"LG_{light_group_name}_tab_begin",
        light_group_name,
        nuke.TABBEGINCLOSEDGROUP,
    )
    lightgroup_mixer_node.addKnob(lightgroup_tab_begin)

    solo_button = nuke.PyScript_Knob(
        f"LG_{light_group_name}_solo",
        "Solo",
        f"light_group_mixer.solo_lightgroup('LG_{light_group_name}')",
    )
    lightgroup_mixer_node.addKnob(solo_button)

    _link_lightgroupgrade_knobs(grader_node, lightgroup_mixer_node)

    lightgroup_tab_end = nuke.Tab_Knob(
        f"LG_{light_group_name}_tab_end",
        light_group_name,
        nuke.TABENDGROUP,
    )

    lightgroup_mixer_node.addKnob(lightgroup_tab_end)


def _create_grader_node(to_connect_to: nuke.Node, lightgroup: str) -> nuke.Node:
    """This function creates a LightGroupGrade nodes and hooks it up."""
    grader_node = nuke.nodes.LightGroupGrade()
    grader_node.setInput(0, to_connect_to)
    grader_node.setName(lightgroup.split(".")[0])
    grader_node["lightgroup"].setValue(lightgroup.split(".")[0])
    return grader_node


def _link_lightgroupgrade_knobs(
    grader_node: nuke.Node, lightgroup_mixer_node: nuke.Node
) -> None:
    """This function links the LightGroupGrade knobs to our main mixer node."""
    for knob in grader_node.knobs():
        if knob not in ("exposure", "multiply", "saturation"):
            continue

        link_knob = nuke.Link_Knob(knob)
        link_knob.setLink(grader_node.name() + "." + knob)
        link_knob.setName(f"{grader_node.name()}_{knob}")
        link_knob.setLabel(knob)
        lightgroup_mixer_node.addKnob(link_knob)


def _get_old_unused_lightgroups(
    lightgroup_mixer_node: nuke.Node, all_lightgroups: list
) -> list:
    """This functions constructs a list of old stored lightgroups that no longer exist."""
    lightgroups_to_remove = []
    for knob in lightgroup_mixer_node.knobs():
        if not knob.startswith("LG_"):
            continue

        delete = True
        for lightgroup in all_lightgroups:
            if knob.startswith(lightgroup):
                delete = False

        if delete:
            if knob.endswith("_tab_end"):
                lightgroups_to_remove.append(knob.split("_tab_")[0])

            lightgroup_mixer_node.removeKnob(lightgroup_mixer_node.knobs()[knob])

    return lightgroups_to_remove


def _remove_lightgroupgrade_nodes(
    lightgroup_mixer_node: nuke.Node, lightgroups_to_remove: list
) -> None:
    """This function removes all LightGroupGrade nodes in a list."""
    for node in lightgroup_mixer_node.nodes():
        if node.Class() == "LightGroupGrade":
            if node.name() in lightgroups_to_remove:
                nuke.delete(node)


def solo_lightgroup(light_group_name: str) -> None:
    """This functions adds a lightgroup to our solo list and changes the button."""
    lightgroup_mixer_node = nuke.thisNode()

    if (
        lightgroup_mixer_node["Showing"].value() == "All lightgroups"
        or lightgroup_mixer_node["Showing"].value() == "Nothing"
    ):
        lightgroup_mixer_node["Showing"].setValue(light_group_name)
    else:
        lightgroup_mixer_node["Showing"].setValue(
            f"{lightgroup_mixer_node['Showing'].value()} {light_group_name}"
        )

    lightgroup_mixer_node[f"{light_group_name}_solo"].setCommand(
        f"light_group_mixer.unsolo_lightgroup('{light_group_name}')"
    )
    lightgroup_mixer_node[f"{light_group_name}_solo"].setLabel("Unsolo")

    _set_solos(lightgroup_mixer_node)


def unsolo_lightgroup(light_group_name: str) -> None:
    """This function removes a lightgroup from our solo list and changes the button."""
    lightgroup_mixer_node = nuke.thisNode()
    solo_light_groups = lightgroup_mixer_node["Showing"].value().split()
    solo_light_groups.remove(light_group_name)
    if len(solo_light_groups) != 0:
        lightgroup_mixer_node["Showing"].setValue(" ".join(solo_light_groups))
    else:
        lightgroup_mixer_node["Showing"].setValue("All lightgroups")

    lightgroup_mixer_node[f"{light_group_name}_solo"].setCommand(
        f"light_group_mixer.solo_lightgroup('{light_group_name}')"
    )
    lightgroup_mixer_node[f"{light_group_name}_solo"].setLabel("Solo")

    _set_solos(lightgroup_mixer_node)


def _set_solos(lightgroup_mixer_node: nuke.Node) -> None:
    """This function enables or disables our nodes based on our solo list."""
    for node in lightgroup_mixer_node.nodes():
        if node.Class() != "LightGroupGrade":
            continue

        if lightgroup_mixer_node["Showing"].value() == "All lightgroups":
            node["disable"].setValue(False)
        elif node.name() in lightgroup_mixer_node["Showing"].value():
            node["disable"].setValue(False)
        else:
            node["disable"].setValue(True)


def reset_solos() -> None:
    """This function sets all LightGroupGrade nodes to enabled."""
    lightgroup_mixer_node = nuke.thisNode()

    if lightgroup_mixer_node["Showing"].value() == "All lightgroups":
        return

    if lightgroup_mixer_node["Showing"].value() == "Nothing":
        lightgroup_mixer_node["Showing"].setValue("All lightgroups")
        return

    solo_light_groups = lightgroup_mixer_node["Showing"].value().split()

    for solo_light_group in solo_light_groups:
        unsolo_lightgroup(solo_light_group)
