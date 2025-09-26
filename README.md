# Captioning filter pipeline

caption.json -> run_anormality_check.py -> filtered_caption.json


## Case 1: Filtering given tolerance
Please refer to `example1_check_and_filter.sh`.

The `tolerance` argument defines how many mistakes are allowed before filtering out the caption.

For example, the following errors are detected and exported as `problem_output.json` (in the format of `tuple: (question_id, caption, error_count)`)
```json
    [
      14,
      "��Instruments: strings ensemble, accordion, ukulele, percussion group including electronic drums and tambourine with bass, string section for dramatic ambience. Upbeat, playful, bright and cheerful orchestral pop song in 21st century sounds. Laidedback beat with strumming techniques and plucky, driving energy. Accented with reverb effect. Use for soundtrack in a daytime TV show for family-friendly action and adventure scenes, feel good mood with bright feel for cinematic storylines, use music from 2010s.",
      2
    ],
    [
      35,
      "�21st, 2020s folk band.\nDriving rhythm from the drums\nSparkly acoustic instruments\nSynth pads and string sounds\nPickin guitar with reverb\nAngular melody with a bright and happy feel and laid-back energy.\nThe string ensemble adds a unique flavor, suitable for funny/quirky, comedic/daytime TV",
      1
    ]
```

If the `tolerance=1`, `question_id=14` will be filtered out.

## Case 2: Self-fixing and then filtering given tolerance
For minor mistakes, we can predefined rules to replace the characters.

For example, removing the `�` characters from the captions before error checking.

Please refer to `example2_selffix_check_and_filter.sh`.

The replacement rules are defined in the `homoglyph_map` inside `llm_postprocessor/llm_postprocessor/utils.py`.