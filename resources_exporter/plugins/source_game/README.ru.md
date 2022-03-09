# [Plugin] Экспортер ресурсов для игр на движке Source

## Требует

* [VTFLib](https://web.archive.org/web/20190508141002/http://nemesis.thewavelength.net/files/files/vtflib132-bin.zip). Для конвертации изображений в vtf.
* [Blender Source Tools](http://steamreview.org/BlenderSourceTools/). Для экспорта `.smd` файлов из `.blend` проектов.
* Некоторые исполняемые файлы, поставляемые с *Source* играми, находятся в папке *bin* .
  * **studiomdl** . Для компиляции моделей в `.mdl` .
  * **vbsp**, **vvis**, **vrad** . Для компиляции карт `.vmf` в `.bsp` .

## Выполняемая Работа

### Общее
* В качестве директории *Source* игры будет использоваться значение свойства `game_root` в конфиге экспортера. Это каталог, в котором находится `gameinfo.txt` или `liblist.gam`. Например, для garry's mod аддона директория игры будет `"Garry's Mod/garrysmod/"`.

### Экспорт Материалов
* `.psd` и все чистые изображения будут конвертированы в `.vtf` и `.vmt`. (если файл изображения находится по пути `models/.../img`, то он будет экспортирован так: `materials/models/.../img`, это позволяет хранить текстуры и модели в одной директории).

### Экспорт Моделей
* При экспорте`.blend`, будут созданы `.smd` файлы для каждой коллекции, а также будет создан `.qc` рядом с `.blend` файлом. Затем `.qc` будет использоваться для компиляции `.mdl` файлов моделей в выходной папке.
* В отличие от `.smd` файлов, файлы `.qc` будут созданы и сохранены только в том случае, если их не существует.

### Восстановление QC Файлов

Это небольшой ряд задач который позволяет импортировать модели из старого *GoldSrc*, и просто из сторонних игр

* Эсли значение свойства `$cdmaterials` не соответствует ожидаемому пути, свойство будет обновлено.
* `.qc` может быть обновлен, если имеет комманды для *GoldSrc*, которые не поддерживаются в новом *движке Source*. Не поддерживаемые комманды удаляются.
* Если в `.qc` найдена комманда `$texrendermode` с параметром `masked`, то в `.vmt` файл материала добавится свойство `$alphatest`, а `.bmp` изображения (которые появляются при декомпиляции *GoldSrc* моделей) будут конвертированы в `.psd` с помощью `<ImageMagic> -colorspace RGB -transparent black img.bmp img.psd`, то есть с заменой черных пикселей на прозрачные.
* `$texrendermode` с параметром `additive`, добавит в `.vmt` файл `$additive`


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