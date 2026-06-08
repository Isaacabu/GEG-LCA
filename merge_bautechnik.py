#!/usr/bin/env python3
import os

# Read both files
index_path = 'dashboard/templates/dashboard/index.html'
bautechnik_path = 'dashboard/templates/dashboard/bautechnik_tab.html'

with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

with open(bautechnik_path, 'r', encoding='utf-8') as f:
    bautechnik_content = f.read()

# Find the insertion point (before last </div>)
# Find the last </div> which closes the page
last_div_index = index_content.rfind('</div>')

if last_div_index != -1:
    # Insert bautechnik content before the last </div>
    new_content = index_content[:last_div_index] + '\n\n' + bautechnik_content + '\n\n' + index_content[last_div_index:]
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Bautechnik-Tab erfolgreich in index.html eingefügt!")
else:
    print("✗ Konnte insertion point nicht finden")
