from transformers import AutoModel
import torch
m = AutoModel.from_pretrained('BAAI/bge-m3', torch_dtype=torch.bfloat16)
# Print all linear layer names
for name, mod in m.named_modules():
    if hasattr(mod, 'weight') and 'Linear' in type(mod).__name__:
        print(name)
