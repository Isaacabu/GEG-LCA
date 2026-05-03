#!/usr/bin/env python3
import os

index_path = 'dashboard/templates/dashboard/index.html'
bautechnik_new_path = 'dashboard/templates/dashboard/bautechnik_tab_complete.html'

# Read index.html
with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

# Find and remove old bautechnik section (from <!-- BAUTECHNIK SEKTION to closing </script>)
import re
pattern = r'<!-- BAUTECHNIK SEKTION.*?</script>'
index_content = re.sub(pattern, '', index_content, flags=re.DOTALL)

# Read new bautechnik content
with open(bautechnik_new_path, 'r', encoding='utf-8') as f:
    bautechnik_content = f.read()

# Insert new content before last </div>
last_div_index = index_content.rfind('</div>')
if last_div_index != -1:
    new_content = index_content[:last_div_index] + '\n\n' + bautechnik_content + '\n\n' + index_content[last_div_index:]
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Kompletter Bautechnik-Tab mit allen Formularen eingefügt!")
else:
    print("✗ Konnte insertion point nicht finden")
