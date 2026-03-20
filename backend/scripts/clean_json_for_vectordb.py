import json
import re
import os
import glob

def clean_json_for_vectordb(input_filepath, output_filepath):
    print(f"Processing: {input_filepath}")
    with open(input_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    vector_docs = []
    act_title = data.get('title', '')
    act_number = data.get('act_number', '')

    for chapter in data.get('chapters', []):
        chap_num = chapter.get('chapter_number', '')
        chap_title = chapter.get('title', '')
        
        for section in chapter.get('sections', []):
            text = section.get('text', '').strip()
            if not text:
                continue
                
            # Basic attempt to extract section number
            sec_num = ''
            match = re.match(r'^(\d+[A-Z]*)\.', text)
            if match:
                sec_num = match.group(1)
                
            vector_docs.append({
                'act_title': act_title,
                'act_number': act_number,
                'chapter_number': chap_num,
                'chapter_title': chap_title,
                'section_number': sec_num,
                'text': text
            })

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_filepath) or '.', exist_ok=True)
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(vector_docs, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(vector_docs)} chunks to: {output_filepath}")

if __name__ == "__main__":
    # Example usage: process the Indian Contract Act file
    input_file = 'data/json/indian_contract_act_1872.json'
    output_file = 'data/json/indian_contract_act_1872_cleaned.json'
    
    if os.path.exists(input_file):
        clean_json_for_vectordb(input_file, output_file)
    else:
        print(f"Could not find {input_file}. Run this script from the workspace root.")
