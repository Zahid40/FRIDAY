import os
import logging

def build_system_prompt() -> str:
    """
    Reads identity, instructions, skills, and memory files,
    compiling them into a single, cohesive system prompt for Friday.
    """
    # Base directory of the loader file is /friday/character
    # The friday root directory is one level up
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    prompt_parts = []
    
    # 1. Identity
    identity_path = os.path.join(base_dir, "character", "identity.md")
    if os.path.exists(identity_path):
        try:
            with open(identity_path, "r", encoding="utf-8") as f:
                prompt_parts.append(f.read().strip())
        except Exception as e:
            logging.error(f"Error loading identity: {e}")
            
    # 2. Instructions
    instructions_path = os.path.join(base_dir, "character", "instructions.md")
    if os.path.exists(instructions_path):
        try:
            with open(instructions_path, "r", encoding="utf-8") as f:
                prompt_parts.append(f.read().strip())
        except Exception as e:
            logging.error(f"Error loading instructions: {e}")
            
    # 3. Skills
    skills_dir = os.path.join(base_dir, "skills")
    if os.path.exists(skills_dir):
        prompt_parts.append("# SKILLS & SPECIALIZED KNOWLEDGE")
        for filename in sorted(os.listdir(skills_dir)):
            if filename.endswith(".md"):
                file_path = os.path.join(skills_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        section_title = filename[:-3].replace("_", " ").upper()
                        prompt_parts.append(f"## {section_title}\n{f.read().strip()}")
                except Exception as e:
                    logging.error(f"Error loading skill file {filename}: {e}")
                    
    # 4. Memory
    memory_dir = os.path.join(base_dir, "memory")
    if os.path.exists(memory_dir):
        prompt_parts.append("# USER CONTEXT & MEMORY")
        for filename in sorted(os.listdir(memory_dir)):
            if filename.endswith(".md"):
                file_path = os.path.join(memory_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        section_title = filename[:-3].replace("_", " ").upper()
                        prompt_parts.append(f"## {section_title}\n{f.read().strip()}")
                except Exception as e:
                    logging.error(f"Error loading memory file {filename}: {e}")
                    
    return "\n\n".join(prompt_parts)
