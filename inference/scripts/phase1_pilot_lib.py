import os, re
from dataclasses import dataclass
from typing import Any
import torch
from transformers import TrainerCallback


# FIX 1 — LAST \boxed{} from Response section only, brace-depth parser
def extract_boxed(md_text):
    """Extract LAST \\boxed{...} content from the '## Reasoning + Response' section only.
    Returns content (handles nested braces) or None if section/box absent or unclosed."""
    HEADER = '## Reasoning + Response'
    idx = md_text.find(HEADER)
    if idx == -1:
        return None
    response = md_text[idx + len(HEADER):]
    marker = '\\boxed{'
    start_idx = response.rfind(marker)   # LAST occurrence
    if start_idx == -1:
        return None
    start = start_idx + len(marker)
    depth = 1
    pos = start
    while pos < len(response) and depth > 0:
        c = response[pos]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return response[start:pos]
        pos += 1
    return None  # unclosed


# FIX 2 — LaTeX whitespace normalization; '\\\\' EXCLUDED (matrix rows preserved)
_LATEX_WS_TOKENS = [
    '\\,', '\\:', '\\;', '\\!', '\\ ',           # math spaces + backslash-space
    '~',                                          # non-breaking
    '\\quad', '\\qquad', '\\enspace',
    '\\thinspace', '\\medspace', '\\thickspace',
    '\\negthinspace', '\\negmedspace', '\\negthickspace',
]
def norm_string(x):
    s = str(x)
    for tok in _LATEX_WS_TOKENS:
        s = s.replace(tok, ' ')
    return re.sub(r'\s+', '', s)


# QC chain — order locked: exact -> norm_string -> numeric -> math-verify
def qc_match(sonnet_boxed, gold):
    s, g = str(sonnet_boxed).strip(), str(gold).strip()
    if not s or not g: return False
    if s == g: return True
    if norm_string(s) == norm_string(g): return True
    try:
        if abs(float(s) - float(g)) < 1e-6: return True
    except Exception: pass
    try:
        from math_verify import parse, verify
        from math_verify.parser import ExprExtractionConfig, LatexExtractionConfig
        E = [LatexExtractionConfig(), ExprExtractionConfig()]
        return bool(verify(parse(g, extraction_config=E), parse(s, extraction_config=E)))
    except Exception:
        return False


# Helper: trace existence check (uniform padding)
def has_sonnet_trace(item_id):
    padded = str(item_id).zfill(4)
    return os.path.exists(f'data/search/teachers/sonnet/item_{padded}.md')


# FIX 4 — boundary-based collator (replaces template-search masking; eliminates vacuous-training trap)
@dataclass
class BoundaryAssistantCollator:
    tokenizer: Any
    def __call__(self, features):
        input_ids_list, labels_list = [], []
        for f in features:
            msgs = f['messages']
            assert msgs[-1]['role'] == 'assistant', f'last message must be assistant, got {msgs[-1]["role"]}'
            prompt_text = self.tokenizer.apply_chat_template(msgs[:-1], tokenize=False, add_generation_prompt=True)
            full_text   = self.tokenizer.apply_chat_template(msgs,     tokenize=False, add_generation_prompt=False)
            prompt_ids = self.tokenizer.encode(prompt_text, add_special_tokens=False)
            full_ids   = self.tokenizer.encode(full_text,   add_special_tokens=False)
            assert full_ids[:len(prompt_ids)] == prompt_ids, 'prompt is not prefix of full (chat template drift)'
            labels = [-100]*len(prompt_ids) + full_ids[len(prompt_ids):]
            input_ids_list.append(full_ids); labels_list.append(labels)
        padded = self.tokenizer.pad({'input_ids': input_ids_list}, return_tensors='pt', padding=True)
        max_len = padded['input_ids'].shape[1]
        labels_padded = torch.full((len(labels_list), max_len), -100, dtype=torch.long)
        for i, lab in enumerate(labels_list):
            labels_padded[i, :len(lab)] = torch.tensor(lab)
        padded['labels'] = labels_padded
        if 'attention_mask' not in padded:
            padded['attention_mask'] = (padded['input_ids'] != self.tokenizer.pad_token_id).long()
        return padded


# FIX 5 — preflight (run AFTER dataset build, BEFORE training)
def preflight_supervised_tokens(dataset, tokenizer, n_check=64):
    collator = BoundaryAssistantCollator(tokenizer=tokenizer)
    sample = [dataset[i] for i in range(min(n_check, len(dataset)))]
    batched = collator(sample)
    sup = (batched['labels'] != -100).sum(dim=1)
    bad = (sup == 0).nonzero().tolist()
    assert not bad, f'Preflight FAIL: rows with 0 supervised tokens: {bad}'
    return {'min_supervised': sup.min().item(), 'max_supervised': sup.max().item()}


# FIX 6 — fail-fast on first 10 training steps
class FailFastCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        if state.global_step > 10 or logs is None: return
        loss, gn = logs.get('loss'), logs.get('grad_norm')
        if loss is not None and (loss == 0.0 or not torch.isfinite(torch.tensor(loss))):
            raise RuntimeError(f'FailFast step {state.global_step}: loss={loss}')
        if gn is not None and not torch.isfinite(torch.tensor(gn)):
            raise RuntimeError(f'FailFast step {state.global_step}: grad_norm={gn}')
