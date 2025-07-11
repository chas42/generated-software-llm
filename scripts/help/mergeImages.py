import os
from PIL import Image
from collections import defaultdict

# Lista de caminhos de imagem
image_paths = [
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/response_time_analysis_convert-image-bolt_0.1s.png",
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/response_time_analysis_credit-card-bolt_0.1s.png",
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/response_time_analysis_monitor-bolt_0.1s.png",
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/response_time_analysis_uptime_bolt_0.1s.png",
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/used_memory_analysis_convert-image-bolt_0.1s.png",
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/used_memory_analysis_credit-card-bolt_0.1s.png",
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/used_memory_analysis_monitor-bolt_0.1s.png",
    "/home/chas/projects/ufrpe-research/llm-software-aging-research/allGraphs/used_memory_analysis_uptime-bolt_0.1s.png"
]

# Extrai prefixo do nome do arquivo (antes do 3º "_")
def extract_prefix(path):
    filename = os.path.basename(path)
    parts = filename.split("_")
    return "_".join(parts[:2])  # Ex: "buffersMemory_analysis"

# Agrupar por prefixo
groups = defaultdict(list)
for path in image_paths:
    prefix = extract_prefix(path)
    groups[prefix].append(path)

# Pasta de saída
output_dir = "/home/chas/projects/ufrpe-research/allGraphs/merge_2x2"
os.makedirs(output_dir, exist_ok=True)

# Criar colagens
for prefix, imgs in groups.items():
    if len(imgs) < 4:
        continue

    loaded_imgs = [Image.open(p) for p in imgs[:4]]
    img_width, img_height = loaded_imgs[0].size

    # Cria imagem grande 2x2
    combined = Image.new('RGB', (img_width * 2, img_height * 2), (255, 255, 255))
    combined.paste(loaded_imgs[0], (0, 0))
    combined.paste(loaded_imgs[1], (img_width, 0))
    combined.paste(loaded_imgs[2], (0, img_height))
    combined.paste(loaded_imgs[3], (img_width, img_height))

    # Salva a colagem
    output_path = os.path.join(output_dir, f"{prefix}_2x2.jpg")
    combined.save(output_path)
    print(f"Salvo: {output_path}")
