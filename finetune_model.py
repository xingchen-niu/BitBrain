import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForLanguageModeling

# 加载数据
with open('finetune_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 准备数据集
class QADataset(torch.utils.data.Dataset):
    def __init__(self, data, tokenizer):
        self.data = data
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        question = item['question']
        answer = item['answer']
        prompt = f"问题：{question}\n回答：{answer}<sep>"
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
        inputs['labels'] = inputs.input_ids.clone()
        return inputs

# 加载预训练的分词器和模型
model_path = 'IEITYuan/Yuan2-2B-Mars-hf'
tokenizer = AutoTokenizer.from_pretrained(model_path, add_eos_token=False, add_bos_token=False, eos_token='<eod>', legacy=False)
tokenizer.add_tokens(['<sep>', '<pad>', '<mask>', '<predict>', '<FIM_SUFFIX>', '<FIM_PREFIX>', '<FIM_MIDDLE>','<commit_before>','<commit_msg>','<commit_after>','<jupyter_start>','<jupyter_text>','<jupyter_code>','<jupyter_output>','<empty_output>'], special_tokens=True)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.bfloat16, trust_remote_code=True)

# 创建数据集和数据加载器
dataset = QADataset(data, tokenizer)
data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

# 设置训练参数
training_args = TrainingArguments(
    output_dir='./finetuned_model',
    overwrite_output_dir=True,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=10_000,
    save_total_limit=2,
    prediction_loss_only=True,
    fp16=True if torch.cuda.is_available() else False,
)

# 创建Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=dataset,
)

# 开始训练
trainer.train()

# 保存微调后的模型
trainer.save_model('./finetuned_model')
tokenizer.save_pretrained('./finetuned_model')
