# A-Level Question Perturbation Pipeline

A complete pipeline for transcribing, perturbing, validating, and extracting A-Level mathematics questions using GPT-5.

## Overview

This project takes screenshots of A-Level mathematics questions and produces perturbed versions compiled into a professional LaTeX document.

### Pipeline Stages

1. **Transcription**: Convert images of A-Level questions to JSON format
2. **Perturbation**: Generate perturbed versions of questions while maintaining validity
3. **Validation**: Verify that perturbed questions are well-posed and mathematically correct
4. **Extraction**: Compile validated questions into a ready-to-compile LaTeX document

## Project Structure

```
alevel-question-generation/
├── script.py                 # Main pipeline script
├── requirements.txt          # Python dependencies
├── json template.txt         # JSON schema for questions
├── img/                      # Input: Place question images here
├── prompts/                  # AI prompts for each stage
│   ├── 1_transcribe_prompt.txt
│   ├── 2_perturb_prompt.txt
│   ├── 3_validate_prompt.txt
│   └── 4_extract_prompt.txt
├── examples/                 # LaTeX style examples
│   ├── example1.tex
│   ├── example2.tex
│   ├── example3.tex
│   └── example4.tex
└── output/                   # Generated outputs
    ├── 1_transcribed.jsonl
    ├── 2_perturbed.jsonl
    ├── 3_validated.jsonl
    └── 4_final_document.tex  # ✨ Final compilable document
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

**Linux/Mac (bash/zsh):**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Prepare Input Images

Place screenshots of A-Level questions (PNG, JPG, or JPEG) in the `img/` directory.

**Important:** Images should contain questions only, **without** answers, solutions, or diagrams.

## Usage

Run the complete pipeline:

```bash
python script.py
```

### Interactive Prompts

During execution, you'll be asked:

1. **Clear /img directory after transcription?** (y/n)
   - Choose `y` to auto-delete images after processing

2. **Special prompt for each stage** (or press Enter to skip)
   - Optional custom instructions for each pipeline stage
   - Examples:
     - Transcription: "All questions are from 2024 AQA A-Level Mathematics Paper 1"
     - Perturbation: "Focus on changing numeric values only, keep structure identical"
     - Extraction: "Use larger font size for better readability"

### Output

The pipeline generates:

- `output/1_transcribed.jsonl` - Transcribed questions in JSON format
- `output/2_perturbed.jsonl` - Perturbed versions of questions
- `output/3_validated.jsonl` - Questions that passed validation
- `output/4_final_document.tex` - **Ready-to-compile LaTeX document** ✨

## JSON Schema

Questions use the following schema:

```json
{
  "id": null,
  "exam": "AQA A-Level Mathematics",
  "year": 2024,
  "difficulty": 3,
  "topics": ["calculus", "integration"],
  "question": "Find $\\int x^2 \\sin(x) \\, dx$.",
  "marks": 8
}
```

### Fields

- `id`: Unique identifier (optional)
- `exam`: Exam board/name (optional)
- `year`: Year of exam (optional)
- `difficulty`: Integer 1-5 (1=Very Easy, 5=Very Hard)
- `topics`: Array of topic strings
- `question`: Question text with LaTeX notation
- `marks`: Mark allocation (integer)

### LaTeX Notation

- **Inline math**: `$x^2$`, `$\\frac{1}{2}$`
- **Display math**: `\\[ \\int_0^1 x^2 \\, dx \\]`
- **Escaping**: In JSON, use double backslashes: `"\\\\frac{1}{2}"` → `\frac{1}{2}`

## Cost Tracking

The script reports detailed cost information for each stage:

- Token usage (input/output)
- API costs (based on GPT-5 pricing: $1.25/M input, $10/M output)
- Elapsed time
- Stage-by-stage breakdown
- Total pipeline costs

## Customization

### Modifying Prompts

Edit files in `prompts/` to customize behavior:

- `1_transcribe_prompt.txt` - Control transcription rules
- `2_perturb_prompt.txt` - Define perturbation strategies
- `3_validate_prompt.txt` - Set validation criteria
- `4_extract_prompt.txt` - Adjust LaTeX formatting style

### Changing LaTeX Style

Replace or add files in `examples/` to change the output document style. The extraction stage will match the format of your example documents.

## Troubleshooting

### No images found

**Error:** `ERROR: No images found in img/`

**Solution:** Place PNG, JPG, or JPEG files in the `img/` directory.

### Validation failures

**Error:** `No questions passed validation`

**Cause:** Perturbed questions may contain errors or ambiguities.

**Solution:** 
- Review `output/2_perturbed.jsonl` to see what was generated
- Adjust the perturbation prompt to be more conservative
- Check if original questions are well-posed

### LaTeX compilation errors

**Error:** Generated `.tex` file doesn't compile

**Solution:**
- Ensure example files in `examples/` are valid LaTeX
- Check for proper escaping in JSON (double backslashes)
- Review the extraction prompt for formatting rules

### Rate limiting

**Error:** API rate limit exceeded

**Solution:** The script includes 1-second delays between requests. For large batches, consider:
- Processing in smaller batches
- Increasing delays in the code
- Upgrading OpenAI API tier

## Requirements

- Python 3.7+
- OpenAI API key with GPT-5 access
- Internet connection

## Model Information

- **Model**: GPT-5
- **Pricing** (as of 2025):
  - Input: $1.25 per million tokens
  - Output: $10.00 per million tokens

## License

This project is a restructured version adapted for A-Level long-answer question perturbation.

