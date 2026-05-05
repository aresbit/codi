# LM Model Behavior Notes

## Output Format

The 5Hz LM model (`acestep-5Hz-lm-4B`) outputs lyrics as **phoneme tokens**, not written characters:

- **Chinese (vocal_language="zh")**: Outputs pinyin with tone numbers, e.g.:
  ```
  [zh] zhan3 kai1 meng4 xiang3 de5 chi4 bang3
  ```
  Translates to: "展开梦想的翅膀" (spread the wings of dreams)

- **English**: Outputs English text directly, e.g.:
  ```
  [en] break the limit
  ```

- **Japanese** (if attempted): Falls back to pinyin; model does not natively support Japanese romaji output.

**Why**: The LM uses phoneme-level tokenization for better alignment with singing synthesis. The synth pipeline maps phonemes directly to audio, avoiding the need for a separate grapheme-to-phoneme conversion step.

## Language Tagging

Each line is tagged with language:
- `[zh]` = Chinese phonemes (pinyin with tone numbers)
- `[en]` = English text
- The model can mix languages in a single song (e.g., Chinese verses with English chorus hook)

## LM Modes

| Mode | Name Constant | Description |
|------|---------------|-------------|
| `generate` | `LM_MODE_GENERATE` | Full generation: metadata + lyrics + audio codes. Requires caption only. |
| `inspire` | `LM_MODE_INSPIRE` | Short query → metadata + lyrics only (no audio codes). Faster, less capable. |
| `format` | `LM_MODE_FORMAT` | Caption + user-provided lyrics → enrich with metadata and audio codes. Uses existing lyrics. |

Default is `generate`. Use `inspire` for quick ideation, `generate` for full production.

## Prompt Engineering Tips

- **Style description matters**: Be specific about genre, instruments, vocal style, mood.
- **Lyrics reference**: Including desired lyrics in the caption influences the output direction, but the model will generate its own version.
- **Structure markers**: Requesting `[INTRO]`, `[VERSE]`, `[CHORUS]` markers in the caption helps structure.
- **Theme focus**: Keep the theme concise. The model responds better to clear emotional direction than abstract poetry.

## format Mode — Using User-Provided Lyrics

Use `lm_mode: "format"` + `lyrics` field to provide exact lyrics. The model will NOT modify them — it only enriches with metadata (BPM, key) and generates audio codes.

```json
{
  "lm_mode": "format",
  "lyrics": "[VERSE 1]\nYour lyrics here...",
  "caption": "Style: Pop Ballad — piano, emotional...",
  "vocal_language": "zh"
}
```

**Behavior**:
- Lyrics are used as-is, no rewriting
- The model still needs `caption` for style/theme context (affects metadata generation)
- `vocal_language` must match the lyrics language
- Works with any language supported by the synth model

**When to use**:
- User has professional/written lyrics they want to keep
- Need precise control over song structure and verses
- Generating covers or adaptations of existing lyrics

## Limitations

- Model is 4B parameters (quantized to Q5_K_M ~3GB) — creativity and coherence are functional but limited compared to larger LLMs.
- In `generate` mode, cannot exactly reproduce user-provided lyrics — always generates original content based on caption.
- In `format` mode, user-provided lyrics are preserved exactly.
- Repetitive patterns in pre-chorus/breakdown sections are common (model loops phrases for rhythmic effect).
- Chinese lyrics always output as pinyin (phonemes) in `generate` mode; in `format` mode, the original Chinese characters are preserved.
