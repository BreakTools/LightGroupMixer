toolbar = nuke.menu("Nodes")
breaktools_menu = toolbar.addMenu("BreakTools", icon="BreakToolsIcon.png")
breaktools_menu.addCommand("LightGroupGrade", "nuke.createNode('LightGroupGrade')")
breaktools_menu.addCommand("LightGroupMixer", "nuke.createNode('LightGroupMixer')")
