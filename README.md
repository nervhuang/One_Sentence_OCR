# One_Sentence_OCR

A minimal OCR project.

## Configuration

You can customize runtime options in a `config.ini` file placed next to the executable/script. Example `config.ini`:

```ini
[options]
remove_newlines = False
ocr_language = chi_sim+eng
force_brackets = True

[window]
# Optional window geometry saved on exit
# x = 100
# y = 100
# width = 400
# height = 300

[selection]
# Optional last selection box saved on capture
# x = 100
# y = 100
# width = 640
# height = 360
```

- `remove_newlines`: when `True` the OCR result will have newlines removed.
- `ocr_language`: language code used by the OCR worker (e.g. `chi_sim+eng`, `jpn+eng`).
- `force_brackets`: when `True` the app will replace fullwidth/CJK brackets and several fullwidth punctuation characters with their ASCII equivalents (e.g. `（` -> `(`, `）` -> `)`, `【` -> `[`).

Remember to restart the application after editing `config.ini` if you edit it manually.
