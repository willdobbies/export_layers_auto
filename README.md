A modified version of the "export layers" krita plugin.

Changes:
- Automate file & directory selection for export:
  - Auto select currently viewed file.
  - Output directory is derived from filename. (example: /home/user/draws/MyProject.kra -> /home/user/draws/MyProject/*.png) 
- Tweak some of the default options (merge groups, png type)
- Separated export code into it's own self-contained module

TODO:
- Output more information during export (json metadata, layer hierarchy, etc)
- Custom output directory & filename patterns (regex)
- Multi-file export option
- Save & restore default options
- Display export progress bar
