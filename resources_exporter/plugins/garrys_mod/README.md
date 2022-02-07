## Garry's Mod addon resources Exporter
* `.psd` and all pure images will convert into `.vtf` and `.vmt`.
* `.blend` export will create `.smd` files for every collection, and `.qc` (`.qc`, once created, will not be overwritten) near to `.blend` file. Then `.qc` will be used to compile `.mdl` model files in the output folder.  

Requires
* [VTFLib](https://web.archive.org/web/20190508141002/http://nemesis.thewavelength.net/files/files/vtflib132-bin.zip). For converting images to vtf.
* **studiomdl** that comes with *Source* games in *bin* folder. For models compilation into `.mdl`.

<details>
<summary>
exporter_config.json
</summary>

```json
{
  "studiomdl_game_path": "C:/Program Files/Strogino CS Portal/Garrys Mod/garrysmod",
  "studiomdl_executable": "studiomdl.exe",
  "vtfcmd_executable": "VTFCmd.exe",
  "image_magic_cmd": "convert",
  "raw_folder": "raw",
  "output_folder": ".",
  "output_root": ".",
  "verbose": true,
  "plugins": [
    "garrys_mod"
  ]
}
```

</details>

<details>
<summary>
File system example
</summary>

```
.
|   addon.txt
|   exporter_config.json
|   files_registry.json
|
+---raw                             (raw resources folder)
|   +---materials
|   |   \---models
|   |       \---kebabs
|   |           +---kebab
|   |           |       kebab_0.psd
|   |           |       kebab_1.psd
|   |           |       kebab_2.psd
|   |           |       kebab_3.psd
|   |           |       kebab_4.psd
|   |           |       kebab_5.psd
|   |           |
|   |           \---skewer
|   |                   skewer.vmt
|   |
|   \---models
|       \---kebabs
|           \---kebab
|                   kebab.blend
|                   kebab.qc        (generated)
|                   kebab_phy.smd   (generated)
|                   kebab_ref.smd   (generated)
|
+---materials                       (fully generated)
|   \---models
|       \---kebabs
|           +---kebab
|           |       kebab_0.vmt
|           |       kebab_0.vtf
|           |       kebab_1.vmt
|           |       kebab_1.vtf
|           |       kebab_2.vmt
|           |       kebab_2.vtf
|           |       kebab_3.vmt
|           |       kebab_3.vtf
|           |       kebab_4.vmt
|           |       kebab_4.vtf
|           |       kebab_5.vmt
|           |       kebab_5.vtf
|           \---skewer
|                   skewer.vmt
|
\---models                          (fully generated)
    \---kebabs
        \---kebab
                kebab.dx80.vtx
                kebab.dx90.vtx
                kebab.mdl
                kebab.phy
                kebab.sw.vtx
                kebab.vvd
```

</details>