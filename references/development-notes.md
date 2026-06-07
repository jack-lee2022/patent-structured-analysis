# Patent Structured Analysis — Development Notes

These notes capture the technical challenges encountered when extracting the 4-step structured analysis logic from the `patent-agent` backend and packaging it as a standalone skill. Keep this for future maintenance, refactoring, or porting work.

---

## 1. Patent Text Format Gotchas

### "What is claimed is:" preamble
The `claims` field from Google Patents / patent-agent database always starts with:
```
What is claimed is:
1. A negative-pressure oral apparatus for alleviating snoring...
```

**Problem**: If you naively treat the entire text as the first claim, the first 1500 chars are just "What is claimed is:" followed by the preamble — giving empty `technical_solution` and `elements`.

**Fix**: Skip the preamble explicitly when splitting by claim numbers:
```python
for line in re.split(r"\n\s*\d+\.", claims_text):
    stripped = line.strip()
    if len(stripped) > 50 and not stripped.lower().startswith("what is claimed is"):
        first_claim = stripped[:1500]
        break
```

### Section extraction via regex
Patent text is NOT clean markdown. The `claims` section is preceded by the literal string `Claims:\n` (not `Claims:`) and the body text contains the word "Claims" in the middle of sentences.

**Problem**: A greedy `r"(?i)claims\s*[:\n]+(.*?)(?=\n\s*...\s*[:\n]|$)"` regex will match `Claims:` as the header, but the first match inside the body text is often the word `claims` in a sentence, not the section header.

**Fix**: Use a dedicated claims pattern that looks for the exact header `Claims:\n` or `What is claimed is:`:
```python
m = re.search(r"(?i)(?:what is claimed is:|claims\s*[:\n]+)\s*(.*?)(?=\n\s*(?:description|abstract|summary|background|detailed description|fig|figure)\s*[:\n]|$)", text, re.DOTALL)
```

---

## 2. Extracting "comprising" elements

### The "wherein" trap
After `comprising:`, the claim lists elements separated by semicolons and newlines. Each element often has a trailing `wherein` clause:
```
comprising:
an oral interface insertable in an oral cavity of the user, wherein the oral interface defines...
a source of negative pressure in fluid communication with...
```

**Problem**: A naive split by `;` or `and` will keep the entire `wherein` clause inside the element name, making the component name too long (80+ characters). This breaks downstream searches (e.g., `find_component_function` will not find the exact string in the description text).

**Fix**: Multi-step cleanup pipeline:
```python
# 1. Split by newlines
lines = raw.split("\n")
for line in lines:
    line = line.strip().strip(";")
    # 2. Stop at standalone "wherein" clauses (not part of the element list)
    if line.lower().startswith("wherein") and len(elements) > 0:
        break
    # 3. Strip trailing "wherein", "configured to", "for" clauses
    clean = re.split(r"[,;]?\s*wherein", line, flags=re.IGNORECASE)[0].strip()
    clean = re.split(r"[,;]?\s*configured to", clean, flags=re.IGNORECASE)[0].strip()
    clean = re.split(r"[,;]?\s*for", clean, flags=re.IGNORECASE)[0].strip()
    # 4. Remove leading article
    clean = re.sub(r"^(an?|the)\s+", "", clean, flags=re.IGNORECASE)
    if clean and len(clean) > 5:
        elements.append(clean)
```

### Result
| Before | After |
|--------|-------|
| `an oral interface insertable in an oral cavity of the user, wherein the oral interface defines a fluid passage configured to be in fluid communication with...` | `oral interface insertable in an oral cavity of the user` |

---

## 3. Key-Term Extraction (Legal-Word Filtering)

Patent claims are full of legal boilerplate that look like technical terms but are not:
- `What`, `Wherein`, `Comprising`, `Consisting`, `Having`, `Being`, `Said`, `Each`, `All`
- `First`, `Second`, `Third`, `Fourth`, `Fifth`, `At`, `Least`, `Most`

**Problem**: A naive regex `\b[A-Z][a-z]+\b` will extract `What`, `The`, `A`, etc. as "key terms".

**Fix**: Build a dedicated `stop` set for patent claim language:
```python
stop = {"What", "The", "A", "An", "This", "That", "These", "Those", "Claim", "Claims",
        "Wherein", "Comprising", "Consisting", "Having", "Being", "Said", "Each", "All",
        "One", "Two", "First", "Second", "Third", "Fourth", "Fifth", "At", "Least", "Most"}
```

Also collect hyphenated technical terms (`negative-pressure`, `liquid-collecting`) with a separate `re.findall(r"\b[a-z]+-[a-z]+(?:-[a-z]+)*\b", ...)` pattern.

---

## 4. Searching the Description (Core-Noun Phrase Matching)

**Problem**: A component name like `oral interface insertable in an oral cavity of the user` is too long and specific to appear verbatim in the Description text. The Description usually refers to it simply as `oral interface` or `the oral interface`.

**Fix**: When searching for a component in the Description, extract the **core noun phrase** (first 3–4 words) and use that as the search key:
```python
core = re.split(r'[,;]?\s*wherein', component, flags=re.IGNORECASE)[0].strip()
core = re.split(r'[,;]?\s*configured to', core, flags=re.IGNORECASE)[0].strip()
core = re.split(r'[,;]?\s*for', core, flags=re.IGNORECASE)[0].strip()
core = re.sub(r'^(an?|the)\s+', '', core, flags=re.IGNORECASE)
search_key = ' '.join(core.split()[:4])
```

This must be applied to:
- `_find_component_function()`
- `_find_figure_reference()`

---

## 5. `"is_optional"` semantics in patent claims

The original patent-agent code had a bug where `is_optional` was set to `True` for all `comprising` claims. This is incorrect.

**Correct semantics**:
- `comprising` = the list of elements is **non-exhaustive** (you can add more), but every listed element is **mandatory**. Therefore `is_optional = False`.
- `consisting of` = the list is **exhaustive** and every element is mandatory. `is_optional = False`.
- `optionally` or `may` in the claim text = explicitly allows omission. `is_optional = True`.

---

## 6. GitHub Push via SSH (Host alias)

The Oracle VM has an SSH key configured for `github.com-kd` (not `github.com`). When pushing, the remote URL must match the SSH `config` alias:

```
Host github.com-kd
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_kd
    IdentitiesOnly yes
```

**Correct remote URL**:
```bash
git remote add origin git@github.com-kd:jack-lee2022/patent-structured-analysis.git
```

Using `git@github.com:...` will fail because SSH will try to use the wrong key (`odoo_installer` or the default key) instead of `id_ed25519_kd`.

---

## 7. Skill Validation

Hermes `skill-creator` ships with a `quick_validate.py` script that checks the skill directory structure. Always run it before committing:

```bash
cd ~/.hermes/skills/skill-creator
python3 scripts/quick_validate.py /path/to/your/skill
```

---

## Checklist for Future Patent-Text Extraction Tasks

- [ ] Does the claims text start with `What is claimed is:`? If yes, strip the preamble.
- [ ] Is the `claims` section header correctly identified (`Claims:\n`, not `claims` in a sentence)?
- [ ] Are `wherein` and `configured to` clauses stripped from element names?
- [ ] Are articles (`a`, `an`, `the`) removed from element names?
- [ ] Is the `stop` word list updated for legal boilerplate?
- [ ] Are hyphenated technical terms captured separately?
- [ ] Is the **core noun phrase** (first 3–4 words) used when searching the Description?
- [ ] Is `is_optional` correctly set based on `comprising` vs. `consisting of` vs. `optionally`?
- [ ] Are figure references normalized (`FIG. 1`, `FIG. 1A`, `Figure 2`, etc.)?
