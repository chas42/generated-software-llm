import base64
import io
import requests
import imageio
import logging
from pathlib import Path

def test_convert_image_and_revert(port: str, logger: logging.Logger) -> bool:
    _PNG = "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAMAAABHPGVmAAAAIGNIUk0AAHomAACAhAAA+gAAAIDoAAB1MAAA6mAAADqYAAAXcJy6UTwAAAJqUExURdbV1dXU1NnY2NfW1sXFxZqZmZiXl5eXl7e2tp6engkJCQICAgMDAwAAAGxsbNjX1769vX18fHp5eXl4eKinp9DPz8vKyqOionV0dLa1tc3MzFhYWDQ0NK+urqKhoZ6dnWRjY4+OjsfGxjAwMAsLC6empqWkpGFgYFhXV6Sjo6moqNHQ0NnX1yYlJR0dHRsbGyUlJXZ1ddLR0Xt6enNycpKRkcXExLW0tIOCgnFwcIuLi7u6uoKCgoSEhNPT046NjXh4eMTDw52cnHd2dpuamklJSUJCQrq5udrZ2WJhYQwMDAcHBwQEBDMyMquqqoeHhxkZGQoKCignJxAQEC0tLTs7O6+vr0hISAYGBk1MTMbFxTY2NjU1NTIxMTk5OWpqatva2jo6Oq2srGlpacnIyK6trRUVFX9+fjg3Ny4uLrCvr9TT01VUVAEBAVJRUVRUVDc3N2tra8jHx8HAwI+Pj8/OzjMzMw4ODqyrq0dGRqCfn3p6em1tbdrY2KqpqQ0NDbKxsbm5uSgoKM7Nzb28vLy7u5CPjyAgICEgIGppaY2NjW5tbYSDgxgXFy0sLLKysqqqqggICERERAUFBaGgoJGQkLGxsbq6uhYWFiYmJsLCwszLy319fWNjYzo5OUBAQC8vL11dXUZGRkxMTE5OTjIyMmRkZGZmZgUEBL++vmBgYCMiIisrK2VlZRMTE8C/v01NTVNSUoWFhdPS0oB/f3h3d5eWlsrJyUVFRZybm4qKiqGhoXx7e87OzoiHh52dnVxbWxUUFBQUFLi3t5SUlLSzs7m4uBoaGhEREXR0dFJSUk5NTUxLS////9h3XYsAAAABYktHRM1t0KNFAAAAB3RJTUUH6AwTECAm6jAkEAAAAtlJREFUaAVjYBgFoyEwGgKjITAaAqMhMBoCoyEwGgKjITAaAqMhMBoCoyFAcggwMjCRDJgZSbWGhZWNRMDOQaodTJxc3DykAV4+fhJtYRYQFCIRCIswk2gJfeKEREdRXzkoFZGcknA5g5GZCVuyZGQQFUPSwsjMT4mNzOISktgiU0paRhaWkoAOkZPH6hYkd+Bj8ivwKjJhUaCkrMIJs4RZVU1dQ0QTiyoihcCWMDLwA/M+MNgYGZhBDH6g8Rxa2kCuDpDLwCCoq6dvYEh+gIEtYTZSNTYxNQNFjrmFpZW1ja2onb2DIzOzlJOzhIsUs4ArL6+bO5HOxqIMZImHmKeXt4qPrx8zo38At1dgUHCImHaoVxiTQLg3V2BEZJRJdExsXDxlPkkQ4k6UT0r2jk5JTUtLl3XJ4M0EWZKVnZObpyqSX8DhqFToWVSMxYlECgF9UlJaVl6RwGRU6VNVzVtTy59QVw/2SUNjWpMjE1NzCgMzc0srM7aUTrwlbVHtHcD4YOrk7erm7fFg5Bfo7QP5pH/CxEnZDIwg08EEkSZiUQbyiWhMvVYCk/akyVOm5rqZ8WcLcoODa9r0GTNneTDNjsKijTQhUMQnzOGJYVedGzEvpWh+7oKFi8qhccIonbt4itySpebYcisp1vAvA6YuqeXlkyeuKJBlZl65avWMNWvXLZgNinim9RsmentP3KhEioFY1fptsmZm2Oy3Zes2JWDgby8tWtlcNXGHUfbOXUUMzM2791RX7aUgyiFWggtISI4HZnCpDYv27d+0xmcTP7AMYGAEi/NTrzSGWLn9wMEIb59DyVJYPU0dQUaGzYdZrY4cBSZc6hiI1RRIAUn1AMJqFxUFgc4mGZAejs3ux0gFJGcZfvHj60gEJ07CaktiQ5S/4dSG06SBM6YklzCMZABifTCqbjQERkNgNARGQ2A0BEZDYDQERkNgNARGQ2A0BEZDgKIQAAAxs/kWZMDNPAAAAABJRU5ErkJggg=="  # Substitua com o conteúdo base64 real da imagem
    SCENARIO_FILE_PATH = Path("/home/chas/Documents/ufrpe/pesquisa/")  # Substitua com o caminho real do arquivo
    _URL = "http://localhost:3000/create-gif"  # Substitua com a URL real

    image_content = base64.b64decode(_PNG)
    frame_content = SCENARIO_FILE_PATH.joinpath("frame.png").read_bytes()

    test_cases = [
        ("300x200", ["image.png", "frame.png"], 23, False),
        ("500x500", ["image.png", "frame.png"], 100, True),
    ]

    for target_size, images, delay, append_reverted in test_cases:
        data = {
            "targetSize": target_size,
            "delay": delay,
            "appendReverted": str(append_reverted).lower(),
        }
        files = []
        
        if "image.png" in images:
            files.append(("images", ("image.png", io.BytesIO(image_content), "image/png")))
        if "frame.png" in images:
            files.append(("images", ("frame.png", io.BytesIO(frame_content), "image/png")))

        try:
            r = requests.post(url=_URL.format(port=port), files=files, data=data)
            r.raise_for_status()  # Verifica erros HTTP (4xx, 5xx)
        except requests.RequestException as e:
            logger.warning("POST request failed: %s", e)
            return False

        if not (len(r.content) > 3 and r.content[:3] == b"GIF"):
            logger.warning("Response is not a valid GIF")
            return False

        try:
            gif = imageio.get_reader(io.BytesIO(r.content))
            actual_frames = sum(1 for _ in gif)  # Conta os quadros corretamente
        except Exception as e:
            logger.warning("Failed to read GIF: %s", e)
            return False

        expected_frames = len(images) * (2 if append_reverted else 1)
        if actual_frames != expected_frames:
            logger.warning("Expected %d frames, but got %d", expected_frames, actual_frames)
            return False

        logger.info("Got GIF with %d frames", actual_frames)

        # Loop pelos frames para verificar a duração
        gif = imageio.get_reader(io.BytesIO(r.content))  # Reabre para iterar corretamente
        for index, frame in enumerate(gif):
            try:
                frame_meta = gif.get_meta_data()  # Pega metadados globais do GIF
                duration = frame_meta.get("duration", 0) // 10  # Evita KeyError
                logger.info("Frame %d: Duration %d ms", index, duration)
                if duration != delay:
                    logger.warning("Frame duration is incorrect: expected %d, got %d", delay, duration)
                    return False
            except Exception as e:
                logger.warning("Failed to get metadata for frame %d: %s", index, e)
                return False

    return True


# 🔹 Configuração do Logger
logger = logging.getLogger("TestLogger")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

# 🔹 Definir a porta correta
port = "8080"  # Ajuste conforme necessário

# 🔹 Executar a função
result = test_convert_image_and_revert(port=port, logger=logger)

if result:
    print("✅ Teste concluído com sucesso!")
else:
    print("❌ Erro no teste.")