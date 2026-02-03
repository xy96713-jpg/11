import os
import re
from pathlib import Path

# Base configuration
SKILL_ROOT = Path(r"d:\anti\技能库")
ROOT_README = Path(r"d:\anti\README.md")
SUB_README = Path(r"d:\anti\技能库\README.md")

# Regex patterns
YAML_NAME_PATTERN = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
YAML_TRIGGERS_PATTERN = re.compile(r"triggers:\s*\[(.*?)\]", re.MULTILINE | re.DOTALL) # Simple list
MARKDOWN_TITLE_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
TRIGGER_SECTION_PATTERN = re.compile(r"触发指令|Triggers|Activation Command", re.IGNORECASE)

def extract_skill_info(dir_path):
    skill_id = dir_path.name.split('_')[0]
    folder_name = dir_path.name
    
    # Defaults
    name = folder_name
    desc = "No description available."
    triggers = []
    
    skill_md = dir_path / "SKILL.md"
    readme_md = dir_path / "README.md"
    
    content = ""
    
    # Priority 1: SKILL.md (YAML frontmatter is best)
    if skill_md.exists():
        try:
            content = skill_md.read_text(encoding='utf-8')
            # Try parsing YAML name
            match = YAML_NAME_PATTERN.search(content)
            if match:
                name = match.group(1).strip()
            
            # Try parsing legacy title if YAML fails or complementary
            title_match = MARKDOWN_TITLE_PATTERN.search(content)
            if title_match:
                name = title_match.group(1).strip()

        except Exception as e:
            print(f"Error reading {skill_md}: {e}")

    # Priority 2: README.md (Fallback or enrichment)
    elif readme_md.exists():
        try:
            content = readme_md.read_text(encoding='utf-8')
            title_match = MARKDOWN_TITLE_PATTERN.search(content)
            if title_match:
                name = title_match.group(1).strip()
                # Remove emojis for cleaner ID matching if needed, but keep for display
        except Exception as e:
            print(f"Error reading {readme_md}: {e}")

    # Heuristic for Triggers (Simple extraction)
    # We look for quoted strings usually associated with triggers
    if 'triggers:' in content or '触发指令' in content:
        # Simple extraction of quoted strings nearby
        lines = content.split('\n')
        capture = False
        for line in lines:
            if TRIGGER_SECTION_PATTERN.search(line):
                capture = True
                continue
            if capture:
                if line.strip().startswith('#') or line.strip() == '---':
                    capture = False
                    break
                # Extract quoted strings like "可以帮我..."
                found = re.findall(r'"([^"]+)"', line)
                triggers.extend(found)
                # Also capture list items - "keyword"
                if line.strip().startswith('- '):
                     triggers.append(line.strip().replace('- ', '').replace('`', ''))

    # Clean up name (remove emojis if it's just the ID/Folder, better to keep extracted title)
    # If name is still the folder name, try to beautify it
    if name == folder_name:
        parts = folder_name.split('_')
        if len(parts) > 1:
            name = parts[1] # Use the text part

    return {
        "id": skill_id,
        "name": name,
        "folder": folder_name,
        "triggers": triggers[:3] # Limit to 3 triggers
    }

def generate_table(skills):
    header = "| ID | 技能名称 | 📂 目录名 | 🔴 激活指令 (Triggers) |\n| :--- | :--- | :--- | :--- |\n"
    rows = []
    for s in skills:
        trigger_str = "<br>".join([f'"{t}"' for t in s['triggers']]) if s['triggers'] else "(自动激活/无需指令)"
        # Clean folder link
        link = f"`{s['folder']}`"
        
        # Formatted Name
        # If the extracted name has an emoji, keep it. 
        # If it looks like "05_Visual", map it to "Visual"
        
        row = f"| **{s['id']}** | **{s['name']}** | {link} | {trigger_str} |"
        rows.append(row)
    return header + "\n".join(rows)

def update_readme(target_file, table_content):
    if not target_file.exists():
        print(f"Target {target_file} not found!")
        return

    content = target_file.read_text(encoding='utf-8')
    
    # We look for the table block. 
    # Assumes the table starts after | ID | ... and ends before the next '---' or header
    
    # A safer way relies on replacing the specific section if we use markers.
    # But since we don't have markers, we'll look for the header line and replace until the next empty line or specific end marker.
    
    lines = content.split('\n')
    new_lines = []
    in_table = False
    table_inserted = False

    for line in lines:
        if "| ID |" in line:
            in_table = True
            continue
        
        if in_table:
            # Detect end of table (empty line or '---' or '##')
            if not line.strip() or line.startswith('---') or line.startswith('##'):
                in_table = False
                new_lines.append(table_content)
                new_lines.append("") # Ensure spacing
                new_lines.append(line)
                table_inserted = True
            continue
        
        if not in_table:
            new_lines.append(line)

    if not table_inserted:
        # If we didn't find the table to replace, maybe append it or warn?
        # Let's verify if we missed it.
        # Fallback: Replace the whole file content is too risky.
        # Let's assume the user has a "Skill Arsenal" section.
        print("Warning: Could not find existing table to replace. Please ensure the header '| ID | 技能名称...' exists.")
        return

    target_file.write_text("\n".join(new_lines), encoding='utf-8')
    print(f"Updated {target_file}")

def main():
    print(" scanning skills...")
    dirs = sorted([d for d in SKILL_ROOT.iterdir() if d.is_dir()])
    skills = []
    
    for d in dirs:
        if not d.name[0].isdigit(): continue # Skip non-numbered folders like 'assets'
        info = extract_skill_info(d)
        skills.append(info)
    
    print(f"Found {len(skills)} skills.")
    table = generate_table(skills)
    
    print("Updating Root README...")
    update_readme(ROOT_README, table)
    
    print("Updating Skill Hub README...")
    update_readme(SUB_README, table)

if __name__ == "__main__":
    main()
