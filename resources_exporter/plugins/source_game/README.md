# [Plugin] Source Engine game resources exporter

## Requires

* [VTFLib](https://web.archive.org/web/20190508141002/http://nemesis.thewavelength.net/files/files/vtflib132-bin.zip). For converting images to vtf.
* Some executables that comes with *Source* games in *bin* folder.
  * **studiomdl**. To compile models into `.mdl`.
  * **vbsp**, **vvis**, **vrad**. To compile `.vmf` maps into `.bsp`.

## Work

### General
* As a *Source* game directory will be used value of property `game_root` in exporter config. It is directory where `gameinfo.txt` or `liblist.gam` is located. For example, for garry's mod addon game dir is `"Garry's Mod/garrysmod/"`.

### Materials Export
* `.psd` and all pure images will convert into `.vtf` and `.vmt`. (if the image file is on the path `models/.../img` then it will be exported on the path `materials/models/.../img`, this allows you to store textures and models in the same directory).

### Models Export
* `.blend` export will create `.smd` files for every collection, and `.qc` near to `.blend` file. Then `.qc` will be used to compile `.mdl` model files in the output folder.  
* unlike smd files, `.qc` files will be generated and saved only if they dont exist.

### QC file repairing

This is a small number of tasks that allows you to import models from the old *GoldSrc*, and just from third-party games

* If the value of the `$cdmaterials` property does not match the expected path, the property will be updated.
* `.qc` can be updated if it has commands for *GoldSrc* that are not supported in the new *Source engine*. Unsupported commands will be removed.
* If the `$texrendermode` command with the `masked` parameter is found in `.qc`, the `$alphatest` property is added to the `.vmt` material file, and `.bmp` images (which appear when *GoldSrc* models are decompiled) are converted to `.psd` with black pixels replaced with transparent ones, using `<ImageMagic> -colorspace RGB -transparent black img.bmp img.psd`.
* `$texrendermode` with the `additive` parameter, will add `$additive` to the `.vmt` file


<details>
<summary>
exporter_config.json
</summary>

```json
{
  "image_magic_cmd": "convert",
  "raw_folder": "raw",
  "output_folder": ".",
  "game_root": ".",
  "verbose": true,
  "plugins": [
    "source_game"
  ],
  "studiomdl_executable": "studiomdl.exe",
  "vbsp_executable": "vbsp.exe",
  "vvis_executable": "vvis.exe",
  "vrad_executable": "vrad.exe",
  "vtfcmd_executable": "VTFCmd.exe",
  "use_goldsrc": false
}
```

</details>

<details>
<summary>
File system example
</summary>

```
.
|   exporter_config.json
|   files_registry.json
|
+---raw                             (raw resources folder)
|   +---materials
|   |   \---models
|   |       \---kebabs
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
|                   kebab_0.psd
|                   kebab_1.psd
|                   kebab_2.psd
|                   kebab_3.psd
|                   kebab_4.psd
|                   kebab_5.psd
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
|           |
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

<br />