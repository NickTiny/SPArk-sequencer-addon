# Dope Sheet

This page covers overlays that are present in the Dope Sheet as well as the Action Editor and Timeline views in Blender. These regions are tied to the active strip, and represent the internal timing of the Scene Strip's target Scene.

![Timeline Overlay](media/dopesheet_overlay.jpg)

## Sequence Viewport Panel

### Timeline Overlay Boolean
Control the display of the Timeline Overlay with this boolean. When enabled a representation of your timeline's Scene Strip timing will be displayed in the Dope Sheet, Action Editor or Timeline region.


## Timeline Overlay

### Strip Gizmo
Each Scene strip is represented by a gizmo indicated with the strip name overlayed into the Dope Sheet, Action Editor or Timeline region. Only Strips that are targeting the active Scene Strip will be displayed.

### Adjust Timing

There are three ways to adjust timing of the Scene Strip from the Timeline Overlay. 

 - **Green Handle:** Adjusts the left handle of the scene strip. This will also adjust any affected Scene Strips on the same Channel in the Sequencer Region.
 - **Red Handle:** Adjusts the right handle of the scene strip. This will also adjust any affected Scene Strips on the same Channel in the Sequencer Region. Similar to the [Adjust Timing](#broken-link) operator in the Strip Menu.
 - **Upper Center Handle:** Select the top of the gizmo to [Slip Strip Content](https://docs.blender.org/manual/en/latest/video_editing/edit/montage/editing.html#slip-strip-contents). This will only affect the internal timing of the Scene Strip and will not affect the length of the strip.