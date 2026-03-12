# --- COPY THIS BLOCK INTO YOUR GOOGLE COLAB NOTEBOOK ---
# --- (Section: Data Preparation) ---

from unsloth import get_chat_template
from datasets import load_dataset

print("[DEBUG] Initializing chat template and loading dataset...")

# 1. Configure the tokenizer for your ShareGPT format (human/gpt)
# Qwen 2.5 natively uses ChatML
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "chatml",
    mapping = {
        "role" : "from", 
        "content" : "value", 
        "user" : "human", 
        "assistant" : "gpt"
    },
)

# 2. Load your local scrubbed dataset
# Ensure you have uploaded 'sharegpt_training_data.jsonl' to the Colab sidebar
dataset = load_dataset("json", data_files="sharegpt_training_data.jsonl", split="train")

# 3. Define formatting function with the vital EOS_TOKEN
def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = [
        tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) 
        + tokenizer.eos_token 
        for convo in convos
    ]
    return { "text" : texts }

# 4. Map the formatting and REMOVE original columns (required for SFTTrainer)
dataset = dataset.map(
    formatting_prompts_func, 
    batched = True, 
    remove_columns = dataset.column_names
)

# --- DEBUG: Verify the first processed sample ---
print(f"[DEBUG] Dataset prepared. Total samples: {len(dataset)}")
print("[DEBUG] Sample of formatted text:")
print(dataset[0]["text"][:500] + "...")
