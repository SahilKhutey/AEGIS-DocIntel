import zipfile
import xml.etree.ElementTree as ET
import os

path = r'c:\Users\ASUS\Documents\AEGIS-DocIntel\Aegis Doc\AEGIS-DocIntel_Master_Task_List.docx'
if os.path.exists(path):
    with zipfile.ZipFile(path) as z:
        xml_content = z.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        rows = tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
        print(f"Total table rows found: {len(rows)}\n")
        for r in rows:
            cells = r.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc')
            cell_texts = [''.join([n.text for n in c.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if n.text]).strip() for c in cells]
            if len(cell_texts) >= 3 and cell_texts[0] and cell_texts[0] != 'ID':
                print(" | ".join(cell_texts))
