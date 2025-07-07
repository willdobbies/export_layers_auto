# Export Layers Auto
A plugin which automates export of individual layers in Krita. Forked from the default plugin which is shipped with the software.

# New Features
+ Added a keyboard shortcut to trigger layer export (current file)
+ TODO: Modify default export options
+ TODO: Display export progress bar

# New Options
### `Name Format` 
- Default: `{document_name} - {layer_name}.{ext}`
- Available Variables: 
| value             | Description                                       |
|-------------------|---------------------------------------------------|       
| {document_name}   | Name of Krita document                            |
| {layer_name}      | Name of layer within Krita                        |
| {ext}             | Image format extension (png, jpg, etc.)           |

+ TODO: output .json metadata files along with layers
+ TODO: Export all open files
