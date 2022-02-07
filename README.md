TODO: write about blender project organization

# Game Resources Exporter v0.8
The game can have a huge number of models, textures, and other resources that need to be exported to the desired format that the engine reads.  
Doing all this manually is boring, time consuming, and generally distracts from the creative process. It is better to leave this task to an automated exporter, plus - strict export rules will give a more stable resource storage architecture.  
This exporter detecting files changes in real time, identifies them, and exports according to the given rules. Its also using separate folders, one for raw resoureces, whose changes will be observed, and one for exported files, which you use in game.  
Exporter was oriented on [Godot](https://godotengine.org), but its not a problem to use it in any different way - for example, [here](resources_exporter/plugins/garrys_mod) is the plugin for GMod addons resources export.  

## Features
* Individual Blender project exporter with configurable export using *custom properties* of objects.
* Godot models, physics bodies and materials generation.
* Extending with plugins.
* Single program for many separate projects.

## Core Exporting Features
* pure sound, image, and model files will just be copied.
* `.psd` will convert into `.png`.
* `.blend` export will create `.obj` or `.glb` models for every blender collection (Except one named 'Collection'), and also will generate Godot `.tres` and `.tscn` files for materials, view models, collision shapes and physics bodies. Also icons can be rendered.
<details>
<summary>
exporter_config.json
</summary>

```json
{
  "image_magic_cmd": "convert",
  "raw_folder": "resources",
  "output_folder": "project/resources",
  "output_root": "project",
  "verbose": true
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
+---resources                                    (raw resources folder)
|   +---models
|   |   \---tools
|   |           macro_exploiter.blend
|   |           macro_exploiter.psd
|   |           macro_exploiter_emission.psd
|   |
|   \---ui
|            game_icon.psd
|            icon_export.export.json
|
\---project
    \---resources                                (fully generated)
        +---models
        |   \---tools
        |           macro_exploiter.obj
        |           macro_exploiter.png
        |           macro_exploiter.tscn
        |           macro_exploiter_emission.png
        |           macro_exploiter_icon.png
        |           macro_exploiter_phy_collision_shape.tscn
        |           macro_exploiter_rigid_body.tscn
        |           mat_macro_exploiter.tres
        |           mat_snow.tres
        |
        \---ui
                game_icon.ico
                game_icon.png
```

</details>

<br />

## Plugins
* ### [Garry's Mod addon resources Exporter](resources_exporter/plugins/garrys_mod)

<br />

## Requirements
* [Python >= 3.9](https://www.python.org/downloads/).
* [ImageMagic](https://imagemagick.org/script/download.php). For images conversion from `.psd` or into `.ico`.
