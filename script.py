#!/usr/bin/env python3
"""
A-Level Question Perturbation Pipeline

This script performs a complete pipeline:
1. Transcribe images of A-Level questions to JSON
2. Perturb the questions while maintaining validity
3. Validate the perturbed questions
4. Extract to a compilable LaTeX document
"""

import os
import json
import base64
import time
import sys
import argparse
from pathlib import Path
from openai import OpenAI

# ============================================================================
# CONFIGURATION
# ============================================================================

# Initialize OpenAI API
API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=API_KEY)

# GPT-5 Pricing (as of 2025)
INPUT_TOKEN_COST = 1.25 / 1_000_000  # $1.25 per million tokens
OUTPUT_TOKEN_COST = 10.00 / 1_000_000  # $10.00 per million tokens

# Get script directory
SCRIPT_DIR = Path(__file__).parent

# Directories
IMG_DIR = SCRIPT_DIR / "img"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
EXAMPLES_DIR = SCRIPT_DIR / "examples"
OUTPUT_DIR = SCRIPT_DIR / "output"

# Files
TEMPLATE_FILE = SCRIPT_DIR / "json template.txt"
TRANSCRIBE_PROMPT = PROMPTS_DIR / "1_transcribe_prompt.txt"
PERTURB_PROMPT = PROMPTS_DIR / "2_perturb_prompt.txt"
VALIDATE_PROMPT = PROMPTS_DIR / "3_validate_prompt.txt"
EXTRACT_PROMPT = PROMPTS_DIR / "4_extract_prompt.txt"

# Output files
OUTPUT_DIR.mkdir(exist_ok=True)
TRANSCRIBED_FILE = OUTPUT_DIR / "1_transcribed.jsonl"
PERTURBED_FILE = OUTPUT_DIR / "2_perturbed.jsonl"
VALIDATED_FILE = OUTPUT_DIR / "3_validated.jsonl"
FINAL_TEX_FILE = OUTPUT_DIR / "4_final_document.tex"

# Global flag for non-interactive mode
NON_INTERACTIVE = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def encode_image(image_path):
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def load_text_file(file_path):
    """Load text content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_example_tex_files(examples_dir):
    """Load all .tex files from examples directory."""
    tex_files = sorted(examples_dir.glob("*.tex"))
    
    if not tex_files:
        print(f"Warning: No .tex example files found in {examples_dir}")
        return []
    
    examples = []
    for tex_file in tex_files:
        content = load_text_file(tex_file)
        examples.append({
            "filename": tex_file.name,
            "content": content
        })
    
    return examples


def ask_special_prompt(stage_name):
    """Ask user for a special prompt for a given stage."""
    if NON_INTERACTIVE:
        print(f"\n{'='*60}")
        print(f"STAGE: {stage_name}")
        print(f"{'='*60}")
        print(f"[Non-interactive mode: Using default prompt for {stage_name}]")
        return ""
    
    print(f"\n{'='*60}")
    print(f"STAGE: {stage_name}")
    print(f"{'='*60}")
    response = input(f"Enter special prompt for {stage_name} (or press Enter to skip): ").strip()
    return response if response else ""


def print_cost_report(stage_name, input_tokens, output_tokens, elapsed_time):
    """Print cost and time report for an API call."""
    input_cost = input_tokens * INPUT_TOKEN_COST
    output_cost = output_tokens * OUTPUT_TOKEN_COST
    total_cost = input_cost + output_cost
    
    print(f"\n--- {stage_name} Complete ---")
    print(f"  Input tokens:  {input_tokens:,}")
    print(f"  Output tokens: {output_tokens:,}")
    print(f"  Total tokens:  {input_tokens + output_tokens:,}")
    print(f"  Elapsed time:  {elapsed_time:.2f}s")
    print(f"  Input cost:    ${input_cost:.4f}")
    print(f"  Output cost:   ${output_cost:.4f}")
    print(f"  Total cost:    ${total_cost:.4f}")
    print(f"{'='*60}")


# ============================================================================
# STAGE 1: TRANSCRIPTION
# ============================================================================

def transcribe_image(image_path, prompt_text, template_text, special_prompt=""):
    """Transcribe an image to JSON using OpenAI Vision API."""
    start_time = time.time()
    
    # Encode the image
    base64_image = encode_image(image_path)
    
    # Inject special prompt
    if "{special_prompt}" in prompt_text:
        special_prompt_text = special_prompt if special_prompt.strip() else "None (use default rules)"
        prompt_with_special = prompt_text.replace("{special_prompt}", special_prompt_text)
    else:
        special_prompt_text = f"\n\n**SPECIAL INSTRUCTIONS:** {special_prompt}" if special_prompt.strip() else ""
        prompt_with_special = prompt_text + special_prompt_text
    
    # Construct full prompt
    full_prompt = f"{prompt_with_special}\n\nTemplate structure:\n{template_text}"
    
    # Call OpenAI Vision API
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": full_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_completion_tokens=8000,
        response_format={"type": "json_object"},
    )
    
    elapsed_time = time.time() - start_time
    
    # Extract response and usage
    result = response.choices[0].message.content
    input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
    output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
    
    return result, input_tokens, output_tokens, elapsed_time


def run_transcription_stage(special_prompt=""):
    """Run the transcription stage on all images in /img directory."""
    print("\n" + "="*60)
    print("STAGE 1: TRANSCRIPTION")
    print("="*60)
    
    # Load prompts
    prompt_text = load_text_file(TRANSCRIBE_PROMPT)
    template_text = load_text_file(TEMPLATE_FILE)
    
    # Get all images
    image_files = sorted(IMG_DIR.glob("*.png")) + sorted(IMG_DIR.glob("*.jpg")) + sorted(IMG_DIR.glob("*.jpeg"))
    
    if not image_files:
        print(f"ERROR: No images found in {IMG_DIR}")
        return [], 0, 0
    
    print(f"Found {len(image_files)} image(s) to transcribe")
    
    # Clear output file
    if TRANSCRIBED_FILE.exists():
        TRANSCRIBED_FILE.unlink()
    
    transcribed_questions = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    for idx, image_path in enumerate(image_files, 1):
        print(f"\nTranscribing [{idx}/{len(image_files)}]: {image_path.name}")
        
        try:
            result, input_tokens, output_tokens, elapsed_time = transcribe_image(
                image_path, prompt_text, template_text, special_prompt
            )
            
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            # Parse JSON
            question_json = json.loads(result)
            
            # Validate required fields
            if "question" not in question_json:
                print(f"  WARNING: Missing 'question' field, skipping")
                continue
            
            # Save to file
            with open(TRANSCRIBED_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(question_json, ensure_ascii=False) + "\n")
            
            transcribed_questions.append(question_json)
            print(f"  ✓ Transcribed successfully ({elapsed_time:.2f}s)")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            continue
    
    print(f"\n✓ Transcription complete: {len(transcribed_questions)}/{len(image_files)} successful")
    print(f"  Saved to: {TRANSCRIBED_FILE}")
    
    return transcribed_questions, total_input_tokens, total_output_tokens


# ============================================================================
# STAGE 2: PERTURBATION
# ============================================================================

def perturb_question(question, prompt_text, special_prompt=""):
    """Perturb a single question using OpenAI API."""
    start_time = time.time()
    
    # Format question for the prompt
    question_text = json.dumps(question, indent=2, ensure_ascii=False)
    
    # Inject special prompt
    if "{special_prompt}" in prompt_text:
        special_prompt_text = special_prompt if special_prompt.strip() else "None (use default rules)"
        prompt_with_special = prompt_text.replace("{special_prompt}", special_prompt_text)
    else:
        special_prompt_text = f"\n\n**SPECIAL INSTRUCTIONS:** {special_prompt}" if special_prompt.strip() else ""
        prompt_with_special = prompt_text + special_prompt_text
    
    # Construct full prompt
    full_prompt = f"{prompt_with_special}\n\nOriginal question:\n\n{question_text}"
    
    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        max_completion_tokens=15000,
        response_format={"type": "json_object"},
    )
    
    elapsed_time = time.time() - start_time
    
    # Extract response and usage
    result = response.choices[0].message.content
    input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
    output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
    
    return result, input_tokens, output_tokens, elapsed_time


def run_perturbation_stage(transcribed_questions, special_prompt=""):
    """Run the perturbation stage on all transcribed questions."""
    print("\n" + "="*60)
    print("STAGE 2: PERTURBATION")
    print("="*60)
    
    if not transcribed_questions:
        print("ERROR: No transcribed questions to perturb")
        return [], 0, 0
    
    # Load prompt
    prompt_text = load_text_file(PERTURB_PROMPT)
    
    print(f"Perturbing {len(transcribed_questions)} question(s)")
    
    # Clear output file
    if PERTURBED_FILE.exists():
        PERTURBED_FILE.unlink()
    
    perturbed_questions = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    for idx, question in enumerate(transcribed_questions, 1):
        print(f"\nPerturbing question [{idx}/{len(transcribed_questions)}]")
        
        # Add small delay to avoid rate limiting
        if idx > 1:
            time.sleep(1)
        
        try:
            result, input_tokens, output_tokens, elapsed_time = perturb_question(
                question, prompt_text, special_prompt
            )
            
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            # Parse JSON
            perturbed_json = json.loads(result)
            
            # Validate required fields
            if "question" not in perturbed_json:
                print(f"  WARNING: Missing 'question' field, skipping")
                continue
            
            # Save to file
            with open(PERTURBED_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(perturbed_json, ensure_ascii=False) + "\n")
            
            perturbed_questions.append(perturbed_json)
            print(f"  ✓ Perturbed successfully ({elapsed_time:.2f}s)")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            continue
    
    print(f"\n✓ Perturbation complete: {len(perturbed_questions)}/{len(transcribed_questions)} successful")
    print(f"  Saved to: {PERTURBED_FILE}")
    
    return perturbed_questions, total_input_tokens, total_output_tokens


# ============================================================================
# STAGE 3: VALIDATION
# ============================================================================

def validate_question(question, prompt_text):
    """Validate a single perturbed question using OpenAI API."""
    start_time = time.time()
    
    # Format question for the prompt
    question_text = json.dumps(question, indent=2, ensure_ascii=False)
    
    # Construct full prompt
    full_prompt = f"{prompt_text}\n\nQuestion to validate:\n\n{question_text}"
    
    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        max_completion_tokens=10000,
        response_format={"type": "json_object"},
    )
    
    elapsed_time = time.time() - start_time
    
    # Extract response and usage
    result = response.choices[0].message.content
    input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
    output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
    
    return result, input_tokens, output_tokens, elapsed_time


def run_validation_stage(perturbed_questions):
    """Run the validation stage on all perturbed questions."""
    print("\n" + "="*60)
    print("STAGE 3: VALIDATION")
    print("="*60)
    
    if not perturbed_questions:
        print("ERROR: No perturbed questions to validate")
        return [], 0, 0
    
    # Load prompt
    prompt_text = load_text_file(VALIDATE_PROMPT)
    
    print(f"Validating {len(perturbed_questions)} question(s)")
    
    # Clear output file
    if VALIDATED_FILE.exists():
        VALIDATED_FILE.unlink()
    
    validated_questions = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    for idx, question in enumerate(perturbed_questions, 1):
        print(f"\nValidating question [{idx}/{len(perturbed_questions)}]")
        
        # Add small delay to avoid rate limiting
        if idx > 1:
            time.sleep(1)
        
        try:
            result, input_tokens, output_tokens, elapsed_time = validate_question(
                question, prompt_text
            )
            
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            # Parse JSON
            validation_result = json.loads(result)
            
            well_posed = validation_result.get("well_posed", False)
            reasoning = validation_result.get("reasoning", "No reasoning provided")
            
            print(f"  Well-posed: {well_posed}")
            print(f"  Time: {elapsed_time:.2f}s")
            
            if not well_posed:
                print(f"  Reason: {reasoning[:1000]}...")
                print(f"  ✗ Question REJECTED")
            else:
                # Save to file
                with open(VALIDATED_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(question, ensure_ascii=False) + "\n")
                
                validated_questions.append(question)
                print(f"  ✓ Question VALIDATED")
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            continue
    
    print(f"\n✓ Validation complete: {len(validated_questions)}/{len(perturbed_questions)} passed")
    print(f"  Saved to: {VALIDATED_FILE}")
    
    return validated_questions, total_input_tokens, total_output_tokens


# ============================================================================
# STAGE 4: EXTRACTION TO LaTeX
# ============================================================================

def extract_to_latex(questions, prompt_text, examples, special_prompt=""):
    """Extract validated questions to LaTeX document using OpenAI API."""
    start_time = time.time()
    
    # Format examples
    examples_text = "\n\n".join([
        f"Example from {ex['filename']}:\n```latex\n{ex['content']}\n```"
        for ex in examples
    ])
    
    # Format questions
    questions_text = json.dumps(questions, indent=2, ensure_ascii=False)
    
    # Inject special prompt
    if "{special_prompt}" in prompt_text:
        special_prompt_text = special_prompt if special_prompt.strip() else "None (use default rules)"
        prompt_with_special = prompt_text.replace("{special_prompt}", special_prompt_text)
    else:
        special_prompt_text = f"\n\n**SPECIAL INSTRUCTIONS:** {special_prompt}" if special_prompt.strip() else ""
        prompt_with_special = prompt_text + special_prompt_text
    
    # Construct full prompt
    full_prompt = f"""{prompt_with_special}

**EXAMPLE LaTeX DOCUMENTS (COMPLETE WITH PREAMBLES):**

{examples_text}

**QUESTIONS TO CONVERT (JSON format):**

```json
{questions_text}
```

IMPORTANT: Generate a COMPLETE, COMPILABLE LaTeX document (including \\documentclass, all \\usepackage statements, preamble configurations, \\begin{{document}}, the formatted questions, and \\end{{document}}).

The output must be ready to save as a .tex file and compile immediately without errors.

Copy ALL package imports, custom commands, and configurations from the example documents.
"""
    
    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        max_completion_tokens=25000,
        response_format={"type": "json_object"},
    )
    
    elapsed_time = time.time() - start_time
    
    # Extract response and usage
    result = response.choices[0].message.content
    input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
    output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
    
    return result, input_tokens, output_tokens, elapsed_time


def run_extraction_stage(validated_questions, special_prompt=""):
    """Run the extraction stage to create final LaTeX document."""
    print("\n" + "="*60)
    print("STAGE 4: EXTRACTION TO LaTeX")
    print("="*60)
    
    if not validated_questions:
        print("ERROR: No validated questions to extract")
        return 0, 0
    
    # Load prompt and examples
    prompt_text = load_text_file(EXTRACT_PROMPT)
    
    if not EXAMPLES_DIR.exists():
        print(f"ERROR: Examples directory not found: {EXAMPLES_DIR}")
        print("Please create an 'examples' directory with .tex example files")
        return 0, 0
    
    examples = load_example_tex_files(EXAMPLES_DIR)
    
    if not examples:
        print(f"ERROR: No .tex example files found in {EXAMPLES_DIR}")
        return 0, 0
    
    print(f"Using {len(examples)} example file(s) as style reference")
    print(f"Converting {len(validated_questions)} question(s) to LaTeX")
    
    try:
        result, input_tokens, output_tokens, elapsed_time = extract_to_latex(
            validated_questions, prompt_text, examples, special_prompt
        )
        
        # Parse JSON response
        response_obj = json.loads(result)
        
        if "latex_document" not in response_obj:
            print("ERROR: Response does not contain 'latex_document' field")
            return input_tokens, output_tokens
        
        latex_output = response_obj["latex_document"]
        
        # Write to file
        with open(FINAL_TEX_FILE, "w", encoding="utf-8") as f:
            f.write(latex_output)
        
        print(f"\n✓ LaTeX document created successfully")
        print(f"  Saved to: {FINAL_TEX_FILE}")
        print(f"  Time: {elapsed_time:.2f}s")
        
        # Print preview
        print("\n--- Preview (first 500 characters) ---")
        print(latex_output[:500])
        if len(latex_output) > 500:
            print("...")
        
        return input_tokens, output_tokens
        
    except Exception as e:
        print(f"ERROR during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Main pipeline function."""
    print("\n" + "="*70)
    print(" "*15 + "A-LEVEL QUESTION PERTURBATION PIPELINE")
    print("="*70)
    
    # Overall timing
    pipeline_start_time = time.time()
    
    # Track total costs
    stage_costs = {}
    
    # Ask about clearing img directory upfront
    clear_img = None
    if IMG_DIR.exists() and any(IMG_DIR.glob("*")):
        if NON_INTERACTIVE:
            clear_img = False
            print("\n[Non-interactive mode: Will NOT clear /img directory after transcription]")
        else:
            print("\n")
            clear_response = input("Clear /img directory after transcription? (y/n): ").strip().lower()
            clear_img = (clear_response == 'y')
    
    # ========================================================================
    # STAGE 1: TRANSCRIPTION
    # ========================================================================
    
    special_prompt_1 = ask_special_prompt("TRANSCRIPTION")
    
    transcribed_questions, input_tokens_1, output_tokens_1 = run_transcription_stage(special_prompt_1)
    
    print_cost_report("TRANSCRIPTION", input_tokens_1, output_tokens_1, time.time() - pipeline_start_time)
    stage_costs["Transcription"] = (input_tokens_1, output_tokens_1)
    
    if not transcribed_questions:
        print("\n✗ Pipeline aborted: No questions transcribed")
        return
    
    # Clear img directory if requested
    if clear_img:
        try:
            deleted_count = 0
            for file_path in IMG_DIR.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
            print(f"\n✓ Cleared {deleted_count} file(s) from {IMG_DIR}")
        except Exception as e:
            print(f"\n✗ Error clearing directory: {e}")
    
    # ========================================================================
    # STAGE 2: PERTURBATION
    # ========================================================================
    
    special_prompt_2 = ask_special_prompt("PERTURBATION")
    
    stage_2_start = time.time()
    perturbed_questions, input_tokens_2, output_tokens_2 = run_perturbation_stage(transcribed_questions, special_prompt_2)
    
    print_cost_report("PERTURBATION", input_tokens_2, output_tokens_2, time.time() - stage_2_start)
    stage_costs["Perturbation"] = (input_tokens_2, output_tokens_2)
    
    if not perturbed_questions:
        print("\n✗ Pipeline aborted: No questions perturbed")
        return
    
    # ========================================================================
    # STAGE 3: VALIDATION
    # ========================================================================
    
    print("\n[No special prompt for validation stage - using default validation criteria]")
    
    stage_3_start = time.time()
    validated_questions, input_tokens_3, output_tokens_3 = run_validation_stage(perturbed_questions)
    
    print_cost_report("VALIDATION", input_tokens_3, output_tokens_3, time.time() - stage_3_start)
    stage_costs["Validation"] = (input_tokens_3, output_tokens_3)
    
    if not validated_questions:
        print("\n✗ Pipeline aborted: No questions passed validation")
        return
    
    # ========================================================================
    # STAGE 4: EXTRACTION TO LaTeX
    # ========================================================================
    
    special_prompt_4 = ask_special_prompt("LaTeX EXTRACTION")
    
    stage_4_start = time.time()
    input_tokens_4, output_tokens_4 = run_extraction_stage(validated_questions, special_prompt_4)
    
    print_cost_report("LaTeX EXTRACTION", input_tokens_4, output_tokens_4, time.time() - stage_4_start)
    stage_costs["Extraction"] = (input_tokens_4, output_tokens_4)
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    pipeline_elapsed_time = time.time() - pipeline_start_time
    
    total_input_tokens = sum(tokens[0] for tokens in stage_costs.values())
    total_output_tokens = sum(tokens[1] for tokens in stage_costs.values())
    total_tokens = total_input_tokens + total_output_tokens
    
    input_cost = total_input_tokens * INPUT_TOKEN_COST
    output_cost = total_output_tokens * OUTPUT_TOKEN_COST
    total_cost = input_cost + output_cost
    
    print("\n" + "="*70)
    print(" "*25 + "FINAL SUMMARY")
    print("="*70)
    
    print("\nPipeline Results:")
    print(f"  Images processed:      {len(transcribed_questions)}")
    print(f"  Questions perturbed:   {len(perturbed_questions)}")
    print(f"  Questions validated:   {len(validated_questions)}")
    print(f"  Final LaTeX document:  {FINAL_TEX_FILE}")
    
    print("\n" + "-"*70)
    print("Token Usage by Stage:")
    print("-"*70)
    for stage_name, (input_tok, output_tok) in stage_costs.items():
        stage_cost = (input_tok * INPUT_TOKEN_COST) + (output_tok * OUTPUT_TOKEN_COST)
        print(f"  {stage_name:20s} | In: {input_tok:8,} | Out: {output_tok:8,} | Cost: ${stage_cost:7.4f}")
    
    print("\n" + "-"*70)
    print("Total Costs:")
    print("-"*70)
    print(f"  Total input tokens:   {total_input_tokens:,}")
    print(f"  Total output tokens:  {total_output_tokens:,}")
    print(f"  Total tokens:         {total_tokens:,}")
    print(f"  Total elapsed time:   {pipeline_elapsed_time:.2f}s")
    print(f"  Input cost:           ${input_cost:.4f}")
    print(f"  Output cost:          ${output_cost:.4f}")
    print(f"  TOTAL COST:           ${total_cost:.4f}")
    print("="*70)
    
    print("\n✓ Pipeline complete!")
    print(f"\nOutput files:")
    print(f"  1. {TRANSCRIBED_FILE}")
    print(f"  2. {PERTURBED_FILE}")
    print(f"  3. {VALIDATED_FILE}")
    print(f"  4. {FINAL_TEX_FILE} (READY TO COMPILE)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A-Level Question Perturbation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py                    # Run interactively (default)
  python script.py --force            # Run without prompts (all defaults)
  python script.py --default          # Same as --force
        """
    )
    parser.add_argument(
        '--force', '--default',
        action='store_true',
        dest='non_interactive',
        help='Run in non-interactive mode: skip all prompts (empty) and answer "n" to all y/n questions'
    )
    
    args = parser.parse_args()
    NON_INTERACTIVE = args.non_interactive
    
    if NON_INTERACTIVE:
        print("\n" + "="*70)
        print("RUNNING IN NON-INTERACTIVE MODE")
        print("  - All special prompts will be empty (using defaults)")
        print("  - All y/n questions will default to 'n'")
        print("="*70)
    
    main()

