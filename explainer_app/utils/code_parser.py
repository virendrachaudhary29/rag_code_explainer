import ast
import uuid

def extract_code_chunks(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    chunks = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            start_line = node.lineno - 1
            end_line = getattr(node, 'end_lineno', None)
            if end_line is None:
                # fallback for Python <3.8, do basic estimate
                end_line = node.body[-1].lineno

            chunk_lines = source.splitlines()[start_line:end_line]
            chunk_text = "\n".join(chunk_lines).strip()
            if chunk_text:
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "content": chunk_text
                })

    return chunks


